import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional


DEFAULT_SECRET_KEY = "change-this-local-development-secret"
SECRET_KEY = os.getenv("TICKETS_SECRET_KEY", DEFAULT_SECRET_KEY)
APP_ENV = os.getenv("APP_ENV", "development").lower()
TOKEN_TTL_SECONDS = 60 * 60 * 12

if APP_ENV in {"production", "prod"} and SECRET_KEY == DEFAULT_SECRET_KEY:
    raise RuntimeError("TICKETS_SECRET_KEY debe configurarse en producción")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def create_password_reset_token() -> str:
    return secrets.token_urlsafe(40)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return hmac.compare_digest(digest.hex(), expected)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode())


def create_access_token(user_id: int) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64encode(signature)}"


def decode_access_token(token: str) -> Optional[int]:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_b64decode(signature_b64), expected_signature):
            return None

        payload = json.loads(_b64decode(payload_b64))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return int(payload["sub"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None
