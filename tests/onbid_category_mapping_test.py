from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "onbid_category_mapping_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "category-mapping-test-secret"

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import derive_onbid_category, get_onbid_category_counts, upsert_auction_item  # noqa: E402


def main() -> int:
    init_db()
    payloads = [
        {"source": "ONBID", "cltrMngNo": "REAL", "pbctCdtnNo": "1", "itemName": "Real", "assetType": "Real estate", "bidStartAt": "2025-01-02"},
        {"source": "ONBID", "cltrMngNo": "MOVABLE", "pbctCdtnNo": "1", "itemName": "Movable", "assetType": "Movable", "bidStartAt": "2025-01-02"},
        {"source": "ONBID", "cltrMngNo": "NATIONAL", "pbctCdtnNo": "1", "itemName": "National", "assetType": "National property", "usage": "national_property", "_source_api": "national_property", "bidStartAt": "2025-01-02"},
        {"source": "ONBID", "cltrMngNo": "OTHER", "pbctCdtnNo": "1", "itemName": "Other", "assetType": "License", "bidStartAt": "2025-01-02"},
    ]
    with session_scope() as session:
        items = [upsert_auction_item(session, payload)[0] for payload in payloads]
        categories = [derive_onbid_category(item) for item in items]
        counts = get_onbid_category_counts(session, public_only=True)

    assert categories == ["real_estate", "movable", "national_property", "other"], categories
    assert counts["all"] == 4, counts
    assert counts["real_estate"] == 1, counts
    assert counts["movable"] == 1, counts
    assert counts["national_property"] == 1, counts
    assert counts["other"] == 1, counts

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID stored category mapping and counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
