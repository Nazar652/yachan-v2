from src.repositories.post_backlink_repo import PostBacklinkRepository


async def test_list_sources_for_target(session, make_result):
    links = [object(), object()]
    session.execute.return_value = make_result(all_=links)
    repo = PostBacklinkRepository(session=session)

    assert await repo.list_sources_for_target(10) == links


async def test_list_targets_for_source(session, make_result):
    links = [object()]
    session.execute.return_value = make_result(all_=links)
    repo = PostBacklinkRepository(session=session)

    assert await repo.list_targets_for_source(5) == links


async def test_create_many_adds_all_and_flushes(session):
    links = [object(), object()]
    repo = PostBacklinkRepository(session=session)

    await repo.create_many(links)

    session.add_all.assert_called_once_with(links)
    session.flush.assert_awaited_once()
