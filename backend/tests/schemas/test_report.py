from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from src.schemas.report import ReportCreate, ReportResponse


def test_report_create_defaults_reason_none():
    assert ReportCreate().reason is None


def test_report_create_rejects_overlong_reason():
    with pytest.raises(ValidationError):
        ReportCreate(reason="x" * 501)


def test_report_response_from_attributes():
    obj = SimpleNamespace(
        id=1,
        post_id=2,
        board_id=3,
        reason="spam",
        is_auto=False,
        is_resolved=False,
        created_at=datetime(2026, 1, 1),
        ip_hash="secret",
    )
    response = ReportResponse.model_validate(obj)
    assert "ip_hash" not in response.model_dump()
    assert response.is_auto is False
