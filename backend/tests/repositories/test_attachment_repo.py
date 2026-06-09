from src.repositories.attachment_repo import AttachmentRepository


async def test_get_by_id(session, make_result):
    attachment = object()
    session.execute.return_value = make_result(one_or_none=attachment)
    repo = AttachmentRepository(session=session)

    assert await repo.get_by_id(1) is attachment


async def test_get_by_md5(session, make_result):
    attachment = object()
    session.execute.return_value = make_result(one_or_none=attachment)
    repo = AttachmentRepository(session=session)

    assert await repo.get_by_md5("d41d8cd98f00b204e9800998ecf8427e") is attachment


async def test_get_first_images_by_post_ids_returns_dict(session, make_result):
    from types import SimpleNamespace

    att = SimpleNamespace(post_id=10)
    session.execute.return_value = make_result(all_=[att])
    repo = AttachmentRepository(session=session)

    result = await repo.get_first_images_by_post_ids([10])

    assert result == {10: att}
    session.execute.assert_awaited_once()


async def test_get_first_images_by_post_ids_empty_input(session):
    repo = AttachmentRepository(session=session)

    result = await repo.get_first_images_by_post_ids([])

    assert result == {}
    session.execute.assert_not_awaited()


async def test_list_by_post_ids_groups_by_post(session, make_result):
    from types import SimpleNamespace

    att1 = SimpleNamespace(post_id=1)
    att2 = SimpleNamespace(post_id=2)
    att3 = SimpleNamespace(post_id=1)
    session.execute.return_value = make_result(all_=[att1, att2, att3])
    repo = AttachmentRepository(session=session)

    result = await repo.list_by_post_ids([1, 2])

    assert result == {1: [att1, att3], 2: [att2]}
    session.execute.assert_awaited_once()


async def test_list_by_post_ids_empty_input(session):
    repo = AttachmentRepository(session=session)

    result = await repo.list_by_post_ids([])

    assert result == {}
    session.execute.assert_not_awaited()


async def test_list_by_post(session, make_result):
    attachments = [object()]
    session.execute.return_value = make_result(all_=attachments)
    repo = AttachmentRepository(session=session)

    assert await repo.list_by_post(5) == attachments


async def test_create(session):
    attachment = object()
    repo = AttachmentRepository(session=session)

    result = await repo.create(attachment)

    assert result is attachment
    session.add.assert_called_once_with(attachment)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(attachment)


async def test_set_media_info(session):
    repo = AttachmentRepository(session=session)

    await repo.set_media_info(
        1, thumbnail_path="t.jpg", width=10, height=20, duration_seconds=None
    )

    session.execute.assert_awaited_once()
