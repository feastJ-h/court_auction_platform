# Codex Devpack v011 마스터 작업지시서
## Beta Launch Hardening · ONBID Navigation Recovery · Commercial Readiness Foundation

작성일: 2026-07-10 KST
대상 저장소: `feastJ-h/court_auction_platform`
기준 브랜치: `codex/devpack-v010-beta-release-candidate-ux`
권장 작업 브랜치: `codex/devpack-v011-beta-launch-hardening`
결과서: `reports/devpacks/devpack_v011_beta_launch_hardening_result_bundle.md`

---

# 0. 최종 목표

이번 devpack은 v010 결과서의 기능을 더 늘리는 작업이 아니다.

첫 번째 목표는 현재 발생한 ONBID 카테고리 메뉴 회귀를 정확히 수정하고, 다시는 helper-level test만 통과한 채 실제 사용자 흐름이 깨지지 않도록 릴리스 검증 체계를 강화하는 것이다.

두 번째 목표는 임시 리뷰 사이트 수준을 넘어, 30~50명 규모의 초대형 폐쇄 베타를 안전하게 운영할 수 있는 릴리스 기반을 만드는 것이다.

최종 사용자 여정:

```text
고정 베타 URL 접속
→ 홈
→ ONBID
→ 전체/부동산/동산/국유일반재산 탭 전환
→ 필터/정렬/페이지 이동
→ 상세 확인
→ 관심/패스/실행취소/메모
→ 내 검토함
→ 재방문
```

서비스의 제품 원칙은 유지한다.

> 우리는 경·공매 투자 판단 플랫폼이 아니라, 경·공매 후보를 빠르게 거르고 기록하게 만드는 무료 기반 검토 보조 플랫폼이다.

---

# 1. 자율 실행 지침

이번 devpack의 정상적인 개발·테스트·외부 검증 과정에서는 사용자에게 허가나 선택을 다시 묻지 않는다.

## 1.1 별도 질문 없이 허용

- Git fetch/pull/status/log/diff
- 새 작업 브랜치 생성
- 코드, 템플릿, 테스트, 문서 수정
- Python/Node/Playwright 패키지 설치
- 공식 문서와 공식 서비스 소량 네트워크 검증
- 작업 전 DB 백업
- 비파괴 DB migration
- migration dry-run/apply
- 로컬 서버 실행
- Cloudflare quick/named tunnel 점검
- 외부 URL QA
- 테스트 계정과 임시 fixture 생성
- 테스트 DB 생성/삭제
- unit/integration/visual/security test
- Lighthouse/axe/dependency audit
- Windows Scheduler 등록 rehearsal
- 작업 브랜치 commit/push
- 실패 원인 수정 후 재실행
- 최소 3회의 개발·검증 반복

## 1.2 질문하지 않고 선택하는 원칙

- 구현 선택지는 현재 FastAPI/SQLite/Windows 구조에 가장 작은 위험을 주는 안을 선택한다.
- 자격증명이 필요한 외부 작업이 막히면 질문하며 멈추지 않는다.
  - 가능한 로컬 구현과 runbook을 완료한다.
  - quick tunnel로 외부 QA를 수행한다.
  - missing credential을 결과서에 명시한다.
- 테스트 실패는 보고만 하지 말고 원인을 수정한 뒤 다시 실행한다.
- 공식 데이터 한계로 목표 달성이 불가능하면 가짜 데이터를 만들지 않는다.
- 한 항목이 막혀도 독립적인 나머지 작업은 계속한다.

---

# 2. 절대 하면 안 되는 작업

## 2.1 Git/배포/데이터

- `main` 직접 작업, merge, push
- 사용자 확인 없는 production 공개 배포
- 운영 DNS 소유권 변경
- Cloudflare 계정 신규 생성 또는 결제
- destructive DB migration
- 백업 없는 DB 변경
- 사용자 데이터 대량 삭제
- Git history force rewrite
- 다른 작업 브랜치 삭제
- `.env`, DB, backup, log, browser profile 커밋
- API key, secret, password, cookie, token 출력
- raw ONBID payload 전체 저장/커밋
- OCR 전문, 내부 파일 경로, 원본 비공개 파일 public 노출

## 2.2 제품 범위

