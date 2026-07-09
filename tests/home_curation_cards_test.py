from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("home_curation_cards_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    seed_items()
    response = TestClient(app).get("/")
    assert response.status_code == 200, response.status_code
    assert 'data-home-curation-cards="true"' in response.text
    for phrase in ("오늘 새로 확인된 물건", "이번 주 마감 임박", "내 지역 신규 물건", "가격 정보 있는 1억 이하"):
        assert phrase in response.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - home curation cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
