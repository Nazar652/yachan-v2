import httpx

from src.core.config import Settings

_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, headers={"x-goog-api-key": self.api_key}, json=body
            )
            response.raise_for_status()

        return extract_text(response.json())
