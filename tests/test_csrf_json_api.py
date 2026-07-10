import re

from fastapi.testclient import TestClient

from main_app import app


def test_json_mutation_requires_header_token():
    client = TestClient(app)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    missing = client.post("/api/product-events", json={"event_name": "filter_apply"}, headers={"X-Enforce-CSRF": "1"})
    assert missing.status_code == 403
    valid = client.post("/api/product-events", json={"event_name": "filter_apply"}, headers={"X-Enforce-CSRF": "1", "X-CSRF-Token": token})
    assert valid.status_code in {200, 201, 204}
