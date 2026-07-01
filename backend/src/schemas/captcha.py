from pydantic import BaseModel


class CaptchaChallengeResponse(BaseModel):
    token: str
    image_base64_light: str  # png encoded as base64, rendered inline by the client in light theme
    image_base64_dark: str  # png encoded as base64, rendered inline by the client in dark theme
