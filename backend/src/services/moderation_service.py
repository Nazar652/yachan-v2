from kink import inject

from src.models.attachment import ModerationStatus
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.post_repo import PostRepository
from src.utils.events import ATTACHMENT_MODERATED, EventPublisher, thread_channel


class ModerationService:
    @inject
    def __init__(
        self,
        attachment_repo: AttachmentRepository,
        post_repo: PostRepository,
        events: EventPublisher,
    ) -> None:
        self.attachment_repo = attachment_repo
        self.post_repo = post_repo
        self.events = events

    async def apply(self, attachment_id: int, verdict: dict[str, object]) -> None:
        raw_score = verdict.get("nsfw_score")
        nsfw_score = float(raw_score) if isinstance(raw_score, (int, float)) else None
        status = ModerationStatus(str(verdict["status"]))

        await self.attachment_repo.set_moderation(
            attachment_id, status=status, nsfw_score=nsfw_score
        )
        await self._notify(attachment_id, status)

    async def _notify(self, attachment_id: int, status: ModerationStatus) -> None:
        attachment = await self.attachment_repo.get_by_id(attachment_id)
        if attachment is None:
            return

        post = await self.post_repo.get_by_id(attachment.post_id)
        if post is None:
            return

        await self.events.publish(
            thread_channel(post.thread_id),
            ATTACHMENT_MODERATED,
            {
                "attachment_id": attachment_id,
                "post_id": attachment.post_id,
                "moderation_status": status.value,
            },
        )
