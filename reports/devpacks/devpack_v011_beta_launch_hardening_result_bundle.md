# Devpack v011 Beta Launch Hardening Result Bundle

작성: 2026-07-10 KST  
브랜치: `codex/devpack-v011-beta-launch-hardening`  
기준: `codex/devpack-v010-beta-release-candidate-ux` (`564bb7b`)  
구현 커밋: `d659542 feat: harden beta launch security and navigation`

## 1. 작업 메타데이터와 시작 Git 상태

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Start branch: codex/devpack-v010-beta-release-candidate-ux
Start status: ?? reports/devpacks/codex_devpack_v011_beta_launch_hardening_master_instruction.md
Remote: origin https://github.com/feastJ-h/court_auction_platform.git
Base HEAD: 564bb7b docs: record v010 push result
Work branch: codex/devpack-v011-beta-launch-hardening
```

미추적 파일은 사용자가 지정한 v011 지시서 하나였고 다른 사용자 변경은 없었다. 기준 브랜치를 `--ff-only` pull한 뒤 새 브랜치를 만들었다.

## 2. 백업과 복원

작업 전 백업:

```text
source: C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db
backup: storage/backups/auction_data_20260710_131932.db
SHA-256: A6DB576E2C0103D2FFB7F4AB236A3E0B31113D8617B4884A4F0586EE4A707FA9
timestamp: 2026-07-10 13:19:32 KST
rows: users 3 / auction_items 1,164 / auction_notices 362 / audit_logs 11
duplicate groups: 0
```

실제 복원 리허설은 백업을 `storage/restore-rehearsal/restore_20260710_134010.db`로 복사해 수행했다. 새 코드 startup과 additive migration을 적용한 뒤 `PRAGMA integrity_check=ok`, 동일 주요 table count를 확인했다. 복원본 SHA-256은 `8C86701B57B99DBCCAAC9C6D833FDD5B5D7768AC22A9F5420E4B9BE8C8B8B593`이다. 원본 DB는 교체하지 않았다.

## 3. v010 실제 회귀와 root cause

기준 URL `/onbid?sort=closing_soon`에서 실제 helper 출력은 다음과 같았다.

```text
all               /onbid?sort=closing_soon
real_estate       /onbid?sort=closing_soon
movable           /onbid?sort=closing_soon
national_property /onbid?sort=closing_soon
```

`build_query_href_shared(... omit={"page", "category"}, category=value)`가 updates를 먼저 merge한 뒤 omit을 적용해 새 category까지 제거한 것이 직접 원인이다. 기존 테스트는 다른 filter와 page 제거만 검사하고 `query["category"]`를 검사하지 않아 2건 모두 통과했다.

## 4. helper와 rendered href 수정

helper 계약을 `base state에서 omit → updates 적용 → default/empty 정리 → doseq urlencode` 순서로 변경했다. false, 0, list, Unicode와 category=`all` canonical omission을 보존한다.

수정 후 실제 렌더링:

| Tab | href | response | active | first page card categories | result |
|---|---|---:|---|---|---|
| 전체 | `/onbid?sort=closing_soon` | 200 | all | movable | PASS |
| 부동산 | `/onbid?sort=closing_soon&category=real_estate` | 200 | real_estate | real_estate | PASS |
| 동산 | `/onbid?sort=closing_soon&category=movable` | 200 | movable | movable | PASS |
| 국유일반재산 | `/onbid?sort=closing_soon&category=national_property` | 200 | national_property | 0건 empty state | PASS |

복합 URL의 region/price/data_quality/sort는 보존되고 page는 제거된다. category filter는 ingestion/audit가 저장한 `public_category`를 단일 source of truth로 사용하도록 변경해 raw payload 문자열 때문에 다른 category card가 섞이던 경계도 제거했다.

## 5. category result/filter/pagination/browser 계약

- category별 모든 렌더링 card에 `data-item-category`를 추가하고 결과 격리를 테스트했다.
- all은 category query를 생략하고 primary 0건 tab도 계속 클릭 가능하다.
- 기존 pagination/filter/chip/sort 상태 보존 13개 matrix 테스트가 모두 통과했다.
- Playwright는 360×800, 390×844, 768×1024, 1024×768, 1440×900에서 body overflow 0, mobile tab internal scroll, detail 이동을 확인했다.
- axe WCAG 2 A/AA critical/serious 0.
- 인앱 브라우저 target은 세션에 제공되지 않아 별도 interactive back/forward 캡처는 만들지 못했다. 실제 Playwright navigation과 external anchor E2E로 검증했다.

## 6. health, process, tunnel

추가 endpoint:

| Endpoint | attempt 1 | attempt 2 | attempt 3 | summary |
|---|---:|---:|---:|---|
| `/health/live` | 200 | 200 | 200 | process/uptime |
| `/health/ready` | 200 | 200 | 200 | config, DB SELECT, public count, security store, last sync summary |
| `/health/version` | 200 | 200 | 200 | version/commit/environment/build time only |
| `/onbid` | 200 | 200 | 200 | rendered response |

`start_beta_review.ps1`는 preflight, 단일 uvicorn worker, readiness wait, PID/log 경로, optional quick tunnel URL을 제공한다. `stop/status/check_beta_health`와 `run_external_beta_e2e.ps1`도 추가했다. quick tunnel URL parser가 `api.trycloudflare.com`을 URL로 오인하던 문제를 재현 후 제외했다.

외부 QA:

```text
ephemeral URL: https://magic-instead-pig-with.trycloudflare.com
DNS A lookup: 3/3 PASS (104.16.230.132 / 104.16.231.132)
external live/ready/version: 3/3 each PASS
external all/real_estate/movable/national_property: PASS
worker count: 1
post-QA cloudflared/app process: stopped
```

Cloudflare named-tunnel credential과 소유 도메인 정보는 없어 임의 생성하지 않았다. `docs/operations/named_tunnel_setup.md`에 `court-auction-beta` 절차를 기록했다.

## 7. config fail-closed와 admin bootstrap

`APP_ENV=development|beta|production`을 추가했다. beta/production에서 다음은 startup 차단된다.

- 기본 또는 32자 미만 `APP_SECRET_KEY`
- `INITIAL_ADMIN_PASSWORD=admin1234!`
- test/memory DB URL
- local login hint 활성화

beta/production startup은 초기 admin을 자동 생성하지 않는다. `python -m backend.cli.bootstrap_admin`만 one-time admin 생성에 사용하며 중복 생성·비밀번호 출력은 하지 않고 최초 변경을 강제한다. startup audit은 secret 값 없이 환경/모드/DB backend/store backend/API key 설정 여부 boolean만 기록한다.

## 8. CSRF와 logout

2시간 수명의 cryptographically random signed double-submit token을 구현했다. cookie와 form/header token을 constant-time 비교하며 beta/production 모든 unsafe method에 적용한다.

- 모든 POST HTML form: hidden `csrf_token` 포함(정적 scan missing 0)
- JSON API: `X-CSRF-Token`
- `beta.js` analytics/preference 요청: header 자동 전송
- missing/wrong/other-client token: 403
- valid token: 정상 처리
- cross-origin: 기존 Origin/Sec-Fetch 경계와 함께 403
- `GET /logout`: 405, `POST /logout`: CSRF 후 persistent revoke

## 9. shared security state

`SecurityStateStore`와 SQLite 구현을 추가했다. session ID와 IP는 keyed HMAC hash만 저장하고 expiry index/cleanup을 제공한다. store instance 재생성 뒤 session revoke와 rate limit이 유지됨을 테스트했다. `REDIS_URL`이 있으면 lazy Redis adapter를 선택한다. 현재 beta 검증은 SQLite store이며 start script가 worker 1개를 강제한다. Redis 실서비스 연결 검증은 credential 부재로 보류했다.

## 10. beta account lifecycle와 legal consent

additive user field 11개와 index를 추가했다. 초대 계정은 `must_change_password=true`, active/inactive, beta expiry, creator admin ID, 실패 횟수/15분 lock을 지원한다. 5회 실패 후 잠금, 성공 시 reset, 비활성·만료 계정 차단과 generic login failure를 적용했다.

최초 로그인 흐름:

```text
login → forced password change → terms/privacy/beta notice version consent → user page
```

세 버전과 accepted_at을 저장하고 audit event를 남긴다. 법률 완전성을 보장한다는 표현은 사용하지 않았다.

## 11. sync/freshness/data integrity

`onbid_sync_runs`에 aggregate 실행 이력을 기록한다. raw payload/API key는 저장하지 않는다. 기존 `CrawlRun`과 함께 success/failure isolation을 유지하며 실패는 기존 공개 데이터를 지우지 않는다.

현재 동적 공개 데이터:

```text
all 1,076 / real_estate 516 / movable 560 / national_property 0 / other 0
duplicate groups 0 / sample public 0 / stale-or-unknown public 0
```

국유일반재산은 fresh 0건을 그대로 표시한다. raw text fallback으로 movable을 국유일반재산 결과에 섞던 경계를 제거했다. 공식 API date semantics의 추가 대량 probe는 실제 key/정책 확인이 필요한 후속 항목이다.

## 12. official ONBID original path

공식 ONBID 검색 결과에서 물건 상세가 `CltrDtlController/mvmnCltrDtl.do`와 `onbidCltrno`, `onbidPbancNo`, `pbctCdtnNo`, `pbctNo` 조합을 사용하는 사례 여러 건을 확인했다. 다만 로컬 각 row의 `pbanc_mng_no`가 공식 `onbidPbancNo`와 동치임을 전체적으로 증명하지 못했으므로 URL을 추측 생성하지 않았다.

현재 안전 정책을 유지한다.

- 수집된 공식 detail URL만 redirect
- 없으면 공식 ONBID 홈, 온비드 번호/공매 번호/물건명 copy와 확인 단계 안내
- analytics는 event + 내부 item ID + field type allowlist만 저장하고 full URL/value/name은 저장하지 않음

## 13. observability와 operations

- validated/generated `X-Request-ID`를 response와 JSON structured request log에 연결했다.
- method/path/status/duration만 기록하며 query/cookie/token/memo/raw URL은 제외했다.
- admin readiness에 version/commit/environment, category count, last successful sync, security store backend를 추가했다.
- 운영/계정/sync/incident/privacy/backup/rollback/tunnel runbook 8개를 추가했다.
- alert script는 live/ready/onbid와 exit code를 제공한다. 5xx history, Windows Event Log/외부 notification adapter, backup/sync threshold의 완전 자동화는 후속 gap이다.

## 14. migration과 rollback

기존 table/column/data 삭제 없이 users column, security table 2개, sync run table 1개와 index만 추가했다. migration은 column introspection과 `IF NOT EXISTS`로 idempotent하다. `docs/migration_ledger.md`를 갱신했다. SQLite column 제거 rollback은 지원하지 않으며 코드 rollback은 새 필드를 무시하고, 데이터 손상 시에만 사전 전체 백업으로 복원한다.

## 15. CI, dependency, Lighthouse

GitHub Actions에 Python 3.12/Node 20, CSS build, default pytest, banned-copy scan, pip/npm audit, JUnit artifact를 추가했다. external E2E는 secret 없는 default CI에서 실행하지 않는다.

```text
pip-audit: No known vulnerabilities found
npm audit --audit-level=high: critical 0 / high 0 / moderate 17
```

moderate 17건은 QA 전용 Lighthouse의 OpenTelemetry/Sentry transitive dependency이며 자동 fix가 Lighthouse breaking downgrade를 요구해 무분별한 force fix를 하지 않았다.

Lighthouse `/onbid`:

```text
performance 1.00
accessibility 1.00
best-practices 0.96
seo 0.54
```

SEO는 beta noindex가 활성화된 검토 build의 의도된 제한이다. 보고서/스크린샷은 `storage/qa/v011` 및 `storage/qa/v010`에 두고 commit하지 않았다.

## 16. 최종 테스트

개발·검증 loop를 3회 이상 수행했다.

```text
targeted v011 blocker tests: 24 passed
default pytest: 80 passed, 2 visual deselected
visual Playwright/axe: 2 passed, 80 deselected
legacy: onbid_module/page_response/router_boundary/isolated_operations PASS
run_beta_qa.ps1 -Visual: PASS
external beta E2E: PASS
backup restore rehearsal: PASS
banned public copy: 0
mojibake: 0
unsafe POST form missing CSRF: 0
sensitive staged file: 0
git diff --check: PASS
```

경고는 FastAPI `on_event` deprecation과 TestClient/httpx 전환 안내 3건이며 기능 실패는 아니다. lifespan 전환은 별도 refactor로 남긴다.

## 17. 변경 파일

주요 코드: `backend/config.py`, `backend/database/{models,session}.py`, `backend/services/{auction_items,auth,csrf,security_state,onbid_sync_runs}.py`, `backend/cli/bootstrap_admin.py`, `backend/workers/onbid_sync.py`, `main_app.py`, 관련 router/template/JS.  
테스트: query/category/rendered/result, config, CSRF HTML/JSON, logout, health, security persistence, lockout, lifecycle, consent, sync history, Playwright.  
운영: start/stop/status/health/external E2E/restore scripts, `.github/workflows/beta-release-gate.yml`, `docs/operations/*`, migration ledger.  
의존성: `redis`, QA용 `lighthouse`.

## 18. 잔여 risk와 beta go/no-go

### 제한 초대 beta: GO

30~50명 invite/admin-created account를 단일 worker와 supervised start script로 운영하는 조건에서 navigation, 보안, 계정, 복원, 외부 접근 blocker가 모두 통과했다.

### 고정 공개 beta hostname: 아직 NO-GO

named tunnel credential/소유 hostname이 없고 quick tunnel은 uptime 보장이 없다. 고정 hostname 공개 전에는 named tunnel 설정과 동일 external gate 재실행이 필요하다.

후속 항목:

1. named tunnel credential/hostname 연결 후 release gate 재실행
2. 실제 beta 계정 2개로 admin invite/reset/expiry 운영 리허설
3. alert threshold·5xx history·notification adapter와 Windows Scheduler 실제 등록
4. Redis configured 환경 연결/장애 fallback 검증
5. official ID mapping이 증명된 row만 direct item URL coverage 확대
6. 국유일반재산 fresh API sample 추가 조사
7. 사용자 export/delete request command와 전용 feedback workflow 완성
8. FastAPI lifespan 및 TestClient/httpx deprecation 정리

## 19. 종료 Git/commit/push

```text
d659542 feat: harden beta launch security and navigation
f179e9c docs: add v011 beta launch result bundle
remote branch: origin/codex/devpack-v011-beta-launch-hardening
push: PASS (new branch, upstream tracking configured)
PR creation URL: https://github.com/feastJ-h/court_auction_platform/pull/new/codex/devpack-v011-beta-launch-hardening
```

main merge/push는 수행하지 않았다. 이 push 결과 기록은 마지막 문서 checkpoint에서 한 번 더 push한다.
