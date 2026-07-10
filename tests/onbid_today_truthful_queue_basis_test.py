from datetime import date

from backend.services.onbid_review import build_today_review_state


def test_today_queue_uses_first_seen_date_not_freshness_date():
    item = {"first_seen_date": "2026-07-10", "freshness_date": "2026-07-09", "preference": {}}
    result = build_today_review_state([item], today=date(2026, 7, 10))
    assert result["total"] == 1
    assert result["basis"] == "first_seen_at"


def test_freshness_only_item_is_not_counted_as_today():
    item = {"first_seen_date": "2026-07-09", "freshness_date": "2026-07-10", "preference": {}}
    assert build_today_review_state([item], today=date(2026, 7, 10))["total"] == 0
