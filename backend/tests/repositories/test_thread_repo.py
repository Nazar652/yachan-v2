from src.repositories.thread_repo import ThreadRepository


async def test_get_by_id(session, make_result):
    thread = object()
    session.execute.return_value = make_result(one_or_none=thread)
    repo = ThreadRepository(session=session)

    assert await repo.get_by_id(1) is thread


async def test_list_by_board(session, make_result):
    threads = [object(), object()]
    session.execute.return_value = make_result(all_=threads)
    repo = ThreadRepository(session=session)

    assert await repo.list_by_board(1, limit=10, offset=0) == threads


async def test_list_latest(session, make_result):
    threads = [object(), object()]
    session.execute.return_value = make_result(all_=threads)
    repo = ThreadRepository(session=session)

    assert await repo.list_latest(limit=2) == threads


async def test_count_by_board(session, make_result):
    result = make_result()
    result.all.return_value = [(1, 4), (2, 9)]
    session.execute.return_value = result
    repo = ThreadRepository(session=session)

    assert await repo.count_by_board() == {1: 4, 2: 9}


async def test_create(session):
    thread = object()
    repo = ThreadRepository(session=session)

    result = await repo.create(thread)

    assert result is thread
    session.add.assert_called_once_with(thread)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(thread)


async def test_set_reply_count(session):
    repo = ThreadRepository(session=session)
    await repo.set_reply_count(1, 7)
    session.execute.assert_awaited_once()


async def test_update_bump_at(session):
    repo = ThreadRepository(session=session)
    await repo.update_bump_at(1)
    session.execute.assert_awaited_once()


async def test_set_locked(session):
    repo = ThreadRepository(session=session)
    await repo.set_locked(1, True)
    session.execute.assert_awaited_once()


async def test_set_sticky(session):
    repo = ThreadRepository(session=session)
    await repo.set_sticky(1, True)
    session.execute.assert_awaited_once()
