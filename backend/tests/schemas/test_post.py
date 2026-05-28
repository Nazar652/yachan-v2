from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.schemas.post import PostCreate, PostEditResponse, PostResponse


def test_post_create_defaults():
    post = PostCreate()
    assert post.name is None
    assert post.body is None
    assert post.sage is False


def test_post_create_rejects_overlong_body():
    with pytest.raises(ValidationError):
        PostCreate(body="x" * 5001)


def test_post_response_excludes_ip_hash_and_defaults_attachments():
    obj = SimpleNamespace(
        id=1,
        post_number=1,
        thread_id=1,
        board_id=1,
        name="Anonymous",
        tripcode=None,
        body="hi",
        body_html="<p>hi</p>",
        sage=False,
        is_op=True,
        is_edited=False,
        edited_at=None,
        created_at=datetime(2026, 1, 1),
        ip_hash="secret",
    )
    response = PostResponse.model_validate(obj)
    assert response.attachments == []
    assert "ip_hash" not in response.model_dump()


def test_post_edit_response_from_attributes():
    obj = SimpleNamespace(
        post_id=5,
        original_body="old",
        original_body_html="<p>old</p>",
        edited_at=datetime(2026, 1, 1),
    )
    response = PostEditResponse.model_validate(obj)
    assert response.post_id == 5
