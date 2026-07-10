from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_detail_no_false_detail_available_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    _, sparse_id = seed_items()
    page = TestClient(app).get(f"/onbid/{sparse_id}")
    assert page.status_code == 200
    assert "상세 설명: 확인 필요" in page.text
    assert "상세 설명: 확인됨" not in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - no false detail available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
