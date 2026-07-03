import anyio.to_thread
from kink import inject

from src.core.embeddings import EmbeddingModel
from src.core.exceptions import NotFoundError
from src.models.post import Post
from src.repositories.board_repo import BoardRepository
from src.repositories.post_embedding_repo import PostEmbeddingRepository
from src.repositories.post_repo import PostRepository
from src.utils.search_text import clean_search_text


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
        vector = self.embedding_model.embed(clean_search_text(post.body))
        await self.post_embedding_repo.upsert(post_id, vector)

    async def index_all(self) -> int:
        posts = await self.post_repo.list_with_body()
        for post in posts:
            vector = self.embedding_model.embed(clean_search_text(post.body or ""))
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

        cleaned = clean_search_text(query)
        # embedding is blocking cpu work; run it in a thread so the request's event loop stays free
        # (onnxruntime releases the gil during inference)
        vector = await anyio.to_thread.run_sync(self.embedding_model.embed, cleaned)

        # hybrid: `cleaned` also drives a lexical match so posts literally containing the query words
        # rank above cross-lingual semantic neighbours
        return await self.post_embedding_repo.search(
            vector, cleaned, board_id=board_id, limit=limit
        )
