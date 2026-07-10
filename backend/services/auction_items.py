from __future__ import annotations

import json
import re
import hashlib
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.config import get_settings
from backend.database.models import (
    AssetEvent,
    AuctionItem,
    AuctionItemSnapshot,
    AuctionNotice,
    AuctionNoticeItemLink,
    CaseAuctionLink,
)


def digits_to_int(value: Any) -> int:
    if value is None:
        return 0
    digits = re.sub(r"\D", "", str(value))
    return int(digits) if digits else 0


def str_value(payload: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


ONBID_CATEGORY_LABELS = {
    "all": "전체",
    "real_estate": "부동산",
    "movable": "동산",
    "national_property": "국유일반재산",
    "other": "기타",
}
ONBID_MIN_PUBLIC_DATE = "2025-01-01"
KST = ZoneInfo("Asia/Seoul")
FRESHNESS_FRESH = "fresh"
FRESHNESS_STALE = "stale"
FRESHNESS_UNKNOWN = "unknown_date"
FRESHNESS_INVALID = "invalid_date"
ONBID_CATEGORY_LABELS.update(
    {
        "all": "전체",
        "real_estate": "부동산",
        "movable": "동산",
        "national_property": "국유일반재산",
        "other": "기타",
    }
)
ONBID_SENTINEL_PUBLIC_DATES = {
    "0001-01-01",
    "1900-01-01",
    "2999-12-30",
    "2999-12-31",
    "9999-12-31",
}
ONBID_DATE_KEYS = (
    "bidStartAt",
    "bid_start_at",
    "cltrBidBgngDt",
    "opbdDtStart",
    "bidEndAt",
    "bid_end_at",
    "cltrBidEndDt",
    "opbdDtEnd",
    "openBidAt",
    "open_bid_at",
    "opengDt",
    "cltrOpbdDt",
    "noticeDate",
    "notice_date",
    "pbancDt",
    "pbancYmd",
    "opbdDt",
    "FRST_BID_SLCTN_YMD",
)

REAL_ESTATE_TOKENS = (
    "real estate",
    "land",
    "building",
    "apartment",
    "office",
    "house",
    "부동산",
    "토지",
    "건물",
    "아파트",
    "주거",
)
MOVABLE_TOKENS = (
    "movable",
    "vehicle",
    "car",
    "ship",
    "machine",
    "equipment",
    "동산",
    "차량",
    "운송",
    "기계",
    "장비",
)


def _payload_from_item(item_or_payload: Any) -> dict[str, Any]:
    if isinstance(item_or_payload, dict):
        return item_or_payload
    raw_payload = getattr(item_or_payload, "raw_payload", "") or "{}"
    try:
        parsed = json.loads(raw_payload)
    except Exception:
        parsed = {}
    return {
        "source_api": parsed.get("_source_api") or parsed.get("sourceApi") or "",
        "asset_type": getattr(item_or_payload, "asset_type", ""),
        "usage": getattr(item_or_payload, "usage", ""),
        "category": parsed.get("category") or "",
        "raw_payload": parsed,
    }


def derive_onbid_category(item_or_payload: Any) -> str:
    payload = _payload_from_item(item_or_payload)
    raw_payload = payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else payload
    source_api = str(payload.get("source_api") or payload.get("_source_api") or raw_payload.get("_source_api") or "").lower()
    explicit = str(payload.get("category") or raw_payload.get("category") or "").lower()
    text = " ".join(
        str(value or "")
        for value in (
            source_api,
            explicit,
            payload.get("asset_type"),
            payload.get("usage"),
            raw_payload.get("prptDivNm"),
            raw_payload.get("cltrUsgLclsCtgrNm"),
            raw_payload.get("cltrUsgMclsCtgrNm"),
            raw_payload.get("cltrUsgSclsCtgrNm"),
            raw_payload.get("apiKind"),
        )
    ).lower()
    if "national_property" in text or "bid_target" in text or "national property" in text or "국유" in text:
        return "national_property"
    if any(token in text for token in REAL_ESTATE_TOKENS):
        return "real_estate"
    if any(token in text for token in MOVABLE_TOKENS):
        return "movable"
    return "other"


def get_onbid_category_label(category: str) -> str:
    return ONBID_CATEGORY_LABELS.get(str(category or "").lower(), ONBID_CATEGORY_LABELS["other"])


def normalize_public_category(category: str) -> str:
    normalized = str(category or "all").lower().strip()
    return normalized if normalized in ONBID_CATEGORY_LABELS else "other"


def parse_onbid_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        text = text[:10]
    elif len(text) >= 8 and text[:8].isdigit():
        text = f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    else:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def now_kst() -> datetime:
    return datetime.now(tz=KST)


def parse_onbid_deadline(value: Any) -> datetime | None:
    """Parse an ONBID deadline in KST, treating a date-only value as end of day."""
    text = str(value or "").strip()
    parsed_date = parse_onbid_date(text)
    if parsed_date is None or is_implausible_onbid_public_date(parsed_date):
        return None
    normalized = text.replace("T", " ")
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y%m%d%H%M%S", "%Y%m%d%H%M"):
        try:
            return datetime.strptime(normalized, pattern).replace(tzinfo=KST)
        except ValueError:
            continue
    return datetime.combine(parsed_date, time(23, 59, 59), tzinfo=KST)


def get_onbid_deadline_status(value: Any, *, now: datetime | None = None) -> dict[str, Any]:
    deadline = parse_onbid_deadline(value)
    if deadline is None:
        return {"label": "일정 확인 필요", "state": "unknown", "days": None, "is_active": False, "deadline": None}
    reference = now or now_kst()
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=KST)
    else:
        reference = reference.astimezone(KST)
    delta_seconds = (deadline - reference).total_seconds()
    if delta_seconds < 0:
        days_after = max(1, (reference.date() - deadline.date()).days)
        return {
            "label": "입찰마감" if days_after == 1 else f"마감 후 {days_after}일",
            "state": "closed",
            "days": -days_after,
            "is_active": False,
            "deadline": deadline,
        }
    days = (deadline.date() - reference.date()).days
    if days == 0:
        label, state = "오늘 마감", "urgent"
    elif days <= 7:
        label, state = ("마감 임박" if days == 1 else f"D-{days}"), "urgent"
    else:
        label, state = f"D-{days}", "normal"
    return {"label": label, "state": state, "days": days, "is_active": True, "deadline": deadline}


def max_public_onbid_date() -> date:
    days = max(0, int(get_settings().onbid_public_max_future_days or 0))
    return date.today() + timedelta(days=days)


def is_implausible_onbid_public_date(parsed: date | None) -> bool:
    if parsed is None:
        return False
    if parsed.isoformat() in ONBID_SENTINEL_PUBLIC_DATES:
        return True
    return parsed > max_public_onbid_date()


