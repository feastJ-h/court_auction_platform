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
        }
        for column_name, ddl in auction_item_migrations.items():
            if column_name not in auction_item_columns:
                connection.execute(text(ddl))

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
