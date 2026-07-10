from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from sqlalchemy import text

from backend.config import get_settings
from backend.database.session import engine


class SecurityStateStore(ABC):
    @abstractmethod
    def revoke_session(self, session_id: str, ttl_seconds: int) -> None: ...

    @abstractmethod
    def is_session_revoked(self, session_id: str) -> bool: ...

    @abstractmethod
    def consume_rate_limit(self, scope: str, subject: str, limit: int, window_seconds: int) -> bool: ...

    @abstractmethod
    def cleanup_expired(self) -> int: ...


def keyed_subject(value: str) -> str:
    return hmac.new(
        get_settings().app_secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class SQLiteSecurityStateStore(SecurityStateStore):
    def revoke_session(self, session_id: str, ttl_seconds: int) -> None:
        if not session_id:
            return
        expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        with engine.begin() as connection:
            connection.execute(
                text("INSERT OR REPLACE INTO security_revoked_sessions(session_hash, expires_at) VALUES (:key, :expires)"),
                {"key": keyed_subject(session_id), "expires": expires.isoformat()},
            )

    def is_session_revoked(self, session_id: str) -> bool:
        if not session_id:
            return False
        now = datetime.now(timezone.utc).isoformat()
        with engine.begin() as connection:
            row = connection.execute(
                text("SELECT 1 FROM security_revoked_sessions WHERE session_hash=:key AND expires_at>:now"),
                {"key": keyed_subject(session_id), "now": now},
            ).first()
        return row is not None

    def consume_rate_limit(self, scope: str, subject: str, limit: int, window_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        window_start = int(now.timestamp()) // window_seconds * window_seconds
        key = keyed_subject(subject)
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM security_rate_limits WHERE expires_at <= :now"),
                {"now": now.isoformat()},
            )
            row = connection.execute(
                text("SELECT count FROM security_rate_limits WHERE scope=:scope AND subject_hash=:key AND window_start=:window"),
                {"scope": scope, "key": key, "window": window_start},
            ).first()
            count = int(row[0]) if row else 0
            if count >= limit:
                return False
            expires = datetime.fromtimestamp(window_start + window_seconds, timezone.utc).isoformat()
            connection.execute(
                text("""
                    INSERT INTO security_rate_limits(scope, subject_hash, window_start, count, expires_at)
                    VALUES (:scope, :key, :window, 1, :expires)
                    ON CONFLICT(scope, subject_hash, window_start)
                    DO UPDATE SET count=count+1, expires_at=:expires
                """),
                {"scope": scope, "key": key, "window": window_start, "expires": expires},
            )
        return True

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with engine.begin() as connection:
            revoked = connection.execute(text("DELETE FROM security_revoked_sessions WHERE expires_at <= :now"), {"now": now}).rowcount
            limits = connection.execute(text("DELETE FROM security_rate_limits WHERE expires_at <= :now"), {"now": now}).rowcount
        return int(revoked or 0) + int(limits or 0)


class RedisSecurityStateStore(SecurityStateStore):
    """Optional multi-instance adapter; imported only when REDIS_URL is set."""

    def __init__(self, url: str):
        import redis

        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.client.ping()

    def revoke_session(self, session_id: str, ttl_seconds: int) -> None:
        if session_id:
            self.client.setex(f"court:revoked:{keyed_subject(session_id)}", ttl_seconds, "1")

    def is_session_revoked(self, session_id: str) -> bool:
        return bool(session_id and self.client.exists(f"court:revoked:{keyed_subject(session_id)}"))

    def consume_rate_limit(self, scope: str, subject: str, limit: int, window_seconds: int) -> bool:
        key = f"court:rate:{scope}:{keyed_subject(subject)}:{int(datetime.now(timezone.utc).timestamp()) // window_seconds}"
        with self.client.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds + 1)
            count, _ = pipe.execute()
        return int(count) <= limit

    def cleanup_expired(self) -> int:
        return 0


_STORE: SecurityStateStore | None = None


def get_security_state_store() -> SecurityStateStore:
    global _STORE
    if _STORE is None:
        redis_url = get_settings().redis_url.strip()
        _STORE = RedisSecurityStateStore(redis_url) if redis_url else SQLiteSecurityStateStore()
    return _STORE
