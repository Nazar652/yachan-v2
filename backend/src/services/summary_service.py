from kink import inject

from src.core.gemini import GeminiClient
from src.models.post import Post
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.utils.events import THREAD_SUMMARIZED, EventPublisher, thread_channel

# a thread earns its first summary at this many replies, a fresh one every time it
# grows by this much since the last; capped posts keep the prompt (and cost) bounded
MIN_POSTS_FOR_SUMMARY = 10
RESUMMARIZE_GROWTH = 25
MAX_STALE_PER_RUN = 20
MAX_POSTS_IN_PROMPT = 60

_INSTRUCTION = (
    "Summarize this imageboard thread in 2-4 sentences. Capture the main topic and "
    "how the discussion developed. Reply in the same language as the thread, with no "
    "preamble — just the summary.\n\n"
)


def select_posts(posts: list[Post]) -> list[Post]:
    # keep the opening post plus the most recent ones so the summary has context
    # from both ends without blowing up the prompt
    if len(posts) <= MAX_POSTS_IN_PROMPT:
        return posts
    return [posts[0], *posts[-(MAX_POSTS_IN_PROMPT - 1) :]]


def build_prompt(title: str | None, posts: list[Post]) -> str:
    lines = [f"Thread title: {title}"] if title else []
    for post in select_posts(posts):
        if post.body:
            lines.append(f"#{post.post_number}: {post.body}")
    return _INSTRUCTION + "\n".join(lines)


class SummaryService:
    @inject
    def __init__(
        self,
        thread_repo: ThreadRepository,
        post_repo: PostRepository,
        gemini_client: GeminiClient,
        events: EventPublisher,
    ) -> None:
        self.thread_repo = thread_repo
        self.post_repo = post_repo
        self.gemini_client = gemini_client
        self.events = events

    async def stale_thread_ids(self) -> list[int]:
        threads = await self.thread_repo.list_threads_needing_summary(
            min_posts=MIN_POSTS_FOR_SUMMARY, growth=RESUMMARIZE_GROWTH, limit=MAX_STALE_PER_RUN
        )
        return [thread.id for thread in threads]

    async def summarize_thread(self, thread_id: int) -> None:
        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None:
            return
        posts = await self.post_repo.get_thread_posts(thread_id)
        if len(posts) < MIN_POSTS_FOR_SUMMARY:
            return
        summary = await self.gemini_client.generate(build_prompt(thread.title, posts))
        if not summary:
            return
        await self.thread_repo.set_summary(thread_id, summary, thread.reply_count)
        await self.events.publish(
            thread_channel(thread_id),
            THREAD_SUMMARIZED,
            {"thread_id": thread_id, "summary": summary},
        )
