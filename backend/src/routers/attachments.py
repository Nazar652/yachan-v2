from fastapi import APIRouter, Depends, File, UploadFile

from src.schemas.attachment import AttachmentResponse
from src.views.attachments_view import AttachmentsView

router = APIRouter(prefix="/{board_slug}", tags=["attachments"])


def _view() -> AttachmentsView:
    return AttachmentsView()


@router.post(
    "/posts/{post_number}/attachments",
    response_model=AttachmentResponse,
    status_code=201,
)
async def upload_attachment(
    board_slug: str,
    post_number: int,
    file: UploadFile = File(),
    view: AttachmentsView = Depends(_view),
) -> AttachmentResponse:
    content = await file.read()
    return await view.add_attachment(
        board_slug, post_number, file.filename or "file", content, file.content_type or ""
    )
