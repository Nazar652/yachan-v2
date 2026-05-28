from src.repositories.attachment_repo import AttachmentRepository


async def test_get_by_id(session, make_result):
    att = object()
    session.execute.return_value = make_result(one_or_none=att)
    repo = AttachmentRepository(session=session)

    assert await repo.get_by_id(1) is att


async def test_get_by_md5(session, make_result):
    att = object()
    session.execute.return_value = make_result(one_or_none=att)
    repo = AttachmentRepository(session=session)

    assert await repo.get_by_md5("d41d8cd98f00b204e9800998ecf8427e") is att


async def test_list_by_post(session, make_result):
    atts = [object()]
    session.execute.return_value = make_result(all_=atts)
    repo = AttachmentRepository(session=session)

    assert await repo.list_by_post(5) == atts


async def test_create(session):
    att = object()
    repo = AttachmentRepository(session=session)

    result = await repo.create(att)

    assert result is att
    session.add.assert_called_once_with(att)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(att)


async def test_set_media_info(session):
    repo = AttachmentRepository(session=session)

    await repo.set_media_info(
        1, thumbnail_path="t.jpg", width=10, height=20, duration_seconds=None
    )

    session.execute.assert_awaited_once()
