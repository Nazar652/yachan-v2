from sqlalchemy.ext.asyncio import AsyncSession

from src.bootstrap.container import setup_di
from src.core.config import Settings
from src.repositories.board_repo import BoardRepository
from src.repositories.post_repo import PostRepository


def test_setup_di_registers_settings_singleton():
    setup_di()
    from kink import di

    assert isinstance(di[Settings], Settings)


def test_setup_di_registers_session_and_repo_factories():
    setup_di()
    from kink import di

    assert AsyncSession in di
    assert PostRepository in di
    assert BoardRepository in di
