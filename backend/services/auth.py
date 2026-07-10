from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database.models import User

HASH_PREFIX = "pbkdf2_sha256"
HASH_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS,
    ).hex()
    return f"{HASH_PREFIX}${HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        prefix, iterations_raw, salt, digest = password_hash.split("$", 3)
        if prefix != HASH_PREFIX:
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_raw),
        ).hex()
        return hmac.compare_digest(computed, digest)
    except Exception:
        return False


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == username))


def get_user_by_id(session: Session, user_id: int | None) -> User | None:
    if not user_id:
        return None
    return session.get(User, user_id)


def list_users(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.role.desc(), User.username.asc())))


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(session, username.strip())
    now = datetime.now(timezone.utc)
    if user is None:
        return None
    locked_until = user.locked_until
    if locked_until is not None and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    expires_at = user.beta_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        not user.is_active
        or user.account_status != "active"
        or (locked_until is not None and locked_until > now)
        or (expires_at is not None and expires_at <= now)
    ):
        return None
    if not verify_password(password, user.password_hash):
        user.failed_login_count = int(user.failed_login_count or 0) + 1
        if user.failed_login_count >= 5:
            user.locked_until = now + timedelta(minutes=15)
        session.flush()
        return None
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    session.flush()
    return user


def create_user(
    session: Session,
    username: str,
    password: str,
    display_name: str = "",
    role: str = "user",
    *,
    must_change_password: bool = True,
    created_by_admin_id: int | None = None,
    beta_expires_at: datetime | None = None,
) -> User:
    clean_username = username.strip()
    if not clean_username:
        raise ValueError("username_required")
    if len(password) < 8:
        raise ValueError("password_too_short")
    if role not in {"admin", "user"}:
        raise ValueError("invalid_role")
    if get_user_by_username(session, clean_username):
        raise ValueError("username_exists")
    user = User(
        username=clean_username,
        password_hash=hash_password(password),
        display_name=display_name.strip() or clean_username,
        role=role,
        is_active=True,
        account_status="active",
        must_change_password=must_change_password,
        created_by_admin_id=created_by_admin_id,
        beta_expires_at=beta_expires_at,
    )
    session.add(user)
    session.flush()
    return user


def change_user_password(session: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise ValueError("current_password_invalid")
    if len(new_password) < 8:
        raise ValueError("password_too_short")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    session.flush()


def set_user_active(session: Session, user_id: int, is_active: bool) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("user_not_found")
    user.is_active = is_active
    user.account_status = "active" if is_active else "inactive"
    session.flush()
    return user


def set_user_role(session: Session, user_id: int, role: str) -> User:
    if role not in {"admin", "user"}:
        raise ValueError("invalid_role")
    user = session.get(User, user_id)
    if user is None:
        raise ValueError("user_not_found")
    user.role = role
    session.flush()
    return user


def accept_current_policies(session: Session, user: User) -> None:
    settings = get_settings()
    user.terms_version_accepted = settings.terms_version
    user.privacy_version_accepted = settings.privacy_version
    user.beta_notice_version_accepted = settings.beta_notice_version
    user.accepted_at = datetime.now(timezone.utc)
    session.flush()


def ensure_initial_admin(session: Session) -> User:
    settings = get_settings()
    username = settings.initial_admin_username.strip() or "admin"
    existing = get_user_by_username(session, username)
    if existing:
        return existing
    if settings.app_env.strip().lower() in {"beta", "production"}:
        raise RuntimeError("Initial admin is not auto-created outside development; run backend.cli.bootstrap_admin")
    admin = User(
        username=username,
        password_hash=hash_password(settings.initial_admin_password),
        display_name=settings.initial_admin_display_name or username,
        role="admin",
        is_active=True,
        account_status="active",
        must_change_password=True,
    )
    session.add(admin)
    session.flush()
    return admin
