import base64

import anyio.to_thread
from kink import inject
from redis.asyncio import Redis

from src.core.exceptions import InvalidCaptchaError
from src.utils import captcha

CAPTCHA_TTL_SECONDS = 300


class CaptchaService:
    @inject
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def issue(self) -> tuple[str, str, str]:
        """Returns (token, light png base64, dark png base64). The answer is kept in redis under the token."""
        token = captcha.new_token()
        answer = captcha.generate_answer()
        await self.redis.set(self._key(token), answer, ex=CAPTCHA_TTL_SECONDS)

        # pillow rendering is cpu-bound; keep it off the event loop
        light_image, dark_image = await anyio.to_thread.run_sync(captcha.render_image_pair, answer)

        return token, base64.b64encode(light_image).decode(), base64.b64encode(dark_image).decode()

    async def validate(self, token: str, answer: str) -> None:
        # getdel consumes the token on any attempt, so a wrong guess cannot be
        # brute-forced against the same challenge — the client must fetch a new one
        stored = await self.redis.getdel(self._key(token))
        if stored is None or stored.upper() != answer.strip().upper():
            raise InvalidCaptchaError()

    @staticmethod
    def _key(token: str) -> str:
        return f"captcha:{token}"
