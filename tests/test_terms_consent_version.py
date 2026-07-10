from datetime import datetime

from backend.config import get_settings
from backend.database.models import User
from backend.services.auth import accept_current_policies


class FlushOnlySession:
    def flush(self):
        return None


def test_consent_records_every_current_version_and_time():
    user = User(username="consent-contract", password_hash="x", display_name="x")
    accept_current_policies(FlushOnlySession(), user)
    settings = get_settings()
    assert user.terms_version_accepted == settings.terms_version
    assert user.privacy_version_accepted == settings.privacy_version
    assert user.beta_notice_version_accepted == settings.beta_notice_version
    assert isinstance(user.accepted_at, datetime)
