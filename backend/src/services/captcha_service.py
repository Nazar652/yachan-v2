import base64

from kink import inject
from redis.asyncio import Redis

from src.core.exceptions import InvalidCaptchaError
from src.utils import captcha

CAPTCHA_TTL_SECONDS = 300


@inject
class CaptchaService:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def issue(self) -> tuple[str, str]:
        """Returns (token, base64 png). The answer is kept in redis under the token."""
        token = captcha.new_token()
        answer = captcha.generate_answer()
        await self.redis.set(self._key(token), answer, ex=CAPTCHA_TTL_SECONDS)
        image = captcha.render_image(answer)
        return token, base64.b64encode(image).decode()

    async def validate(self, token: str, answer: str) -> None:
        stored = await self.redis.get(self._key(token))
        if stored is None or stored.upper() != answer.strip().upper():
            raise InvalidCaptchaError()
        # one-time use: a solved captcha cannot be replayed
        await self.redis.delete(self._key(token))

    @staticmethod
    def _key(token: str) -> str:
        return f"captcha:{token}"
