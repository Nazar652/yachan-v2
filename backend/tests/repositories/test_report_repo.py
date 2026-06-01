from src.repositories.report_repo import ReportRepository


async def test_get_by_id(session, make_result):
    report = object()
    session.execute.return_value = make_result(one_or_none=report)
    repo = ReportRepository(session=session)

    assert await repo.get_by_id(1) is report


async def test_list_unresolved_without_board(session, make_result):
    reports = [object()]
    session.execute.return_value = make_result(all_=reports)
    repo = ReportRepository(session=session)

    assert await repo.list_unresolved() == reports


async def test_list_unresolved_with_board(session, make_result):
    reports = [object(), object()]
    session.execute.return_value = make_result(all_=reports)
    repo = ReportRepository(session=session)

    assert await repo.list_unresolved(board_id=5) == reports


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
