from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from fastapi import Request

from backend.config import get_settings


CSRF_COOKIE_NAME = "court_csrf"
CSRF_MAX_AGE_SECONDS = 60 * 60 * 2


def _signature(payload: str) -> str:
    return hmac.new(get_settings().app_secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def new_csrf_token() -> str:
    payload = f"{int(time.time())}.{secrets.token_urlsafe(32)}"
    return f"{payload}.{_signature(payload)}"


def valid_csrf_token(token: str | None) -> bool:
    if not token or token.count(".") != 2:
        return False
    timestamp, nonce, signature = token.split(".", 2)
    payload = f"{timestamp}.{nonce}"
    if not hmac.compare_digest(signature, _signature(payload)):
        return False
    try:
        age = int(time.time()) - int(timestamp)
    except ValueError:
        return False
    return 0 <= age <= CSRF_MAX_AGE_SECONDS


def csrf_token_for_request(request: Request) -> str:
    existing = request.cookies.get(CSRF_COOKIE_NAME, "")
    token = existing if valid_csrf_token(existing) else new_csrf_token()
    request.state.csrf_token = token
    return token


def verify_double_submit(cookie_token: str | None, submitted_token: str | None) -> bool:
    return bool(
        valid_csrf_token(cookie_token)
        and valid_csrf_token(submitted_token)
        and hmac.compare_digest(cookie_token or "", submitted_token or "")
    )
