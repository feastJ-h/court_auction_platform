from __future__ import annotations

from _v007_helpers import configure_test_env

TEST_DB_PATH = configure_test_env("home_closing_card_empty_state_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    page = TestClient(app).get("/")
    assert page.status_code == 200
    assert "/onbid?closing_within_days=7" in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - home closing empty state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
