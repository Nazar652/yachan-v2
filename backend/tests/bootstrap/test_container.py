from sqlalchemy.ext.asyncio import AsyncSession
from src.bootstrap.container import setup_di
from src.core.config import Settings
from src.core.storage import LocalStorage
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository
from src.utils.markup import MarkupRenderer


def test_setup_di_registers_settings_singleton():
    setup_di()
    from kink import di

    assert isinstance(di[Settings], Settings)


def test_setup_di_registers_core_singletons():
    setup_di()
    from kink import di

    assert isinstance(di[MarkupRenderer], MarkupRenderer)
    assert isinstance(di[LocalStorage], LocalStorage)


def test_setup_di_registers_session_and_repo_factories():
    setup_di()
    from kink import di

    assert AsyncSession in di
    assert PostRepository in di
    assert BoardRepository in di
