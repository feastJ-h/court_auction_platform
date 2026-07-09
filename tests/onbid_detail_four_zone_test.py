from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_detail_four_zone_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    page = TestClient(app).get(f"/onbid/{item_id}")
    assert page.status_code == 200, page.status_code
    for zone in ("source-status", "objective-facts", "source-checkpoints", "personal-actions"):
        assert f'data-detail-zone="{zone}"' in page.text
    assert "최종 판단 전 원문과 관계 서류를 직접 확인" in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - detail four zone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
