from src.repositories.mod_account_repo import ModAccountRepository


async def test_get_by_id(session, make_result):
    account = object()
    session.execute.return_value = make_result(one_or_none=account)
    repo = ModAccountRepository(session=session)

    assert await repo.get_by_id(1) is account


async def test_get_by_username(session, make_result):
    account = object()
    session.execute.return_value = make_result(one_or_none=account)
    repo = ModAccountRepository(session=session)

    assert await repo.get_by_username("admin") is account


async def test_get_by_username_none(session, make_result):
    session.execute.return_value = make_result(one_or_none=None)
    repo = ModAccountRepository(session=session)

    assert await repo.get_by_username("nope") is None


async def test_create(session):
    account = object()
    repo = ModAccountRepository(session=session)

    result = await repo.create(account)

    assert result is account
    session.add.assert_called_once_with(account)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(account)
