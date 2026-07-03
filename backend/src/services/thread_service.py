from kink import inject

from src.core.exceptions import (
    BoardNotFoundError,
    OpRequiresImageError,
    ThreadNotFoundError,
)
from src.core.storage import Storage
from src.models.attachment import Attachment
from src.models.post import Post
from src.models.thread import Thread
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.board_repo import BoardRepository
from src.repositories.post_backlink_repo import PostBacklinkRepository
from src.repositories.post_edit_repo import PostEditRepository
from src.repositories.post_repo import PostRepository
from src.repositories.report_repo import ReportRepository
from src.repositories.thread_repo import ThreadRepository
from src.schemas.thread import ThreadCreate
from src.services.ban_service import BanService
from src.services.markup_service import MarkupService
from src.utils.names import parse_name

ThreadWithPreview = tuple[Thread, Post | None, list[Attachment], list[Post]]
LatestThreadPreview = tuple[Thread, str, Attachment | None, Post | None]


class ThreadService:
    @inject
    def __init__(
        self,
        thread_repo: ThreadRepository,
        post_repo: PostRepository,
        board_repo: BoardRepository,
        attachment_repo: AttachmentRepository,
        backlink_repo: PostBacklinkRepository,
        post_edit_repo: PostEditRepository,
        report_repo: ReportRepository,
        storage: Storage,
        markup: MarkupService,
        ban_service: BanService,
    ) -> None:
        self.thread_repo = thread_repo
        self.post_repo = post_repo
        self.board_repo = board_repo
        self.attachment_repo = attachment_repo
        self.backlink_repo = backlink_repo
        self.post_edit_repo = post_edit_repo
        self.report_repo = report_repo
        self.storage = storage
        self.markup = markup
        self.ban_service = ban_service

    async def create_thread(
        self, board_slug: str, data: ThreadCreate, ip_hash: str, has_image: bool
    ) -> tuple[Thread, Post]:
        if not has_image:
            raise OpRequiresImageError("a new thread requires an image")

        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        await self.ban_service.assert_not_banned(ip_hash, board.id)

        thread = await self.thread_repo.create(
            Thread(board_id=board.id, title=data.title)
        )
        name, tripcode = parse_name(data.name)
        op_post = await self.post_repo.create(
            Post(
                post_number=await self.post_repo.next_post_number(board_slug),
                thread_id=thread.id,
                board_id=board.id,
                name=name,
                tripcode=tripcode,
                body=data.body,
                body_html=self.markup.render(data.body),
                sage=data.sage,
                is_op=True,
                ip_hash=ip_hash,
            )
        )
        return thread, op_post

    async def get_thread_detail(
        self, board_slug: str, thread_id: int
    ) -> tuple[Thread, list[Post], dict[int, list[Attachment]]]:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None or thread.board_id != board.id:
            raise ThreadNotFoundError(thread_id)

        posts = await self.post_repo.get_thread_posts(thread_id)
        post_ids = [post.id for post in posts]

        attachments_by_post = await self.attachment_repo.list_by_post_ids(post_ids)
        return thread, posts, attachments_by_post

    async def delete_thread(self, board_slug: str, thread_id: int) -> Thread:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None or thread.board_id != board.id:
            raise ThreadNotFoundError(thread_id)

        post_ids = await self.post_repo.list_ids_by_thread(thread_id)
        attachments = await self.attachment_repo.list_by_thread(thread_id)

        # drop every child row first; nothing here cascades at the db level
        await self.backlink_repo.delete_by_post_ids(post_ids)
        await self.post_edit_repo.delete_by_post_ids(post_ids)
        await self.report_repo.delete_by_post_ids(post_ids)
        await self.attachment_repo.delete_by_post_ids(post_ids)
        await self.post_repo.delete_by_thread(thread_id)
        await self.thread_repo.delete(thread_id)
        # make the deletes visible to the orphan check below
        await self.thread_repo.flush()

        await self._delete_orphaned_blobs(attachments)

        return thread

    async def _delete_orphaned_blobs(self, attachments: list[Attachment]) -> None:
        # files are deduped by md5, so a blob is only removed once no surviving
        # attachment references it; thumbnails share the same md5 as their blob
        thumbnails_by_path: dict[str, str | None] = {}
        for attachment in attachments:
            thumbnails_by_path.setdefault(attachment.file_path, attachment.thumbnail_path)

        for file_path, thumbnail_path in thumbnails_by_path.items():
            if await self.attachment_repo.count_by_file_path(file_path) > 0:
                continue
            await self.storage.delete(file_path)
            if thumbnail_path is not None:
                await self.storage.delete(thumbnail_path)

    async def list_threads(
        self, board_slug: str, limit: int = 50, offset: int = 0
    ) -> list[ThreadWithPreview]:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        threads = await self.thread_repo.list_by_board(board.id, limit, offset)
        thread_ids = [t.id for t in threads]

        op_posts = await self.post_repo.get_op_posts_by_thread_ids(thread_ids)
        op_post_ids = [p.id for p in op_posts.values()]
        op_images = await self.attachment_repo.list_images_by_post_ids(op_post_ids)
        last_replies = await self.post_repo.get_last_replies_by_thread_ids(thread_ids)

        result: list[ThreadWithPreview] = []
        for thread in threads:
            op_post = op_posts.get(thread.id)
            images = op_images.get(op_post.id, []) if op_post else []
            replies = last_replies.get(thread.id, [])
            result.append((thread, op_post, images, replies))
        return result

    async def list_latest_threads(self, limit: int = 5) -> list[LatestThreadPreview]:
        threads = await self.thread_repo.list_latest(limit)
        thread_ids = [t.id for t in threads]

        boards = await self.board_repo.list_all()
        slug_by_board_id = {board.id: board.slug for board in boards}

        op_posts = await self.post_repo.get_op_posts_by_thread_ids(thread_ids)
        op_post_ids = [p.id for p in op_posts.values()]
        first_images = await self.attachment_repo.get_first_images_by_post_ids(op_post_ids)
        last_replies = await self.post_repo.get_last_replies_by_thread_ids(
            thread_ids, limit_per_thread=1
        )

        result: list[LatestThreadPreview] = []
        for thread in threads:
            op_post = op_posts.get(thread.id)
            first_image = first_images.get(op_post.id) if op_post else None
            replies = last_replies.get(thread.id, [])
            result.append(
                (
                    thread,
                    slug_by_board_id.get(thread.board_id, ""),
                    first_image,
                    replies[0] if replies else None,
                )
            )
        return result
