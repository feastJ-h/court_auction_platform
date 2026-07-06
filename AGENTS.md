# AGENTS.md

이 파일은 `court_auction_platform` 저장소에서 Codex CLI가 작업할 때 반드시 따라야 하는 repo-level 작업 규칙이다. 사람용 README가 아니라, 코딩 에이전트가 반복 실수를 줄이고 장시간 작업을 안정적으로 수행하도록 돕는 운영 지침이다.

## 0. 현재 기준 상태

- 프로젝트 경로: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- 원격 저장소: `https://github.com/feastJ-h/court_auction_platform.git`
- 기준 태그: `baseline-v002-20260706`
- v003 작업 브랜치: `codex/devpack-v003-public-first-personalization`
- v002 baseline 커밋: `48f47c7 baseline after devpack v002`
- v002 이후 새 개발팩은 반드시 별도 브랜치에서 진행한다.

## 1. 작업 시작 전 필수 확인

모든 작업 시작 전 아래 명령을 실행하고 결과를 최종 결과서에 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
```

정상 기대값:

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Branch: codex/devpack-v003-public-first-personalization 또는 해당 devpack 브랜치
Remote: https://github.com/feastJ-h/court_auction_platform.git
```

다음 상황이면 기능 개발을 시작하지 않는다.

- Git root가 `court_auction_platform`이 아니다.
- 현재 브랜치가 `main`이다.
- `git status --short`에 사용자가 만든 미확인 변경이 있고, 지시서에서 처리 기준이 없다.
- `.env`, DB, `storage/`, 로그, 원문 파일이 stage되어 있다.
- `git rev-parse`가 실패한다.

## 2. Git 절대 규칙

- 사용자 명시 승인 없이 `git init`을 실행하지 않는다.
- `main` 브랜치에서 직접 개발하지 않는다.
- `git reset --hard`, `git clean -fd`, `git clean -fdx`는 사용자 명시 승인 없이 실행하지 않는다.
- `.git` 디렉터리를 삭제하지 않는다.
- 잘못된 Git metadata가 발견되면 삭제하지 말고 rename 또는 보고서 기록으로 보존한다.
- 기능 개발은 항상 devpack 브랜치에서 수행한다.
- 커밋은 가능하면 논리 단위로 나누되, 최종 결과 문서는 하나의 bundle로 통합한다.
- push는 지시서에서 허용했거나 사용자가 승인한 경우에만 수행한다.

## 3. 커밋 금지 대상

다음은 절대 커밋하지 않는다.

```text
.env
.env.*
*.db
*.sqlite
*.sqlite3
storage/
storage/logs/
logs/
*.log
runtime_settings.json
.git.bad-init-*
.git.empty-invalid-*
__pycache__/
.pytest_cache/
.venv/
venv/
```

커밋 전 반드시 실행한다.

```powershell
git diff --cached --name-only | Select-String -Pattern '(^|/|\\)(\.env|storage|logs)(/|\\|$)|\.(db|sqlite|sqlite3)$|runtime_settings\.json|\.git\.bad-init'
```

출력이 있으면 커밋하지 말고 해당 파일을 stage에서 제거한 뒤 결과서에 기록한다.

주의: `backend/document_pipeline/storage.py`, `backend/runtime_settings.py`, `backend/services/audit_logs.py`처럼 소스 파일명에 `storage`, `runtime_settings`, `logs`가 포함된 것은 런타임 데이터가 아니다. 다만 자동 검사 결과가 애매하면 경로 단위로 확인한다.

## 4. 프로젝트 서비스 경계

이 프로젝트는 두 축으로 구성된다.

### 4.1 회생/파산

- 법원 공고와 첨부 문서를 수집한다.
- 원문 저장, OCR, AI 분석, 관리자 검토, 사용자 관심/패스/메모 기능을 제공한다.
- AI 분석은 현재 회생/파산 영역에 집중한다.
- 비로그인 공개 화면에서는 기본 목록/기본 상세만 보여주고, AI 분석과 내부 원문 파일은 숨긴다.

### 4.2 온비드 공매

- 온비드 API를 통해 공매 물건, 상세, 공고, 공고 물건정보를 수집한다.
- 온비드는 대량 공매 데이터 수집, 정규화, 검색, 가격/상태 추적, 공고 연결 확인에 집중한다.
- 온비드 전체 물건에 AI 분석을 자동 적용하지 않는다.
- 회생/파산 사건과 온비드 물건을 억지로 자동 연결하지 않는다. 필요한 경우 수동 연결 또는 후보 추천 단계에서 별도로 검토한다.

## 5. 공개/로그인/관리자 정책

### 비로그인 사용자

- 온비드 목록/상세를 볼 수 있다.
- 회생/파산 목록/기본 상세를 볼 수 있다.
- 외부 원문 링크를 볼 수 있다.
- 회생/파산 AI 분석은 볼 수 없다.
- 내부 저장 원문 파일은 볼 수 없다.
- 관심/패스/메모 버튼을 누르면 로그인 안내를 받는다.

### 로그인 사용자

- 온비드 관심/패스/감시/메모를 사용할 수 있다.
- 회생/파산 관심/패스/감시/메모를 사용할 수 있다.
- 회생/파산 AI 분석 결과를 볼 수 있다.
- 내 관심/패스/메모 목록을 관리할 수 있다.

### 관리자

- 기존 수집/분석/품질/사용자 관리 기능을 유지한다.
- 관리자 화면에는 광고를 표시하지 않는다.
- 관리자 API는 반드시 관리자 인증을 요구한다.

## 6. 원문/파일 접근 정책

