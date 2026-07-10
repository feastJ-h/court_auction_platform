from backend.services.onbid_review import diversify_onbid_items


def _item(index, notice="N", agency="A"):
    return {"id": index, "pbanc_mng_no": notice, "agency_name": agency}


def test_notice_cap_limits_repeated_notice():
    selected = diversify_onbid_items([_item(i) for i in range(10)], limit=20, max_per_notice=3)
    assert len(selected) == 3


def test_agency_cap_limits_repeated_agency():
    selected = diversify_onbid_items([_item(i, notice=f"N{i}") for i in range(10)], limit=20, max_per_agency=4)
    assert len(selected) == 4


def test_diversity_is_display_only_and_does_not_mutate_input():
    items = [_item(i) for i in range(5)]
    snapshot = [dict(item) for item in items]
    diversify_onbid_items(items, limit=2)
    assert items == snapshot
