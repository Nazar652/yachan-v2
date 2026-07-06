from kink import inject

from src.core.storage import Storage
from src.schemas.search import SearchResultResponse, SimilarThreadResponse
from src.services.board_service import BoardService
from src.services.search_service import SearchService, SimilarThreadMatch
from src.views.serializers import is_media_hidden

OP_SNIPPET_LENGTH = 120


def op_snippet(body: str | None) -> str | None:
    if body is None:
        return None
    stripped = body.strip()
    if len(stripped) <= OP_SNIPPET_LENGTH:
        return stripped
    return stripped[:OP_SNIPPET_LENGTH].rstrip() + "…"


class SearchView:
    @inject
    def __init__(
        self, search_service: SearchService, board_service: BoardService, storage: Storage
    ) -> None:
        self.search_service = search_service
        self.board_service = board_service
        self.storage = storage

    async def search(
        self, query: str, board_slug: str | None, limit: int
    ) -> list[SearchResultResponse]:
        hits = await self.search_service.search(query, board_slug=board_slug, limit=limit)
        return [
            SearchResultResponse(
                board_slug=slug,
                thread_id=post.thread_id,
                post_number=post.post_number,
                is_op=post.is_op,
                name=post.name,
                body=post.body,
                body_html=post.body_html,
                created_at=post.created_at,
                # cosine distance -> similarity; higher is closer
                score=round(1.0 - distance, 4),
            )
            for post, slug, distance in hits
        ]

    async def similar_threads(self, board_slug: str, thread_id: int) -> list[SimilarThreadResponse]:
        matches = await self.search_service.similar_threads(board_slug, thread_id)
        return await self._to_responses(matches)

    async def similar_threads_for_text(
        self, board_slug: str, q: str
    ) -> list[SimilarThreadResponse]:
        matches = await self.search_service.similar_threads_for_text(board_slug, q)
        return await self._to_responses(matches)

    async def _to_responses(
        self, matches: list[SimilarThreadMatch]
    ) -> list[SimilarThreadResponse]:
        nsfw_by_slug = {
            board.slug: board.is_nsfw for board in await self.board_service.list_boards()
        }

        responses = []
        for thread, slug, op_post, images, distance in matches:
            visible_images = [
                image
                for image in images
                if not is_media_hidden(image.moderation_status, nsfw_by_slug.get(slug, False))
            ]
            first_image = visible_images[0] if visible_images else None
            thumbnail_url = (
                self.storage.public_url(first_image.thumbnail_path or first_image.file_path)
                if first_image
                else None
            )
            responses.append(
                SimilarThreadResponse(
                    board_slug=slug,
                    thread_id=thread.id,
                    title=thread.title,
                    op_snippet=op_snippet(op_post.body),
                    thumbnail_url=thumbnail_url,
                    reply_count=thread.reply_count,
                    # cosine distance -> similarity; higher is closer
                    score=round(1.0 - distance, 4),
                )
            )
        return responses
