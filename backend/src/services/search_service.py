import anyio.to_thread
from kink import inject

from src.core.embeddings import EmbeddingModel
from src.core.exceptions import BoardNotFoundError, NotFoundError, ThreadNotFoundError
from src.models.attachment import Attachment
from src.models.post import Post
from src.models.thread import Thread
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.board_repo import BoardRepository
from src.repositories.post_embedding_repo import PostEmbeddingRepository
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.utils.search_text import clean_search_text

SIMILAR_LIMIT = 5
# cosine distance cutoff; starting value, to be tuned against live data
SIMILAR_MAX_DISTANCE = 0.65

SimilarThreadMatch = tuple[Thread, str, Post, list[Attachment], float]


class SearchService:
    @inject
    def __init__(
        self,
        post_repo: PostRepository,
        post_embedding_repo: PostEmbeddingRepository,
        board_repo: BoardRepository,
        thread_repo: ThreadRepository,
        attachment_repo: AttachmentRepository,
        embedding_model: EmbeddingModel,
    ) -> None:
        self.post_repo = post_repo
        self.post_embedding_repo = post_embedding_repo
        self.board_repo = board_repo
        self.thread_repo = thread_repo
        self.attachment_repo = attachment_repo
        self.embedding_model = embedding_model

    async def index_post(self, post_id: int) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if post is None or not post.body:
            return
        vector = self.embedding_model.embed(clean_search_text(post.body))
        await self.post_embedding_repo.upsert(post_id, vector)

    async def index_all(self) -> int:
        posts = await self.post_repo.list_with_body()
        for post in posts:
            vector = self.embedding_model.embed(clean_search_text(post.body or ""))
            await self.post_embedding_repo.upsert(post.id, vector)
        return len(posts)

    async def search(
        self, query: str, *, board_slug: str | None = None, limit: int = 20
    ) -> list[tuple[Post, str, float]]:
        board_id = None
        if board_slug is not None:
            board = await self.board_repo.get_by_slug(board_slug)
            if board is None:
                raise NotFoundError(f"board '{board_slug}' not found")
            board_id = board.id

        cleaned = clean_search_text(query)
        # embedding is blocking cpu work; run it in a thread so the request's event loop stays free
        # (onnxruntime releases the gil during inference)
        vector = await anyio.to_thread.run_sync(self.embedding_model.embed, cleaned)

        # hybrid: `cleaned` also drives a lexical match so posts literally containing the query words
        # rank above cross-lingual semantic neighbours
        return await self.post_embedding_repo.search(
            vector, cleaned, board_id=board_id, limit=limit
        )

    async def similar_threads(self, board_slug: str, thread_id: int) -> list[SimilarThreadMatch]:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None or thread.board_id != board.id:
            raise ThreadNotFoundError(thread_id)

        op_posts = await self.post_repo.get_op_posts_by_thread_ids([thread_id])
        op_post = op_posts.get(thread_id)
        if op_post is None:
            return []

        embedding = await self.post_embedding_repo.get_by_post_id(op_post.id)
        if embedding is None:
            return []

        # cross-board on purpose, same as plain-text search
        matches = await self.post_embedding_repo.similar_threads(
            embedding,
            exclude_thread_id=thread_id,
            limit=SIMILAR_LIMIT,
            max_distance=SIMILAR_MAX_DISTANCE,
        )
        return await self._with_op_images(matches)

    async def similar_threads_for_text(
        self, board_slug: str, text: str
    ) -> list[SimilarThreadMatch]:
        cleaned = clean_search_text(text)
        if not cleaned:
            return []

        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        vector = await anyio.to_thread.run_sync(self.embedding_model.embed, cleaned)

        # duplicate detection is scoped to the board the thread is being created on
        matches = await self.post_embedding_repo.similar_threads(
            vector,
            exclude_thread_id=0,
            board_id=board.id,
            limit=SIMILAR_LIMIT,
            max_distance=SIMILAR_MAX_DISTANCE,
        )
        return await self._with_op_images(matches)

    async def _with_op_images(
        self, matches: list[tuple[Thread, str, Post, float]]
    ) -> list[SimilarThreadMatch]:
        op_post_ids = [op_post.id for _, _, op_post, _ in matches]
        images_by_post_id = await self.attachment_repo.list_images_by_post_ids(op_post_ids)
        return [
            (thread, slug, op_post, images_by_post_id.get(op_post.id, []), distance)
            for thread, slug, op_post, distance in matches
        ]
