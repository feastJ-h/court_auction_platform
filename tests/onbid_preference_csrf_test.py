from fastapi.testclient import TestClient

from main_app import app


def test_cross_site_preference_request_is_rejected_before_auth():
    response = TestClient(app).post(
        "/api/onbid/1/preference",
        json={"passed": True},
        headers={"Origin": "https://attacker.invalid", "Sec-Fetch-Site": "cross-site"},
    )
    assert response.status_code == 403
