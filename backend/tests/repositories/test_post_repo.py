from src.repositories.post_repo import PostRepository


async def test_get_by_id_returns_scalar(session, make_result):
    post = object()
    session.execute.return_value = make_result(one_or_none=post)
    repo = PostRepository(session=session)

    assert await repo.get_by_id(1) is post
    session.execute.assert_awaited_once()


async def test_get_by_id_returns_none(session, make_result):
    session.execute.return_value = make_result(one_or_none=None)
    repo = PostRepository(session=session)

    assert await repo.get_by_id(999) is None


async def test_get_by_board_and_number(session, make_result):
    post = object()
    session.execute.return_value = make_result(one_or_none=post)
    repo = PostRepository(session=session)

    assert await repo.get_by_board_and_number(1, 42) is post
    session.execute.assert_awaited_once()


async def test_get_thread_posts_returns_list(session, make_result):
    posts = [object(), object()]
    session.execute.return_value = make_result(all_=posts)
    repo = PostRepository(session=session)

    assert await repo.get_thread_posts(7) == posts


async def test_next_post_number_returns_sequence_value(session, make_result):
    session.execute.return_value = make_result(one=101)
    repo = PostRepository(session=session)

    assert await repo.next_post_number("b") == 101
    session.execute.assert_awaited_once()


async def test_create_adds_flushes_refreshes(session):
    post = object()
    repo = PostRepository(session=session)

    result = await repo.create(post)

    assert result is post
    session.add.assert_called_once_with(post)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(post)


async def test_mark_edited_updates_then_returns_fresh(session, make_result):
    edited = object()
    session.execute.side_effect = [make_result(), make_result(one=edited)]
    repo = PostRepository(session=session)

    result = await repo.mark_edited(5, "new body", "<p>new body</p>")

    assert result is edited
    assert session.execute.await_count == 2
    session.flush.assert_awaited_once()


async def test_soft_delete_executes_update(session):
    repo = PostRepository(session=session)

    await repo.soft_delete(5, deleted_by=2)

    session.execute.assert_awaited_once()