- AI 권리분석
- 안전/위험 판정
- 투자 추천
- 추천 입찰가
- 예상 낙찰가
- 수익성 평가
- 명도 가능성 판단
- 전문가 추천/검증/매칭
- 실제 결제/구독
- 실제 광고 네트워크
- 전문가 marketplace
- Archi-Pro 실제 연동
- Development Insight 실제 사업성/수익 계산
- 사용자 행동 데이터 외부 판매
- 대량 programmatic SEO 페이지
- FOMO/경쟁자 수/놓치면 손해 알림
- 검증되지 않은 ONBID item URL 생성
- stale/unknown/fixture를 현재 데이터로 공개

## 2.3 public 금지 표현

```text
AI 분석
권리분석
안전한 물건
위험한 물건
추천 물건
알짜
숨은 진주
저평가
수익률
낙찰 보장
명도 쉬움
검증 전문가
공식 파트너
투자 기회
돈 되는 물건
완벽한 분석
```

---

# 3. 시작 절차

## 3.1 Git 기준점

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -12
```

```powershell
git checkout codex/devpack-v010-beta-release-candidate-ux
git pull --ff-only origin codex/devpack-v010-beta-release-candidate-ux
git checkout -b codex/devpack-v011-beta-launch-hardening
```

브랜치가 이미 있으면 fetch 후 현재 상태를 기록하고 이어서 작업한다.

## 3.2 백업

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

결과서 기록:

- source DB
- backup path
- SHA-256
- row counts
- timestamp KST

## 3.3 baseline 증거 수집

변경 전에 반드시 현재 버그를 재현한다.

다음 URL에서 각 탭 href를 추출한다.

```text
/onbid?sort=closing_soon
```

결과서에 다음 표를 남긴다.

```text
Tab | Rendered href | Expected category | Actual active category | First-card categories
```

전체/부동산/동산/국유일반재산 네 개 모두 기록한다.

현재 터널 URL이 살아 있으면 외부에서도 재현한다.

```text
https://gain-emacs-crawford-caroline.trycloudflare.com/onbid?sort=closing_soon
```

접속되지 않으면:

- `Resolve-DnsName`
- `curl.exe -I`
- cloudflared process
- port 8000 listener
- uvicorn process

을 확인하고 결과를 기록한다.

---

# 4. P0-1 카테고리 탭 회귀 수정

## 4.1 직접 원인

현재 다음 호출은 잘못된 helper semantics와 결합된다.

```python
build_query_href_shared(
    base_path,
    filters,
    omit={"page", "category"},
    category=value,
)
```

현재 helper는 updates 적용 후 omit을 수행하므로 새 category도 제거된다.

## 4.2 helper 계약 수정

`build_query_href()`의 계약을 명확히 한다.

```text
1. base state에서 omit key 제거
2. updates 적용
3. empty/ALL/default 정리
4. urlencode
```

`updates`는 omit보다 우선해야 한다.

권장 구현:

```python
def build_query_href(base_path, state=None, *, omit=None, **updates):
    omitted = omit or set()
    merged = {
        key: value
        for key, value in (state or {}).items()
        if key not in omitted
    }
    merged.update(updates)
    cleaned = clean_query_state(merged)
    query = urlencode(cleaned, doseq=True)
    return f"{base_path}?{query}" if query else base_path
