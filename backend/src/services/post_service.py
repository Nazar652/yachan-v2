from datetime import timedelta

from kink import inject

from src.core.clock import utcnow
from src.core.exceptions import (
    BoardNotFoundError,
    EditWindowExpiredError,
    NotPostAuthorError,
    PostAlreadyEditedError,
    PostNotFoundError,
    ThreadLockedError,
    ThreadNotFoundError,
)
from src.core.names import parse_name
from src.models.post import Post
from src.models.post_backlink import PostBacklink
from src.models.post_edit import PostEdit
from src.repositories.board_repo import BoardRepository
from src.repositories.post_backlink_repo import PostBacklinkRepository
from src.repositories.post_edit_repo import PostEditRepository
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.schemas.post import PostCreate, PostEditCreate
from src.services.ban_service import BanService
from src.services.markup_service import MarkupService

EDIT_WINDOW = timedelta(minutes=30)


@inject
class PostService:
    def __init__(
        self,
        post_repo: PostRepository,
        post_edit_repo: PostEditRepository,
        thread_repo: ThreadRepository,
        board_repo: BoardRepository,
        backlink_repo: PostBacklinkRepository,
        markup: MarkupService,
        ban_service: BanService,
    ) -> None:
        self.post_repo = post_repo
        self.post_edit_repo = post_edit_repo
        self.thread_repo = thread_repo
        self.board_repo = board_repo
        self.backlink_repo = backlink_repo
        self.markup = markup
        self.ban_service = ban_service

    async def create_reply(
        self, board_slug: str, thread_id: int, data: PostCreate, ip_hash: str
    ) -> Post:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None or thread.board_id != board.id:
            raise ThreadNotFoundError(thread_id)
        if thread.is_locked:
            raise ThreadLockedError(thread_id)

        await self.ban_service.assert_not_banned(ip_hash, board.id)

        name, tripcode = parse_name(data.name)
        post = await self.post_repo.create(
            Post(
                post_number=await self.post_repo.next_post_number(board_slug),
                thread_id=thread_id,
                board_id=board.id,
                name=name,
                tripcode=tripcode,
                body=data.body,
                body_html=self.markup.render(data.body),
                sage=data.sage,
                is_op=False,
                ip_hash=ip_hash,
            )
        )

        await self._store_backlinks(board.id, post.id, data.body)

        # bump the thread unless the poster saged or the bump limit is reached
        await self.thread_repo.increment_reply_count(thread_id)
        if not data.sage and thread.reply_count + 1 <= board.bump_limit:
            await self.thread_repo.update_bump_at(thread_id)

        return post

    async def edit_post(
        self, board_slug: str, post_number: int, data: PostEditCreate, ip_hash: str
    ) -> Post:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        post = await self.post_repo.get_by_board_and_number(board.id, post_number)
        if post is None:
            raise PostNotFoundError(post_number)
        if post.ip_hash != ip_hash:
            raise NotPostAuthorError()
        if post.is_edited:
            raise PostAlreadyEditedError()
        if utcnow() - post.created_at > EDIT_WINDOW:
            raise EditWindowExpiredError()

        # keep the original around before overwriting
        await self.post_edit_repo.create(
            PostEdit(
                post_id=post.id,
                original_body=post.body,
                original_body_html=post.body_html,
            )
        )
        return await self.post_repo.mark_edited(
            post.id, data.new_body, self.markup.render(data.new_body)
        )

    async def get_post(self, board_slug: str, post_number: int) -> Post:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        post = await self.post_repo.get_by_board_and_number(board.id, post_number)
        if post is None:
            raise PostNotFoundError(post_number)
        return post

    async def get_post_history(self, board_slug: str, post_number: int) -> PostEdit | None:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        post = await self.post_repo.get_by_board_and_number(board.id, post_number)
        if post is None:
            raise PostNotFoundError(post_number)

        return await self.post_edit_repo.get_by_post_id(post.id)

    async def _store_backlinks(self, board_id: int, source_post_id: int, body: str | None) -> None:
        links = []
        for ref in self.markup.extract_refs(body):
            target = await self.post_repo.get_by_board_and_number(board_id, ref)
            if target is not None and target.id != source_post_id:
                links.append(
                    PostBacklink(source_post_id=source_post_id, target_post_id=target.id)
                )
        if links:
            await self.backlink_repo.create_many(links)