def is_onbid_sample_payload(payload: dict[str, Any]) -> bool:
    raw = payload.get("_raw") if isinstance(payload.get("_raw"), dict) else {}
    values = list(payload.values()) + list(raw.values())
    text = " ".join(str(value or "") for value in values).lower()
    sample_markers = (
        "sample",
        "fixture",
        "onbid-real-202607",
        "onbid-movable-202607",
        "onbid-national-202607",
        "notice-cltr-202607",
    )
    return any(marker in text for marker in sample_markers)


def is_onbid_sample_item(item: AuctionItem) -> bool:
    try:
        raw_payload = json.loads(getattr(item, "raw_payload", "") or "{}")
    except Exception:
        raw_payload = {}
    text = " ".join(
        str(value or "")
        for value in (
            getattr(item, "cltr_mng_no", ""),
            getattr(item, "pbanc_mng_no", ""),
            getattr(item, "item_name", ""),
            getattr(item, "address", ""),
            getattr(item, "asset_type", ""),
            raw_payload,
        )
    ).lower()
    sample_markers = (
        "sample",
        "fixture",
        "onbid-real-202607",
        "onbid-movable-202607",
        "onbid-national-202607",
        "notice-cltr-202607",
    )
    return any(marker in text for marker in sample_markers)


def extract_onbid_freshness_date(payload_or_item: Any) -> str:
    raw_payload: dict[str, Any] = {}
    if isinstance(payload_or_item, dict):
        raw_payload = payload_or_item.get("_raw") if isinstance(payload_or_item.get("_raw"), dict) else payload_or_item
        candidates = [payload_or_item.get(key) for key in ONBID_DATE_KEYS]
        candidates.extend(raw_payload.get(key) for key in ONBID_DATE_KEYS)
    else:
        try:
            raw_payload = json.loads(getattr(payload_or_item, "raw_payload", "") or "{}")
        except Exception:
            raw_payload = {}
        candidates = [
            getattr(payload_or_item, "bid_start_at", ""),
            getattr(payload_or_item, "bid_end_at", ""),
            getattr(payload_or_item, "open_bid_at", ""),
            getattr(payload_or_item, "freshness_date", ""),
        ]
        candidates.extend(raw_payload.get(key) for key in ONBID_DATE_KEYS)
        raw_list = raw_payload.get("_raw_list") if isinstance(raw_payload.get("_raw_list"), dict) else {}
        raw_detail = raw_payload.get("_raw_detail") if isinstance(raw_payload.get("_raw_detail"), dict) else {}
        candidates.extend(raw_list.get(key) for key in ONBID_DATE_KEYS)
        candidates.extend(raw_detail.get(key) for key in ONBID_DATE_KEYS)
    parsed_candidates: list[date] = []
    invalid_candidates: list[date] = []
    for candidate in candidates:
        parsed = parse_onbid_date(candidate)
        if parsed is not None:
            if is_implausible_onbid_public_date(parsed):
                invalid_candidates.append(parsed)
            else:
                parsed_candidates.append(parsed)
    if parsed_candidates:
        return max(parsed_candidates).isoformat()
    if invalid_candidates:
        return max(invalid_candidates).isoformat()
    return ""


def evaluate_onbid_freshness(value: str, *, min_date: str | None = None) -> str:
    min_public_date = parse_onbid_date(min_date or get_settings().onbid_min_public_date or ONBID_MIN_PUBLIC_DATE)
    parsed = parse_onbid_date(value)
    if parsed is None:
        return FRESHNESS_UNKNOWN
    if is_implausible_onbid_public_date(parsed):
        return FRESHNESS_INVALID
    if min_public_date is None:
        min_public_date = parse_onbid_date(ONBID_MIN_PUBLIC_DATE)
    return FRESHNESS_FRESH if parsed >= min_public_date else FRESHNESS_STALE


def evaluate_onbid_payload_freshness(payload_or_item: Any, *, min_date: str | None = None) -> dict[str, Any]:
    freshness_date = extract_onbid_freshness_date(payload_or_item)
    status = evaluate_onbid_freshness(freshness_date, min_date=min_date)
    is_sample = isinstance(payload_or_item, dict) and is_onbid_sample_payload(payload_or_item)
    return {
        "freshness_date": freshness_date,
        "freshness_status": status,
        "public_visible": status == FRESHNESS_FRESH and (get_settings().review_show_sample or not is_sample),
    }


def is_onbid_item_public_visible(item: AuctionItem, *, min_date: str | None = None) -> bool:
    if not get_settings().review_show_sample and is_onbid_sample_item(item):
        return False
    status = getattr(item, "freshness_status", "") or ""
    freshness_date = getattr(item, "freshness_date", "") or ""
    if freshness_date and is_implausible_onbid_public_date(parse_onbid_date(freshness_date)):
        return False
    if not freshness_date or status in (FRESHNESS_UNKNOWN, FRESHNESS_INVALID):
        freshness = evaluate_onbid_payload_freshness(item, min_date=min_date)
        status = freshness["freshness_status"]
    return status == FRESHNESS_FRESH


def build_onbid_info_badges(item: AuctionItem) -> dict[str, Any]:
    has_price = bool(item.minimum_bid_price or item.appraisal_price)
    has_location = bool((item.address or "").strip())
    has_schedule = bool((item.bid_end_at or "").strip())
    has_notice = bool(item.notice_links or item.pbanc_mng_no)
    detail_values = (item.item_description, item.attachment_summary, item.cautions, item.bid_condition, item.contract_condition)
    has_detail = sum(bool(str(value or "").strip()) for value in detail_values) >= 1
    has_source_url = bool(get_onbid_external_url(item))
    available: list[str] = []
    missing: list[str] = []
    checks = [
        (has_price, "가격 정보: 확인됨", "가격 정보: 확인 필요"),
        (has_location, "소재지: 확인됨", "소재지: 확인 필요"),
        (has_schedule, "입찰 일정: 확인됨", "입찰 일정: 확인 필요"),
        (has_notice, "공고 연결: 확인됨", "공고 연결: 확인 필요"),
        (has_detail, "상세 설명: 확인됨", "상세 설명: 확인 필요"),
        (has_source_url, "원문 링크: 확인됨", "원문 링크: 확인 필요"),
    ]
    for ok, available_label, missing_label in checks:
        (available if ok else missing).append(available_label if ok else missing_label)
    return {
        "available": available,
        "missing": missing,
        "has_critical_missing": not (has_price and has_location and has_schedule),
    }


def apply_data_quality_filter(statement, data_quality: str):
    if data_quality != "needs_confirmation":
        return statement
    return statement.where(
        or_(
            AuctionItem.minimum_bid_price <= 0,
            AuctionItem.appraisal_price <= 0,
            AuctionItem.address == "",
            AuctionItem.bid_end_at == "",
            AuctionItem.item_description == "",
            AuctionItem.attachment_summary == "",
            ~AuctionItem.notice_links.any(),
        )
    )


def supports_development_insight(item_or_category: Any) -> bool:
    if isinstance(item_or_category, str):
        category = normalize_public_category(item_or_category)
    else:
        category = normalize_public_category(getattr(item_or_category, "public_category", "") or derive_onbid_category(item_or_category))
    return category == "real_estate"