```

helper 변경이 price preset, chip removal, pagination에 미치는 영향을 전체 회귀 테스트한다.

## 4.3 카테고리 href 계약

기준 URL:

```text
/onbid?sort=closing_soon
```

기대:

```text
전체            /onbid?sort=closing_soon
부동산          /onbid?sort=closing_soon&category=real_estate
동산            /onbid?sort=closing_soon&category=movable
국유일반재산    /onbid?sort=closing_soon&category=national_property
```

query order는 달라도 된다.

다른 필터가 있을 때:

```text
/onbid?region=서울&price_max=100000000&data_quality=needs_confirmation&sort=price_asc&page=9
```

부동산 탭 클릭 후:

```text
region=서울
price_max=100000000
data_quality=needs_confirmation
sort=price_asc
category=real_estate
page 없음
```

이어야 한다.

## 4.4 결과 데이터 계약

부동산 탭:

- active category `real_estate`
- 모든 public card `real_estate`
- total count가 부동산 faceted count와 일치

동산 탭:

- active category `movable`
- 모든 public card `movable`

국유일반재산:

- active category `national_property`
- 0건이면 정확한 empty state
- 다른 category row가 섞이면 실패

전체:

- category query 제거 가능
- active category `all`

## 4.5 브라우저 history

- 전체 → 부동산 → 동산
- browser back: 부동산
- browser back: 전체
- forward: 부동산

active tab과 cards가 URL과 일치해야 한다.

---

# 5. P0-2 테스트 공백 수정

## 5.1 기존 테스트 수정

`tests/onbid_category_tab_state_preservation_test.py`에 반드시 추가:

```python
assert query["category"] == ["real_estate"]
```

전체 탭은 category query가 없어도 됨을 확인한다.

## 5.2 helper unit tests

신규:

```text
tests/test_query_href_replace_semantics.py
```

케이스:

- omit base key + same key update
- omit page + category update
- category all default omission
- false/0 값 보존 여부
- list/doseq
- unicode region
- all filter preservation

## 5.3 rendered route contract

신규:

```text
tests/test_onbid_category_rendered_links.py
```

TestClient로 HTML을 파싱해 실제 anchor href를 검증한다.

helper를 직접 호출하는 테스트만으로 완료하지 않는다.

## 5.4 result contract

신규:

```text
tests/test_onbid_category_result_integrity.py
```

각 route의 반환 cards가 category 조건을 만족하는지 확인한다.

## 5.5 Playwright E2E

신규 또는 강화:

```text
tests/test_beta_category_navigation_visual.py
```

각 tab을 실제 클릭한다.

검증:

- URL
- aria-current
- count label
- result header total
- first 20 cards category
- empty state
- back/forward
- mobile horizontal tabs
- JS disabled 상태에서도 anchor navigation

## 5.6 외부 staging E2E

로컬 test만으로 완료 판정하지 않는다.

Cloudflare URL에서 같은 script를 실행할 수 있도록:

```powershell
.\run_external_beta_e2e.ps1 -BaseUrl https://...
```

를 만든다.

---

# 6. P0-3 터널과 안정적 베타 주소

## 6.1 health endpoints

추가:

```text
GET /health/live
GET /health/ready
GET /health/version
```

`/health/live`:

- process alive
- DB query 금지 또는 최소
- 200 JSON

`/health/ready`:

- DB `SELECT 1`
- migration/schema readiness
- public ONBID count
- last successful sync age
- required config validation
- critical dependency state

ready가 아니면 503.

`/health/version`:

- app version
- Git commit
- environment (`development`, `beta`, `production`)
- build time
- secret 없음

## 6.2 stable staging

기존 Cloudflare credential과 DNS 권한이 있으면 named tunnel을 구성한다.

권장 이름:

```text
court-auction-beta
```

정확한 hostname은 기존 사용자 도메인과 자격증명을 확인해 결정한다. 임의의 외부 도메인을 구매하지 않는다.

credential이 없으면:

- named tunnel runbook 작성
- `start_beta_review.ps1` 작성
- uvicorn 시작
- health wait
- quick tunnel 시작
- URL 추출
- DNS resolve 확인
- external E2E 실행
- PID/log 위치 출력

## 6.3 tunnel release gate

완료 전:

- DNS 3회 확인
- `/health/live` 3회
- `/health/ready` 3회
- `/onbid` 3회
- 5분 간격까지 기다리지는 말고, 작업 세션 안에서 시작 직후/중간/종료 직전 반복
- 502/503 발생 시 로그와 원인 수정

## 6.4 process supervision

Windows beta runbook:

- uvicorn single worker 또는 명시된 worker 수
- app start script
- app stop script
- app status script
- stale PID 처리
- stdout/stderr rotation
- unexpected exit restart strategy
- Windows Task Scheduler 또는 기존 서비스 관리 방식 rehearsal

실제 시스템 등록이 안전하고 권한이 있으면 수행 가능하나, production 자동 부팅 등록은 결과서에 정확히 표시한다.

---

# 7. P0-4 환경설정 fail-closed

## 7.1 environment profile

추가 설정:

```text
APP_ENV=development|beta|production
```

## 7.2 beta/production 금지 기본값

beta/production에서 다음이면 startup 실패:

```text
APP_SECRET_KEY=local-dev-change-me
INITIAL_ADMIN_PASSWORD=admin1234!
APP_SECRET_KEY 길이/entropy 부족
DB_URL이 의도하지 않은 test DB
DEBUG 또는 local login hint 활성
```

## 7.3 초기 관리자 bootstrap

앱 startup에서 기본 관리자 자동 생성하지 않는다.

개발 환경만 기존 편의 기능 허용 가능.

beta/production은 one-time command:

```powershell
python -m backend.cli.bootstrap_admin
```

요구:

- username/password env 또는 secure prompt
- 이미 존재하면 중복 생성 안 함
- 비밀번호 로그 출력 안 함
- 완료 후 one-time credential 제거 안내
- 초기 로그인 후 비밀번호 변경 강제 가능

## 7.4 startup audit

민감값을 제외한 설정 검사 결과만 로그:

```text
app_env
review_mode
beta_mode
beta_noindex
db backend
security store backend
redis configured boolean
onbid key configured boolean
```

---

# 8. P0-5 실제 CSRF 토큰

현재 Origin/Sec-Fetch-Site 검사는 유지하되, 추가로 session-bound CSRF를 구현한다.

## 8.1 token 방식

다음 중 현재 구조에 맞는 보수적 방식을 선택:

- signed double-submit cookie
- session-bound synchronizer token

요구:

- cryptographically random
- signed/verified
- session ID에 연결
- 일정 수명
- constant-time comparison

## 8.2 HTML forms

모든 unsafe form:

```html
<input type="hidden" name="csrf_token" value="...">
```

대상:

- login
- logout
- password change
- interest/pass/watch/note
- pass undo fallback
- issue report
- share create/revoke
- admin user actions
- admin issue actions
- admin sync
- Development Insight state mutation

## 8.3 JSON API

요구 header:

```text
X-CSRF-Token
```

`beta.js` preference API에 적용한다.

## 8.4 logout

`GET /logout`을 state mutation으로 사용하지 않는다.

- `POST /logout`
- header/nav form
- CSRF
- GET은 405 또는 안전한 confirm page

## 8.5 tests

- token 없음 403
- 잘못된 token 403
- 다른 session token 403
- 정상 token PASS
- origin 정상/token 없음 403
- token 정상/cross-origin 403
- logout GET mutation 없음

---

# 9. P0-6 공유 가능한 security state

## 9.1 interface

```text
SecurityStateStore
- revoke_session
- is_session_revoked
- consume_rate_limit
- cleanup_expired
```

## 9.2 beta 기본 구현

SQLite 기반 shared implementation을 제공한다.

- process restart 후 revoke 유지
- 여러 worker가 같은 DB에서 확인 가능
- TTL index
- cleanup script
- 개인정보 최소 저장
- raw IP를 장기 저장하지 않도록 keyed hash 가능

## 9.3 Redis adapter

`REDIS_URL`이 있으면 Redis adapter 사용 가능하도록 한다.

Redis가 없다고 beta 개발을 중단하지 않는다.

## 9.4 single-instance rule

SQLite security store가 준비되기 전까지는 beta server single worker를 강제한다.

결과서에 실제 worker 수를 기록한다.

---

# 10. P0-7 초대형 폐쇄 베타 계정 정책

공개 회원가입과 이메일 발송을 이번 범위에서 무리하게 만들지 않는다.

초기 beta는 invite/admin-created account로 운영한다.

## 10.1 사용자 필드/상태

필요 시 additive migration:

```text
account_status
must_change_password
terms_version_accepted
privacy_version_accepted
accepted_at
last_login_at
failed_login_count
locked_until
beta_expires_at
created_by_admin_id
```

이메일이 없다면 임의 이메일을 요구하지 않는다.

## 10.2 관리자 account flow

- beta user 생성
- temporary password 생성 또는 입력
- password를 결과 화면에 장기 노출하지 않음
- 첫 로그인 password change 강제
- 활성/정지
- beta 만료일
- role 변경 audit
- account reset

## 10.3 로그인 안전

- 사용자 존재 여부를 노출하지 않는 generic error
- 반복 실패 cooldown
- 성공 시 failed count reset
- inactive/expired account 차단
- audit event

## 10.4 동의

첫 로그인 또는 정책 version 변경 시:

- 베타 이용 안내
- 이용약관
- 개인정보 처리방침
- 원문 최종 확인 안내

동의 version/time을 기록한다.

법률적 완전성을 보장한다고 쓰지 않는다.

---

# 11. P0-8 운영 관측과 장애 알림

## 11.1 structured logging

- JSON line 또는 구조화 logger
- request_id
- method/path/status/duration
- user ID는 필요 시 내부 numeric ID만
- raw query의 민감값 제거
- password/token/cookie/memo/raw URL 제외

## 11.2 request ID

- incoming `X-Request-ID` 검증 또는 생성
- response header에 반환
- error log 연결

## 11.3 metrics/admin dashboard

`/admin/operations-readiness` 또는 통합 dashboard에 추가:

- app version/commit
- uptime
- DB health
- last sync success/failure
- sync age
- public counts by category
- active/upcoming count
- original-link fallback rate
- 4xx/5xx counts
- recent exceptions
- login failure/lock count
- issue reports pending
- backup age
- security store backend
- beta user active count

## 11.4 alert script

```text
check_beta_health.ps1
```

조건:

- live/ready failure
- last sync older than threshold
- public active count sudden 0
- duplicate count > 0
- 5xx threshold
- backup too old

외부 메시징 credential이 없으면:

- exit code
- local alert log
- Windows Event Log 가능 여부
- notification adapter interface/runbook

을 만든다.

---

# 12. P0-9 데이터 동기화와 신뢰성

## 12.1 증분 sync

현재 1,000건 이상이므로 수량 증가 목적의 bulk fetch는 금지한다.

목표:

- 신규/변경 항목 증분
- 중복 0
- stale/unknown 공개 0
- sync run history
- failure isolation
- 기존 public 데이터 유지

## 12.2 sync run table

필요 시 additive migration:

```text
run_id
api_kind
started_at
finished_at
status
fetched
inserted
updated
duplicates
dropped_stale
dropped_unknown
error_code
error_summary_sanitized
```

raw payload나 key 저장 금지.

## 12.3 schedule

공식 API 제한과 기존 운영 정책을 확인한 뒤 보수적인 configurable cadence를 설정한다.

예:

- list sync: 하루 수회 이하
- detail enrichment: 제한 batch
- cleanup/audit: daily

정확한 횟수는 공식 정책/현재 호출량을 확인해 환경설정으로 둔다.

## 12.4 data freshness UI

- 마지막 성공 동기화 KST
- 일정 시간 이상 오래되면 `자료 업데이트 확인 중`
- 장애 시 오래된 데이터를 최신처럼 표시하지 않음

## 12.5 raw status conflict

v009에서 남았던 raw source-status conflict queue를 관리자에서 resolve/acknowledge할 수 있게 한다.

public display는 deadline-derived state 유지.

---

# 13. P1 공식 ONBID 원문 확인 흐름

현재 direct item URL coverage 0%를 숨기지 않는다.

## 13.1 공식 경로 검증

- 공식 ONBID 페이지/문서만 사용
- 5~10개 대표 항목
- 부동산/동산 각각
- 번호로 검색 가능한지 수동 검증
- exact URL pattern이 안정적인지 검증
- login/session 종속인지 확인

## 13.2 안전한 fallback

exact deep link가 확실하지 않으면:

- 공식 ONBID 홈 링크
- 온비드 번호 copy
- 공매 번호 copy
- 물건명 copy
- 직접 확인 단계 안내

`원문 보기`라는 가짜 deep link를 만들지 않는다.

## 13.3 analytics

full URL, copied value, item name을 저장하지 않는다.

event + item ID + field type만 저장.

---

# 14. P1 국유일반재산 트랙

- fresh row 0 상태를 정직하게 유지
- stale/unknown 공개 금지
- 공식 API date semantics 조사
- list date와 bid date 분리
- normalization dry-run report
- 최대 소량 probe
- 확보 불가능하면 empty state 유지

베타 오픈을 국유일반재산 수량 때문에 막지는 않지만, 탭 오동작은 막는다.

---

# 15. P1 UX 회귀 및 beta polishing

## 15.1 category tabs

- sticky가 global nav를 가리지 않음
- mobile selected tab 자동 visible
- 0건 탭 클릭 가능
- focus/keyboard
- count/total consistency

## 15.2 filter/pagination

- category 변경 시 page reset
- pagination에서 category 유지
- chip 제거 시 category 유지
- sort 변경 시 category 유지/page reset
- price preset에서 category 유지
- browser refresh/back/forward

## 15.3 pass/undo

- beta.js JSON API에 CSRF
- 연속 패스 undo 정책 명확
- 현재 total/range optional update
- 실패 시 복원
- hidden card가 page refresh 후 계속 숨겨짐

## 15.4 empty/error states

- 0건 category
- invalid category
- page overflow
- DB unavailable readiness
- sync stale
- original path missing

## 15.5 mobile

- 360/390/768/1024/1440
- body overflow 0
- category tab internal scroll only
- filter drawer
- compact pagination
- toast
- detail action bar

---

# 16. P1 법적 고지·개인정보·데이터 거버넌스

## 16.1 legal document version

settings 또는 DB에 version:

```text
TERMS_VERSION
PRIVACY_VERSION
BETA_NOTICE_VERSION
```

## 16.2 개인정보 데이터 맵 문서

작성:

```text
docs/operations/privacy_data_map.md
```

포함:

- User 계정 필드
- session data
- preference
- memo
- analytics
- audit log
- issue report
- share token
- retention
- access role
- deletion/export path

## 16.3 retention policy

초기 정책을 설정 가능하게 한다.

- session/revoke
- rate limit
- analytics
- audit
- issue report
- revoked share
- inactive beta account

임의로 영구 보관하지 않는다.

## 16.4 user requests

베타 운영용 최소 admin workflow:

- account deactivate
- user data export
- preference/memo delete request
- share revoke
- audit 기록

실제 자동 계정 탈퇴 UI는 범위가 커지면 다음 단계로 남겨도 되지만 운영 절차와 command를 제공한다.

---

# 17. P1 백업·복원·migration·rollback

## 17.1 실제 restore rehearsal

이번에는 backup만 만들고 끝내지 않는다.

- production DB가 아닌 별도 temporary path에 restore
- integrity check
- 주요 table count
- app smoke with restored DB
- 원본 DB 교체 금지
- 결과서 SHA/count 기록

## 17.2 migration

- additive only
- migration ledger
- old DB → new code startup
- migration idempotence
- failed migration behavior

## 17.3 rollback

작성:

```text
docs/operations/beta_release_rollback.md
```

포함:

- previous commit checkout
- app stop/start
- DB restore criteria
- migration rollback limitations
- tunnel rollback
- health validation

---

# 18. P1 CI 및 release gate

## 18.1 default pytest

최소 40개 이상의 의미 있는 product test 유지.

```powershell
python -m pytest -m "not integration and not external and not visual"
```

## 18.2 required test groups

```text
query helper
rendered category href
category result integrity
pagination/filter state
preference/pass/undo
CSRF
session/config fail-closed
security store
health/readiness
account lifecycle
sync history
backup restore
legal consent
privacy boundaries
```

## 18.3 visual E2E

```powershell
python -m pytest -m visual
```

## 18.4 external E2E

```powershell
.\run_external_beta_e2e.ps1 -BaseUrl $BaseUrl
```

외부 E2E가 통과하지 않으면 beta open 판정 금지.

## 18.5 GitHub Actions

가능한 경우 workflow 추가:

- Python setup
- Node/static CSS build
- default pytest
- banned copy scan
- mojibake scan
- dependency audit
- artifact: test report

secret이 필요한 external E2E는 CI default에서 제외하고 수동 workflow로 둔다.

## 18.6 dependency scan

- `pip-audit` 또는 동등
- `npm audit`
- critical/high 발견 시 조치 또는 명확한 보류
- 무분별한 major upgrade 금지

---

# 19. P1 상용서비스 운영 문서

작성 또는 갱신:

```text
docs/operations/beta_launch_runbook.md
docs/operations/beta_account_policy.md
docs/operations/onbid_sync_policy.md
docs/operations/incident_response.md
docs/operations/backup_restore_runbook.md
docs/operations/privacy_data_map.md
docs/operations/beta_release_rollback.md
docs/operations/named_tunnel_setup.md
```

## incident severity 예시

```text
SEV-1: 개인정보/secret 노출, 데이터 손상
SEV-2: 로그인/ONBID 전체 장애, 잘못된 상태 대량 노출
SEV-3: category/filter/특정 기능 장애
SEV-4: 문구/레이아웃 경미 문제
```

SEV 정의는 운영 우선순위용이며 법적 판단을 의미하지 않는다.

---

# 20. 상용서비스 BM 준비 — 구현 금지/계측만

이번 devpack에서 결제나 광고를 실제 활성화하지 않는다.

다만 향후 검증에 필요한 안전한 계측을 정리한다.

## 20.1 beta funnel

```text
landing_view
onbid_list_view
category_tab_click
filter_apply
item_detail_view
favorite
pass
undo_pass
note_save
original_fallback_view
return_visit
```

## 20.2 admin beta dashboard

- invited users
- activated users
- weekly active
- return rate
- pass action users
- favorite users
- note users
- detail → original fallback ratio
- report count
- errors

개인 사용자를 광고주에게 노출하거나 외부 판매하지 않는다.

## 20.3 feedback

베타 feedback form:

- 탐색 불편
- 자료 오류
- 기능 오류
- 문구 오해 가능성
- 기타

자유 입력에 개인정보를 쓰지 말라는 안내.

---

# 21. 개발·검증 루프

최소 3회 수행한다.

## Loop 1 — 회귀 수정

1. category bug 재현
2. helper 계약 수정
3. unit tests
4. rendered HTML tests
5. local Playwright category navigation
6. filter/pagination regression

## Loop 2 — beta security/operations

1. config fail-closed
2. admin bootstrap
3. CSRF token
4. POST logout
5. shared security state
6. account lifecycle
7. health/readiness/version
8. structured logging/admin operations
9. backup restore rehearsal

## Loop 3 — external release candidate

1. local full QA
2. app start script
3. tunnel start
4. DNS/health verification
5. external category E2E
6. login/pass/undo E2E
7. mobile/axe/Lighthouse
8. failure fixes
9. final rerun
10. result bundle

## Loop 4 — 필요 시

다음 중 하나라도 실패하면 추가한다.

- category href missing
- wrong category cards
- external tunnel inaccessible
- ready 503
- default credential accepted in beta
- CSRF missing request succeeds
- GET logout mutates
- pytest failure
- visual E2E failure
- backup restore failure
- secret/raw/private data exposure
- mobile overflow
- legal consent not recorded

---

# 22. 필수 테스트 상세

## 22.1 category blocker tests

```text
tests/test_query_href_replace_semantics.py
tests/test_onbid_category_rendered_links.py
tests/test_onbid_category_result_integrity.py
tests/test_onbid_category_navigation_history.py
tests/test_onbid_category_filter_pagination_matrix.py
tests/test_beta_category_navigation_visual.py
```

matrix 최소:

```text
category × sort
category × region
category × price
category × data quality
category × page
category × back/forward
```

## 22.2 security tests

```text
tests/test_beta_config_fail_closed.py
tests/test_csrf_html_forms.py
tests/test_csrf_json_api.py
tests/test_logout_post_only.py
tests/test_security_state_persistence.py
tests/test_login_lockout.py
tests/test_session_revocation_restart.py
```

## 22.3 operations tests

```text
tests/test_health_live.py
tests/test_health_ready.py
tests/test_health_version_no_secret.py
tests/test_sync_run_history.py
tests/test_backup_restore_rehearsal.py
tests/test_beta_user_lifecycle.py
tests/test_terms_consent_version.py
```

## 22.4 privacy tests

- private memo never public
- share token revoke
- analytics metadata allowlist
- raw URL/payload blocked
- admin export role boundary
- account deactivation login block

---

# 23. 외부 QA 증거 형식

결과서에 아래 표 필수:

## 23.1 category navigation

```text
Base URL:

