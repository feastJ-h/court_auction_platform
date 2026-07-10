from fastapi.testclient import TestClient

from main_app import app


def test_logout_get_does_not_mutate_session():
    response = TestClient(app).get("/logout", follow_redirects=False)
    assert response.status_code == 405