def normalize_match_text(value: str) -> str:
    text = str(value or "").lower()
    replacements = {
        "서울특별시": "서울",
        "서울시": "서울",
        "인천광역시": "인천",
        "충청남도": "충남",
        "경상북도": "경북",
        "전라남도": "전남",
        "주식회사": "",
        "(주)": "",
        "㈜": "",
    }
    for source, target in replacements.items():
        text = text.replace(source.lower(), target.lower())
    return re.sub(r"[^0-9a-z가-힣]", "", text)


def token_score(left: str, right: str, points: int) -> int:
    left_norm = normalize_match_text(left)
    right_norm = normalize_match_text(right)
    if not left_norm or not right_norm:
        return 0
    if left_norm in right_norm or right_norm in left_norm:
        return points
    left_tokens = {token for token in re.split(r"\s+", left) if len(token) >= 2}
    right_tokens = {token for token in re.split(r"\s+", right) if len(token) >= 2}
    if left_tokens and right_tokens and left_tokens.intersection(right_tokens):
        return max(5, points // 2)
    return 0


def calculate_discount_rate(appraisal_price: int, minimum_bid_price: int) -> float:
    if appraisal_price <= 0 or minimum_bid_price <= 0:
        return 0.0
    return round(max(0.0, 1 - (minimum_bid_price / appraisal_price)) * 100, 2)


def calculate_minimum_price_rate(appraisal_price: int, minimum_bid_price: int) -> float:
    if appraisal_price <= 0 or minimum_bid_price <= 0:
        return 0.0
    return round((minimum_bid_price / appraisal_price) * 100, 2)


def calculate_recovery_estimates(item: AuctionItem) -> dict[str, int]:
    conservative = int(item.minimum_bid_price * 0.9)
    base = int(item.minimum_bid_price)
    optimistic = int(item.appraisal_price * 0.75) if item.appraisal_price else base
    return {
        "conservative": conservative,
        "base": base,
        "optimistic": optimistic,
    }


def calculate_liquidation_score(item: AuctionItem) -> tuple[int, list[str]]:
    score = 50
    reasons: list[str] = []
    discount = calculate_discount_rate(item.appraisal_price, item.minimum_bid_price)
    if discount >= 30:
        score += 10
        reasons.append("감정가와 최저입찰가 차이가 큽니다. 가격 산정 근거는 원문에서 확인하세요.")
    elif discount >= 10:
        score += 5
        reasons.append("감정가와 최저입찰가 차이가 있습니다. 가격 정보는 원문 확인이 필요합니다.")
    else:
        reasons.append("가격 정보는 원문에서 직접 확인하세요.")

    d_day = calculate_d_day(item.bid_end_at)["days"]
    if d_day is None:
        score -= 5
        reasons.append("입찰 마감일 확인이 필요합니다.")
    elif 0 <= d_day <= 7:
        score -= 5
        reasons.append("입찰 마감이 임박했습니다.")
    elif d_day > 7:
        score += 5
        reasons.append("검토 가능한 시간이 남아 있습니다.")

    if item.attachment_summary or item.item_description:
        score += 5
        reasons.append("공고 또는 상세 자료가 있습니다.")
    else:
        score -= 5
        reasons.append("상세 자료 보강이 필요합니다.")

    if "유찰" in item.status:
        score -= 5
        reasons.append("유찰 이력이 있는지 원문에서 확인하세요.")
    if "종료" in item.status:
        score -= 20
        reasons.append("종료 상태로 보입니다.")
    if "부동산" in item.asset_type:
        score += 3
        reasons.append("부동산 항목입니다.")

    return max(0, min(100, score)), reasons


def calculate_d_day(value: str, *, now: datetime | None = None) -> dict[str, Any]:
    return get_onbid_deadline_status(value, now=now)


def normalize_auction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_payload = payload.get("_raw") if isinstance(payload.get("_raw"), dict) else payload
    source_api = str_value(payload, "_source_api", "source_api")
    cltr_mng_no = str_value(payload, "cltrMngNo", "cltr_mng_no")
    pbct_cdtn_no = str_value(payload, "pbctCdtnNo", "pbct_cdtn_no")
    if not cltr_mng_no:
        seed = "|".join(str_value(payload, key) for key in ("pbancMngNo", "noticeNo", "itemNo", "cltrNm", "itemName"))
        cltr_mng_no = "derived-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    if not pbct_cdtn_no:
        seed = "|".join(str_value(payload, key) for key in ("pbctNo", "pbctNsq", "pbancMngNo", "itemNo", "cltrNm", "itemName"))
        pbct_cdtn_no = "derived-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    category = derive_onbid_category(
        {
            "source_api": source_api,
            "asset_type": str_value(payload, "assetType", "asset_type", "자산구분", default="부동산"),
            "usage": str_value(payload, "usage", "용도"),
            "category": str_value(payload, "category"),
            "raw_payload": raw_payload,
        }
    )
    freshness = evaluate_onbid_payload_freshness(payload)
    return {
        "source": str_value(payload, "source", default="ONBID"),
        "cltr_mng_no": cltr_mng_no,
        "pbct_cdtn_no": pbct_cdtn_no,
        "pbanc_mng_no": str_value(payload, "pbancMngNo", "pbanc_mng_no"),
        "onbid_cltr_no": str_value(payload, "onbidCltrno", "onbid_cltr_no"),
        "pbct_no": str_value(payload, "pbctNo", "pbct_no"),
        "pbct_nsq": str_value(payload, "pbctNsq", "pbct_nsq"),
        "item_name": str_value(payload, "itemName", "item_name", "물건명"),
        "asset_type": str_value(payload, "assetType", "asset_type", "자산구분", default="부동산"),
        "disposal_method": str_value(payload, "disposalMethod", "disposal_method", "처분방식"),
        "bid_method": str_value(payload, "bidMethod", "bid_method", "입찰방식"),
        "address": str_value(payload, "address", "소재지"),
        "latitude": str_value(payload, "latitude"),
        "longitude": str_value(payload, "longitude"),
        "appraisal_price": digits_to_int(payload.get("appraisalPrice") or payload.get("appraisal_price") or payload.get("감정가")),
        "minimum_bid_price": digits_to_int(payload.get("minimumBidPrice") or payload.get("minimum_bid_price") or payload.get("최저입찰가")),
        "bid_deposit": digits_to_int(payload.get("bidDeposit") or payload.get("bid_deposit")),
        "bid_start_at": str_value(payload, "bidStartAt", "bid_start_at", "입찰시작일"),
        "bid_end_at": str_value(payload, "bidEndAt", "bid_end_at", "입찰마감일"),
        "open_bid_at": str_value(payload, "openBidAt", "open_bid_at", "개찰일"),
        "status": str_value(payload, "status", "진행상태", default="입찰예정"),
        "agency_name": str_value(payload, "agencyName", "agency_name", "공고기관"),
        "photo_url": str_value(payload, "photoUrl", "photo_url"),
        "attachment_summary": str_value(payload, "attachmentSummary", "attachment_summary", "첨부파일"),
        "land_area": str_value(payload, "landArea", "land_area", "토지면적"),
        "building_area": str_value(payload, "buildingArea", "building_area", "건물면적"),
        "land_category": str_value(payload, "landCategory", "land_category", "지목"),
        "usage": str_value(payload, "usage", "용도"),
        "item_description": str_value(payload, "itemDescription", "item_description", "물건 설명"),
        "bid_condition": str_value(payload, "bidCondition", "bid_condition", "입찰 조건"),
        "contract_condition": str_value(payload, "contractCondition", "contract_condition", "계약 조건"),
        "cautions": str_value(payload, "cautions", "유의사항"),
        "public_category": category,
        "freshness_date": freshness["freshness_date"],
        "freshness_status": freshness["freshness_status"],
        "public_visible": bool(freshness["public_visible"]),
        "raw_payload": json_dump({"_source_api": source_api, **raw_payload} if source_api else raw_payload),
    }