Tab | href | response | final URL | active tab | total | card categories | PASS/FAIL
```

## 23.2 health

```text
Endpoint | attempt 1 | attempt 2 | attempt 3 | body summary
```

## 23.3 login flow

```text
login
first-password-change
terms consent
favorite
pass
undo
note
logout POST
revoked session blocked
```

## 23.4 viewport

```text
360x800
390x844
768x1024
1024x768
1440x900
```

스크린샷은 `storage/qa/v011`에 저장하고 commit하지 않는다.

---

# 24. Beta Go/No-Go 기준

## 24.1 navigation

```text
all category href correct
all category result integrity PASS
category/filter/page matrix PASS
external E2E PASS
```

## 24.2 availability

```text
stable URL 또는 재현 가능한 start script
live PASS
ready PASS
version PASS
no unexplained 502/503
```

## 24.3 security

```text
beta default secret startup blocked
beta default admin password startup blocked
CSRF token enforced
logout POST only
session revoke persistent
login rate/lockout
secret staged 0
```

## 24.4 accounts/legal

```text
invite/admin-created beta account
first password change
active/expired states
terms/privacy/beta notice consent version
admin audit
```

## 24.5 data

```text
public active data > 0
duplicates 0
sample exposure 0
stale/unknown exposure 0
last sync visible
sync failure does not erase existing public data
```

## 24.6 quality

```text
default pytest PASS
visual PASS
external E2E PASS
axe critical/serious 0
body overflow 0
banned copy 0
mojibake 0
backup restore PASS
```

## 24.7 판정 강제 규칙

다음 중 하나면 `베타 오픈 보류`:

- category menu failure
- external URL inaccessible without recovery procedure
- default credentials accepted
- CSRF bypass
- private data exposure
- backup restore failure
- ready health false
- required tests fail

---

# 25. 결과서 형식

파일:

```text
reports/devpacks/devpack_v011_beta_launch_hardening_result_bundle.md
```

반드시 포함:

1. 작업 메타데이터
2. 시작 Git 상태
3. 백업 정보
4. v010 결과서와 실제 회귀 비교
5. category root cause
6. helper 변경 전/후
7. rendered href 전/후 표
8. category result integrity
9. filter/pagination matrix
10. local Playwright
11. external E2E
12. tunnel/DNS/process 상태
13. health endpoints
14. config fail-closed
15. admin bootstrap
16. CSRF/POST logout
17. security store
18. beta account lifecycle
19. legal consent version
20. sync/data freshness
21. original fallback
22. national property status
23. structured log/operations dashboard
24. backup restore rehearsal
25. migration/rollback
26. pytest collection/result
27. visual/axe/Lighthouse
28. dependency audit
29. 개인정보/secret/raw exposure scan
30. 변경 파일 목록
31. 남은 리스크
32. beta go/no-go 판정
33. 다음 단계
34. 종료 Git 상태
35. commit/push

결과서는 구현하지 못한 항목을 PASS로 쓰지 않는다.

---

# 26. Commit/Push

논리적 checkpoint:

```text
fix: restore onbid category navigation
feat: harden beta security and account lifecycle
feat: add beta health monitoring and operations
 test: add external beta release gates
 docs: add v011 beta launch result bundle
