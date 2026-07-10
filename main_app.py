import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from html import escape
import json
import logging
from math import ceil
from collections import defaultdict, deque
from threading import Lock
import time
import secrets
import uuid
from urllib.parse import parse_qs, urlencode, urlsplit
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from backend.analysis.business_rules import evaluate_marketability
from backend.config import PROJECT_ROOT, get_settings, validate_runtime_config
from backend.database.crud import (
    list_admin_events,
)
from backend.database.models import AssetEvent, AuctionItem
from backend.database.analysis_results import (
    list_results_for_events,
    serialize_result,
)
from backend.database.session import init_db, session_scope
from backend.jobs.repository import get_latest_job_for_event
from backend.jobs.repository import get_latest_ocr_job_for_event
from backend.jobs.event_repository import list_job_events
from backend.services.analysis_reviews import (
    list_reviews_for_results,
)
from backend.services.audit_logs import create_audit_log
from backend.services.onbid_review import select_home_preview
from backend.services.metadata_corrections import update_event_metadata
from backend.services.auth import (
    accept_current_policies,
    authenticate_user,
    change_user_password,
    get_user_by_id,
)
from backend.services.csrf import CSRF_COOKIE_NAME, csrf_token_for_request, verify_double_submit
from backend.services.security_state import get_security_state_store
from backend.services.onbid_sync_runs import latest_successful_sync
from backend.services.auction_items import (
    apply_public_onbid_freshness_filter,
    count_auction_items,
    get_onbid_category_counts,
    list_auction_items,
    serialize_auction_item,
)
from backend.services.user_event_notes import get_user_event_note_map
from backend.web.routers.admin_operations import register_admin_operation_routes
from backend.web.routers.admin_users import register_admin_user_routes
from backend.web.routers.analysis import register_analysis_routes
from backend.web.routers.auctions import register_auction_routes
from backend.web.routers.cases import register_case_routes
from backend.web.routers.documents import register_document_routes
from backend.web.routers.ocr_operations import register_ocr_operation_routes
from backend.jobs.service import (
    JobServiceError,
    serialize_job,
)
from backend.jobs.readiness import get_analysis_readiness


app = FastAPI(title="Court Auction Platform")
templates = Jinja2Templates(
    directory=str(PROJECT_ROOT / "frontend" / "templates"),
    context_processors=[lambda request: {"csrf_token": csrf_token_for_request(request)}],
)
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "frontend" / "static")), name="static")

SESSION_COOKIE_NAME = "court_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
_RATE_LIMIT_BUCKETS: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()
_REVOKED_SESSION_IDS: set[str] = set()
_REVOKED_SESSION_LOCK = Lock()
STARTED_AT = time.monotonic()
LOGGER = logging.getLogger("court_auction.http")


def _safe_error_response(request: Request, status_code: int, detail: str) -> Response:
    if request.url.path.startswith("/api/") or "application/json" in request.headers.get("accept", ""):
        return JSONResponse({"detail": detail}, status_code=status_code)
    titles = {403: "접근할 수 없습니다", 404: "페이지를 찾을 수 없습니다", 429: "요청이 너무 많습니다", 500: "일시적인 오류가 발생했습니다"}
    title = titles.get(status_code, "요청을 처리할 수 없습니다")
    body = (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{status_code} | Court Auction</title></head><body>"
        '<main style="max-width:44rem;margin:10vh auto;padding:2rem;font-family:sans-serif">'
        f"<p>{status_code}</p><h1>{escape(title)}</h1><p>{escape(detail)}</p>"
        '<p><a href="/">홈으로 돌아가기</a></p></main></body></html>'
    )
    return Response(body, status_code=status_code, media_type="text/html")


@app.exception_handler(HTTPException)
async def http_error_page(request: Request, exc: HTTPException):
    messages = {
        403: "로그인 상태와 접근 권한을 확인해 주세요.",
        404: "주소가 변경되었거나 공개되지 않은 항목일 수 있습니다.",
        429: "잠시 후 다시 시도해 주세요.",
    }
    return _safe_error_response(request, exc.status_code, messages.get(exc.status_code, "요청을 처리하지 못했습니다."))


