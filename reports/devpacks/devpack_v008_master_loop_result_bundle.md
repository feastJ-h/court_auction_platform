# Devpack v008 Master Loop Result Bundle

Updated: 2026-07-10 KST

## 1. 작업 메타데이터

- 저장소: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- 기준 브랜치: `codex/devpack-v007-product-ux-safety-analytics`
- 작업 브랜치: `codex/devpack-v008-master-review-data-ux-loop`
- 지시서: `reports/devpacks/codex_devpack_v008_master_loop_instruction.md`
- 핵심 방향: 공개 ONBID UX 복구, 오늘 보기/목록/상세/내 검토함 개선, 운영 UI 추가, 제한 수집 및 QA 반복

## 2. 시작 Git 상태

```text
git rev-parse --show-toplevel
C:/Users/xogns/Documents/testAuction/court_auction_platform

git branch --show-current
codex/devpack-v007-product-ux-safety-analytics

git status --short
?? reports/devpacks/codex_devpack_v008_master_loop_instruction.md

git remote -v
origin https://github.com/feastJ-h/court_auction_platform.git (fetch)
origin https://github.com/feastJ-h/court_auction_platform.git (push)

git --no-pager log --oneline --decorate -8
a2b9ae7 (HEAD -> codex/devpack-v007-product-ux-safety-analytics, origin/codex/devpack-v007-product-ux-safety-analytics) feat: add v007 review ux safety analytics foundation
```

브랜치 생성:

```text
git checkout -b codex/devpack-v008-master-review-data-ux-loop
```

## 3. 백업 / DB 작업

작업 전 백업:

```text
backup: C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260710_065322.db
sha256: DE754FACDE6C183D3703F580D8A0E326C6E4AE84CE0A44AE33284F6DACF82BEF
source: C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db
restore tested: not run
```

Derived field repair:

```text
before dry-run: {"checked": 188, "updated": 0, "would_update": 68}
apply: {"checked": 188, "updated": 68, "would_update": 68}
after dry-run: {"checked": 226, "updated": 0, "would_update": 0}
```

Schema 변경은 없었으므로 `docs/migration_ledger.md`는 수정하지 않았다.

## 4. 데이터 확충 / Audit

초기 audit:

```text
{"total": 188, "fresh": 107, "stale": 61, "invalid_date": 20, "unknown_date": 0,
 "by_category": {"real_estate": 145, "movable": 42, "national_property": 1, "other": 0, "all": 0}}
```

제한 ONBID 호출:

```text
real_estate page 1 limit 20: fetched 20, accepted_fresh 20, inserted 18, duplicates 2
movable page 1 limit 20: fetched 20, accepted_fresh 20, inserted 20, duplicates 0
national_property page 1 limit 20: fetched 20, accepted_fresh 0, dropped_stale 18, dropped_unknown_date 2
```

사후 audit:

```text
{"total": 226, "fresh": 145, "stale": 61, "invalid_date": 20, "unknown_date": 0,
 "by_category": {"real_estate": 143, "movable": 62, "national_property": 21, "other": 0, "all": 0}}
```

Public-visible fresh non-sample:

```text
total: 138
real_estate: 78
movable: 60
national_property: 0 public-visible fresh rows after current filters
active_or_upcoming: 78
ended: 60
detail_real_estate: 78
detail_movable: 60
duplicate_key_count: 0
sample/fixture public exposure: 0
```

v008 목표인 250건, real_estate 120건, movable 80건, active/upcoming 150건은 아직 미달이다. 1페이지 제한 수집 2개는 성공했지만 national_property는 stale/unknown으로 공개 반영되지 않았다.

## 5. 구현 요약

- 홈을 “소개 페이지”보다 “오늘 검토 입구”에 가깝게 변경했다.
  - 4개 큐레이션 카드: 오늘 새로 확인된 물건, 이번 주 마감 임박, 내 지역 신규 물건, 가격 정보 있는 1억 이하
  - 최근 공개 ONBID preview와 분류 현황 추가
