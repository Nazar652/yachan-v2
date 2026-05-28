from src.core.clock import utcnow
from src.repositories.ban_repo import BanRepository


async def test_get_active_for_ip_returns_first(session, make_result):
    ban = object()
    session.execute.return_value = make_result(first=ban)
    repo = BanRepository(session=session)

    result = await repo.get_active_for_ip("hash", board_id=1, now=utcnow())

    assert result is ban
    session.execute.assert_awaited_once()


async def test_get_active_for_ip_none(session, make_result):
    session.execute.return_value = make_result(first=None)
    repo = BanRepository(session=session)

    result = await repo.get_active_for_ip("hash", board_id=None, now=utcnow())

    assert result is None


async def test_list_active(session, make_result):
    bans = [object(), object()]
    session.execute.return_value = make_result(all_=bans)
    repo = BanRepository(session=session)

    assert await repo.list_active() == bans


async def test_create(session):
    ban = object()
    repo = BanRepository(session=session)

    result = await repo.create(ban)

    assert result is ban
    session.add.assert_called_once_with(ban)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(ban)


async def test_deactivate(session):
    repo = BanRepository(session=session)
    await repo.deactivate(1)
    session.execute.assert_awaited_once()


async def test_deactivate_expired_returns_rowcount(session, make_result):
    session.execute.return_value = make_result(rowcount=3)
    repo = BanRepository(session=session)

    assert await repo.deactivate_expired(utcnow()) == 3