@app.exception_handler(Exception)
async def unhandled_error_page(request: Request, exc: Exception):
    return _safe_error_response(request, 500, "내부 정보는 공개하지 않습니다. 잠시 후 다시 시도해 주세요.")


def _rate_limit_rule(request: Request) -> tuple[str, int, int] | None:
    path = request.url.path
    method = request.method.upper()
    if method == "POST" and path == "/login":
        return ("login", 10, 60)
    if method == "POST" and (path.endswith("/issue-report") or path.endswith("/review-summary")):
        return ("engagement", 20, 60)
    if method == "POST" and "/shared-summaries/" in path:
        return ("share", 20, 60)
    if method == "GET" and path.endswith("/original-link"):
        return ("original", 60, 60)
    if method == "POST" and path == "/api/admin/auctions/onbid/sync":
        return ("admin-sync", 5, 60)
    return None


def _rate_limited(request: Request) -> bool:
    rule = _rate_limit_rule(request)
    if rule is None:
        return False
    name, limit, window = rule
    client = request.client.host if request.client else "unknown"
    try:
        return not get_security_state_store().consume_rate_limit(name, client, limit, window)
    except Exception:
        return get_settings().app_env != "development"


def _cross_site_unsafe_request(request: Request) -> bool:
    if request.method.upper() in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return False
    fetch_site = request.headers.get("sec-fetch-site", "").lower()
    if fetch_site == "cross-site":
        return True
    origin = request.headers.get("origin", "")
    if not origin:
        return False
    parsed = urlsplit(origin)
    return bool(parsed.netloc and parsed.netloc.lower() != request.url.netloc.lower())


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id", "")
    if not request_id or len(request_id) > 128 or not all(ch.isalnum() or ch in "-_." for ch in request_id):
        request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.monotonic()
    settings = get_settings()
    enforce_csrf = settings.app_env in {"beta", "production"} or request.headers.get("x-enforce-csrf") == "1"
    if enforce_csrf and request.method.upper() not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        submitted = request.headers.get("x-csrf-token", "")
        if not submitted:
            content_type = request.headers.get("content-type", "")
            body = await request.body()
            if "application/x-www-form-urlencoded" in content_type:
                submitted = parse_qs(body.decode("utf-8", errors="replace")).get("csrf_token", [""])[0]
            elif "multipart/form-data" in content_type:
                marker = b'name="csrf_token"'
                position = body.find(marker)
                if position >= 0:
                    value_start = body.find(b"\r\n\r\n", position)
                    value_end = body.find(b"\r\n", value_start + 4)
                    if value_start >= 0 and value_end >= 0:
                        submitted = body[value_start + 4:value_end].decode("utf-8", errors="replace")
        if not verify_double_submit(request.cookies.get(CSRF_COOKIE_NAME), submitted):
            return JSONResponse({"detail": "CSRF token validation failed."}, status_code=403)
    if _cross_site_unsafe_request(request):
        return JSONResponse({"detail": "요청 출처를 확인할 수 없습니다."}, status_code=403)
    if _rate_limited(request):
        return JSONResponse(
            {"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."},
            status_code=429,
            headers={"Retry-After": "60"},
        )
    response = await call_next(request)
    token = getattr(request.state, "csrf_token", "")
    if token and request.cookies.get(CSRF_COOKIE_NAME) != token:
        response.set_cookie(
            CSRF_COOKIE_NAME,
            token,
            max_age=60 * 60 * 2,
            httponly=False,
            secure=request.url.scheme == "https",
            samesite="strict",
        )
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    )
    if settings.review_mode or settings.beta_noindex:
        response.headers.setdefault("X-Robots-Tag", "noindex, noarchive")
    if settings.review_mode:
        response.headers.setdefault("X-Review-Mode", "true")
    LOGGER.info(json.dumps({
        "event": "http_request",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
    }, ensure_ascii=False))
    return response


def login_redirect(next_url: str = "/user") -> RedirectResponse:
    target = safe_local_path(next_url, "/user")
    return RedirectResponse(url=f"/login?{urlencode({'next': target})}", status_code=303)


