from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_detail_data_consistency_test")

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import build_onbid_info_badges, get_auction_item  # noqa: E402


def main() -> int:
    init_db()
    _, sparse_id = seed_items()
    with session_scope() as session:
        badges = build_onbid_info_badges(get_auction_item(session, sparse_id))
    assert "상세 설명: 확인됨" not in badges["available"]
    assert "상세 설명: 확인 필요" in badges["missing"]
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - detail consistency")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
