from pydantic import BaseModel


class CaptchaChallengeResponse(BaseModel):
    token: str
    image_base64: str  # png image encoded as base64, rendered inline by the client
