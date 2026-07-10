from urllib.parse import parse_qs, urlsplit

from backend.web.pagination import build_query_href


def query_of(href: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(href).query, keep_blank_values=True)


def test_omit_removes_base_before_same_key_update():
    query = query_of(build_query_href("/onbid", {"category": "movable", "page": 9}, omit={"category", "page"}, category="real_estate"))
    assert query == {"category": ["real_estate"]}


def test_all_category_is_canonical_omission():
    assert build_query_href("/onbid", {"category": "movable"}, omit={"category"}, category="all") == "/onbid"


def test_false_zero_list_and_unicode_are_preserved():
    query = query_of(build_query_href("/onbid", {"region": "서울"}, enabled=False, price_min=0, tag=["a", "b"]))
    assert query == {"region": ["서울"], "enabled": ["False"], "price_min": ["0"], "tag": ["a", "b"]}


def test_category_update_preserves_every_unrelated_filter():
    state = {"region": "서울", "price_max": 100_000_000, "data_quality": "needs_confirmation", "sort": "price_asc", "page": 9}
    query = query_of(build_query_href("/onbid", state, omit={"page", "category"}, category="real_estate"))
    assert query == {
        "region": ["서울"],
        "price_max": ["100000000"],
        "data_quality": ["needs_confirmation"],
        "sort": ["price_asc"],
        "category": ["real_estate"],
    }
