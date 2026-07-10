from backend.config import Settings, validate_runtime_config


def settings_for(**overrides):
    values = {
        "APP_ENV": "beta",
        "APP_SECRET_KEY": "x" * 48,
        "INITIAL_ADMIN_PASSWORD": "a-secure-temporary-password",
        "DB_URL": "sqlite:///./auction_data.db",
        "LOCAL_DEV_LOGIN_HINT": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_beta_rejects_default_secret_and_admin_password():
    problems = validate_runtime_config(settings_for(APP_SECRET_KEY="local-dev-change-me", INITIAL_ADMIN_PASSWORD="admin1234!"))
    assert any("APP_SECRET_KEY" in problem for problem in problems)
    assert any("INITIAL_ADMIN_PASSWORD" in problem for problem in problems)


def test_beta_accepts_non_default_minimum_configuration():
    assert validate_runtime_config(settings_for()) == []


def test_beta_rejects_test_database_and_login_hint():
    problems = validate_runtime_config(settings_for(DB_URL="sqlite:///./storage/test/app.db", LOCAL_DEV_LOGIN_HINT=True))
    assert any("DB_URL" in problem for problem in problems)
    assert any("LOCAL_DEV_LOGIN_HINT" in problem for problem in problems)
