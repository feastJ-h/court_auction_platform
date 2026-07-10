import pytest

from backend.web.pagination import build_pagination


@pytest.mark.parametrize(("current", "expected"), [(-1, 1), (0, 1), (999, 12)])
def test_invalid_page_is_clamped(current, expected):
    assert build_pagination("/onbid", current_page=current, total_pages=12)["page"] == expected
