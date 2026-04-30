import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from src.models import Board, MediaFile, MediaType, Post, Thread, User


def test_imageboard_models_persist_relationships() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        board = Board(code="b", title="Random")
        user = User(username="anon")
        session.add(board)
        session.add(user)
        session.commit()
        session.refresh(board)
        session.refresh(user)

        thread = Thread(board_id=board.id, user_id=user.id, title="First thread")
        session.add(thread)
        session.commit()
        session.refresh(thread)

        op_post = Post(thread_id=thread.id, user_id=user.id, is_op=True, content="Hello")
        session.add(op_post)
        session.commit()
        session.refresh(op_post)

        media = MediaFile(post_id=op_post.id, media_type=MediaType.IMAGE, file_url="/files/op.jpg")
        session.add(media)
        session.commit()

        loaded_thread = session.exec(select(Thread).where(Thread.id == thread.id)).one()
        loaded_post = session.exec(select(Post).where(Post.id == op_post.id)).one()

        assert loaded_thread.board_id == board.id
        assert loaded_post.thread_id == loaded_thread.id


def test_thread_starter_requires_image_or_gif() -> None:
    with pytest.raises(ValueError):
        Thread.ensure_op_has_image(
            [MediaFile(post_id=1, media_type=MediaType.VIDEO, file_url="/files/op.mp4")]
        )

    Thread.ensure_op_has_image(
        [MediaFile(post_id=1, media_type=MediaType.IMAGE, file_url="/files/op.jpg")]
    )
