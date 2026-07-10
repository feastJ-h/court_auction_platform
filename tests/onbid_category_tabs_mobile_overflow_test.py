from tests._v010_contracts import source


def test_category_tabs_scroll_inside_without_wrapping_body():
    tabs = source("frontend/templates/shared/onbid_category_tabs.html")
    page = source("frontend/templates/auctions/index.html")
    assert "overflow-x-auto" in tabs and "flex-nowrap" in tabs and "min-h-11" in tabs
    assert "overflow-x-hidden" in page
