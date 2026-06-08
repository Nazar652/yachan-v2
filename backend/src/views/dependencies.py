from fastapi import Header
from starlette.requests import Request

from src.core.config import Settings
from src.core.exceptions import UnauthorizedError
from src.utils.ip import hash_ip


def client_ip_hash(request: Request, settings: Settings) -> str:
    raw_ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    return hash_ip(raw_ip, settings.ip_hash_salt)


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing bearer token")
    return authorization[len("bearer ") :].strip()
