from kink import inject

from src.models.attachment import ModerationStatus
from src.repositories.attachment_repo import AttachmentRepository


class ModerationService:
    @inject
    def __init__(self, attachment_repo: AttachmentRepository) -> None:
        self.attachment_repo = attachment_repo

    async def apply(self, attachment_id: int, verdict: dict[str, object]) -> None:
        # verdict is the JSON payload from the moderation service (see
        # docs/moderation-contract.md); an UPDATE by id, so re-applying is safe
        raw_score = verdict.get("nsfw_score")
        nsfw_score = float(raw_score) if isinstance(raw_score, (int, float)) else None
        await self.attachment_repo.set_moderation(
            attachment_id,
            status=ModerationStatus(str(verdict["status"])),
            nsfw_score=nsfw_score,
        )
