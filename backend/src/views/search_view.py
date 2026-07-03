from kink import inject

from src.schemas.search import SearchResultResponse
from src.services.search_service import SearchService


class SearchView:
    @inject
    def __init__(self, search_service: SearchService) -> None:
        self.search_service = search_service

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