def safe_local_path(value: str, fallback: str = "/user") -> str:
    parsed = urlsplit(value or "")
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return fallback
    return value


def _session_signature(payload: str) -> str:
    secret = get_settings().app_secret_key.encode("utf-8")
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def encode_session_cookie(data: dict) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode("utf-8")).decode("ascii")
    return f"{payload}.{_session_signature(payload)}"


def decode_session_cookie(value: str | None) -> dict:
    if not value or "." not in value:
        return {}
    payload, signature = value.rsplit(".", 1)
    if not hmac.compare_digest(signature, _session_signature(payload)):
        return {}
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
        expires_at = int(data.get("exp") or 0)
        if expires_at and expires_at < int(datetime.now(timezone.utc).timestamp()):
            return {}
        return data
    except Exception:
        return {}


def get_current_user(request: Request, session):
    session_data = decode_session_cookie(request.cookies.get(SESSION_COOKIE_NAME))
    session_id = str(session_data.get("sid") or "")
    if session_id and get_security_state_store().is_session_revoked(session_id):
        return None
    user_id = session_data.get("user_id")
    user = get_user_by_id(session, int(user_id)) if user_id else None
    if user is None or not user.is_active or user.account_status != "active":
        return None
    if user.beta_expires_at:
        expires = user.beta_expires_at if user.beta_expires_at.tzinfo else user.beta_expires_at.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            return None
    return user


def require_user(request: Request, session):
    user = get_current_user(request, session)
    if user is None:
        return None
    return user


def require_admin(request: Request, session):
    user = get_current_user(request, session)
    if user is None or user.role != "admin":
        return None
    return user


register_auction_routes(
    app,
    templates,
    require_user=require_user,
    require_admin=require_admin,
    login_redirect=login_redirect,
)
register_admin_user_routes(
    app,
    templates,
    require_admin=require_admin,
    login_redirect=login_redirect,
)
def compute_d_day_str(bidding_date: str) -> tuple[str, str]:
    if not bidding_date or bidding_date == "미정":
        return "미정", "unknown"
    try:
        target_date = datetime.strptime(bidding_date, "%Y-%m-%d").date()
    except ValueError:
        return "미정", "unknown"

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    delta = (target_date - today).days
    if delta > 7:
        return f"D-{delta}", "normal"
    if 0 < delta <= 7:
        return f"D-{delta}", "urgent"
    if delta == 0:
        return "D-Day", "urgent"
    return f"D+{abs(delta)}(마감)", "closed"


def attach_view_metadata(events) -> None:
    for event in events:
        analysis = event.analyses[0] if event.analyses else None
        d_day_str, d_day_state = compute_d_day_str(analysis.bidding_date if analysis else "미정")
        event.d_day_str = d_day_str
        event.d_day_state = d_day_state
        event.marketability = evaluate_marketability(event)


def attach_user_note_metadata(session, events, user_id: int) -> None:
    notes = get_user_event_note_map(session, user_id, [event.id for event in events])
    for event in events:
        note = notes.get(event.id)
        event.user_note = note.note if note else ""
        event.user_tags = note.tags if note else ""


def attach_analysis_result_metadata(session, events) -> None:
    grouped = list_results_for_events(session, [event.id for event in events])
    result_ids = [result.id for results in grouped.values() for result in results]
    reviews_by_result_id = list_reviews_for_results(session, result_ids)
    for event in events:
        results = grouped.get(event.id, [])
        event.analysis_results = results
        by_provider: dict[str, dict[str, dict]] = {}
        for result in results:
            serialized = serialize_result(result)
            serialized["reviews"] = reviews_by_result_id.get(result.id, [])
            by_provider.setdefault(result.model_provider, {})[result.analysis_type] = serialized
        event.model_results = by_provider

        gemini = by_provider.get("gemini", {})
        chatgpt = by_provider.get("chatgpt", {})
        codex = by_provider.get("codex_app_server", {}) or by_provider.get("codex_cli", {})
        event.gemini_status = _model_status(gemini)
        event.chatgpt_status = _model_status(chatgpt or codex)
        event.dual_complete = event.gemini_status == "완료" and event.chatgpt_status == "완료"
        event.model_disagreement = _has_model_disagreement(gemini, chatgpt or codex)
        event.comparison_summary = _comparison_summary(gemini, chatgpt or codex)


