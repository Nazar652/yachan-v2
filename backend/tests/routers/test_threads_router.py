from src.routers.threads import thread_create_from_form


def test_thread_create_from_form_defaults():
    data = thread_create_from_form()
    assert data.title is None
    assert data.name is None
    assert data.body is None
    assert data.sage is False


def test_thread_create_from_form_maps_fields():
    data = thread_create_from_form(
        title="topic",
        name="anon",
        body="first post",
        sage=True,
    )
    assert data.title == "topic"
    assert data.name == "anon"
    assert data.body == "first post"
    assert data.sage is True
