from kink import inject

from src.core.exceptions import (
    BoardNotFoundError,
    OpRequiresImageError,
    ThreadNotFoundError,
)
from src.models.attachment import Attachment
from src.models.post import Post
from src.models.thread import Thread
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.schemas.thread import ThreadCreate
from src.services.ban_service import BanService
from src.services.markup_service import MarkupService
from src.utils.names import parse_name


class ThreadService:
    @inject
    def __init__(
        self,
        thread_repo: ThreadRepository,
        post_repo: PostRepository,
        board_repo: BoardRepository,
        attachment_repo: AttachmentRepository,
        markup: MarkupService,
        ban_service: BanService,
    ) -> None:
        self.thread_repo = thread_repo
        self.post_repo = post_repo
        self.board_repo = board_repo
        self.attachment_repo = attachment_repo
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
        attachments_by_post = {
            post.id: await self.attachment_repo.list_by_post(post.id) for post in posts
        }
        return thread, posts, attachments_by_post

    async def list_threads(
        self, board_slug: str, limit: int = 50, offset: int = 0
    ) -> list[Thread]:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        return await self.thread_repo.list_by_board(board.id, limit, offset)
