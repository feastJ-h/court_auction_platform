from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings, resolve_db_url
from backend.database.models import Base


def create_db_engine() -> Engine:
    settings = get_settings()
    db_url = resolve_db_url(settings.db_url)
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args, future=True)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)
    ensure_schema_migrations(engine)
    ensure_analysis_results_seed(engine)
    ensure_initial_admin_user()


def ensure_schema_migrations(db_engine: Engine) -> None:
    db_url = str(db_engine.url)
    if not db_url.startswith("sqlite"):
        return

    with db_engine.begin() as connection:
        user_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        user_migrations = {
            "account_status": "ALTER TABLE users ADD COLUMN account_status TEXT NOT NULL DEFAULT 'active'",
            "must_change_password": "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0",
            "terms_version_accepted": "ALTER TABLE users ADD COLUMN terms_version_accepted TEXT NOT NULL DEFAULT ''",
            "privacy_version_accepted": "ALTER TABLE users ADD COLUMN privacy_version_accepted TEXT NOT NULL DEFAULT ''",
            "beta_notice_version_accepted": "ALTER TABLE users ADD COLUMN beta_notice_version_accepted TEXT NOT NULL DEFAULT ''",
            "accepted_at": "ALTER TABLE users ADD COLUMN accepted_at DATETIME NULL",
            "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL",
            "failed_login_count": "ALTER TABLE users ADD COLUMN failed_login_count INTEGER NOT NULL DEFAULT 0",
            "locked_until": "ALTER TABLE users ADD COLUMN locked_until DATETIME NULL",
            "beta_expires_at": "ALTER TABLE users ADD COLUMN beta_expires_at DATETIME NULL",
            "created_by_admin_id": "ALTER TABLE users ADD COLUMN created_by_admin_id INTEGER NULL",
        }
        for column_name, ddl in user_migrations.items():
            if column_name not in user_columns:
                connection.execute(text(ddl))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_account_status ON users(account_status)"))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS security_revoked_sessions (
                session_hash TEXT PRIMARY KEY,
                expires_at TEXT NOT NULL
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_security_revoked_expires ON security_revoked_sessions(expires_at)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS security_rate_limits (
                scope TEXT NOT NULL,
                subject_hash TEXT NOT NULL,
                window_start INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                expires_at TEXT NOT NULL,
                PRIMARY KEY(scope, subject_hash, window_start)
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_security_rate_expires ON security_rate_limits(expires_at)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS onbid_sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                api_kind TEXT NOT NULL,
                started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME NULL,
                status TEXT NOT NULL DEFAULT 'running',
                fetched INTEGER NOT NULL DEFAULT 0,
                inserted INTEGER NOT NULL DEFAULT 0,
                updated INTEGER NOT NULL DEFAULT 0,
                duplicates INTEGER NOT NULL DEFAULT 0,
                dropped_stale INTEGER NOT NULL DEFAULT 0,
                dropped_unknown INTEGER NOT NULL DEFAULT 0,
                error_code TEXT NOT NULL DEFAULT '',
                error_summary_sanitized TEXT NOT NULL DEFAULT ''
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_sync_runs_status ON onbid_sync_runs(status)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_sync_runs_started_at ON onbid_sync_runs(started_at)"))
        ai_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(ai_analyses)")).fetchall()
        }
        if "detailed_analysis" not in ai_columns:
            connection.execute(
                text("ALTER TABLE ai_analyses ADD COLUMN detailed_analysis TEXT NOT NULL DEFAULT ''")
            )

        job_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(analysis_jobs)")).fetchall()
        }
        job_migrations = {
            "codex_thread_id": "ALTER TABLE analysis_jobs ADD COLUMN codex_thread_id TEXT NOT NULL DEFAULT ''",
            "codex_turn_id": "ALTER TABLE analysis_jobs ADD COLUMN codex_turn_id TEXT NOT NULL DEFAULT ''",
            "progress_message": "ALTER TABLE analysis_jobs ADD COLUMN progress_message TEXT NOT NULL DEFAULT ''",
            "progress_percent": "ALTER TABLE analysis_jobs ADD COLUMN progress_percent INTEGER NOT NULL DEFAULT 0",
            "last_event_at": "ALTER TABLE analysis_jobs ADD COLUMN last_event_at DATETIME NULL",
            "cancel_requested": "ALTER TABLE analysis_jobs ADD COLUMN cancel_requested BOOLEAN NOT NULL DEFAULT 0",
            "provider_mode": "ALTER TABLE analysis_jobs ADD COLUMN provider_mode TEXT NOT NULL DEFAULT 'exec'",
            "backup_path": "ALTER TABLE analysis_jobs ADD COLUMN backup_path TEXT NOT NULL DEFAULT ''",
            "execution_mode": "ALTER TABLE analysis_jobs ADD COLUMN execution_mode TEXT NOT NULL DEFAULT ''",
        }
        for column_name, ddl in job_migrations.items():
            if column_name not in job_columns:
                connection.execute(text(ddl))
        connection.execute(
            text(
                """
                UPDATE analysis_jobs
                SET execution_mode = CASE
                    WHEN codex_thread_id LIKE 'mock-%' OR codex_turn_id LIKE 'mock-%' THEN 'mock'
                    WHEN provider_mode = 'app_server' THEN 'codex_app_server'
                    ELSE 'codex_exec'
                END
                WHERE execution_mode = ''
                """
            )
        )

        auction_item_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(auction_items)")).fetchall()
        }
        auction_item_migrations = {
            "onbid_cltr_no": "ALTER TABLE auction_items ADD COLUMN onbid_cltr_no TEXT NOT NULL DEFAULT ''",
            "pbct_no": "ALTER TABLE auction_items ADD COLUMN pbct_no TEXT NOT NULL DEFAULT ''",
            "pbct_nsq": "ALTER TABLE auction_items ADD COLUMN pbct_nsq TEXT NOT NULL DEFAULT ''",
            "public_category": "ALTER TABLE auction_items ADD COLUMN public_category TEXT NOT NULL DEFAULT 'other'",
            "freshness_date": "ALTER TABLE auction_items ADD COLUMN freshness_date TEXT NOT NULL DEFAULT ''",
            "freshness_status": "ALTER TABLE auction_items ADD COLUMN freshness_status TEXT NOT NULL DEFAULT 'unknown_date'",
            "public_visible": "ALTER TABLE auction_items ADD COLUMN public_visible BOOLEAN NOT NULL DEFAULT 0",
        }
        for column_name, ddl in auction_item_migrations.items():
            if column_name not in auction_item_columns:
                connection.execute(text(ddl))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_auction_items_public_category ON auction_items(public_category)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_auction_items_freshness_date ON auction_items(freshness_date)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_auction_items_freshness_status ON auction_items(freshness_status)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_auction_items_public_visible ON auction_items(public_visible)"))

        auction_notice_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(auction_notices)")).fetchall()
        }
        auction_notice_migrations = {
            "notice_no": "ALTER TABLE auction_notices ADD COLUMN notice_no TEXT NOT NULL DEFAULT ''",
            "pbct_no": "ALTER TABLE auction_notices ADD COLUMN pbct_no TEXT NOT NULL DEFAULT ''",
            "pbct_nsq": "ALTER TABLE auction_notices ADD COLUMN pbct_nsq TEXT NOT NULL DEFAULT ''",
            "pbct_cdtn_no": "ALTER TABLE auction_notices ADD COLUMN pbct_cdtn_no TEXT NOT NULL DEFAULT ''",
            "notice_status": "ALTER TABLE auction_notices ADD COLUMN notice_status TEXT NOT NULL DEFAULT ''",
            "notice_type": "ALTER TABLE auction_notices ADD COLUMN notice_type TEXT NOT NULL DEFAULT ''",
            "notice_date": "ALTER TABLE auction_notices ADD COLUMN notice_date TEXT NOT NULL DEFAULT ''",
            "bid_start_at": "ALTER TABLE auction_notices ADD COLUMN bid_start_at TEXT NOT NULL DEFAULT ''",
            "bid_end_at": "ALTER TABLE auction_notices ADD COLUMN bid_end_at TEXT NOT NULL DEFAULT ''",
            "open_at": "ALTER TABLE auction_notices ADD COLUMN open_at TEXT NOT NULL DEFAULT ''",
            "department_name": "ALTER TABLE auction_notices ADD COLUMN department_name TEXT NOT NULL DEFAULT ''",
            "detail_url": "ALTER TABLE auction_notices ADD COLUMN detail_url TEXT NOT NULL DEFAULT ''",
            "item_count": "ALTER TABLE auction_notices ADD COLUMN item_count INTEGER NOT NULL DEFAULT 0",
            "detail_payload": "ALTER TABLE auction_notices ADD COLUMN detail_payload TEXT NOT NULL DEFAULT '{}'",
            "last_seen_at": "ALTER TABLE auction_notices ADD COLUMN last_seen_at DATETIME NULL",
        }
        for column_name, ddl in auction_notice_migrations.items():
            if column_name not in auction_notice_columns:
                connection.execute(text(ddl))

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name VARCHAR(128) NOT NULL,
                    auction_item_id INTEGER NULL REFERENCES auction_items(id),
                    user_id INTEGER NULL REFERENCES users(id),
                    session_id VARCHAR(128) NOT NULL DEFAULT '',
                    category VARCHAR(64) NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_product_analytics_events_event_name ON product_analytics_events(event_name)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_product_analytics_events_auction_item_id ON product_analytics_events(auction_item_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_product_analytics_events_user_id ON product_analytics_events(user_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_product_analytics_events_session_id ON product_analytics_events(session_id)"))

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS onbid_data_issue_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    auction_item_id INTEGER NOT NULL REFERENCES auction_items(id),
                    user_id INTEGER NULL REFERENCES users(id),
                    reporter_session_id VARCHAR(128) NOT NULL DEFAULT '',
                    issue_types_json TEXT NOT NULL DEFAULT '[]',
                    note TEXT NOT NULL DEFAULT '',
                    contains_personal_info BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_data_issue_reports_auction_item_id ON onbid_data_issue_reports(auction_item_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_data_issue_reports_user_id ON onbid_data_issue_reports(user_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_data_issue_reports_reporter_session_id ON onbid_data_issue_reports(reporter_session_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_data_issue_reports_status ON onbid_data_issue_reports(status)"))

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS onbid_review_summary_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    auction_item_id INTEGER NOT NULL REFERENCES auction_items(id),
                    created_by_user_id INTEGER NULL REFERENCES users(id),
                    public_note TEXT NOT NULL DEFAULT '',
                    summary_json TEXT NOT NULL DEFAULT '{}',
                    revoked_at DATETIME NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_review_summary_shares_token ON onbid_review_summary_shares(token)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_review_summary_shares_auction_item_id ON onbid_review_summary_shares(auction_item_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_onbid_review_summary_shares_created_by_user_id ON onbid_review_summary_shares(created_by_user_id)"))


def ensure_analysis_results_seed(db_engine: Engine) -> None:
    db_url = str(db_engine.url)
    if not db_url.startswith("sqlite"):
        return

    with db_engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        if "analysis_results" not in tables:
            return

        connection.execute(
            text(
                """
                INSERT INTO analysis_results (
                    event_id, model_provider, model_name, analysis_type, source_hash, status,
                    item_details, min_price, bidding_date, risk_comment, detailed_analysis,
                    structured_json_path, markdown_path, confidence, is_hallucinated,
                    prompt_version, run_count
                )
                SELECT
                    ai.event_id,
                    COALESCE(NULLIF(ai.analysis_provider, ''), 'chatgpt'),
                    COALESCE(NULLIF(ai.analysis_provider, ''), 'chatgpt'),
                    'basic',
                    rd.file_hash,
                    'SUCCEEDED',
                    ai.item_details,
                    ai.min_price,
                    ai.bidding_date,
                    ai.risk_comment,
                    '',
                    '',
                    '',
                    '',
                    ai.is_hallucinated,
                    'legacy-v1',
                    1
                FROM ai_analyses ai
                JOIN asset_events ev ON ev.id = ai.event_id
                JOIN raw_documents rd ON rd.id = ev.raw_doc_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM analysis_results ar
                    WHERE ar.event_id = ai.event_id
                      AND ar.model_provider = COALESCE(NULLIF(ai.analysis_provider, ''), 'chatgpt')
                      AND ar.analysis_type = 'basic'
                      AND ar.source_hash = rd.file_hash
                      AND ar.superseded_at IS NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE analysis_results
                SET model_provider = CASE
                    WHEN model_provider = 'app_server' THEN 'codex_app_server'
                    WHEN model_provider = 'exec' THEN 'codex_cli'
                    WHEN model_provider = 'openai' THEN 'chatgpt'
                    ELSE model_provider
                END
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE analysis_results
                SET model_provider = CASE
                    WHEN model_provider = 'app_server' THEN 'codex_app_server'
                    WHEN model_provider = 'exec' THEN 'codex_cli'
                    WHEN model_provider = 'openai' THEN 'chatgpt'
                    ELSE model_provider
                END
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO analysis_results (
                    event_id, model_provider, model_name, analysis_type, source_hash, status,
                    item_details, min_price, bidding_date, risk_comment, detailed_analysis,
                    structured_json_path, markdown_path, confidence, is_hallucinated,
                    prompt_version, run_count
                )
                SELECT
                    ai.event_id,
                    COALESCE(
                        NULLIF((
                            SELECT aj.provider_mode
                            FROM analysis_jobs aj
                            WHERE aj.event_id = ai.event_id AND aj.status = 'SUCCEEDED'
                            ORDER BY aj.id DESC
                            LIMIT 1
                        ), ''),
                        COALESCE(NULLIF(ai.analysis_provider, ''), 'chatgpt')
                    ),
                    COALESCE(
                        NULLIF((
                            SELECT aj.execution_mode
                            FROM analysis_jobs aj
                            WHERE aj.event_id = ai.event_id AND aj.status = 'SUCCEEDED'
                            ORDER BY aj.id DESC
                            LIMIT 1
                        ), ''),
                        COALESCE(NULLIF(ai.analysis_provider, ''), 'chatgpt')
                    ),
                    'deep',
                    rd.file_hash,
                    'SUCCEEDED',
                    ai.item_details,
                    ai.min_price,
                    ai.bidding_date,
                    ai.risk_comment,
                    ai.detailed_analysis,
                    COALESCE((
                        SELECT aj.output_json_path
                        FROM analysis_jobs aj
                        WHERE aj.event_id = ai.event_id AND aj.status = 'SUCCEEDED'
                        ORDER BY aj.id DESC
                        LIMIT 1
                    ), ''),
                    COALESCE((
                        SELECT aj.output_markdown_path
                        FROM analysis_jobs aj
                        WHERE aj.event_id = ai.event_id AND aj.status = 'SUCCEEDED'
                        ORDER BY aj.id DESC
                        LIMIT 1
                    ), ''),
                    '',
                    ai.is_hallucinated,
                    'legacy-v1',
                    1
                FROM ai_analyses ai
                JOIN asset_events ev ON ev.id = ai.event_id
                JOIN raw_documents rd ON rd.id = ev.raw_doc_id
                WHERE TRIM(COALESCE(ai.detailed_analysis, '')) <> ''
                  AND NOT EXISTS (
                    SELECT 1
                    FROM analysis_results ar
                    WHERE ar.event_id = ai.event_id
                      AND ar.analysis_type = 'deep'
                      AND ar.source_hash = rd.file_hash
                      AND ar.superseded_at IS NULL
                )
                """
            )
        )


def ensure_initial_admin_user() -> None:
    from backend.services.auth import ensure_initial_admin

    with session_scope() as session:
        ensure_initial_admin(session)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
