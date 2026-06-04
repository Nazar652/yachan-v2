from fastapi import APIRouter, Depends

from src.bootstrap.container import get_dependency
from src.schemas.captcha import CaptchaChallengeResponse
from src.views.captcha_view import CaptchaView

router = APIRouter(prefix="/captcha", tags=["captcha"])


@router.get("", response_model=CaptchaChallengeResponse)
async def issue_captcha(view: CaptchaView = Depends(lambda: get_dependency(CaptchaView))) -> CaptchaChallengeResponse:
    return await view.issue()
