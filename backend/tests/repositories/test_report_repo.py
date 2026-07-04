from unittest.mock import MagicMock

from src.repositories.report_repo import ReportRepository


async def test_get_by_id(session, make_result):
    report = object()
    session.execute.return_value = make_result(one_or_none=report)
    repo = ReportRepository(session=session)

    assert await repo.get_by_id(1) is report


async def test_list_unresolved_without_board(session):
    report = object()
    result = MagicMock()
    result.all.return_value = [(report, 3, 5, "b")]
    session.execute.return_value = result
    repo = ReportRepository(session=session)

    assert await repo.list_unresolved() == [(report, 3, 5, "b")]


async def test_list_unresolved_with_board(session):
    result = MagicMock()
    result.all.return_value = []
    session.execute.return_value = result
    repo = ReportRepository(session=session)

    assert await repo.list_unresolved(board_id=5) == []


async def test_create(session):
    report = object()
    repo = ReportRepository(session=session)

    result = await repo.create(report)

    assert result is report
    session.add.assert_called_once_with(report)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(report)


async def test_mark_resolved(session):
    repo = ReportRepository(session=session)
    await repo.mark_resolved(1, resolved_by=2)
    session.execute.assert_awaited_once()


async def test_count_unresolved_for_post(session, make_result):
    session.execute.return_value = make_result(one=4)
    repo = ReportRepository(session=session)

    assert await repo.count_unresolved_for_post(7) == 4


async def test_count_unresolved_for_post_by_ip(session, make_result):
    session.execute.return_value = make_result(one=2)
    repo = ReportRepository(session=session)

    assert await repo.count_unresolved_for_post_by_ip(7, "iphash") == 2


async def test_count_auto_for_post(session, make_result):
    session.execute.return_value = make_result(one=1)
    repo = ReportRepository(session=session)

    assert await repo.count_auto_for_post(7) == 1


async def test_delete_by_post_ids(session):
    repo = ReportRepository(session=session)

    await repo.delete_by_post_ids([1, 2])

    session.execute.assert_awaited_once()


async def test_delete_by_post_ids_empty_input(session):
    repo = ReportRepository(session=session)

    await repo.delete_by_post_ids([])

    session.execute.assert_not_awaited()