def upsert_auction_item(session: Session, payload: dict[str, Any]) -> tuple[AuctionItem, bool]:
    data = normalize_auction_payload(payload)
    existing = session.scalar(
        select(AuctionItem).where(
            AuctionItem.source == data["source"],
            AuctionItem.cltr_mng_no == data["cltr_mng_no"],
            AuctionItem.pbct_cdtn_no == data["pbct_cdtn_no"],
        )
    )
    created = existing is None
    item = existing or AuctionItem()
    for key, value in data.items():
        setattr(item, key, value)
    if created:
        session.add(item)
    session.flush()
    session.add(
        AuctionItemSnapshot(
            auction_item_id=item.id,
            status=item.status,
            appraisal_price=item.appraisal_price,
            minimum_bid_price=item.minimum_bid_price,
            bid_start_at=item.bid_start_at,
            bid_end_at=item.bid_end_at,
            open_bid_at=item.open_bid_at,
            raw_payload=item.raw_payload,
        )
    )
    if item.pbanc_mng_no:
        upsert_auction_notice(session, item, payload)
    session.flush()
    return item, created


def upsert_auction_notice(session: Session, item: AuctionItem, payload: dict[str, Any]) -> AuctionNotice:
    notice_payload = {
        **payload,
        "source": item.source,
        "pbancMngNo": item.pbanc_mng_no,
        "pbctNo": item.pbct_no,
        "pbctNsq": item.pbct_nsq,
        "pbctCdtnNo": item.pbct_cdtn_no,
        "noticeTitle": str_value(payload, "noticeTitle", "notice_title", default=item.item_name),
        "noticeBody": str_value(payload, "noticeBody", "notice_body", default=item.item_description),
        "agencyName": item.agency_name,
        "disposalMethod": item.disposal_method,
        "bidMethod": item.bid_method,
        "bidStartAt": item.bid_start_at,
        "bidEndAt": item.bid_end_at,
        "openBidAt": item.open_bid_at,
    }
    notice, _ = upsert_auction_notice_payload(session, notice_payload)
    session.flush()
    return notice


def normalize_notice_datetime(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) >= 12 and text[:12].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]} {text[8:10]}:{text[10:12]}"
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def normalize_onbid_notice(payload: dict[str, Any], *, detail_payload: dict[str, Any] | None = None, item_count: int | None = None) -> dict[str, Any]:
    merged = dict(payload)
    if detail_payload:
        for key, value in detail_payload.items():
            if value not in (None, ""):
                merged[key] = value
    raw_payload = payload.get("_raw") if isinstance(payload.get("_raw"), dict) else payload
    return {
        "source": str_value(merged, "source", default="ONBID"),
        "pbanc_mng_no": str_value(merged, "pbancMngNo", "onbidPbancNo", "pbancNo", "pbanc_mng_no", "noticeNo"),
        "notice_no": str_value(merged, "noticeNo", "pbancNo", "onbidPbancNo", "pbancMngNo"),
        "pbct_no": str_value(merged, "pbctNo", "pbct_no"),
        "pbct_nsq": str_value(merged, "pbctNsq", "pbct_nsq"),
        "pbct_cdtn_no": str_value(merged, "pbctCdtnNo", "pbct_cdtn_no"),
        "notice_title": str_value(
            merged,
            "pbancNm",
            "pbancTtl",
            "noticeTitle",
            "notice_title",
            "title",
            "onbidPbancNm",
            "cltrNm",
            "itemName",
        ),
        "notice_body": str_value(
            merged,
            "noticeBody",
            "notice_body",
            "pbancDtlCn",
            "pbancCont",
            "dtlCont",
            "cltrEtcCont",
            "itemDescription",
        ),
        "notice_status": str_value(merged, "pbancStatNm", "pbctStatNm", "noticeStatus", "status"),
        "notice_type": str_value(merged, "pbancKndNm", "pbancTypeNm", "noticeType"),
        "notice_date": normalize_notice_datetime(str_value(merged, "pbancDt", "opbdDt", "noticeDate")),
        "bid_start_at": normalize_notice_datetime(str_value(merged, "bidStartAt", "cltrBidBgngDt", "pbctBgngDt", "opbdDtStart")),
        "bid_end_at": normalize_notice_datetime(str_value(merged, "bidEndAt", "cltrBidEndDt", "pbctEndDt", "opbdDtEnd")),
        "open_at": normalize_notice_datetime(str_value(merged, "openBidAt", "opengDt", "openAt")),
        "agency_name": str_value(merged, "orgNm", "rqstOrgNm", "agencyName", "institutionName"),
        "department_name": str_value(merged, "deptNm", "departmentName", "chargerDeptNm"),
        "disposal_method": str_value(merged, "dspsMthodNm", "dtlDspsMthodNm", "disposalMethod"),
        "bid_method": str_value(merged, "cptnMthodNm", "bidDivNm", "bidMthodNm", "bidMethod"),
        "detail_url": str_value(merged, "dtlUrl", "detailUrl", "pbancUrl"),
        "item_count": int(item_count if item_count is not None else digits_to_int(str_value(merged, "cltrCnt", "itemCount", default="0"))),
        "raw_payload": json_dump(raw_payload),
        "detail_payload": json_dump(detail_payload or {}),
    }


def upsert_auction_notice_payload(
    session: Session,
    payload: dict[str, Any],
    *,
    detail_payload: dict[str, Any] | None = None,
    item_count: int | None = None,
) -> tuple[AuctionNotice, bool]:
    data = normalize_onbid_notice(payload, detail_payload=detail_payload, item_count=item_count)
    statement = select(AuctionNotice).where(AuctionNotice.source == data["source"])
    if data["pbanc_mng_no"]:
        statement = statement.where(AuctionNotice.pbanc_mng_no == data["pbanc_mng_no"])
    else:
        statement = statement.where(AuctionNotice.notice_no == data["notice_no"])
    existing = session.scalar(statement)
    created = existing is None
    notice = existing or AuctionNotice(source=data["source"], pbanc_mng_no=data["pbanc_mng_no"])
    for key, value in data.items():
        setattr(notice, key, value)
    now = datetime.now()
    notice.last_seen_at = now
    notice.updated_at = now
    if created:
        session.add(notice)
    session.flush()
    return notice, created


