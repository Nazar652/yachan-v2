import anyio.to_thread
import jwt
from kink import inject

from src.core.config import Settings
from src.core.exceptions import (
    BoardNotFoundError,
    InvalidCredentialsError,
    ModAccountExistsError,
    ModInactiveError,
    PostNotFoundError,
    ThreadNotFoundError,
)
from src.models.ban import Ban
from src.models.mod_account import ModAccount, ModRole
from src.models.post import Post
from src.models.thread import Thread
from src.repositories.board_repo import BoardRepository
from src.repositories.mod_account_repo import ModAccountRepository
from src.repositories.post_repo import PostRepository
from src.repositories.thread_repo import ThreadRepository
from src.schemas.mod import BanCreate
from src.services.ban_service import BanService
from src.utils.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class ModService:
    @inject
    def __init__(
        self,
        mod_account_repo: ModAccountRepository,
        post_repo: PostRepository,
        thread_repo: ThreadRepository,
        board_repo: BoardRepository,
        ban_service: BanService,
        settings: Settings,
    ) -> None:
        self.mod_account_repo = mod_account_repo
        self.post_repo = post_repo
        self.thread_repo = thread_repo
        self.board_repo = board_repo
        self.ban_service = ban_service
        self.settings = settings

    async def create_account(
        self, username: str, password: str, role: ModRole
    ) -> ModAccount:
        if await self.mod_account_repo.get_by_username(username) is not None:
            raise ModAccountExistsError(username)
        password_hash = await anyio.to_thread.run_sync(hash_password, password)
        return await self.mod_account_repo.create(
            ModAccount(username=username, password_hash=password_hash, role=role)
        )

    async def authenticate(self, username: str, password: str) -> tuple[str, ModRole]:
        account = await self.mod_account_repo.get_by_username(username)
        if account is None:
            raise InvalidCredentialsError()

        if not await anyio.to_thread.run_sync(verify_password, password, account.password_hash):
            raise InvalidCredentialsError()
        if not account.is_active:
            raise ModInactiveError()
        return create_access_token(str(account.id), self.settings), account.role

    async def resolve_mod(self, token: str) -> ModAccount:
        try:
            payload = decode_access_token(token, self.settings)
        except jwt.InvalidTokenError as error:
            raise InvalidCredentialsError() from error
        account = await self.mod_account_repo.get_by_id(int(payload["sub"]))
        if account is None or not account.is_active:
            raise ModInactiveError()
        return account

    async def is_admin(self, token: str | None) -> bool:
        if token is None:
            return False
        account = await self.resolve_mod(token)
        return account.role == ModRole.ADMIN

    async def delete_post(self, board_slug: str, post_number: int, mod: ModAccount) -> None:
        post = await self._require_post(board_slug, post_number)
        await self.post_repo.soft_delete(post.id, deleted_by=mod.id)
        reply_count = await self.post_repo.count_replies(post.thread_id)
        await self.thread_repo.set_reply_count(post.thread_id, reply_count)

    async def set_thread_locked(
        self, board_slug: str, thread_id: int, locked: bool
    ) -> Thread:
        thread = await self._require_thread(board_slug, thread_id)
        await self.thread_repo.set_locked(thread.id, locked)
        thread.is_locked = locked
        return thread

    async def set_thread_sticky(
        self, board_slug: str, thread_id: int, sticky: bool
    ) -> Thread:
        thread = await self._require_thread(board_slug, thread_id)
        await self.thread_repo.set_sticky(thread.id, sticky)
        thread.is_sticky = sticky
        return thread

    async def ban_poster(
        self, board_slug: str, post_number: int, data: BanCreate, mod: ModAccount
    ) -> Ban:
        post = await self._require_post(board_slug, post_number)
        return await self.ban_service.create_ban(
            ip_hash=post.ip_hash,
            board_id=data.board_id,
            reason=data.reason,
            expires_at=data.expires_at,
            created_by=mod.id,
        )

    async def _require_post(self, board_slug: str, post_number: int) -> Post:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        post = await self.post_repo.get_by_board_and_number(board.id, post_number)
        if post is None:
            raise PostNotFoundError(post_number)
        return post

    async def _require_thread(self, board_slug: str, thread_id: int) -> Thread:
        board = await self.board_repo.get_by_slug(board_slug)
        if board is None:
            raise BoardNotFoundError(board_slug)

        thread = await self.thread_repo.get_by_id(thread_id)
        if thread is None or thread.board_id != board.id:
            raise ThreadNotFoundError(thread_id)
        return thread
