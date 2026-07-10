from tests._v010_contracts import source


def test_preference_api_accepts_pass_and_undo_states():
    router = source("backend/web/routers/auctions.py")
    assert 'payload.get("passed")' in router
    assert 'elif payload.get("passed") is False' in router
    assert 'return {"status": "saved", "preference": serialize_preference(preference)}' in router


def test_undo_is_recorded_as_an_engagement_event():
    router = source("backend/web/routers/auctions.py")
    assert 'event_name = "undo_pass"' in router
