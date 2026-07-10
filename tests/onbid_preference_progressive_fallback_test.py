from tests._v010_contracts import source


def test_preference_actions_remain_real_post_forms_without_javascript():
    page = source("frontend/templates/auctions/index.html")
    assert 'action="/onbid/{{ item.id }}/preference" method="post"' in page
    assert 'name="next_url"' in page
