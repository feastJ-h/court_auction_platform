from tests._v010_contracts import source


def test_logged_out_summary_hides_personal_zero_stats():
    template = source("frontend/templates/auctions/today.html")
    assert "{% if current_user %}" in template
    assert "최대 20건 · 공고/기관 편중 제한" in template