def _model_status(results_by_type: dict[str, dict]) -> str:
    if not results_by_type:
        return "미완료"
    if any(result.get("status") == "FAILED" for result in results_by_type.values()):
        return "실패"
    if any(result.get("status") in {"PENDING", "RUNNING"} for result in results_by_type.values()):
        return "진행"
    if any(result.get("status") in {"SUCCEEDED", "CACHED"} for result in results_by_type.values()):
        return "완료"
    return "미완료"


def _representative_result(results_by_type: dict[str, dict]) -> dict | None:
    return results_by_type.get("deep") or results_by_type.get("basic")


def _has_model_disagreement(left: dict[str, dict], right: dict[str, dict]) -> bool:
    left_result = _representative_result(left)
    right_result = _representative_result(right)
    if not left_result or not right_result:
        return False
    left_price = "".join(ch for ch in str(left_result.get("min_price") or "") if ch.isdigit())
    right_price = "".join(ch for ch in str(right_result.get("min_price") or "") if ch.isdigit())
    if left_price and right_price and left_price != right_price:
        return True
    risk_words = ("위험", "유치권", "법정지상권", "명도", "소송", "회수 불확실", "확인 필요")
    left_risk = {word for word in risk_words if word in str(left_result.get("risk_comment") or left_result.get("detailed_analysis") or "")}
    right_risk = {word for word in risk_words if word in str(right_result.get("risk_comment") or right_result.get("detailed_analysis") or "")}
    return bool(left_risk.symmetric_difference(right_risk))


def _comparison_summary(left: dict[str, dict], right: dict[str, dict]) -> dict:
    left_result = _representative_result(left)
    right_result = _representative_result(right)
    if not left_result and not right_result:
        return {
            "state": "missing",
            "headline": "모델별 분석 결과가 아직 부족합니다.",
            "common": "Gemini와 ChatGPT/Codex 결과가 모두 준비되면 비교할 수 있습니다.",
            "difference": "비교 전",
        }
    if not left_result or not right_result:
        return {
            "state": "partial",
            "headline": "한쪽 모델 분석만 준비되었습니다.",
            "common": "현재 준비된 모델 결과를 우선 검토하세요.",
            "difference": "다른 모델 결과가 생성되면 가격/리스크 판단 차이를 표시합니다.",
        }
    disagreement = _has_model_disagreement(left, right)
    return {
        "state": "disagree" if disagreement else "aligned",
        "headline": "모델 의견 차이가 감지되었습니다." if disagreement else "두 모델의 핵심 판단이 크게 어긋나지 않습니다.",
        "common": "두 결과 모두 원문 근거와 추가 확인 서류를 기준으로 검토해야 합니다.",
        "difference": "가격 또는 리스크 키워드가 다릅니다." if disagreement else "주요 가격/리스크 신호가 대체로 유사합니다.",
    }


