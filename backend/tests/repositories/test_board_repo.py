import pytest

from src.repositories.board_repo import BoardRepository


async def test_get_by_id(session, make_result):
    board = object()
    session.execute.return_value = make_result(one_or_none=board)
    repo = BoardRepository(session=session)

    assert await repo.get_by_id(1) is board


async def test_get_by_slug(session, make_result):
    board = object()
    session.execute.return_value = make_result(one_or_none=board)
    repo = BoardRepository(session=session)

    assert await repo.get_by_slug("b") is board


async def test_list_all(session, make_result):
    boards = [object(), object()]
    session.execute.return_value = make_result(all_=boards)
    repo = BoardRepository(session=session)

    assert await repo.list_all() == boards


async def test_create(session):
    board = object()
    repo = BoardRepository(session=session)

    result = await repo.create(board)

    assert result is board
    session.add.assert_called_once_with(board)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(board)


async def test_create_post_number_sequence(session):
    repo = BoardRepository(session=session)

    await repo.create_post_number_sequence("b")

    session.execute.assert_awaited_once()


async def test_drop_post_number_sequence(session):
    repo = BoardRepository(session=session)

    await repo.drop_post_number_sequence("b")

    session.execute.assert_awaited_once()


async def test_create_sequence_rejects_bad_slug(session):
    repo = BoardRepository(session=session)

    with pytest.raises(ValueError):
        await repo.create_post_number_sequence("bad slug")
    session.execute.assert_not_called()