- 외부 원문 URL은 공개 페이지에 노출 가능하다.
- 내부 저장 원문 파일, OCR 결과 전문, raw payload, raw document file path는 공개하지 않는다.
- `/documents/raw/{raw_doc_id}` 같은 내부 원문 다운로드 경계는 로그인 또는 관리자 보호를 유지한다.
- 링크는 새 창으로 열고 `rel="noopener noreferrer"`를 사용한다.
- URL이 비어 있거나 신뢰하기 어려우면 버튼을 숨기거나 비활성화한다.

## 7. 온비드 데이터 무결성 규칙

온비드 물건 중복 기준은 유지한다.

```text
source + cltr_mng_no + pbct_cdtn_no
```

다음 식별자는 보조 식별자로 유지한다.

```text
onbid_cltr_no
pbct_no
pbct_nsq
pbanc_mng_no
notice_no
```

공고-물건 링크 unique 기준은 유지한다.

```text
source + notice_id + auction_item_id
```

온비드 공고 흐름:

```text
api_kind="notice"
-> fetch_notice_items
-> optional fetch_notice_detail
-> upsert_auction_notice_payload
-> optional fetch_notice_cltr_items
-> normalize_onbid_api_item(source_api="notice_cltr")
-> upsert_auction_item
-> upsert_auction_notice_item_link
```

## 8. DB/마이그레이션 규칙

- SQLite 기존 DB를 파괴하지 않는다.
- 기존 컬럼 삭제, 테이블 삭제, 데이터 삭제는 금지한다.
- 신규 테이블/컬럼은 비파괴 방식으로 추가한다.
- schema 변경 시 `docs/migration_ledger.md`를 업데이트한다.
- destructive migration이 필요하면 구현하지 말고 결과서에 보류 항목으로 기록한다.
- 운영 DB 변경 전에는 `backup_database.ps1` 실행을 권장한다.
- Alembic 본격 도입은 별도 devpack에서 다룬다. 현재 devpack에서 임의 전환하지 않는다.

## 9. 작업 방식

- devpack 지시서를 먼저 읽고 그대로 따른다.
- 사소한 의문은 사용자에게 묻지 말고 지시서의 판단 기준에 따라 진행한다.
- 다음 경우에는 구현을 억지로 진행하지 말고 안전하게 보류하거나 대안을 적용한 뒤 결과서에 기록한다.
  - 실제 API 키가 필요한 경우
  - 파괴적 DB 변경이 필요한 경우
  - 원문 파일/개인정보 노출 위험이 있는 경우
  - AI 분석 데이터가 비로그인 응답으로 노출될 위험이 있는 경우
  - 기존 테스트를 무력화해야만 통과하는 경우
  - Git root/branch가 불명확한 경우
- Core Scope를 먼저 완료한다.
- Core Scope가 테스트로 검증되면 Extended Scope로 진행한다.
- Extended Scope가 안정적으로 완료되면 Stretch Scope를 우선순위대로 진행한다.

## 10. 문서/결과서 규칙

새 devpack부터는 지시서와 결과서 파일 수를 줄인다.

지시서:

```text
reports/devpacks/devpack_v00x_instruction.md
```

결과 bundle:

```text
reports/devpacks/devpack_v00x_result_bundle.md
```

최신 상태 요약:

```text
reports/project-result_current.md
```

원칙:

- 중간 결과서를 여러 개 만들지 않는다.
- 모든 중간 판단, 보류, 테스트, 실패, 변경 파일 목록은 최종 result bundle 하나에 통합한다.
- 새 markdown 문서는 꼭 필요한 경우에만 만들고, 가능하면 result bundle에 통합한다.
- schema 변경 시 `docs/migration_ledger.md`는 업데이트한다.
- AGENTS.md 변경이 필요하면 변경 이유를 result bundle에 기록한다.

## 11. 권장 테스트 명령

일반 시스템 Python에 의존성이 없을 수 있다. 기본 검증은 번들 Codex runtime Python을 우선 사용한다.

번들 Python:

```powershell
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

기본 테스트:

```powershell
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
```

온비드 샘플 스케줄러:

```powershell
.\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

추가 테스트를 만들면 result bundle에 명령과 결과를 기록한다.

## 12. 개발 완료 기준

작업 완료 전 아래를 확인한다.

```powershell
git status --short
git --no-pager diff --stat
git --no-pager log --oneline --decorate -5
```

완료 기준:

- 기능 요구사항 구현 또는 보류 사유 명확화
- 권한 경계 테스트 통과
- 기존 핵심 테스트 통과
- 민감 파일 미커밋 확인
- schema 변경 시 migration ledger 업데이트
- 최종 result bundle 작성
- `reports/project-result_current.md` 업데이트

## 13. 금지된 우회

- 테스트를 삭제하거나 무력화해서 통과시키지 않는다.
- 비로그인 화면에서 숨기는 것만으로 보안 처리를 끝내지 않는다. API/serializer 단계에서도 민감 필드를 제거한다.
- 내부 파일 경로를 공개 화면에 노출하지 않는다.
- 실제 API 키를 출력하거나 보고서에 쓰지 않는다.
- 로그 파일 전체를 결과서에 붙여넣지 않는다. 필요한 핵심 줄만 요약한다.
- 문제를 덮고 성공처럼 보고하지 않는다.

## 14. v003 이후 큰 방향

- v003: Public Beta Readiness Pack 1. 공개 탐색, 로그인 개인화, 권한 경계, 필터/SEO/고지/광고 슬롯 준비.
- v004: 온비드 데이터 품질/필터 고도화, 실제 API 샘플 보강, 국유일반재산 API 샘플 기반 설계.
- v005: 운영 안정화, 백업/복원 리허설, 스케줄러 등록 점검, 실패 알림.
- v006: 베타 출시 polish, 법적 고지 정식화, 개인정보 처리방침, AdSense 실제 연동, SEO 강화.
