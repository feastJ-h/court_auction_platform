from tests._v010_contracts import source


def test_mobile_pagination_is_single_summary_row():
    shared = source("frontend/templates/shared/pagination.html")
    assert 'data-pagination-mobile="true"' in shared
    assert "{{ pagination.page }} / {{ pagination.total_pages }}" in shared
    assert "sm:hidden" in shared
