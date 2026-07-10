import re

from fastapi.testclient import TestClient

from backend.services.csrf import CSRF_COOKIE_NAME
from main_app import app


def token_from(markup: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', markup)
    assert match
    return match.group(1)


def test_login_form_uses_signed_double_submit_token():
    client = TestClient(app)
    page = client.get("/login")
    token = token_from(page.text)
    assert client.cookies.get(CSRF_COOKIE_NAME) == token
    missing = client.post("/login", data={"username": "nobody", "password": "wrong"}, headers={"X-Enforce-CSRF": "1"})
    assert missing.status_code == 403
    wrong = client.post("/login", data={"username": "nobody", "password": "wrong", "csrf_token": token + "x"}, headers={"X-Enforce-CSRF": "1"})
    assert wrong.status_code == 403
    valid = client.post("/login", data={"username": "nobody", "password": "wrong", "csrf_token": token}, headers={"X-Enforce-CSRF": "1"}, follow_redirects=False)
    assert valid.status_code == 303


def test_token_from_another_session_is_rejected():
    first = TestClient(app)
    second = TestClient(app)
    foreign = token_from(first.get("/login").text)
    second.get("/login")
    response = second.post("/login", data={"username": "nobody", "password": "wrong", "csrf_token": foreign}, headers={"X-Enforce-CSRF": "1"})
    assert response.status_code == 403
