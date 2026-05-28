from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import InvalidCaptchaError
from src.services.captcha_service import CaptchaService


def _service(redis):
    return CaptchaService(redis=redis)


async def test_issue_stores_answer_and_returns_token_and_image():
    redis = MagicMock()
    redis.set = AsyncMock()
    service = _service(redis)

    token, image_base64 = await service.issue()

    assert isinstance(token, str) and token
    assert isinstance(image_base64, str) and image_base64
    redis.set.assert_awaited_once()


async def test_validate_accepts_correct_answer_case_insensitive():
    redis = MagicMock()
    redis.get = AsyncMock(return_value="ABCDE")
    redis.delete = AsyncMock()
    service = _service(redis)

    await service.validate("token", "abcde")

    redis.delete.assert_awaited_once()  # consumed after success


async def test_validate_rejects_wrong_answer():
    redis = MagicMock()
    redis.get = AsyncMock(return_value="ABCDE")
    redis.delete = AsyncMock()
    service = _service(redis)

    with pytest.raises(InvalidCaptchaError):
        await service.validate("token", "wrong")
    redis.delete.assert_not_called()


async def test_validate_rejects_expired_or_unknown_token():
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    service = _service(redis)

    with pytest.raises(InvalidCaptchaError):
        await service.validate("token", "abcde")
