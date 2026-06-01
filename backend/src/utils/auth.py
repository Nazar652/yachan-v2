import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt

from src.core.config import Settings

_PBKDF2_ALGO = "sha256"
_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO, password.encode(), salt, _PBKDF2_ITERATIONS
    )
    salt_b64 = base64.b64encode(salt).decode()
    hash_b64 = base64.b64encode(derived_key).decode()
    return f"${_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt_b64}${hash_b64}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, algo, iterations, salt_b64, hash_b64 = encoded.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        derived_key = hashlib.pbkdf2_hmac(algo, password.encode(), salt, int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived_key, expected)


def create_access_token(subject: str, settings: Settings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
