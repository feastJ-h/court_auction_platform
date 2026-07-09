# devpack_v007_nightly_result_bundle.md

## 1. 작업 메타데이터

- 작업일: 2026-07-10 KST
- 시작 브랜치: `codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal`
- 작업 브랜치: `codex/devpack-v007-product-ux-safety-analytics`
- 기준 지시서: `reports/devpacks/codex_devpack_v007_nightly_instruction.md`
- 목표: v13.1 기획 반영, 공개 UX 문구 안전화, 오늘 보기/자료 확인/제보/공유/analytics/Development Insight CTA 구현
- commit/push: 최종 커밋 전 작성. push는 최종 단계에서 별도 기록.

## 2. 시작 git status/log

```text
git rev-parse --show-toplevel
C:/Users/xogns/Documents/testAuction/court_auction_platform

git branch --show-current
codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal

git status --short
 M run_onbid_fresh_probe.ps1
 M run_onbid_probe.ps1
?? docs/master_plan_v13_1_final.md
?? reports/devpacks/codex_devpack_v007_nightly_instruction.md
?? reports/devpacks/devpack_v006_a3_result_bundle.md

git remote -v
origin https://github.com/feastJ-h/court_auction_platform.git (fetch)
origin https://github.com/feastJ-h/court_auction_platform.git (push)

git --no-pager log --oneline --decorate -5
894ee0e docs: add v006-a3 devpack instructions
d16afb2 feat: add official onbid list params and fresh probes v006-a2
10710ce docs: add v006-a2 devpack instructions
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
c7df5b7 docs: add v006 devpack instructions
```

## 3. v006-a3 상태 반영

v006-a3 잔여 변경은 지시서에 명시된 파일과 일치했다.

- `run_onbid_fresh_probe.ps1`
- `run_onbid_probe.ps1`
- `reports/devpacks/devpack_v006_a3_result_bundle.md`

별도 커밋:

```text
c1ddc59 docs: add v006-a3 result bundle and probe page wrapper
```

그 후 v007 브랜치를 생성했다.

```powershell
git checkout -b codex/devpack-v007-product-ux-safety-analytics
```

## 4. 백업

DB schema 변경이 있으므로 실제 DB 적용 전 백업을 수행했다.

```text
backup: C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260710_014324.db
sha256: 20BED6D406F1571BBD91EA3B96DC0BFA1420C2099E6D458FCE263D909ED95EEB
source: C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db
restore tested: not run
```

직접 실행은 PowerShell execution policy로 실패했고, 다음 명령으로 재실행했다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

백업 후 실제 로컬 DB에 비파괴 마이그레이션을 적용했다.

```powershell
& $Py -c "from backend.database.session import init_db; init_db(); print('init_db complete')"
```

## 5. 변경 파일 목록

- `backend/database/models.py`
- `backend/database/session.py`
- `backend/services/auction_items.py`
- `backend/services/product_engagement.py`
- `backend/web/routers/auctions.py`
- `docs/migration_ledger.md`
- `docs/product/master_plan_v13_1_final.md`
- `frontend/templates/auctions/detail.html`
- `frontend/templates/auctions/development_insight.html`
- `frontend/templates/auctions/index.html`
- `frontend/templates/auctions/shared_summary.html`
- `frontend/templates/auctions/today.html`
- `frontend/templates/cases/detail.html`
- `frontend/templates/cases/index.html`
- `frontend/templates/public/about.html`
- `frontend/templates/public/home.html`
- `frontend/templates/public/terms.html`
- `frontend/templates/shared/my_nav.html`
- `reports/devpacks/codex_devpack_v007_nightly_instruction.md`
- `reports/devpacks/devpack_v007_nightly_result_bundle.md`
- `reports/project-result_current.md`
- `tests/_v007_helpers.py`
- `tests/development_insight_cta_safety_test.py`
- `tests/onbid_data_issue_report_test.py`
- `tests/onbid_data_quality_needed_filter_test.py`
- `tests/onbid_review_summary_share_test.py`
- `tests/onbid_today_review_completion_test.py`
- `tests/product_analytics_events_test.py`
- `tests/product_copy_safety_test.py`

Runtime DB/backup/log/raw files are not intended for commit.

## 6. 구현 기능 요약

### 6.1 문구 안전성 정리

- 공개 ONBID/case/public templates에서 사용자 노출 `AI 분석` 표현을 원문 확인 포인트/내부 검토 데이터 표현으로 교체했다.
- 공개 템플릿 검색 결과 금지 표현 잔여 없음:

```powershell
Get-ChildItem -Path frontend\templates\public,frontend\templates\auctions,frontend\templates\cases -Recurse -File | Select-String -Pattern "AI 분석|권리분석|추천 물건|수익률|낙찰 보장|전문가 보고서"
```

출력 없음.

### 6.2 오늘 보기/오늘 검토 완료

- `/onbid/today` 추가.
- 로그인 사용자는 오늘 fresh public items를 관심/패스로 정리할 수 있다.
- 오늘 항목이 모두 관심 또는 패스로 처리되면 완료 문구와 요약 숫자를 표시한다.
- 비로그인 사용자는 저장 form 없이 로그인 CTA만 본다.

### 6.3 자료 확인 필요 필터

- `/onbid?data_quality=needs_confirmation` 추가.
- 가격, 일정, 주소, 상세/공고 연결 등 공개 검토에 필요한 기본 자료가 부족한 fresh public rows만 분리한다.
- 기존 public freshness/sample/stale/unknown-date 필터를 유지한다.

### 6.4 오류 제보 / 자료 보완 요청

