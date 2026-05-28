from kink import di
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import new_session
from src.core.markup import MarkupRenderer
from src.core.storage import LocalStorage
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.ban_repo import BanRepository
from src.repositories.board_repo import BoardRepository
from src.repositories.mod_account_repo import ModAccountRepository
from src.repositories.post_backlink_repo import PostBacklinkRepository
from src.repositories.post_edit_repo import PostEditRepository
from src.repositories.post_repo import PostRepository
from src.repositories.report_repo import ReportRepository
from src.repositories.thread_repo import ThreadRepository

from .scope import resolve_scoped


def setup_di() -> None:
    settings = get_settings()
    di[Settings] = settings

    # stateless singletons, shared across all requests
    di[MarkupRenderer] = MarkupRenderer()
    di[LocalStorage] = LocalStorage(settings)

    # one AsyncSession per request, shared by every repository in that request
    # so they all run inside the same transaction
    di[AsyncSession] = lambda container: resolve_scoped(AsyncSession, factory=new_session)

    # passing the class itself as factory works because kink's @inject fires when
    # the factory is called, injecting AsyncSession from the scope above
    di[BoardRepository] = lambda container: resolve_scoped(BoardRepository, BoardRepository)
    di[ThreadRepository] = lambda container: resolve_scoped(ThreadRepository, ThreadRepository)
    di[PostRepository] = lambda container: resolve_scoped(PostRepository, PostRepository)
    di[PostEditRepository] = lambda container: resolve_scoped(PostEditRepository, PostEditRepository)
    di[PostBacklinkRepository] = lambda container: resolve_scoped(PostBacklinkRepository, PostBacklinkRepository)
    di[AttachmentRepository] = lambda container: resolve_scoped(AttachmentRepository, AttachmentRepository)
    di[BanRepository] = lambda container: resolve_scoped(BanRepository, BanRepository)
    di[ReportRepository] = lambda container: resolve_scoped(ReportRepository, ReportRepository)
    di[ModAccountRepository] = lambda container: resolve_scoped(ModAccountRepository, ModAccountRepository)
