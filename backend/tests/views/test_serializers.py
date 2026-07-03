from unittest.mock import MagicMock

from src.models.attachment import ModerationStatus
from src.schemas.attachment import AttachmentResponse
from src.schemas.post import PostResponse
from src.views.serializers import attachment_response, is_media_hidden, post_response
from tests.views._factories import attachment_ns, post_ns


def _storage():
    storage = MagicMock()
    storage.public_url = MagicMock(side_effect=lambda key: f"/media/{key}")
    return storage


def test_attachment_response_builds_urls():
    response = attachment_response(
        attachment_ns(file_path="abc.png", thumbnail_path="thumb/abc.jpg"), _storage(), False
    )
    assert isinstance(response, AttachmentResponse)
    assert response.url == "/media/abc.png"
    assert response.thumbnail_url == "/media/thumb/abc.jpg"
    assert response.moderation_status is ModerationStatus.SAFE


def test_attachment_response_no_thumbnail():
    response = attachment_response(attachment_ns(thumbnail_path=None), _storage(), False)
    assert response.thumbnail_url is None


def test_attachment_response_hides_blocked_even_on_nsfw_board():
    response = attachment_response(
        attachment_ns(thumbnail_path="thumb/abc.jpg", moderation_status=ModerationStatus.BLOCKED),
        _storage(),
        True,
    )
    assert response.url is None
    assert response.thumbnail_url is None
    assert response.moderation_status is ModerationStatus.BLOCKED


def test_attachment_response_hides_flagged_on_non_nsfw_board():
    response = attachment_response(
        attachment_ns(moderation_status=ModerationStatus.FLAGGED), _storage(), False
    )
    assert response.url is None


def test_attachment_response_shows_flagged_on_nsfw_board():
    response = attachment_response(
        attachment_ns(file_path="abc.png", moderation_status=ModerationStatus.FLAGGED),
        _storage(),
        True,
    )
    assert response.url == "/media/abc.png"


def test_is_media_hidden_rules():
    assert is_media_hidden(ModerationStatus.BLOCKED, True) is True
    assert is_media_hidden(ModerationStatus.FLAGGED, False) is True
    assert is_media_hidden(ModerationStatus.FLAGGED, True) is False
    assert is_media_hidden(ModerationStatus.SAFE, False) is False
    assert is_media_hidden(ModerationStatus.PENDING, False) is False


def test_post_response_maps_attachments():
    response = post_response(
        post_ns(id=10), [attachment_ns(), attachment_ns(id=8)], _storage(), False
    )
    assert isinstance(response, PostResponse)
    assert len(response.attachments) == 2
    assert "ip_hash" not in response.model_dump()