- `/onbid/{auction_item_id}/issue-report` POST 추가.
- 객관식 issue types와 200자 note를 저장한다.
- 제보 내용은 공개 상세에 즉시 노출하지 않는다.
- 개인정보 노출 의심 flag를 저장한다.

### 6.5 검색 공유 요약

- 로그인 사용자만 `/onbid/{auction_item_id}/review-summary`로 생성 가능.
- `/onbid/share/{token}` 공개 공유 페이지 추가.
- 공유 페이지는 `noindex, noarchive` 적용.
- private memo, user account, raw AI/OCR, raw payload, internal path를 제외하고 공개 item facts만 표시한다.

### 6.6 Analytics 이벤트

- `product_analytics_events` 테이블 추가.
- 이벤트: today queue view, preference actions, original link click, issue report, share create/open/copy, Development Insight CTA view/click.
- metadata에서 raw memo, raw payload, source URL, raw URL류를 제거한다.

### 6.7 Development Insight CTA

- real_estate ONBID detail에만 보수적 CTA 표시.
- 실제 Archi-Pro/API 연동 없음.
- 수익성/사업성/법률 판단 보장 문구 금지 및 disclaimer 표시.

### 6.8 내 검색함 개선

- `/my/onbid/notes` 추가.
- shared my nav에 메모 탭 추가.

## 7. 개인정보/secret/raw payload 노출 점검

- analytics metadata는 raw memo/raw payload/full URL 저장을 차단한다.
- issue report는 pending operational record로만 저장하고 공개 페이지에 report body를 표시하지 않는다.
- shared summary는 public facts만 저장하고 private note를 제외한다.
- public share response에 `X-Robots-Tag: noindex, noarchive`를 적용한다.
- API key/secret 출력 없음.
- raw DB/backup/log/storage files는 Git 변경 목록에 포함하지 않음.

## 8. public route QA 결과

테스트로 확인:

- `/onbid` 200
- `/onbid/{id}` 200
- `/onbid/today` 200
- `/onbid?data_quality=needs_confirmation` 200
- `/onbid/share/{token}` 200, noindex
- `/onbid/{id}/development-insight` 200 for real_estate, 404 for non-real-estate
- anonymous `/onbid/today` preference forms hidden and login CTA exposed
- public shared summary private memo/raw payload/AI copy not exposed

## 9. 테스트 실행 결과

py_compile:

```powershell
& $Py -m py_compile backend\database\models.py backend\database\session.py backend\services\auction_items.py backend\services\product_engagement.py backend\web\routers\auctions.py tests\_v007_helpers.py tests\product_copy_safety_test.py tests\onbid_today_review_completion_test.py tests\onbid_data_quality_needed_filter_test.py tests\onbid_data_issue_report_test.py tests\onbid_review_summary_share_test.py tests\product_analytics_events_test.py tests\development_insight_cta_safety_test.py
```

PASS.

Existing required tests:

```text
tests/onbid_freshness_policy_test.py -> PASS
tests/onbid_public_filter_state_test.py -> PASS
tests/onbid_category_mapping_test.py -> PASS
tests/sitemap_fresh_public_routes_test.py -> PASS
tests/onbid_module_test.py -> PASS
tests/page_response_smoke_test.py -> PASS
tests/public_access_auth_boundary_test.py -> PASS
tests/router_boundary_test.py -> PASS
tests/isolated_operations_test.py -> PASS
```

New v007 tests:

```text
tests/product_copy_safety_test.py -> PASS
tests/onbid_today_review_completion_test.py -> PASS
tests/onbid_data_quality_needed_filter_test.py -> PASS
tests/onbid_data_issue_report_test.py -> PASS
tests/onbid_review_summary_share_test.py -> PASS
tests/product_analytics_events_test.py -> PASS
tests/development_insight_cta_safety_test.py -> PASS
```

Full pytest attempt:

```text
& $Py -m pytest
FAIL: No module named pytest
```

Common warning on TestClient tests:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## 10. 한국어 UI 보존 확인

- 신규 public-facing 문구는 한국어로 작성.
- 공개 템플릿 금지 표현 검색 결과 출력 없음.
- 기존 깨진 mojibake 영역은 전면 재번역하지 않고 v007 변경 범위의 사용자 노출 문구만 정리했다.

## 11. 잔여 리스크

- `repair_onbid_derived_fields.ps1 -Apply`는 이번 범위에서 실행하지 않았다.
- issue report 관리자 review UI는 아직 없음.
- shared summary revoke/manage UI는 아직 없음.
- Development Insight는 안내/계측만 구현했고 외부 API/계산 기능은 없다.
- full pytest는 pytest 미설치로 실행하지 못했다.

## 12. 다음 devpack 추천

1. issue report admin queue 및 처리 상태 변경 UI
2. shared summary revoke/manage UI
3. 실제 운영 review session 백업/복원 리허설과 log retention 기준
4. 공고목록 API 및 national_property API 별도 검증
5. Gate 0 원문 확인 포인트 테스트셋 확장

## 13. 종료 git status/log

```text
git status --short
출력 없음

git --no-pager diff --stat
출력 없음

git --no-pager log --oneline --decorate -5
HEAD, origin/codex/devpack-v007-product-ux-safety-analytics -> feat: add v007 review ux safety analytics foundation
c1ddc59 (codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a3 result bundle and probe page wrapper
894ee0e (origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a3 devpack instructions
d16afb2 feat: add official onbid list params and fresh probes v006-a2
10710ce docs: add v006-a2 devpack instructions
```

최종 push:

```text
git push -u origin codex/devpack-v007-product-ux-safety-analytics
원격 브랜치 생성 완료

amend 후 원격 브랜치는 `git push --force-with-lease origin codex/devpack-v007-product-ux-safety-analytics`로 갱신했다.
```