def upsert_auction_notice_item_link(
    session: Session,
    notice: AuctionNotice,
    auction_item: AuctionItem,
    payload: dict[str, Any],
) -> tuple[AuctionNoticeItemLink, bool]:
    existing = session.scalar(
        select(AuctionNoticeItemLink).where(
            AuctionNoticeItemLink.source == notice.source,
            AuctionNoticeItemLink.notice_id == notice.id,
            AuctionNoticeItemLink.auction_item_id == auction_item.id,
        )
    )
    created = existing is None
    link = existing or AuctionNoticeItemLink(
        source=notice.source,
        notice_id=notice.id,
        auction_item_id=auction_item.id,
    )
    link.notice_no = notice.notice_no
    link.pbanc_mng_no = notice.pbanc_mng_no
    link.pbct_no = auction_item.pbct_no or notice.pbct_no
    link.pbct_nsq = auction_item.pbct_nsq or notice.pbct_nsq
    link.cltr_mng_no = auction_item.cltr_mng_no
    link.pbct_cdtn_no = auction_item.pbct_cdtn_no or notice.pbct_cdtn_no
    link.raw_payload = json_dump(payload.get("_raw") if isinstance(payload.get("_raw"), dict) else payload)
    link.updated_at = datetime.now()
    if created:
        session.add(link)
    session.flush()
    return link, created


def list_auction_items(
    session: Session,
    *,
    status: str = "ALL",
    asset_type: str = "ALL",
    keyword: str = "",
    linked: str = "ALL",
    region: str = "",
    usage: str = "",
    agency: str = "",
    price_min: int | None = None,
    price_max: int | None = None,
    closing_within_days: int | None = None,
    min_discount_rate: float | None = None,
    has_notice: str = "ALL",
    has_detail: str = "ALL",
    data_quality: str = "ALL",
    category: str = "all",
    public_only: bool = False,
    active_only: bool = False,
    notice_id: int | None = None,
    pbanc_mng_no: str = "",
    sort: str = "closing_soon",
    limit: int = 50,
    offset: int = 0,
) -> list[AuctionItem]:
    statement = select(AuctionItem).options(
        joinedload(AuctionItem.case_links),
        joinedload(AuctionItem.notice_links).joinedload(AuctionNoticeItemLink.notice),
    )
    if public_only:
        statement = apply_public_onbid_freshness_filter(statement)
    if status != "ALL":
        statement = statement.where(AuctionItem.status == status)
    if asset_type != "ALL":
        statement = statement.where(AuctionItem.asset_type == asset_type)
    if keyword:
        pattern = f"%{keyword}%"
        statement = statement.where(or_(AuctionItem.item_name.like(pattern), AuctionItem.address.like(pattern), AuctionItem.cltr_mng_no.like(pattern)))
    if region:
        statement = statement.where(AuctionItem.address.like(f"%{region}%"))
    if usage:
        statement = statement.where(or_(AuctionItem.usage.like(f"%{usage}%"), AuctionItem.land_category.like(f"%{usage}%")))
    if agency:
        statement = statement.where(AuctionItem.agency_name.like(f"%{agency}%"))
    if price_min is not None:
        statement = statement.where(AuctionItem.minimum_bid_price >= price_min)
    if price_max is not None:
        statement = statement.where(AuctionItem.minimum_bid_price <= price_max)
    if closing_within_days is not None:
        today = date.today()
        end_date = today + timedelta(days=closing_within_days)
        statement = statement.where(AuctionItem.bid_end_at >= today.isoformat(), AuctionItem.bid_end_at <= f"{end_date.isoformat()}T23:59:59")
    if linked == "linked":
        statement = statement.where(AuctionItem.case_links.any())
    if linked == "unlinked":
        statement = statement.where(~AuctionItem.case_links.any())
    if has_notice == "yes":
        statement = statement.where(AuctionItem.notice_links.any())
    if has_notice == "no":
        statement = statement.where(~AuctionItem.notice_links.any())
    if has_detail == "yes":
        statement = statement.where(or_(AuctionItem.item_description != "", AuctionItem.attachment_summary != ""))
    if has_detail == "no":
        statement = statement.where(AuctionItem.item_description == "", AuctionItem.attachment_summary == "")
    statement = apply_data_quality_filter(statement, data_quality)
    statement = apply_onbid_category_filter(statement, category)
    if notice_id is not None:
        statement = statement.where(AuctionItem.notice_links.any(AuctionNoticeItemLink.notice_id == notice_id))
    if pbanc_mng_no:
        statement = statement.where(AuctionItem.pbanc_mng_no == pbanc_mng_no)
    if min_discount_rate is not None:
        discount_expr = (1 - (AuctionItem.minimum_bid_price * 1.0 / func.nullif(AuctionItem.appraisal_price, 0))) * 100
        statement = statement.where(AuctionItem.appraisal_price > 0, discount_expr >= min_discount_rate)
    orderings = {
        "newest": (AuctionItem.created_at.desc(), AuctionItem.id.desc()),
        "discount_desc": (AuctionItem.appraisal_price.desc(), AuctionItem.minimum_bid_price.asc()),
        "price_asc": (AuctionItem.minimum_bid_price.asc(), AuctionItem.id.desc()),
        "price_desc": (AuctionItem.minimum_bid_price.desc(), AuctionItem.id.desc()),
        "updated_desc": (AuctionItem.updated_at.desc(), AuctionItem.id.desc()),
    }
    active_first = case((AuctionItem.bid_end_at >= date.today().isoformat(), 0), else_=1)
    ordering = orderings.get(sort, (active_first.asc(), AuctionItem.bid_end_at.asc(), AuctionItem.id.desc()))
    items = list(session.scalars(statement.order_by(*ordering)).unique())
    if active_only or closing_within_days is not None or sort == "closing_soon":
        statuses = {item.id: get_onbid_deadline_status(item.bid_end_at) for item in items}
        if active_only:
            items = [item for item in items if statuses[item.id]["is_active"]]
        if closing_within_days is not None:
            items = [item for item in items if statuses[item.id]["is_active"] and statuses[item.id]["days"] <= closing_within_days]
        if sort == "closing_soon":
            items.sort(key=lambda item: (0 if statuses[item.id]["is_active"] else 1, statuses[item.id]["days"] if statuses[item.id]["is_active"] else 10**6, item.id * -1))
    return items[offset : offset + limit]