```

최종:

```powershell
git status --short
git diff --check
git diff --name-only
```

금지 파일 scan:

```text
.env
*.db
storage/backups/*
storage/logs/*
storage/qa/*
cloudflared credentials
browser profile
session/cookie files
raw payload
```

```powershell
git push -u origin codex/devpack-v011-beta-launch-hardening
```

`main` merge/push 금지.

---

# 27. 최종 실행 지시

이번 작업에서는 정상적인 개발 판단을 사용자에게 묻지 않는다.

끝까지 다음 순서로 진행한다.

```text
현재 버그 재현
→ 코드 원인 증명
→ 회귀 수정
→ 핵심 테스트 보강
→ 보안/계정/운영 기반 구현
→ backup restore
→ local full QA
→ tunnel 실행
→ external E2E
→ 실패 수정
→ 전체 재검증
→ go/no-go 판정
→ 결과서
→ 작업 브랜치 commit/push
```

가장 중요한 완료 조건:

> 전체·부동산·동산·국유일반재산 탭이 실제로 서로 다른 URL과 서로 다른 결과를 보여주며, 로컬 helper test뿐 아니라 외부 브라우저 클릭으로 검증되어야 한다.

그 조건을 충족하지 못하면 다른 기능이 많이 완성되어도 베타 오픈 가능으로 판정하지 않는다.
