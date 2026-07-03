from kink import di
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import new_session
from src.core.embeddings import EmbeddingModel, get_embedding_model
from src.core.gemini import GeminiClient
from src.core.redis import get_redis
from src.core.storage import Storage, build_storage
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.ban_repo import BanRepository
from src.repositories.board_repo import BoardRepository
from src.repositories.mod_account_repo import ModAccountRepository
from src.repositories.post_backlink_repo import PostBacklinkRepository
from src.repositories.post_edit_repo import PostEditRepository
from src.repositories.post_embedding_repo import PostEmbeddingRepository
from src.repositories.post_repo import PostRepository
from src.repositories.report_repo import ReportRepository
from src.repositories.thread_repo import ThreadRepository
from src.services.ban_service import BanService
from src.services.board_service import BoardService
from src.services.captcha_service import CaptchaService
from src.services.file_service import FileService
from src.services.markup_service import MarkupService
from src.services.mod_service import ModService
from src.services.moderation_service import ModerationService
from src.services.post_service import PostService
from src.services.report_service import ReportService
from src.services.search_service import SearchService
from src.services.stats_service import StatsService
from src.services.summary_service import SummaryService
from src.services.thread_service import ThreadService
from src.utils.events import EventPublisher
from src.utils.markup import MarkupRenderer
from src.utils.online import OnlineTracker
from src.utils.rate_limit import RateLimiter
from src.views.boards_view import BoardsView
from src.views.captcha_view import CaptchaView
from src.views.mod_view import ModView
from src.views.posts_view import PostsView
from src.views.reports_view import ReportsView
from src.views.search_view import SearchView
from src.views.stats_view import StatsView
from src.views.threads_view import ThreadsView
from src.views.ws_view import WsView


from .scope import resolve_scoped


def setup_di() -> None:
    settings = get_settings()
    di[Settings] = settings

    di[MarkupRenderer] = MarkupRenderer()
    di[Storage] = build_storage(settings)
    redis_instance = get_redis()
    di[Redis] = redis_instance
    di[RateLimiter] = RateLimiter(redis_instance)
    di[EventPublisher] = EventPublisher(redis_instance)
    di[OnlineTracker] = OnlineTracker(redis_instance)

    # the embedding model is a process-wide singleton loaded lazily on first use
    # (get_embedding_model is lru_cached), so startup does not pay the model load
    di.factories[EmbeddingModel] = lambda container: get_embedding_model()

    di[GeminiClient] = GeminiClient.from_settings(settings)

    di.factories[AsyncSession] = lambda container: resolve_scoped(AsyncSession, factory=new_session)

    di.factories[BoardRepository] = lambda container: resolve_scoped(BoardRepository, BoardRepository)
    di.factories[ThreadRepository] = lambda container: resolve_scoped(ThreadRepository, ThreadRepository)
    di.factories[PostRepository] = lambda container: resolve_scoped(PostRepository, PostRepository)
    di.factories[PostEditRepository] = lambda container: resolve_scoped(PostEditRepository, PostEditRepository)
    di.factories[PostBacklinkRepository] = lambda container: resolve_scoped(
        PostBacklinkRepository, PostBacklinkRepository
    )
    di.factories[PostEmbeddingRepository] = lambda container: resolve_scoped(
        PostEmbeddingRepository, PostEmbeddingRepository
    )
    di.factories[AttachmentRepository] = lambda container: resolve_scoped(AttachmentRepository, AttachmentRepository)
    di.factories[BanRepository] = lambda container: resolve_scoped(BanRepository, BanRepository)
    di.factories[ReportRepository] = lambda container: resolve_scoped(ReportRepository, ReportRepository)
    di.factories[ModAccountRepository] = lambda container: resolve_scoped(ModAccountRepository, ModAccountRepository)

    di.factories[MarkupService] = lambda container: resolve_scoped(MarkupService, MarkupService)
    di.factories[BanService] = lambda container: resolve_scoped(BanService, BanService)
    di.factories[BoardService] = lambda container: resolve_scoped(BoardService, BoardService)
    di.factories[ThreadService] = lambda container: resolve_scoped(ThreadService, ThreadService)
    di.factories[PostService] = lambda container: resolve_scoped(PostService, PostService)
    di.factories[FileService] = lambda container: resolve_scoped(FileService, FileService)
    di.factories[ReportService] = lambda container: resolve_scoped(ReportService, ReportService)
    di.factories[CaptchaService] = lambda container: resolve_scoped(CaptchaService, CaptchaService)
    di.factories[ModService] = lambda container: resolve_scoped(ModService, ModService)
    di.factories[ModerationService] = lambda container: resolve_scoped(
        ModerationService, ModerationService
    )
    di.factories[StatsService] = lambda container: resolve_scoped(StatsService, StatsService)
    di.factories[SearchService] = lambda container: resolve_scoped(SearchService, SearchService)
    di.factories[SummaryService] = lambda container: resolve_scoped(SummaryService, SummaryService)

    di.factories[BoardsView] = lambda container: resolve_scoped(BoardsView, BoardsView)
    di.factories[CaptchaView] = lambda container: resolve_scoped(CaptchaView, CaptchaView)
    di.factories[ModView] = lambda container: resolve_scoped(ModView, ModView)
    di.factories[ThreadsView] = lambda container: resolve_scoped(ThreadsView, ThreadsView)
    di.factories[PostsView] = lambda container: resolve_scoped(PostsView, PostsView)
    di.factories[ReportsView] = lambda container: resolve_scoped(ReportsView, ReportsView)
    di.factories[StatsView] = lambda container: resolve_scoped(StatsView, StatsView)
    di.factories[SearchView] = lambda container: resolve_scoped(SearchView, SearchView)
    di.factories[WsView] = lambda container: resolve_scoped(WsView, WsView)


def get_dependency[T](cls: type[T]) -> T:
    return di[cls]
