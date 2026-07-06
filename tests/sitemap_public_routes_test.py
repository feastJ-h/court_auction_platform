from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "sitemap_public_routes_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "sitemap-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from backend.workers.onbid_sync import run_onbid_sync  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    assert run_onbid_sync(limit=1, sample=True, api_kind="national_property")["status"] == "SUCCEEDED"
    client = TestClient(app)

    for path in ("/privacy", "/terms", "/disclaimer", "/robots.txt", "/sitemap.xml"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200, f"{path}: {response.status_code}"

    redirect = client.get("/privacy-draft", follow_redirects=False)
    assert redirect.status_code in (302, 303), redirect.status_code
    assert redirect.headers["location"] == "/privacy"

    robots = client.get("/robots.txt").text
    for blocked in ("/admin", "/api/admin", "/user", "/my", "/documents/raw", "/storage"):
        assert f"Disallow: {blocked}" in robots, robots

    sitemap = client.get("/sitemap.xml").text
    assert "/privacy" in sitemap
    assert "/terms" in sitemap
    assert "/onbid/" in sitemap
    for forbidden in ("/admin", "/api/admin", "/documents/raw", "/user", "/my"):
        assert forbidden not in sitemap, sitemap

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - sitemap, robots, and legal public routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
