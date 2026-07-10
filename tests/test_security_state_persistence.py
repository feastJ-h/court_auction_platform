import secrets

from backend.services.security_state import SQLiteSecurityStateStore


def test_session_revocation_survives_store_recreation():
    session_id = "test-" + secrets.token_urlsafe(20)
    SQLiteSecurityStateStore().revoke_session(session_id, 60)
    assert SQLiteSecurityStateStore().is_session_revoked(session_id)


def test_rate_limit_is_shared_by_store_instances():
    subject = "test-" + secrets.token_urlsafe(20)
    assert SQLiteSecurityStateStore().consume_rate_limit("test", subject, 1, 60)
    assert not SQLiteSecurityStateStore().consume_rate_limit("test", subject, 1, 60)
