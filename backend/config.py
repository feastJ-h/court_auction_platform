from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    db_url: str = Field(default="sqlite:///./auction_data.db", alias="DB_URL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash-latest", alias="GEMINI_MODEL")
    analysis_provider: str = Field(default="chatgpt", alias="ANALYSIS_PROVIDER")
    chatgpt_api_key: str = Field(default="", alias="CHATGPT_API_KEY")
    chatgpt_model: str = Field(default="gpt-5.5", alias="CHATGPT_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")
    enable_pii_masking: bool = Field(default=False, alias="ENABLE_PII_MASKING")
    app_secret_key: str = Field(default="local-dev-change-me", alias="APP_SECRET_KEY")
    initial_admin_username: str = Field(default="admin", alias="INITIAL_ADMIN_USERNAME")
    initial_admin_password: str = Field(default="admin1234!", alias="INITIAL_ADMIN_PASSWORD")
    initial_admin_display_name: str = Field(default="관리자", alias="INITIAL_ADMIN_DISPLAY_NAME")
    tesseract_cmd: str = Field(default="", alias="TESSERACT_CMD")
    ocr_language: str = Field(default="kor+eng", alias="OCR_LANGUAGE")
    ocr_dpi: int = Field(default=220, alias="OCR_DPI")
    ocr_max_pages: int = Field(default=8, alias="OCR_MAX_PAGES")
    onbid_api_key: str = Field(default="", alias="ONBID_API_KEY")
    onbid_api_base_url: str = Field(default="", alias="ONBID_API_BASE_URL")
    onbid_api_operation: str = Field(default="getRlstCltrList2", alias="ONBID_API_OPERATION")
    onbid_real_estate_detail_base_url: str = Field(default="", alias="ONBID_REAL_ESTATE_DETAIL_BASE_URL")
    onbid_real_estate_detail_operation: str = Field(default="", alias="ONBID_REAL_ESTATE_DETAIL_OPERATION")
    onbid_movable_api_base_url: str = Field(default="", alias="ONBID_MOVABLE_API_BASE_URL")
    onbid_movable_list_operation: str = Field(default="", alias="ONBID_MOVABLE_LIST_OPERATION")
    onbid_movable_detail_base_url: str = Field(default="", alias="ONBID_MOVABLE_DETAIL_BASE_URL")
    onbid_movable_detail_operation: str = Field(default="", alias="ONBID_MOVABLE_DETAIL_OPERATION")
    onbid_notice_list_base_url: str = Field(default="", alias="ONBID_NOTICE_LIST_BASE_URL")
    onbid_notice_list_operation: str = Field(default="", alias="ONBID_NOTICE_LIST_OPERATION")
    onbid_notice_detail_base_url: str = Field(default="", alias="ONBID_NOTICE_DETAIL_BASE_URL")
    onbid_notice_detail_operation: str = Field(default="", alias="ONBID_NOTICE_DETAIL_OPERATION")
    onbid_notice_cltr_base_url: str = Field(default="", alias="ONBID_NOTICE_CLTR_BASE_URL")
    onbid_notice_cltr_operation: str = Field(default="", alias="ONBID_NOTICE_CLTR_OPERATION")
    onbid_bid_target_base_url: str = Field(default="", alias="ONBID_BID_TARGET_BASE_URL")
    onbid_bid_target_operation: str = Field(default="", alias="ONBID_BID_TARGET_OPERATION")

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def raw_quarantine_dir() -> Path:
    path = PROJECT_ROOT / "storage" / "raw_quarantine"
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir() -> Path:
    path = PROJECT_ROOT / "storage" / "processed"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_db_url(db_url: str) -> str:
    if not db_url.startswith("sqlite:///./"):
        return db_url
    relative = db_url.replace("sqlite:///./", "", 1)
    return f"sqlite:///{PROJECT_ROOT / relative}"
