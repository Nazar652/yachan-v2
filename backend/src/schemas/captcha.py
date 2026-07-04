from pydantic import BaseModel


class CaptchaChallengeResponse(BaseModel):
    token: str
    image_base64_light: str
    image_base64_dark: str
