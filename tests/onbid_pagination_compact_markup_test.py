from tests._v010_contracts import source


def test_onbid_uses_shared_compact_pagination():
    page = source("frontend/templates/auctions/index.html")
    shared = source("frontend/templates/shared/pagination.html")
    assert 'shared/pagination.html' in page
    assert 'data-compact-pagination="true"' in shared
    assert "pagination.page_links" not in page
