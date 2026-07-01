from kink import inject

from src.schemas.captcha import CaptchaChallengeResponse
from src.services.captcha_service import CaptchaService


class CaptchaView:
    @inject
    def __init__(self, captcha_service: CaptchaService) -> None:
        self.captcha_service = captcha_service

    async def issue(self) -> CaptchaChallengeResponse:
        token, image_base64_light, image_base64_dark = await self.captcha_service.issue()
        return CaptchaChallengeResponse(
            token=token,
            image_base64_light=image_base64_light,
            image_base64_dark=image_base64_dark,
        )
