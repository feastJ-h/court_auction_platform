from __future__ import annotations

import json
import re
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

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


def build_onbid_info_badges(item: AuctionItem) -> dict[str, Any]:
    has_price = bool(item.minimum_bid_price or item.appraisal_price)
    has_location = bool((item.address or "").strip())
    has_schedule = bool((item.bid_end_at or "").strip())
    has_notice = bool(item.notice_links or item.pbanc_mng_no)
    has_detail = bool(item.item_description or item.attachment_summary or item.cautions)
    has_source_url = any(link.notice and link.notice.detail_url for link in item.notice_links)
    available: list[str] = []
    missing: list[str] = []
    checks = [
        (has_price, "가격 정보 있음", "가격 정보 확인 필요"),
        (has_location, "소재지 있음", "소재지 정보 확인 필요"),
        (has_schedule, "입찰 일정 있음", "입찰 일정 확인 필요"),
        (has_notice, "공고 연결", "공고 연결 확인 필요"),
        (has_detail, "상세 정보 있음", "상세 정보 수집 필요"),
        (has_source_url, "원문 링크 있음", "원문 링크 확인 필요"),
    ]
    for ok, available_label, missing_label in checks:
        (available if ok else missing).append(available_label if ok else missing_label)
    return {
        "available": available,
        "missing": missing,
        "has_critical_missing": not (has_price and has_location and has_schedule),
    }


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
        score += 15
        reasons.append("저감률이 높아 가격 매력도가 있습니다.")
    elif discount >= 10:
        score += 8
        reasons.append("일정 수준의 가격 매력이 있습니다.")
    else:
        reasons.append("가격 매력도는 추가 검토가 필요합니다.")

    d_day = calculate_d_day(item.bid_end_at)["days"]
    if d_day is None:
        score -= 5
        reasons.append("입찰마감일이 불명확합니다.")
    elif 0 <= d_day <= 7:
        score -= 5
        reasons.append("입찰마감이 임박했습니다.")
    elif d_day > 7:
        score += 8
        reasons.append("검토 시간이 남아 있습니다.")

    if item.attachment_summary or item.item_description:
        score += 10
        reasons.append("공고/상세 자료가 있어 검토 가능합니다.")
    else:
        score -= 5
        reasons.append("상세 자료 보강이 필요합니다.")

    if "유찰" in item.status:
        score -= 10
        reasons.append("유찰 이력이 있어 보수적 접근이 필요합니다.")
    if "낙찰" in item.status:
        score -= 20
        reasons.append("이미 낙찰 상태일 수 있습니다.")
    if "부동산" in item.asset_type:
        score += 8
        reasons.append("부동산은 회생/파산 자산 연결 우선순위가 높습니다.")

    return max(0, min(100, score)), reasons


def calculate_d_day(value: str) -> dict[str, Any]:
    if not value:
        return {"label": "미정", "state": "unknown", "days": None}
    date_text = str(value)[:10]
    try:
        target = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return {"label": "미정", "state": "unknown", "days": None}
    delta = (target - date.today()).days
    if delta == 0:
        return {"label": "D-Day", "state": "urgent", "days": 0}
    if delta < 0:
        return {"label": f"D+{abs(delta)}", "state": "closed", "days": delta}
    return {"label": f"D-{delta}", "state": "urgent" if delta <= 7 else "normal", "days": delta}


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
    return {
        "source": str_value(payload, "source", default="ONBID"),
        "cltr_mng_no": cltr_mng_no,
        "pbct_cdtn_no": pbct_cdtn_no,
        "pbanc_mng_no": str_value(payload, "pbancMngNo", "pbanc_mng_no"),
        "onbid_cltr_no": str_value(payload, "onbidCltrno", "onbid_cltr_no"),
        "pbct_no": str_value(payload, "pbctNo", "pbct_no"),
        "pbct_nsq": str_value(payload, "pbctNsq", "pbct_nsq"),
        "item_name": str_value(payload, "itemName", "item_name", "물건명"),
        "asset_type": str_value(payload, "assetType", "asset_type", "재산구분", default="부동산"),
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
    category: str = "all",
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
        statement = statement.where(AuctionItem.bid_end_at >= today.isoformat(), AuctionItem.bid_end_at <= end_date.isoformat())
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
    ordering = orderings.get(sort, (AuctionItem.bid_end_at.asc(), AuctionItem.id.desc()))
    return list(
        session.scalars(
            statement.order_by(*ordering).limit(limit).offset(offset)
        ).unique()
    )


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
    category: str = "all",
    notice_id: int | None = None,
    pbanc_mng_no: str = "",
) -> int:
    statement = select(func.count(AuctionItem.id))
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
        statement = statement.where(AuctionItem.bid_end_at >= today.isoformat(), AuctionItem.bid_end_at <= end_date.isoformat())
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
    statement = apply_onbid_category_filter(statement, category)
    if notice_id is not None:
        statement = statement.where(AuctionItem.notice_links.any(AuctionNoticeItemLink.notice_id == notice_id))
    if pbanc_mng_no:
        statement = statement.where(AuctionItem.pbanc_mng_no == pbanc_mng_no)
    if min_discount_rate is not None:
        discount_expr = (1 - (AuctionItem.minimum_bid_price * 1.0 / func.nullif(AuctionItem.appraisal_price, 0))) * 100
        statement = statement.where(AuctionItem.appraisal_price > 0, discount_expr >= min_discount_rate)
    return session.scalar(statement) or 0


def apply_onbid_category_filter(statement, category: str):
    normalized = str(category or "all").lower()
    if normalized in ("", "all"):
        return statement
    if normalized == "national_property":
        return statement.where(
            or_(
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
        )
    return statement


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
        reasons.append(f"주소 유사 +{address_score}")
    title_score = token_score(event.title, item.item_name, 20)
    if title_score:
        score += title_score
        reasons.append(f"물건명/공고명 유사 +{title_score}")
    if event.case_number and event.case_number in item.item_description + item.cautions + item.raw_payload:
        score += 50
        reasons.append("공고문에 사건번호 포함 +50")
    if event.asset.main_category and event.asset.main_category in item.asset_type:
        score += 10
        reasons.append("자산 유형 일치 +10")
    if score < 30:
        return None
    if score >= 80:
        strength = "강한 후보"
    elif score >= 50:
        strength = "검토 후보"
    else:
        strength = "약한 후보"
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
        "status": item.status,
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
        "info_badges": info_badges,
        "d_day": calculate_d_day(item.bid_end_at),
        "link_count": len(item.case_links),
        "notice_count": len(notices),
        "notices": notices,
        "has_detail": bool(item.item_description or item.attachment_summary or item.cautions),
        "external_url": notices[0]["detail_url"] if notices and notices[0]["detail_url"] else "",
    }
