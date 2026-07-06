import asyncio

from backend.database.session import engine, init_db
from orchestrator import MAX_PIPELINE_ITEMS, run_pipeline
from sqlalchemy import text


def test_pipeline_real_court_and_gemini() -> None:
    result = asyncio.run(run_pipeline(max_items=MAX_PIPELINE_ITEMS))
    assert result.downloaded <= MAX_PIPELINE_ITEMS
    assert result.stored <= MAX_PIPELINE_ITEMS
    assert result.downloaded == MAX_PIPELINE_ITEMS
    assert result.stored == MAX_PIPELINE_ITEMS

    init_db()
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                select
                  (select count(*) from raw_documents) as raw_count,
                  (select count(*) from assets) as asset_count,
                  (select count(*) from asset_events) as event_count,
                  (select count(*) from ai_analyses) as ai_count,
                  (select count(*) from ai_analyses where item_details != '') as item_details_count,
                  (select count(*) from ai_analyses where bidding_date != '미정') as bidding_date_count
                """
            )
        ).mappings().one()

    assert row["raw_count"] == MAX_PIPELINE_ITEMS
    assert row["asset_count"] == MAX_PIPELINE_ITEMS
    assert row["event_count"] == MAX_PIPELINE_ITEMS
    assert row["ai_count"] == MAX_PIPELINE_ITEMS
    assert row["item_details_count"] == MAX_PIPELINE_ITEMS
    assert row["bidding_date_count"] >= 1


if __name__ == "__main__":
    test_pipeline_real_court_and_gemini()
    print("Sprint 5 orchestrator pipeline test passed")
