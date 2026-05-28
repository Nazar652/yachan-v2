from src.repositories.post_edit_repo import PostEditRepository


async def test_get_by_post_id(session, make_result):
    edit = object()
    session.execute.return_value = make_result(one_or_none=edit)
    repo = PostEditRepository(session=session)

    assert await repo.get_by_post_id(3) is edit
    session.execute.assert_awaited_once()


async def test_get_by_post_id_none(session, make_result):
    session.execute.return_value = make_result(one_or_none=None)
    repo = PostEditRepository(session=session)

    assert await repo.get_by_post_id(3) is None


async def test_create(session):
    edit = object()
    repo = PostEditRepository(session=session)

    result = await repo.create(edit)

    assert result is edit
    session.add.assert_called_once_with(edit)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(edit)
