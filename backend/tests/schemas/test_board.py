from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from src.schemas.board import BoardCreate, BoardResponse, BoardUpdate


def test_board_create_defaults_bump_limit():
    board = BoardCreate(slug="b", title="Random")
    assert board.bump_limit == 300


@pytest.mark.parametrize("bad_slug", ["", "B", "has space", "a" * 21, "a-b"])
def test_board_create_rejects_bad_slug(bad_slug):
    with pytest.raises(ValidationError):
        BoardCreate(slug=bad_slug, title="x")


def test_board_create_rejects_non_positive_bump_limit():
    with pytest.raises(ValidationError):
        BoardCreate(slug="b", title="x", bump_limit=0)


def test_board_update_omitted_fields_are_not_set():
    update = BoardUpdate(title="new")
    assert update.model_dump(exclude_unset=True) == {"title": "new"}


def test_board_update_allows_clearing_description_with_null():
    update = BoardUpdate(description=None)
    assert update.model_dump(exclude_unset=True) == {"description": None}


@pytest.mark.parametrize("field", ["title", "bump_limit", "is_active"])
def test_board_update_rejects_explicit_null_on_required_fields(field):
    with pytest.raises(ValidationError):
        BoardUpdate(**{field: None})


def test_board_response_from_attributes():
    obj = SimpleNamespace(
        id=1,
        slug="b",
        title="Random",
        description=None,
        bump_limit=300,
        is_active=True,
        created_at=datetime(2026, 1, 1),
    )
    response = BoardResponse.model_validate(obj)
    assert response.slug == "b"
