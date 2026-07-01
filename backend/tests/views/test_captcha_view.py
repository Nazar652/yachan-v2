from unittest.mock import AsyncMock, MagicMock

from src.schemas.captcha import CaptchaChallengeResponse
from src.views.captcha_view import CaptchaView


async def test_issue_returns_challenge_response():
    captcha_service = MagicMock()
    captcha_service.issue = AsyncMock(return_value=("token123", "lightpng", "darkpng"))
    view = CaptchaView(captcha_service=captcha_service)

    result = await view.issue()

    assert isinstance(result, CaptchaChallengeResponse)
    assert result.token == "token123"
    assert result.image_base64_light == "lightpng"
    assert result.image_base64_dark == "darkpng"
