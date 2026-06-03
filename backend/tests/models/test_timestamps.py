from datetime import datetime

from src.models.board import Board
from src.models.post_edit import PostEdit


def test_mixin_populates_both_timestamps_on_instantiation():
    board = Board(slug="b", title="Random")
    assert isinstance(board.created_at, datetime)
    assert isinstance(board.updated_at, datetime)


def test_updated_at_column_carries_onupdate():
    # the onupdate callable is what bumps updated_at on every orm update
    assert Board.__table__.c.updated_at.onupdate is not None


def test_mixin_adds_timestamps_to_models_that_lacked_created_at():
    # PostEdit had no created_at before the mixin; now it gets both
    edit = PostEdit(post_id=1)
    assert isinstance(edit.created_at, datetime)
    assert isinstance(edit.updated_at, datetime)
