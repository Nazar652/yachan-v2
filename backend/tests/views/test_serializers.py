from unittest.mock import MagicMock

from src.schemas.attachment import AttachmentResponse
from src.schemas.post import PostResponse
from src.views.serializers import attachment_response, post_response
from tests.views._factories import attachment_ns, post_ns


def _storage():
    storage = MagicMock()
    storage.public_url = MagicMock(side_effect=lambda key: f"/media/{key}")
    return storage


def test_attachment_response_builds_urls():
    response = attachment_response(
        attachment_ns(file_path="abc.png", thumbnail_path="thumb/abc.jpg"), _storage()
    )
    assert isinstance(response, AttachmentResponse)
    assert response.url == "/media/abc.png"
    assert response.thumbnail_url == "/media/thumb/abc.jpg"


def test_attachment_response_no_thumbnail():
    response = attachment_response(attachment_ns(thumbnail_path=None), _storage())
    assert response.thumbnail_url is None


def test_post_response_maps_attachments():
    response = post_response(post_ns(id=10), [attachment_ns(), attachment_ns(id=8)], _storage())
    assert isinstance(response, PostResponse)
    assert len(response.attachments) == 2
    assert "ip_hash" not in response.model_dump()