def count_auction_items(
    session: Session,
    *,
    status: str = "ALL",
    asset_type: str = "ALL",
    keyword: str = "",
    linked: str = "ALL",
    region: str = "",
    usage: str = "",
    agency: str = "",
    price_min: int | None = None,
    price_max: int | None = None,
    closing_within_days: int | None = None,
    min_discount_rate: float | None = None,
    has_notice: str = "ALL",
    has_detail: str = "ALL",
    data_quality: str = "ALL",
    category: str = "all",
    public_only: bool = False,
    active_only: bool = False,
    notice_id: int | None = None,
    pbanc_mng_no: str = "",
) -> int:
    statement = select(func.count(AuctionItem.id))
    if public_only:
        statement = apply_public_onbid_freshness_filter(statement)
    if status != "ALL":
        statement = statement.where(AuctionItem.status == status)
    if asset_type != "ALL":
        statement = statement.where(AuctionItem.asset_type == asset_type)
    if keyword:
        pattern = f"%{keyword}%"
        statement = statement.where(or_(AuctionItem.item_name.like(pattern), AuctionItem.address.like(pattern), AuctionItem.cltr_mng_no.like(pattern)))
    if region:
        statement = statement.where(AuctionItem.address.like(f"%{region}%"))
    if usage:
        statement = statement.where(or_(AuctionItem.usage.like(f"%{usage}%"), AuctionItem.land_category.like(f"%{usage}%")))
    if agency:
        statement = statement.where(AuctionItem.agency_name.like(f"%{agency}%"))
    if price_min is not None:
        statement = statement.where(AuctionItem.minimum_bid_price >= price_min)
    if price_max is not None:
        statement = statement.where(AuctionItem.minimum_bid_price <= price_max)
    if closing_within_days is not None:
        today = date.today()
        end_date = today + timedelta(days=closing_within_days)
        statement = statement.where(AuctionItem.bid_end_at >= today.isoformat(), AuctionItem.bid_end_at <= f"{end_date.isoformat()}T23:59:59")
    if linked == "linked":
        statement = statement.where(AuctionItem.case_links.any())
    if linked == "unlinked":
        statement = statement.where(~AuctionItem.case_links.any())
    if has_notice == "yes":
        statement = statement.where(AuctionItem.notice_links.any())
    if has_notice == "no":
        statement = statement.where(~AuctionItem.notice_links.any())
    if has_detail == "yes":
        statement = statement.where(or_(AuctionItem.item_description != "", AuctionItem.attachment_summary != ""))
    if has_detail == "no":
        statement = statement.where(AuctionItem.item_description == "", AuctionItem.attachment_summary == "")
    statement = apply_data_quality_filter(statement, data_quality)
    statement = apply_onbid_category_filter(statement, category)
    if notice_id is not None:
        statement = statement.where(AuctionItem.notice_links.any(AuctionNoticeItemLink.notice_id == notice_id))
    if pbanc_mng_no:
        statement = statement.where(AuctionItem.pbanc_mng_no == pbanc_mng_no)
    if min_discount_rate is not None:
        discount_expr = (1 - (AuctionItem.minimum_bid_price * 1.0 / func.nullif(AuctionItem.appraisal_price, 0))) * 100
        statement = statement.where(AuctionItem.appraisal_price > 0, discount_expr >= min_discount_rate)
    if active_only or closing_within_days is not None:
        items = list(session.scalars(statement.with_only_columns(AuctionItem)))
        return sum(
            1
            for item in items
            if get_onbid_deadline_status(item.bid_end_at)["is_active"]
            and (closing_within_days is None or get_onbid_deadline_status(item.bid_end_at)["days"] <= closing_within_days)
        )
    return session.scalar(statement) or 0


def apply_onbid_category_filter(statement, category: str):
    normalized = normalize_public_category(category)
    if normalized in ("", "all"):
        return statement
    if normalized == "national_property":
        return statement.where(
            or_(
                AuctionItem.public_category == "national_property",
                AuctionItem.raw_payload.like("%national_property%"),
                AuctionItem.raw_payload.like("%bid_target%"),
                AuctionItem.raw_payload.like("%국유%"),
            )
        )
    real_estate_condition = or_(
        AuctionItem.asset_type.like("%Real estate%"),
        AuctionItem.asset_type.like("%부동산%"),
        AuctionItem.asset_type.like("%토지%"),
        AuctionItem.asset_type.like("%건물%"),
        AuctionItem.usage.like("%부동산%"),
        AuctionItem.usage.like("%토지%"),
        AuctionItem.usage.like("%건물%"),
        AuctionItem.raw_payload.like("%real_estate%"),
        AuctionItem.public_category == "real_estate",
    )
    movable_condition = or_(
        AuctionItem.asset_type.like("%Movable%"),
        AuctionItem.asset_type.like("%동산%"),
        AuctionItem.asset_type.like("%차량%"),
        AuctionItem.asset_type.like("%기계%"),
        AuctionItem.usage.like("%차량%"),
        AuctionItem.usage.like("%기계%"),
        AuctionItem.usage.like("%장비%"),
        AuctionItem.raw_payload.like("%movable%"),
        AuctionItem.public_category == "movable",
    )
    if normalized == "real_estate":
        return statement.where(real_estate_condition)
    if normalized == "movable":
        return statement.where(movable_condition)
    if normalized == "other":
        return statement.where(
            ~real_estate_condition,
            ~movable_condition,
            ~AuctionItem.raw_payload.like("%national_property%"),
            ~AuctionItem.raw_payload.like("%bid_target%"),
            or_(AuctionItem.public_category == "other", AuctionItem.public_category == ""),
        )
    return statement


def apply_public_onbid_freshness_filter(statement, *, min_date: str | None = None):
    settings = get_settings()
    min_public_date = min_date or settings.onbid_min_public_date or ONBID_MIN_PUBLIC_DATE
    max_public_date = max_public_onbid_date().isoformat()
    sample_condition = or_(
        AuctionItem.cltr_mng_no.like("%ONBID-REAL-202607%"),
        AuctionItem.cltr_mng_no.like("%ONBID-MOVABLE-202607%"),
        AuctionItem.cltr_mng_no.like("%ONBID-NATIONAL-202607%"),
        AuctionItem.cltr_mng_no.like("%NOTICE-CLTR-202607%"),
        AuctionItem.item_name.like("%sample%"),
        AuctionItem.item_name.like("%fixture%"),
        AuctionItem.address.like("%sample%"),
        AuctionItem.raw_payload.like("%sample%"),
        AuctionItem.raw_payload.like("%fixture%"),
    )
    if not settings.onbid_public_hide_stale:
        statement = statement.where(AuctionItem.source == "ONBID")
        return statement if settings.review_show_sample else statement.where(~sample_condition)
    date_candidates = (
        (
            (AuctionItem.freshness_status == FRESHNESS_FRESH)
            & (AuctionItem.freshness_date >= min_public_date)
            & (AuctionItem.freshness_date <= max_public_date)
        ),
        (
            AuctionItem.bid_start_at.like("20%")
            & (AuctionItem.bid_start_at >= min_public_date)
            & (AuctionItem.bid_start_at <= max_public_date)
        ),
        (
            AuctionItem.bid_end_at.like("20%")
            & (AuctionItem.bid_end_at >= min_public_date)
            & (AuctionItem.bid_end_at <= max_public_date)
        ),
        (
            AuctionItem.open_bid_at.like("20%")
            & (AuctionItem.open_bid_at >= min_public_date)
            & (AuctionItem.open_bid_at <= max_public_date)
        ),
    )
    base_conditions = [AuctionItem.source == "ONBID"]
    if not settings.review_show_sample:
        base_conditions.append(~sample_condition)
    if settings.onbid_public_hide_unknown_date:
        return statement.where(
            *base_conditions,
            or_(*date_candidates),
        )
    return statement.where(
        *base_conditions,
        or_(AuctionItem.freshness_status == FRESHNESS_UNKNOWN, *date_candidates),
    )


