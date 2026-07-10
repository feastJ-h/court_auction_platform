import secrets

from backend.database.session import SessionLocal
from backend.services.auth import change_user_password, create_user, set_user_active


def test_invited_user_must_change_password_and_can_be_deactivated():
    session = SessionLocal()
    try:
        user = create_user(session, "invite-" + secrets.token_hex(8), "temporary-password-123", created_by_admin_id=1)
        assert user.must_change_password and user.account_status == "active"
        change_user_password(session, user, "temporary-password-123", "new-secure-password-456")
        assert not user.must_change_password
        set_user_active(session, user.id, False)
        assert not user.is_active and user.account_status == "inactive"
    finally:
        session.rollback()
        session.close()