def build_event_payload(event) -> dict:
    analysis = event.analyses[0] if event.analyses else None
    evidence = event.raw_document.evidence
    marketability = getattr(event, "marketability", evaluate_marketability(event))
    raw_text = event.extracted_text or ""
    evidence_text = evidence.detail_page_text if evidence else ""
    latest_job = getattr(event, "latest_deep_job", None)
    latest_ocr_job = getattr(event, "latest_ocr_job", None)
    raw_document_id = event.raw_document.id if event.raw_document else None
    model_results = getattr(event, "model_results", {})
    return {
        "id": event.id,
        "raw_document_id": raw_document_id,
        "case_number": event.case_number,
        "title": event.title,
        "url": event.url,
        "status": event.status,
        "parse_status": event.parse_status,
        "notice_date": event.notice_date,
        "expire_date": event.expire_date,
        "main_category": event.asset.main_category,
        "sub_category": event.asset.sub_category,
        "address": event.asset.address,
        "min_price": analysis.min_price if analysis else "0",
        "bidding_date": analysis.bidding_date if analysis else "미정",
        "d_day_str": event.d_day_str,
        "d_day_state": event.d_day_state,
        "item_details": analysis.item_details if analysis else "텍스트 추출 또는 AI 분석 대기 중입니다.",
        "risk_comment": analysis.risk_comment if analysis else "AI 분석 결과가 아직 없습니다.",
        "detailed_analysis": analysis.detailed_analysis if analysis else "",
        "analysis_provider": analysis.analysis_provider if analysis else "not_analyzed",
        "has_analysis": bool(analysis),
        "market_label": marketability.label,
        "market_grade": marketability.grade,
        "market_reasons": marketability.reasons,
        "raw_text": raw_text,
        "evidence_text": evidence_text,
        "raw_text_length": len(raw_text),
        "evidence_text_length": len(evidence_text),
        "raw_file_url": f"/documents/raw/{raw_document_id}" if raw_document_id else "",
        "raw_file_path": event.raw_document.file_path if event.raw_document else "",
        "latest_job": serialize_job(latest_job),
        "latest_ocr_job": serialize_job(latest_ocr_job),
        "analysis_results": model_results,
        "gemini_status": getattr(event, "gemini_status", "미완료"),
        "chatgpt_status": getattr(event, "chatgpt_status", "미완료"),
        "dual_complete": getattr(event, "dual_complete", False),
        "model_disagreement": getattr(event, "model_disagreement", False),
        "comparison_summary": getattr(event, "comparison_summary", {}),
        "analysis_readiness": get_analysis_readiness(event),
        "user_note": getattr(event, "user_note", ""),
        "user_tags": getattr(event, "user_tags", ""),
    }


def is_stale_job(job) -> bool:
    if not job or job.status != "RUNNING":
        return False
    reference = job.last_event_at or job.started_at
    if reference is None:
        return False
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - reference > timedelta(minutes=10)


def event_matches_admin_filters(event, job_status: str, model: str, parse_status: str) -> bool:
    job = getattr(event, "latest_deep_job", None)
    if job_status and job_status != "ALL":
        if job_status == "NONE":
            if job is not None:
                return False
        elif not job or job.status != job_status:
            return False

    if parse_status and parse_status != "ALL" and event.parse_status != parse_status:
        return False

    if model and model != "ALL":
        results = getattr(event, "model_results", {})
        if model == "gemini" and "gemini" not in results:
            return False
        if model == "chatgpt" and not any(key in results for key in ("chatgpt", "codex_app_server", "codex_cli")):
            return False
        if model == "codex" and not any(key in results for key in ("codex_app_server", "codex_cli")):
            return False
    return True


