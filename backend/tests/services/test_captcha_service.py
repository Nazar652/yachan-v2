from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.exceptions import InvalidCaptchaError
from src.services.captcha_service import CaptchaService


def _service(redis):
    return CaptchaService(redis=redis)


async def test_issue_stores_answer_and_returns_token_and_images():
    redis = MagicMock()
    redis.set = AsyncMock()
    service = _service(redis)

    token, image_base64_light, image_base64_dark = await service.issue()

    assert isinstance(token, str) and token
    assert isinstance(image_base64_light, str) and image_base64_light
    assert isinstance(image_base64_dark, str) and image_base64_dark
    assert image_base64_light != image_base64_dark
    redis.set.assert_awaited_once()


async def test_validate_accepts_correct_answer_case_insensitive():
    redis = MagicMock()
    redis.getdel = AsyncMock(return_value="ABCDE")
    service = _service(redis)

    await service.validate("token", "abcde")

    redis.getdel.assert_awaited_once()  # consumed on the attempt


async def test_validate_rejects_and_consumes_wrong_answer():
    redis = MagicMock()
    redis.getdel = AsyncMock(return_value="ABCDE")
    service = _service(redis)

    with pytest.raises(InvalidCaptchaError):
        await service.validate("token", "wrong")
    # the token is consumed even on a wrong guess, so it cannot be brute-forced
    redis.getdel.assert_awaited_once()


async def test_validate_rejects_expired_or_unknown_token():
    redis = MagicMock()
    redis.getdel = AsyncMock(return_value=None)
    service = _service(redis)

    with pytest.raises(InvalidCaptchaError):
        await service.validate("token", "abcde")