def get_onbid_category_counts(session: Session, *, public_only: bool = False) -> dict[str, int]:
    counts = {key: 0 for key in ONBID_CATEGORY_LABELS}
    for item in session.scalars(select(AuctionItem).where(AuctionItem.source == "ONBID")):
        if public_only and not is_onbid_item_public_visible(item):
            continue
        category = normalize_public_category(getattr(item, "public_category", "") or derive_onbid_category(item))
        counts[category] = counts.get(category, 0) + 1
    counts["all"] = sum(count for key, count in counts.items() if key != "all")
    return counts


def audit_onbid_freshness(session: Session, *, min_date: str | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": 0,
        FRESHNESS_FRESH: 0,
        FRESHNESS_STALE: 0,
        FRESHNESS_UNKNOWN: 0,
        FRESHNESS_INVALID: 0,
        "by_category": {key: 0 for key in ONBID_CATEGORY_LABELS},
    }
    for item in session.scalars(select(AuctionItem).where(AuctionItem.source == "ONBID")):
        summary["total"] += 1
        freshness = evaluate_onbid_payload_freshness(item, min_date=min_date)
        summary[freshness["freshness_status"]] += 1
        category = normalize_public_category(getattr(item, "public_category", "") or derive_onbid_category(item))
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
    return summary


def repair_onbid_derived_fields(session: Session, *, dry_run: bool = True, min_date: str | None = None) -> dict[str, int]:
    result = {"checked": 0, "would_update": 0, "updated": 0}
    for item in session.scalars(select(AuctionItem).where(AuctionItem.source == "ONBID")):
        result["checked"] += 1
        category = derive_onbid_category(item)
        freshness = evaluate_onbid_payload_freshness(item, min_date=min_date)
        changed = (
            item.public_category != category
            or item.freshness_date != freshness["freshness_date"]
            or item.freshness_status != freshness["freshness_status"]
            or bool(item.public_visible) != bool(freshness["public_visible"])
        )
        if not changed:
            continue
        result["would_update"] += 1
        if dry_run:
            continue
        item.public_category = category
        item.freshness_date = freshness["freshness_date"]
        item.freshness_status = freshness["freshness_status"]
        item.public_visible = bool(freshness["public_visible"])
        result["updated"] += 1
    if not dry_run:
        session.flush()
    return result


def get_auction_item(session: Session, item_id: int) -> AuctionItem | None:
    return session.scalar(
        select(AuctionItem)
        .options(
            joinedload(AuctionItem.snapshots),
            joinedload(AuctionItem.results),
            joinedload(AuctionItem.case_links).joinedload(CaseAuctionLink.case_event),
            joinedload(AuctionItem.notice_links).joinedload(AuctionNoticeItemLink.notice),
        )
        .where(AuctionItem.id == item_id)
    )


def list_same_notice_items(session: Session, item: AuctionItem, *, limit: int = 20) -> list[AuctionItem]:
    notice_ids = [link.notice_id for link in item.notice_links]
    if notice_ids:
        return list(
            session.scalars(
                select(AuctionItem)
                .options(joinedload(AuctionItem.notice_links).joinedload(AuctionNoticeItemLink.notice))
                .where(
                    AuctionItem.id != item.id,
                    AuctionItem.notice_links.any(AuctionNoticeItemLink.notice_id.in_(notice_ids)),
                )
                .order_by(AuctionItem.minimum_bid_price.asc(), AuctionItem.id.desc())
                .limit(limit)
            ).unique()
        )
    if item.pbanc_mng_no:
        return list(
            session.scalars(
                select(AuctionItem)
                .options(joinedload(AuctionItem.notice_links).joinedload(AuctionNoticeItemLink.notice))
                .where(AuctionItem.id != item.id, AuctionItem.pbanc_mng_no == item.pbanc_mng_no)
                .order_by(AuctionItem.minimum_bid_price.asc(), AuctionItem.id.desc())
                .limit(limit)
            ).unique()
        )
    return []


def create_case_auction_link(
    session: Session,
    *,
    case_id: int,
    auction_item_id: int,
    link_status: str = "confirmed",
    match_type: str = "manual",
    match_score: float = 100,
    memo: str = "",
    assigned_user_id: int | None = None,
) -> CaseAuctionLink:
    existing = session.scalar(
        select(CaseAuctionLink).where(
            CaseAuctionLink.case_id == case_id,
            CaseAuctionLink.auction_item_id == auction_item_id,
        )
    )
    link = existing or CaseAuctionLink(case_id=case_id, auction_item_id=auction_item_id)
    link.link_status = link_status
    link.match_type = match_type
    link.match_score = Decimal(str(match_score))
    link.memo = memo
    link.assigned_user_id = assigned_user_id
    if existing is None:
        event = session.get(AssetEvent, case_id)
        if event:
            link.asset_id = event.asset_id
        session.add(link)
    session.flush()
    return link


def build_link_candidate(event: AssetEvent, item: AuctionItem) -> dict[str, Any] | None:
    score = 0
    reasons: list[str] = []
    address_score = token_score(event.asset.address, item.address, 50)
    if address_score:
        score += address_score
        reasons.append(f"二쇱냼 ?좎궗 +{address_score}")
    title_score = token_score(event.title, item.item_name, 20)
    if title_score:
        score += title_score
        reasons.append(f"臾쇨굔紐?怨듦퀬紐??좎궗 +{title_score}")
    if event.case_number and event.case_number in item.item_description + item.cautions + item.raw_payload:
        score += 50
        reasons.append("怨듦퀬臾몄뿉 ?ш굔踰덊샇 ?ы븿 +50")
    if event.asset.main_category and event.asset.main_category in item.asset_type:
        score += 10
        reasons.append("?먯궛 ?좏삎 ?쇱튂 +10")
    if score < 30:
        return None
    if score >= 80:
        strength = "媛뺥븳 ?꾨낫"
    elif score >= 50:
        strength = "寃???꾨낫"
    else:
        strength = "?쏀븳 ?꾨낫"
    return {
        "case_id": event.id,
        "case_number": event.case_number,
        "case_title": event.title,
        "case_address": event.asset.address,
        "auction_item_id": item.id,
        "auction_item_name": item.item_name,
        "auction_address": item.address,
        "score": min(score, 100),
        "strength": strength,
        "reasons": reasons,
    }


