from backend.services.onbid_review import select_home_preview


def test_home_preview_mixes_real_estate_and_movable_when_available():
    items = [
        {"id": index, "category": "movable", "pbanc_mng_no": f"M{index}"}
        for index in range(10)
    ] + [
        {"id": 100 + index, "category": "real_estate", "pbanc_mng_no": f"R{index}"}
        for index in range(3)
    ]
    selected = select_home_preview(items, limit=4)
    assert [item["category"] for item in selected].count("real_estate") == 2
    assert [item["category"] for item in selected].count("movable") == 2


def test_home_preview_limits_same_notice_to_one():
    items = [
        {"id": 1, "category": "real_estate", "pbanc_mng_no": "SAME"},
        {"id": 2, "category": "real_estate", "pbanc_mng_no": "SAME"},
        {"id": 3, "category": "movable", "pbanc_mng_no": "OTHER"},
    ]
    selected = select_home_preview(items, limit=3)
    assert sum(item["pbanc_mng_no"] == "SAME" for item in selected) == 1
