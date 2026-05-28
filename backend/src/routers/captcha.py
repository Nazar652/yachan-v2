from fastapi import APIRouter, Depends

from src.schemas.captcha import CaptchaChallengeResponse
from src.views.captcha_view import CaptchaView

router = APIRouter(prefix="/captcha", tags=["captcha"])


def _view() -> CaptchaView:
    return CaptchaView()


@router.get("", response_model=CaptchaChallengeResponse)
async def issue_captcha(view: CaptchaView = Depends(_view)) -> CaptchaChallengeResponse:
    return await view.issue()