def find_link_candidates_for_auction(session: Session, auction_item_id: int, limit: int = 20) -> list[dict[str, Any]]:
    item = get_auction_item(session, auction_item_id)
    if item is None:
        return []
    events = list(
        session.scalars(
            select(AssetEvent)
            .options(joinedload(AssetEvent.asset))
            .order_by(AssetEvent.notice_date.desc(), AssetEvent.id.desc())
            .limit(200)
        ).unique()
    )
    existing_case_ids = {link.case_id for link in item.case_links}
    candidates = [
        candidate
        for event in events
        if event.id not in existing_case_ids
        for candidate in [build_link_candidate(event, item)]
        if candidate is not None
    ]
    return sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)[:limit]


def find_auction_candidates_for_case(session: Session, case_id: int, limit: int = 20) -> list[dict[str, Any]]:
    event = session.scalar(
        select(AssetEvent)
        .options(joinedload(AssetEvent.asset))
        .where(AssetEvent.id == case_id)
    )
    if event is None:
        return []
    items = list(
        session.scalars(
            select(AuctionItem)
            .options(joinedload(AuctionItem.case_links))
            .order_by(AuctionItem.bid_end_at.asc(), AuctionItem.id.desc())
            .limit(200)
        ).unique()
    )
    linked_item_ids = {
        link.auction_item_id
        for item in items
        for link in item.case_links
        if link.case_id == case_id
    }
    candidates = [
        candidate
        for item in items
        if item.id not in linked_item_ids
        for candidate in [build_link_candidate(event, item)]
        if candidate is not None
    ]
    return sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)[:limit]


def serialize_auction_item(item: AuctionItem) -> dict[str, Any]:
    discount = calculate_discount_rate(item.appraisal_price, item.minimum_bid_price)
    minimum_rate = calculate_minimum_price_rate(item.appraisal_price, item.minimum_bid_price)
    score, reasons = calculate_liquidation_score(item)
    category = derive_onbid_category(item)
    info_badges = build_onbid_info_badges(item)
    deadline_status = calculate_d_day(item.bid_end_at)
    raw_status = (item.status or "").strip()
    if deadline_status["state"] == "closed":
        display_status = "입찰마감"
    elif deadline_status["state"] == "unknown":
        display_status = "일정 확인 필요"
    elif "종료" in raw_status or "마감" in raw_status:
        display_status = "종료됨"
    else:
        display_status = raw_status or "입찰진행중"
    notices = [
        {
            "id": link.notice.id,
            "notice_title": link.notice.notice_title,
            "notice_status": link.notice.notice_status,
            "notice_type": link.notice.notice_type,
            "notice_date": link.notice.notice_date,
            "bid_start_at": link.notice.bid_start_at,
            "bid_end_at": link.notice.bid_end_at,
            "agency_name": link.notice.agency_name,
            "department_name": link.notice.department_name,
            "detail_url": link.notice.detail_url,
        }
        for link in item.notice_links
        if link.notice
    ]
    created_at = item.created_at
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    first_seen_at = created_at.astimezone(KST) if created_at else None
    updated_at = item.updated_at
    if updated_at and updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    last_updated_at = updated_at.astimezone(KST) if updated_at else None
    return {
        "id": item.id,
        "source": item.source,
        "cltr_mng_no": item.cltr_mng_no,
        "pbct_cdtn_no": item.pbct_cdtn_no,
        "pbanc_mng_no": item.pbanc_mng_no,
        "onbid_cltr_no": item.onbid_cltr_no,
        "pbct_no": item.pbct_no,
        "pbct_nsq": item.pbct_nsq,
        "item_name": item.item_name,
        "asset_type": item.asset_type,
        "disposal_method": item.disposal_method,
        "bid_method": item.bid_method,
        "address": item.address,
        "appraisal_price": item.appraisal_price,
        "minimum_bid_price": item.minimum_bid_price,
        "bid_deposit": item.bid_deposit,
        "bid_start_at": item.bid_start_at,
        "bid_end_at": item.bid_end_at,
        "open_bid_at": item.open_bid_at,
        "status": display_status,
        "source_status": raw_status,
        "agency_name": item.agency_name,
        "photo_url": item.photo_url,
        "attachment_summary": item.attachment_summary,
        "land_area": item.land_area,
        "building_area": item.building_area,
        "land_category": item.land_category,
        "usage": item.usage,
        "item_description": item.item_description,
        "bid_condition": item.bid_condition,
        "contract_condition": item.contract_condition,
        "cautions": item.cautions,
        "discount_rate": discount,
        "minimum_price_rate": minimum_rate,
        "recovery_estimates": calculate_recovery_estimates(item),
        "liquidation_score": score,
        "liquidation_reasons": reasons,
        "category": category,
        "category_label": get_onbid_category_label(category),
        "freshness_date": item.freshness_date or extract_onbid_freshness_date(item),
        "first_seen_at": first_seen_at.isoformat() if first_seen_at else "",
        "first_seen_date": first_seen_at.date().isoformat() if first_seen_at else "",
        "last_updated_at": last_updated_at.isoformat() if last_updated_at else "",
        "freshness_status": item.freshness_status or evaluate_onbid_payload_freshness(item)["freshness_status"],
        "public_visible": is_onbid_item_public_visible(item),
        "info_badges": info_badges,
        "d_day": deadline_status,
        "link_count": len(item.case_links),
        "notice_count": len(notices),
        "notices": notices,
        "has_detail": bool(item.item_description or item.attachment_summary or item.cautions or item.bid_condition or item.contract_condition),
        "supports_development_insight": supports_development_insight(item),
        "external_url": get_onbid_external_url(item),
        "original_search_fields": {
            "onbid_cltr_no": item.onbid_cltr_no,
            "pbct_no": item.pbct_no or item.pbct_cdtn_no,
            "agency_name": item.agency_name,
            "item_name": item.item_name,
            "bid_end_at": item.bid_end_at,
        },
    }


def get_onbid_external_url(item: AuctionItem) -> str:
    candidates: list[str] = []
    for link in item.notice_links:
        if link.notice and link.notice.detail_url:
            candidates.append(link.notice.detail_url)
    try:
        payload = json.loads(item.raw_payload or "{}")
    except (TypeError, json.JSONDecodeError):
        payload = {}
    for source in (payload, payload.get("_raw_list", {}), payload.get("_raw_detail", {})):
        if isinstance(source, dict):
            candidates.extend(str(source.get(key) or "") for key in ("detailUrl", "dtlUrl", "pbancUrl", "sourceUrl", "originalUrl"))
    for candidate in candidates:
        parsed = urlparse(candidate.strip())
        if parsed.scheme in {"http", "https"} and parsed.netloc and not any(token in parsed.query.lower() for token in ("servicekey=", "api_key=", "apikey=", "token=")):
            return candidate.strip()
    return ""