def raise_job_error(exc: JobServiceError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


register_admin_operation_routes(
    app,
    templates,
    require_admin=require_admin,
    login_redirect=login_redirect,
    attach_view_metadata=attach_view_metadata,
    attach_analysis_result_metadata=attach_analysis_result_metadata,
    event_matches_admin_filters=event_matches_admin_filters,
    is_stale_job=is_stale_job,
)
register_case_routes(
    app,
    templates,
    require_user=require_user,
    login_redirect=login_redirect,
    attach_view_metadata=attach_view_metadata,
    attach_analysis_result_metadata=attach_analysis_result_metadata,
    attach_user_note_metadata=attach_user_note_metadata,
    build_event_payload=build_event_payload,
)
register_analysis_routes(
    app,
    require_admin=require_admin,
    login_redirect=login_redirect,
    raise_job_error=raise_job_error,
)
register_ocr_operation_routes(
    app,
    require_admin=require_admin,
    raise_job_error=raise_job_error,
)
register_document_routes(
    app,
    require_user=require_user,
)


@app.on_event("startup")
def on_startup() -> None:
    problems = validate_runtime_config()
    if problems:
        raise RuntimeError("Unsafe runtime configuration: " + "; ".join(problems))
    init_db()
    settings = get_settings()
    LOGGER.info(json.dumps({
        "event": "startup_audit",
        "app_env": settings.app_env,
        "review_mode": settings.review_mode,
        "beta_mode": settings.beta_mode,
        "beta_noindex": settings.beta_noindex,
        "db_backend": settings.db_url.split(":", 1)[0],
        "security_store_backend": type(get_security_state_store()).__name__,
        "redis_configured": bool(settings.redis_url),
        "onbid_key_configured": bool(settings.onbid_api_key),
    }))


@app.get("/health/live")
def health_live():
    return {"status": "live", "uptime_seconds": int(time.monotonic() - STARTED_AT)}


@app.get("/health/ready")
def health_ready():
    checks: dict[str, object] = {"config": not validate_runtime_config()}
    try:
        with session_scope() as session:
            session.execute(select(1))
            checks["database"] = True
            checks["public_onbid_count"] = count_auction_items(session, public_only=True)
        get_security_state_store().cleanup_expired()
        checks["security_state"] = True
        checks["last_successful_sync"] = latest_successful_sync()
    except Exception:
        checks["database"] = False
        checks["security_state"] = False
    ready = bool(checks.get("config") and checks.get("database") and checks.get("security_state"))
    return JSONResponse({"status": "ready" if ready else "not_ready", "checks": checks}, status_code=200 if ready else 503)


@app.get("/health/version")
def health_version():
    settings = get_settings()
    return {
        "version": settings.app_version,
        "git_commit": settings.app_git_commit,
        "environment": settings.app_env,
        "build_time": settings.app_build_time,
    }


@app.get("/")
def root(request: Request):
    with session_scope() as session:
        current_user = require_user(request, session)
        category_counts = get_onbid_category_counts(session, public_only=True)
        active_item_views = [
            serialize_auction_item(item)
            for item in list_auction_items(session, public_only=True, active_only=True, sort="newest", limit=5000)
        ]
        today_kst = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        today_count = sum(1 for item in active_item_views if item.get("first_seen_date") == today_kst)
        metro_count = sum(
            1 for item in active_item_views
            if any(region in (item.get("address") or "") for region in ("서울", "경기", "인천"))
        )
        low_price_count = sum(
            1 for item in active_item_views
            if 0 < int(item.get("minimum_bid_price") or 0) <= 100_000_000
        )
        home_cards = [
            {
                "title": "오늘 처음 수집된 물건",
                "count": today_count,
                "description": "오늘 최초 수집 시각이 기록된 공개 온비드 항목입니다.",
                "href": "/onbid/today",
            },
            {
                "title": "이번 주 마감 임박",
                "count": count_auction_items(session, public_only=True, active_only=True, closing_within_days=7),
                "description": "진행 중이거나 예정된 항목 중 7일 이내 마감입니다.",
                "href": "/onbid?closing_within_days=7",
            },
            {
                "title": "서울·수도권 검토 가능",
                "count": metro_count,
                "description": "서울·경기·인천 소재의 현재 공개 가능한 항목입니다.",
                "href": "/onbid?region=%EC%84%9C%EC%9A%B8",
            },
            {
                "title": "가격 정보 있는 1억 이하",
                "count": low_price_count,
                "description": "최저입찰가가 확인되고 1억 원 이하인 항목입니다.",
                "href": "/onbid?price_max=100000000",
            },
        ]
        preview_items = select_home_preview(active_item_views, limit=4)
        return templates.TemplateResponse(
            request,
            "public/home.html",
            {
                "current_user": current_user,
                "settings": get_settings(),
                "active_section": "home",
                "active_subsection": "",
                "active_category": "",
                "breadcrumbs": [],
                "review_mode": get_settings().review_mode,
                "home_cards": home_cards,
                "category_counts": category_counts,
                "preview_items": preview_items,
                "last_data_updated": max((item.get("last_updated_at", "") for item in active_item_views), default=""),
            },
        )


@app.get("/about")
def about_page(request: Request):
    with session_scope() as session:
        return templates.TemplateResponse(
            request,
            "public/about.html",
            {
                "current_user": require_user(request, session),
                "settings": get_settings(),
                "active_section": "home",
                "active_subsection": "",
                "active_category": "",
                "breadcrumbs": [{"label": "소개", "href": "/about"}],
                "review_mode": get_settings().review_mode,
            },
        )


@app.get("/disclaimer")
def disclaimer_page(request: Request):
    with session_scope() as session:
        return templates.TemplateResponse(
            request,
            "public/disclaimer.html",
            {
                "current_user": require_user(request, session),
                "settings": get_settings(),
                "active_section": "legal",
                "active_subsection": "disclaimer",
                "active_category": "",
                "breadcrumbs": [{"label": "고지사항", "href": "/disclaimer"}],
                "review_mode": get_settings().review_mode,
            },
        )


@app.get("/privacy-draft")
def privacy_draft_page(request: Request):
    return RedirectResponse(url="/privacy", status_code=303)


@app.get("/privacy")
def privacy_page(request: Request):
    with session_scope() as session:
        return templates.TemplateResponse(
            request,
            "public/privacy_draft.html",
            {
                "current_user": require_user(request, session),
                "settings": get_settings(),
                "active_section": "legal",
                "active_subsection": "privacy",
                "active_category": "",
                "breadcrumbs": [{"label": "개인정보 처리방침", "href": "/privacy"}],
                "review_mode": get_settings().review_mode,
            },
        )


@app.get("/terms")
def terms_page(request: Request):
    with session_scope() as session:
        return templates.TemplateResponse(
            request,
            "public/terms.html",
            {
                "current_user": require_user(request, session),
                "settings": get_settings(),
                "active_section": "legal",
                "active_subsection": "terms",
                "active_category": "",
                "breadcrumbs": [{"label": "이용약관", "href": "/terms"}],
                "review_mode": get_settings().review_mode,
            },
        )


@app.get("/robots.txt")
def robots_txt() -> Response:
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin",
            "Disallow: /api/admin",
            "Disallow: /user",
            "Disallow: /my",
            "Disallow: /documents/raw",
            "Disallow: /storage",
            "Sitemap: /sitemap.xml",
            "",
        ]
    )
    return Response(content=body, media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml() -> Response:
    paths = ["/", "/onbid", "/cases", "/about", "/disclaimer", "/privacy", "/terms"]
    with session_scope() as session:
        onbid_statement = apply_public_onbid_freshness_filter(
            select(AuctionItem.id).where(AuctionItem.source == "ONBID", AuctionItem.item_name != "")
        )
        onbid_ids = [
            item_id
            for item_id in session.scalars(
                onbid_statement.order_by(AuctionItem.updated_at.desc(), AuctionItem.id.desc()).limit(100)
            )
        ]
        case_ids = [
            event_id
            for event_id in session.scalars(
                select(AssetEvent.id)
                .where(AssetEvent.title != "", AssetEvent.url != "")
                .order_by(AssetEvent.notice_date.desc(), AssetEvent.id.desc())
                .limit(100)
            )
        ]
    paths.extend(f"/onbid/{item_id}" for item_id in onbid_ids)
    paths.extend(f"/cases/{event_id}" for event_id in case_ids)
    urlset = "".join(f"<url><loc>{escape(path)}</loc></url>" for path in paths)
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urlset}</urlset>'
    return Response(content=body, media_type="application/xml")


