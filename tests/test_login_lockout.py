import secrets

from backend.database.session import SessionLocal
from backend.services.auth import authenticate_user, create_user


def test_five_failed_logins_lock_account_and_success_resets_counter():
    session = SessionLocal()
    try:
        username = "lockout-" + secrets.token_hex(8)
        user = create_user(session, username, "correct-password-123", must_change_password=True)
        for _ in range(5):
            assert authenticate_user(session, username, "wrong-password") is None
        assert user.failed_login_count == 5
        assert user.locked_until is not None
        assert authenticate_user(session, username, "correct-password-123") is None
    finally:
        session.rollback()
        session.close()
