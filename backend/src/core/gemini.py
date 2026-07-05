import logging
from time import perf_counter

import httpx

from src.core.config import Settings
from src.core.logging import log_event, redact_headers

_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

logger = logging.getLogger("src.external")


def extract_text(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts") or []
    return "".join(part.get("text", "") for part in parts).strip()


class GeminiClient:
    def __init__(self, api_key: str, model: str, timeout: float = 30.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_settings(cls, settings: Settings) -> GeminiClient:
        return cls(settings.gemini_api_key, settings.summary_model)

    async def generate(self, prompt: str) -> str:
        url = f"{_API_BASE}/{self.model}:generateContent"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"x-goog-api-key": self.api_key}

        start = perf_counter()
        status_code: int | None = None
        response_text = ""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=body)

            status_code = response.status_code
            response_text = response.text
            response.raise_for_status()
        finally:
            is_success = status_code is not None and 200 <= status_code < 300

            log_event(
                logger,
                "external_call",
                target="gemini",
                url=url,
                headers=redact_headers(headers),
                status_code=status_code,
                duration_ms=round((perf_counter() - start) * 1000, 2),
                response_body=response_text if not is_success else {"size": len(response_text)},
            )

        return extract_text(response.json())
