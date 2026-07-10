from fastapi.testclient import TestClient

from main_app import app


def test_health_live_ready_and_version_contracts():
    client = TestClient(app)
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    version = client.get("/health/version")
    assert live.status_code == 200 and live.json()["status"] == "live"
    assert ready.status_code == 200 and ready.json()["status"] == "ready"
    assert version.status_code == 200
    payload = version.json()
    assert set(payload) == {"version", "git_commit", "environment", "build_time"}
    serialized = str(payload).lower()
    assert "secret" not in serialized and "password" not in serialized and "token" not in serialized
