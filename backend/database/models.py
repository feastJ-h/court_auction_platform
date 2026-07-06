from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    events: Mapped[list["AssetEvent"]] = relationship(back_populates="raw_document")
    evidence: Mapped["CollectionEvidence | None"] = relationship(back_populates="raw_document")


class CollectionEvidence(Base):
    __tablename__ = "collection_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_doc_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id"), nullable=False, unique=True)
    source_title: Mapped[str] = mapped_column(String(512), nullable=False)
    attachment_name: Mapped[str] = mapped_column(String(512), nullable=False)
    notice_date: Mapped[str] = mapped_column(String(10), nullable=False, default="UNKNOWN")
    expire_date: Mapped[str] = mapped_column(String(10), nullable=False, default="UNKNOWN")
    detail_page_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    raw_document: Mapped[RawDocument] = relationship(back_populates="evidence")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    main_category: Mapped[str] = mapped_column(String(32), nullable=False)
    sub_category: Mapped[str] = mapped_column(String(128), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)

    events: Mapped[list["AssetEvent"]] = relationship(back_populates="asset")


class AssetEvent(Base):
    __tablename__ = "asset_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    raw_doc_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id"), nullable=False)
    case_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    notice_date: Mapped[str] = mapped_column(String(10), nullable=False, default="UNKNOWN")
    expire_date: Mapped[str] = mapped_column(String(10), nullable=False, default="UNKNOWN")
    parse_status: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)

    asset: Mapped[Asset] = relationship(back_populates="events")
    raw_document: Mapped[RawDocument] = relationship(back_populates="events")
    analyses: Mapped[list["AiAnalysis"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    user_actions: Mapped[list["UserEventAction"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    event_actions: Mapped[list["UserEventAction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    event_notes: Mapped[list["UserEventNote"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserEventAction(Base):
    __tablename__ = "user_event_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="event_actions")
    event: Mapped[AssetEvent] = relationship(back_populates="user_actions")


class UserEventNote(Base):
    __tablename__ = "user_event_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event_notes_user_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False, index=True)
    tags: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="event_notes")
    event: Mapped[AssetEvent] = relationship()


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False)
    item_details: Mapped[str] = mapped_column(Text, nullable=False)
    min_price: Mapped[str] = mapped_column(String(128), nullable=False)
    bidding_date: Mapped[str] = mapped_column(String(10), nullable=False, default="미정")
    risk_comment: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_hallucinated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    analysis_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="chatgpt")

    event: Mapped[AssetEvent] = relationship(back_populates="analyses")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False, index=True)
    model_provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCEEDED", index=True)
    item_details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    min_price: Mapped[str] = mapped_column(String(128), nullable=False, default="0")
    bidding_date: Mapped[str] = mapped_column(String(10), nullable=False, default="미정")
    risk_comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    detailed_analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    structured_json_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    markdown_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    confidence: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    is_hallucinated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, default="DEEP_ANALYSIS")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="codex_cli")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    requested_by: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    input_snapshot_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    output_json_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    output_markdown_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    stderr_log_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    backup_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    error_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    codex_thread_id: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    codex_turn_id: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    progress_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="exec")
    execution_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    event: Mapped[AssetEvent] = relationship(back_populates="analysis_jobs")
    events: Mapped[list["AnalysisJobEvent"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class AnalysisJobEvent(Base):
    __tablename__ = "analysis_job_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_payload: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    job: Mapped[AnalysisJob] = relationship(back_populates="events")


class AnalysisWorkerHeartbeat(Base):
    __tablename__ = "analysis_worker_heartbeats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    worker_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_mode: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN", index=True)
    current_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    app_server_endpoint: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AnalysisReview(Base):
    __tablename__ = "analysis_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_result_id: Mapped[int] = mapped_column(ForeignKey("analysis_results.id"), nullable=False, index=True)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False, default="admin")
    price_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hallucination_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_start_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    target_end_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    pages_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_downloaded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_downloads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    log_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")


class AuctionItem(Base):
    __tablename__ = "auction_items"
    __table_args__ = (
        UniqueConstraint("source", "cltr_mng_no", "pbct_cdtn_no", name="uq_auction_items_source_cltr_pbct"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ONBID", index=True)
    cltr_mng_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_cdtn_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbanc_mng_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    onbid_cltr_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_nsq: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    item_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    disposal_method: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    bid_method: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    latitude: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    longitude: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    appraisal_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    minimum_bid_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    bid_deposit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    bid_start_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bid_end_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    open_bid_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN", index=True)
    agency_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    photo_url: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    attachment_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    land_area: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    building_area: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    land_category: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    usage: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    item_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    bid_condition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    contract_condition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cautions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    snapshots: Mapped[list["AuctionItemSnapshot"]] = relationship(back_populates="auction_item", cascade="all, delete-orphan")
    results: Mapped[list["AuctionResult"]] = relationship(back_populates="auction_item", cascade="all, delete-orphan")
    case_links: Mapped[list["CaseAuctionLink"]] = relationship(back_populates="auction_item", cascade="all, delete-orphan")
    notice_links: Mapped[list["AuctionNoticeItemLink"]] = relationship(back_populates="auction_item", cascade="all, delete-orphan")


class AuctionItemSnapshot(Base):
    __tablename__ = "auction_item_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_item_id: Mapped[int] = mapped_column(ForeignKey("auction_items.id"), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    appraisal_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    minimum_bid_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    bid_start_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bid_end_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    open_bid_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    auction_item: Mapped[AuctionItem] = relationship(back_populates="snapshots")


class AuctionNotice(Base):
    __tablename__ = "auction_notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ONBID", index=True)
    pbanc_mng_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    notice_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_nsq: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    pbct_cdtn_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    notice_title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notice_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notice_status: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    notice_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    notice_date: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bid_start_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bid_end_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    open_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    agency_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    department_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    disposal_method: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    bid_method: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    detail_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    detail_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item_links: Mapped[list["AuctionNoticeItemLink"]] = relationship(back_populates="notice", cascade="all, delete-orphan")


class AuctionNoticeItemLink(Base):
    __tablename__ = "auction_notice_item_links"
    __table_args__ = (
        UniqueConstraint("source", "notice_id", "auction_item_id", name="uq_notice_item_link_notice_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("auction_notices.id"), nullable=False, index=True)
    auction_item_id: Mapped[int] = mapped_column(ForeignKey("auction_items.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ONBID", index=True)
    notice_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbanc_mng_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_nsq: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    cltr_mng_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    pbct_cdtn_no: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    notice: Mapped[AuctionNotice] = relationship(back_populates="item_links")
    auction_item: Mapped[AuctionItem] = relationship(back_populates="notice_links")


class AuctionResult(Base):
    __tablename__ = "auction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_item_id: Mapped[int] = mapped_column(ForeignKey("auction_items.id"), nullable=False, index=True)
    result_status: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    winning_price: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    winning_rate: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bidder_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    auction_item: Mapped[AuctionItem] = relationship(back_populates="results")


class CaseAuctionLink(Base):
    __tablename__ = "case_auction_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("asset_events.id"), nullable=False, index=True)
    auction_item_id: Mapped[int] = mapped_column(ForeignKey("auction_items.id"), nullable=False, index=True)
    debtor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    link_status: Mapped[str] = mapped_column(String(50), nullable=False, default="candidate", index=True)
    match_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    memo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    auction_item: Mapped[AuctionItem] = relationship(back_populates="case_links")
    case_event: Mapped[AssetEvent] = relationship()
    asset: Mapped[Asset | None] = relationship()
    assigned_user: Mapped[User | None] = relationship()


class AuctionAlert(Base):
    __tablename__ = "auction_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auction_item_id: Mapped[int] = mapped_column(ForeignKey("auction_items.id"), nullable=False, index=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("asset_events.id"), nullable=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    alert_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    receiver_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    target_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    summary: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    actor: Mapped[User | None] = relationship()
