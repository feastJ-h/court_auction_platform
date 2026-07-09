from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_today_route_external_shape_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    seed_items()
    client = TestClient(app)
    page = client.get("/onbid/today")
    assert page.status_code == 200, page.status_code
    assert "로그인 후 정리" in page.text
    assert 'action="/onbid/' not in page.text
    assert "오늘 보기" in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - today route external shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
