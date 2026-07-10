from datetime import date

from backend.services.onbid_review import build_today_review_state


def test_empty_queue_is_not_complete():
    assert build_today_review_state([], today=date(2026, 7, 10))["complete"] is False


def test_queue_is_complete_only_after_every_item_is_classified():
    items = [
        {"first_seen_date": "2026-07-10", "preference": {"is_passed": True}},
        {"first_seen_date": "2026-07-10", "preference": {"is_favorite": True}},
    ]
    assert build_today_review_state(items, today=date(2026, 7, 10))["complete"] is True
