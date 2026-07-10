from tests._v010_contracts import source


def test_pass_updates_preference_without_deleting_item():
    router = source("backend/web/routers/auctions.py")
    preferences = source("backend/services/user_auction_preferences.py")
    assert "update_preference(" in router
    assert "session.delete" not in preferences
    assert "preference.is_passed = passed" in preferences