- `/onbid` 목록을 카드형 검토 보드로 정리했다.
  - 자료 확인 필요 필터 안내
  - 원문 보기/원문 링크 확인 필요 표시
  - 비로그인 관심/패스 로그인 CTA
  - 기본 정렬에서 active/upcoming을 ended보다 우선하도록 보정
- `/onbid/today`를 비로그인 200, 로그인 저장형 정리 화면으로 정리했다.
- `/onbid/{id}` 상세를 4-Zone으로 정리했다.
  - 자료 상태 선언
  - 객관 팩트
  - 원문 확인 포인트
  - 개인 액션
- Development Insight CTA는 real_estate에만 표시되고 movable에는 숨긴다.
- 공유 요약 관리 화면을 추가했다.
  - `/my/onbid/shared-summaries`
  - revoke: `/my/onbid/shared-summaries/{token}/revoke`
- 관리자 운영 화면을 추가했다.
  - `/admin/onbid-issue-reports`
  - `/admin/product-analytics`
- 공개 템플릿의 mojibake 문구를 복구하고 금지 표현 스캔을 통과하도록 정리했다.

## 6. 개인정보 / Secret / Raw 노출 점검

- API key/secret 출력 없음.
- raw payload 전체 저장/커밋 없음.
- DB/backup/log/storage 파일은 Git 변경 목록에 포함되지 않음.
- 공유 요약은 noindex/noarchive를 유지하고 private memo/raw payload/internal path를 노출하지 않음.
- ONBID issue report 내용은 관리자 화면에만 표시되며 public 상세에는 자동 노출하지 않음.

## 7. Local QA

uvicorn local route QA:

```text
/ status=200 mojibake=False banned=False
/onbid status=200 mojibake=False banned=False
/onbid/today status=200 mojibake=False banned=False
/onbid?category=real_estate status=200 mojibake=False banned=False
/onbid?category=movable status=200 mojibake=False banned=False
/onbid?category=national_property status=200 mojibake=False banned=False
/onbid?data_quality=needs_confirmation status=200 mojibake=False banned=False
/onbid?closing_within_days=7 status=200 mojibake=False banned=False
/cases status=200 mojibake=False banned=False
/disclaimer status=200 mojibake=False banned=False
```

상세 CTA QA:

```text
/onbid/206 status=200 development_cta=True
/onbid/226 status=200 development_cta=False
```

현재 운영 DB public item에는 원문 detail URL이 연결된 항목이 없어 실제 운영 DB 상세의 `원문 보기` 버튼은 숨김/확인 필요 상태로 표시된다. isolated test fixture에서는 원문 링크 표시를 검증했다.

## 8. Cloudflare 외부 QA

Quick tunnel:

```text
https://lamp-walnut-auckland-connected.trycloudflare.com
```

외부 route QA:

```text
/ status=200 mojibake=False banned=False
/onbid status=200 mojibake=False banned=False
/onbid/today status=200 mojibake=False banned=False
/onbid?category=real_estate status=200 mojibake=False banned=False
/onbid?category=movable status=200 mojibake=False banned=False
/onbid?category=national_property status=200 mojibake=False banned=False
/onbid?data_quality=needs_confirmation status=200 mojibake=False banned=False
/onbid?closing_within_days=7 status=200 mojibake=False banned=False
/cases status=200 mojibake=False banned=False
/disclaimer status=200 mojibake=False banned=False
```

외부 상세 QA:

```text
/onbid/206 status=200 development_cta=True mojibake=False
/onbid/226 status=200 development_cta=False mojibake=False
/onbid/206/development-insight status=200 mojibake=False
```

QA 후 uvicorn/cloudflared 프로세스는 종료했다.

## 9. 테스트 결과

py_compile:

```powershell
& $Py -m py_compile backend\database\models.py backend\database\session.py backend\services\auction_items.py backend\services\product_engagement.py backend\web\routers\auctions.py backend\web\routers\admin_operations.py main_app.py
```

개별 테스트 PASS:

