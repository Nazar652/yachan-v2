from kink import inject

from src.core.embeddings import EmbeddingModel
from src.core.exceptions import NotFoundError
from src.models.post import Post
from src.repositories.board_repo import BoardRepository
from src.repositories.post_embedding_repo import PostEmbeddingRepository
from src.repositories.post_repo import PostRepository


class SearchService:
    @inject
    def __init__(
        self,
        post_repo: PostRepository,
        post_embedding_repo: PostEmbeddingRepository,
        board_repo: BoardRepository,
        embedding_model: EmbeddingModel,
    ) -> None:
        self.post_repo = post_repo
        self.post_embedding_repo = post_embedding_repo
        self.board_repo = board_repo
        self.embedding_model = embedding_model

    async def index_post(self, post_id: int) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if post is None or not post.body:
            return
        vector = self.embedding_model.embed(post.body)
        await self.post_embedding_repo.upsert(post_id, vector)

    async def index_all(self) -> int:
        posts = await self.post_repo.list_with_body()
        for post in posts:
            vector = self.embedding_model.embed(post.body or "")
            await self.post_embedding_repo.upsert(post.id, vector)
        return len(posts)

    async def search(
        self, query: str, *, board_slug: str | None = None, limit: int = 20
    ) -> list[tuple[Post, str, float]]:
        board_id = None
        if board_slug is not None:
            board = await self.board_repo.get_by_slug(board_slug)
            if board is None:
                raise NotFoundError(f"board '{board_slug}' not found")
            board_id = board.id
        # embedding the query is a small synchronous cpu step, kept in the backend
        # on purpose (see the semantic-search design); the vector search is plain sql
        vector = self.embedding_model.embed(query)
        return await self.post_embedding_repo.search(vector, board_id=board_id, limit=limit)