@app.get("/login")
def login_page(request: Request, next: str = Query("/user"), error: str = Query("")):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "next_url": safe_local_path(next, "/user"),
            "error": error,
            "active_section": "auth",
            "active_subsection": "",
            "active_category": "",
            "breadcrumbs": [{"label": "로그인", "href": "/login"}],
            "settings": settings,
            "show_local_admin_hint": settings.local_dev_login_hint and not settings.review_mode,
            "review_mode": settings.review_mode,
        },
    )


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/user"),
) -> RedirectResponse:
    with session_scope() as session:
        user = authenticate_user(session, username, password)
        if user is None:
            return RedirectResponse(url="/login?error=1", status_code=303)
        settings = get_settings()
        needs_consent = (
            user.terms_version_accepted != settings.terms_version
            or user.privacy_version_accepted != settings.privacy_version
            or user.beta_notice_version_accepted != settings.beta_notice_version
        )
        target = "/account/password" if user.must_change_password else ("/account/consent" if needs_consent else safe_local_path(next_url, "/user"))
        response = RedirectResponse(url=target, status_code=303)
        expires_at = int(datetime.now(timezone.utc).timestamp()) + SESSION_MAX_AGE_SECONDS
        response.set_cookie(
            SESSION_COOKIE_NAME,
            encode_session_cookie({"user_id": user.id, "username": user.username, "role": user.role, "exp": expires_at, "sid": secrets.token_urlsafe(24)}),
            max_age=SESSION_MAX_AGE_SECONDS,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
        return response


@app.post("/logout")
def logout(request: Request) -> RedirectResponse:
    session_data = decode_session_cookie(request.cookies.get(SESSION_COOKIE_NAME))
    session_id = str(session_data.get("sid") or "")
    if session_id:
        get_security_state_store().revoke_session(session_id, SESSION_MAX_AGE_SECONDS)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/account/password")
def change_password_page(request: Request, error: str = Query(""), success: str = Query("")):
    with session_scope() as session:
        current_user = require_user(request, session)
        if current_user is None:
            return login_redirect("/account/password")
        return templates.TemplateResponse(
            request,
            "auth/change_password.html",
            {
                "current_user": current_user,
                "error": error,
                "success": success,
            },
        )


@app.post("/account/password")
def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
) -> RedirectResponse:
    with session_scope() as session:
        current_user = require_user(request, session)
        if current_user is None:
            return login_redirect("/account/password")
        try:
            change_user_password(session, current_user, current_password, new_password)
        except ValueError as exc:
            return RedirectResponse(url=f"/account/password?error={str(exc)}", status_code=303)
        create_audit_log(
            session,
            current_user.id,
            "USER_PASSWORD_CHANGED",
            "user",
            current_user.id,
            "User changed own password",
        )
    return RedirectResponse(url="/account/consent", status_code=303)