```text
tests/onbid_freshness_policy_test.py
tests/onbid_public_filter_state_test.py
tests/onbid_category_mapping_test.py
tests/sitemap_fresh_public_routes_test.py
tests/onbid_module_test.py
tests/page_response_smoke_test.py
tests/public_access_auth_boundary_test.py
tests/router_boundary_test.py
tests/isolated_operations_test.py
tests/onbid_data_quality_needed_filter_test.py
tests/onbid_data_issue_report_test.py
tests/development_insight_cta_safety_test.py
tests/onbid_review_summary_share_test.py
tests/product_analytics_events_test.py
tests/product_copy_safety_test.py
tests/onbid_today_review_completion_test.py
tests/admin_readiness_dashboard_test.py
tests/no_mojibake_public_copy_test.py
tests/home_curation_cards_test.py
tests/onbid_today_route_external_shape_test.py
tests/onbid_default_active_priority_test.py
tests/onbid_original_link_prominence_test.py
tests/onbid_detail_four_zone_test.py
tests/development_insight_cta_visibility_test.py
tests/onbid_admin_issue_queue_test.py
tests/onbid_shared_summary_manage_test.py
tests/product_analytics_admin_summary_test.py
tests/onbid_dataset_quality_threshold_test.py
```

`python -m pytest`:

```text
pytest installed with approved network access.
collected 5 items
1 passed, 4 failed
```

Failures are pre-existing/environment-dependent pytest-discovered tests:

- `backend/ai_engine/test_analyzer.py`: default provider expected `chatgpt`, runtime returned `gemini`.
- `backend/crawler/test_scraper.py`: court website Playwright navigation blocked by network access.
- `backend/parser/test_parser.py`: existing downloaded PDF parsed as `OCR_REQUIRED` with empty extracted text.
- `test_orchestrator.py`: same court website network access block.

지시서의 script-style 필수 테스트들은 PASS했다.

## 10. 변경 파일 요약

- Backend:
  - `backend/services/auction_items.py`
  - `backend/services/product_engagement.py`
  - `backend/web/routers/admin_operations.py`
  - `backend/web/routers/auctions.py`
  - `main_app.py`
- Templates:
  - `frontend/templates/public/home.html`
  - `frontend/templates/auctions/index.html`
  - `frontend/templates/auctions/today.html`
  - `frontend/templates/auctions/detail.html`
  - `frontend/templates/auctions/development_insight.html`
  - `frontend/templates/auctions/my_list.html`
  - `frontend/templates/auctions/shared_summary.html`
  - `frontend/templates/auctions/shared_manage.html`
  - `frontend/templates/admin/onbid_issue_reports.html`
  - `frontend/templates/admin/product_analytics.html`
  - `frontend/templates/shared/admin_nav.html`
  - `frontend/templates/shared/my_nav.html`
- Tests:
  - `tests/development_insight_cta_safety_test.py`
  - 11개 v008 신규 테스트 파일
- Reports:
  - `reports/devpacks/codex_devpack_v008_master_loop_instruction.md`
  - `reports/devpacks/devpack_v008_master_loop_result_bundle.md`
  - `reports/project-result_current.md`

## 11. 남은 리스크 / 다음 devpack

- public-visible fresh non-sample 138건으로 v008 목표 250건 미달.
- national_property는 API 응답은 있었지만 이번 범위에서 fresh public row를 확보하지 못함.
- 운영 DB public rows 중 원문 detail URL 연결 항목이 없어 실제 운영 상세에서 원문 보기 버튼이 대부분 숨김/확인 필요 상태.
- 전체 pytest는 구형 실통신/환경 의존 테스트 때문에 실패하므로 별도 devpack에서 pytest 수집 정책 정리가 필요.
- ONBID notice/public announcements의 실제 item 연결 보강은 다음 devpack에서 추가 수집 전략이 필요.

## 12. 종료 전 Git 확인

종료 시점에는 민감 파일을 stage하지 않고 코드/템플릿/테스트/보고서만 커밋 대상으로 삼는다.
