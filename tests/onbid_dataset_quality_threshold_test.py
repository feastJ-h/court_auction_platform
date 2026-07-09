from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_dataset_quality_threshold_test")

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import audit_onbid_freshness, count_auction_items, get_onbid_category_counts  # noqa: E402


def main() -> int:
    init_db()
    seed_items()
    with session_scope() as session:
        audit = audit_onbid_freshness(session, min_date="2025-01-01")
        counts = get_onbid_category_counts(session, public_only=True)
        public_visible = count_auction_items(session, public_only=True)
    assert audit["total"] >= 2, audit
    assert public_visible >= 2, public_visible
    assert counts["real_estate"] >= 1, counts
    assert counts["movable"] >= 1, counts
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - dataset quality threshold smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
