from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_admin_data_quality_dashboard_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import create_user  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    seed_items()
    client = TestClient(app)
    with session_scope() as session:
        create_user(session, "quality_admin", "quality-admin-pass!", "Quality Admin", "admin")
    login = client.post("/login", data={"username": "quality_admin", "password": "quality-admin-pass!", "next_url": "/admin/onbid-data-quality"}, follow_redirects=False)
    assert login.status_code in (302, 303)
    page = client.get("/admin/onbid-data-quality", cookies=login.cookies)
    assert page.status_code == 200
    assert "Original URL coverage" in page.text
    assert "False detail available" in page.text
    api = client.get("/api/admin/onbid-data-quality", cookies=login.cookies)
    assert api.status_code == 200
    assert "missing_original_url_count" in api.json()
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - admin data quality dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
