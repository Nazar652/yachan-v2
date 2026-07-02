from src.models.attachment import MediaType, ModerationStatus
from src.schemas.attachment import AttachmentResponse


def test_attachment_response_minimal_defaults():
    response = AttachmentResponse(
        id=1,
        media_type=MediaType.IMAGE,
        original_name="cat.png",
        url="/media/cat.png",
        mime_type="image/png",
        moderation_status=ModerationStatus.SAFE,
    )
    assert response.thumbnail_url is None
    assert response.width is None


def test_attachment_response_full():
    response = AttachmentResponse(
        id=1,
        media_type=MediaType.VIDEO,
        original_name="clip.webm",
        url="/media/clip.webm",
        thumbnail_url="/media/clip.jpg",
        mime_type="video/webm",
        width=640,
        height=480,
        duration_seconds=12.5,
        size_bytes=1000,
        moderation_status=ModerationStatus.SAFE,
    )
    assert response.media_type is MediaType.VIDEO
    assert response.duration_seconds == 12.5