@app.get("/account/consent")
def account_consent_page(request: Request):
    with session_scope() as session:
        current_user = require_user(request, session)
        if current_user is None:
            return login_redirect("/account/consent")
        return templates.TemplateResponse(
            request,
            "auth/consent.html",
            {"current_user": current_user, "settings": get_settings()},
        )


@app.post("/account/consent")
def account_consent_submit(request: Request, accept: str = Form(...)):
    with session_scope() as session:
        current_user = require_user(request, session)
        if current_user is None:
            return login_redirect("/account/consent")
        if accept != "yes":
            raise HTTPException(status_code=400, detail="Policy consent is required for beta access.")
        accept_current_policies(session, current_user)
        create_audit_log(session, current_user.id, "USER_POLICY_CONSENT", "user", current_user.id, "User accepted current policy versions")
    return RedirectResponse(url="/user", status_code=303)


@app.get("/user/settings")
def user_settings_page(request: Request):
    with session_scope() as session:
        current_user = require_user(request, session)
        if current_user is None:
            return login_redirect("/user/settings")
        return templates.TemplateResponse(
            request,
            "user/settings.html",
            {
                "current_user": current_user,
            },
        )




@app.post("/admin/events/{event_id}/metadata")
def update_admin_event_metadata(
    request: Request,
    event_id: int,
    notice_date: str = Form("UNKNOWN"),
    expire_date: str = Form("UNKNOWN"),
    parse_status: str = Form("UNKNOWN"),
    title: str = Form(""),
) -> RedirectResponse:
    with session_scope() as session:
        current_user = require_admin(request, session)
        if current_user is None:
            return login_redirect("/admin")
        try:
            change = update_event_metadata(
                session,
                event_id=event_id,
                notice_date=notice_date,
                expire_date=expire_date,
                parse_status=parse_status,
                title=title,
            )
            create_audit_log(
                session,
                current_user.id,
                "ADMIN_EVENT_METADATA_UPDATED",
                "asset_event",
                event_id,
                "Admin updated event metadata",
                change,
            )
        except ValueError as exc:
            return RedirectResponse(url=f"/admin?metadata_error={str(exc)}", status_code=303)
    return RedirectResponse(url="/admin", status_code=303)
