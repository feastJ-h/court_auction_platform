from __future__ import annotations

from typing import Callable

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse


RequireUser = Callable[[Request, object], object | None]
RequireAdmin = Callable[[Request, object], object | None]
LoginRedirect = Callable[[str], RedirectResponse]
AttachEvents = Callable[[object], None]
AttachAnalysisResults = Callable[[object, object], None]
AttachUserNotes = Callable[[object, object, int], None]
BuildEventPayload = Callable[[object], dict]
AdminFilter = Callable[[object, str, str, str], bool]
StaleJobCheck = Callable[[object], bool]


def admin_login_required() -> HTTPException:
    return HTTPException(status_code=401, detail="Admin login required.")


def safe_redirect_target(value: str, fallback: str = "/user") -> str:
    return value if value.startswith("/") else fallback
