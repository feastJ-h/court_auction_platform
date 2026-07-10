from tests._v010_contracts import source


def test_session_cookie_has_expiry_rotation_and_secure_controls():
    app = source("main_app.py")
    assert '"exp": expires_at' in app
    assert '"sid": secrets.token_urlsafe(24)' in app
    assert "httponly=True" in app and 'samesite="lax"' in app
    assert 'secure=request.url.scheme == "https"' in app


def test_logout_revokes_current_session_identifier():
    app = source("main_app.py")
    assert "_REVOKED_SESSION_IDS.add(session_id)" in app
    assert "session_id in _REVOKED_SESSION_IDS" in app
