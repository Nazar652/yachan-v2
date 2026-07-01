def test_beat_scheduled_tasks_are_registered():
    from src.celery_app import celery

    # import_default_modules() is the include-import step a worker runs on start;
    # the tasks beat references by name must end up registered.
    celery.loader.import_default_modules()

    assert "expire_bans" in celery.tasks
    assert "process_attachment" in celery.tasks
    assert "apply_moderation_verdict" in celery.tasks
    assert "moderate_image" in celery.tasks
