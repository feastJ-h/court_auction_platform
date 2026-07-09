# devpack_v006_a3_result_bundle.md

## 1. 작업 메타데이터

- 작업일: 2026-07-07
- 브랜치: `codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal`
- 지시서: `reports/devpacks/devpack_v006_a3_instruction.md`
- 목표: 부동산/동산 ONBID public-visible fresh non-sample 데이터를 90~120건 수준으로 확보하고 public `/onbid` QA에 사용할 수 있게 준비
- commit/push: 미실행

## 2. 시작 git status/log/diff

```text
git status --short
출력 없음

git --no-pager log --oneline --decorate -5
894ee0e (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a3 devpack instructions
d16afb2 feat: add official onbid list params and fresh probes v006-a2
10710ce docs: add v006-a2 devpack instructions
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
c7df5b7 docs: add v006 devpack instructions

git diff --name-only
출력 없음
```

## 3. v006-a2 기준 상태 확인

- a2 결과 커밋 확인: `d16afb2 feat: add official onbid list params and fresh probes v006-a2`
- 작업 시작 시 working tree: clean
- a2 미커밋 잔여 변경: 없음

## 4. 변경 파일 목록

- `run_onbid_fresh_probe.ps1`
- `run_onbid_probe.ps1`
- `reports/devpacks/devpack_v006_a3_result_bundle.md`

DB 파일, backup 파일, log 파일, raw payload dump 파일은 Git 추적 변경에 포함하지 않았습니다.

## 5. PageNo 지원 여부 및 수정 여부

- 확인 결과: `backend.workers.onbid_sync`와 `backend.onbid.client`는 이미 `page_no`를 list API `pageNo`로 전달하고 있었음.
- 부족한 부분: `run_onbid_fresh_probe.ps1`, `run_onbid_probe.ps1`에 `-PageNo` 래퍼 인자가 없었음.
- 수정 내용:
  - 두 PowerShell 래퍼에 `[int]$PageNo = 1` 추가
  - `run_onbid_fresh_probe.ps1`에서 `run_onbid_probe.ps1 -PageNo`로 전달
  - `run_onbid_probe.ps1`에서 Python `--page-no`로 전달
  - 시작 로그에 `PageNo`만 추가, API key 출력 없음

## 6. DB 백업

- 백업 실행 여부: 실행
- 백업 시각: 2026-07-07 12:27:54 KST
- 백업 파일 경로: `C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260707_122754.db`
- sha256: `6AEE09A127C88AA4345676337965AD008BB548B03BC5FBFEADB6C0D35F476D73`
- source: `C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db`
- 복원 미실행 확인: 복원하지 않음

## 7. baseline audit

```text
audit_onbid_freshness.ps1 -MinDate 2025-01-01
{"by_category": {"all": 0, "movable": 22, "national_property": 1, "other": 0, "real_estate": 105}, "fresh": 47, "invalid_date": 20, "stale": 61, "total": 128, "unknown_date": 0}

repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
{"checked": 128, "updated": 0, "would_update": 48}
```

서비스 public filter 기준 baseline:

```text
public-visible fresh non-sample total: 40
public-visible fresh non-sample real_estate: 20
public-visible fresh non-sample movable: 20
sample/fixture row count: 7
duplicate key count: 0
detail marker count real_estate: 24
detail marker count movable: 2
```

## 8. 실행한 API 호출 목록

초기 sandbox 내 네트워크 호출 2건은 Windows 소켓 권한 오류로 실패했고, API 응답 본문은 받지 못했습니다. 동일 제한 호출을 승인된 외부 네트워크 실행으로 재시도했습니다.

| ApiKind | PageNo | Limit | MaxPages | MinDate | PrptDivCd | PvctTrgtYn | BidPrdYmdStart | BidPrdYmdEnd | fetched | accepted_fresh | inserted | duplicates | dropped_stale | dropped_unknown_date |
|---|---:|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| real_estate | 2 | 20 | 1 | 2025-01-01 | 0007,0005,0004,0002,0003,0006,0008,0011,0013 | N | 20260707 | 20260905 | 20 | 20 | 20 | 0 | 0 | 0 |
| movable | 2 | 20 | 1 | 2025-01-01 | 0007,0005,0004,0002,0003,0006,0008,0011,0013 | N | 20260707 | 20260905 | 20 | 20 | 20 | 0 | 0 | 0 |
| real_estate | 3 | 20 | 1 | 2025-01-01 | 0007,0005,0004,0002,0003,0006,0008,0011,0013 | N | 20260707 | 20260905 | 20 | 20 | 20 | 0 | 0 | 0 |
| real_estate | 2 | 20 | 1 | 2025-01-01 | 0007,0005,0004,0002,0003,0006,0008,0011,0013 | N | 20260707 | 20260905 | 20 | 20 | 0 | 20 | 0 | 0 |
| movable | 2 | 20 | 1 | 2025-01-01 | 0007,0005,0004,0002,0003,0006,0008,0011,0013 | N | 20260707 | 20260905 | 20 | 20 | 0 | 20 | 0 | 0 |

상세 검증 호출:

```text
real_estate PageNo=2 IncludeDetails=True DetailLimit=1
movable PageNo=2 IncludeDetails=True DetailLimit=1
```

공고목록 API 호출: 없음  
national_property/국유재산 전용 API 호출: 없음

## 9. API key 및 raw payload 미출력 확인

- API key 출력: 없음
- raw payload 전체 출력: 없음
- result bundle에 API response body 전체 첨부: 없음
- 사진 URL 전체 목록 첨부: 없음
- 내부 파일 경로/raw document path 출력: 없음

## 10. 추가 수집 결과

real_estate:

```text
PageNo=2 fetched=20 accepted_fresh=20 inserted=20 duplicates=0
PageNo=3 fetched=20 accepted_fresh=20 inserted=20 duplicates=0
```

movable:

```text
PageNo=2 fetched=20 accepted_fresh=20 inserted=20 duplicates=0
```

목록 수집 중단 사유:

```text
public-visible fresh non-sample total이 100건에 도달해 추가 목록 수집 중단.
movable PageNo=3은 호출하지 않음.
```

## 11. 상세 API 검증 결과

```text
real_estate detail attempted: 1
real_estate detail succeeded: 1
movable detail attempted: 1
movable detail succeeded: 1
fresh public rows with _raw_detail marker:
  real_estate: 25
  movable: 3
raw payload 전체 미출력: 확인
```

## 12. fresh audit 전/후 비교

```text
baseline:
  total=128 fresh=47 stale=61 invalid_date=20 unknown_date=0

after page 2 collection:
  total=168 fresh=87 stale=61 invalid_date=20 unknown_date=0

final:
  total=188 fresh=107 stale=61 invalid_date=20 unknown_date=0
```

최종 dry-run repair:

```text
{"checked": 188, "updated": 0, "would_update": 48}
```

## 13. public-visible fresh non-sample 전/후 비교

```text
baseline total: 40
baseline real_estate: 20
baseline movable: 20

after page 2 total: 80
after page 2 real_estate: 40
after page 2 movable: 40

final total: 100
final real_estate: 60
final movable: 40
```

## 14. 최종 QA 데이터셋 규모

```text
최종 public-visible fresh non-sample total: 100
최종 public-visible fresh non-sample real_estate: 60
최종 public-visible fresh non-sample movable: 40

최종 DB total: 188
최종 fresh: 107
최종 stale: 61
최종 invalid_date: 20
최종 unknown_date: 0

sample/fixture row count: 7
detail marker count real_estate: 25
detail marker count movable: 3
duplicate key count: 0
```

## 15. fixture 생성 여부

- fixture 생성 여부: 생성하지 않음
- 사유: 로컬 DB에 public `/onbid` QA용 100건 데이터셋이 확보되어 별도 Git 추적 fixture가 필요하지 않음
- raw payload fixture 생성: 없음
- API key 포함 fixture: 없음
- private/internal path 포함 fixture: 없음

## 16. Git에 커밋하면 안 되는 파일 확인

- `auction_data.db`: Git 추적 변경에 표시되지 않음
- `storage/backups/*`: Git 추적 변경에 표시되지 않음
- `storage/logs/*`: Git 추적 변경에 표시되지 않음
- raw payload dump: 생성하지 않음
- 테스트 DB: Git 추적 변경에 표시되지 않음
- commit/push: 미실행

## 17. public route QA 결과

기존 테스트는 isolated DB를 사용하므로, 실제 수집 DB 대상으로 별도 TestClient QA를 실행했습니다.

```text
/onbid status: 200
/onbid 목록 row 존재: true
/onbid?category=real_estate status: 200
/onbid?category=movable status: 200
real_estate category row 존재: true
movable category row 존재: true
초기화 문구 유지: true
Reset 문구 미노출: true
비로그인 상세 status: 200
비로그인 상세에서 관심/감시/패스/메모 form 미노출: true
비로그인 상세에서 로그인 CTA 노출: true
```

비고:

- 상세 페이지에 `AI 분석` 문자열은 존재하지만, 확인된 문맥은 `로그인 후에 AI 분석 문구를 확인할 수 있습니다.`라는 공개 상태 안내 문구입니다.
- raw AI 분석 본문 노출은 확인되지 않았습니다.

## 18. repair Apply 권장 여부

```text
repair Apply 권장 여부: 아니오
권장 사유: public 목록은 fallback/service filter 기준으로 100건을 정상 표시하며, 이번 a3 범위는 수집/QA 데이터셋 확보이다.
실행 전 필수 조건: 사용자 별도 승인, 최신 DB 백업 확인, dry-run would_update 영향 검토
제안 명령:
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

이번 작업에서 `-Apply`는 실행하지 않았습니다.

## 19. 한국어 UI 보존 확인

- 기존 한글 UI를 영어로 바꾼 변경: 없음
- 새 사용자 표시 문구의 기본 언어: 해당 없음
- 영어가 남아 있는 영역: 코드 식별자 / 환경변수 / API kind / 외부 서비스명 / CLI 출력
- 의도치 않은 번역 변경 확인: 완료
- 확인한 템플릿/파일:
  - `frontend/templates/auctions/detail.html`
  - `frontend/templates/shared/onbid_category_tabs.html`
  - `frontend/templates/shared/public_nav.html`
  - `run_onbid_fresh_probe.ps1`
  - `run_onbid_probe.ps1`

## 20. 테스트 실행 결과

```text
& $Py tests/onbid_freshness_policy_test.py
PASS - ONBID freshness policy hides stale and unknown-date public rows

& $Py tests/onbid_public_filter_state_test.py
PASS - ONBID public filter state

& $Py tests/onbid_category_mapping_test.py
PASS - ONBID stored category mapping and counts

& $Py tests/sitemap_fresh_public_routes_test.py
PASS - sitemap includes only fresh public ONBID items

& $Py tests/onbid_module_test.py
PASS - ONBID item, notice, observability, and case link

& $Py tests/page_response_smoke_test.py
PASS - page response smoke test

& $Py tests/public_access_auth_boundary_test.py
PASS - public access and auth boundary
```

공통 경고:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## 21. 남은 리스크

- `repair_onbid_derived_fields.ps1 -DryRun`의 `would_update=48`은 남아 있으나, a3 지시서상 Apply는 사용자 승인 없이는 금지이므로 실행하지 않았습니다.
- 상세 marker는 부동산 25건, 동산 3건으로 동산 상세 보강 수가 적습니다. a3에서는 상세 API를 소량 검증으로 제한했습니다.
- 수집 데이터는 로컬 DB 기반 QA 데이터셋이며 DB 파일은 Git에 포함하지 않았습니다.

## 22. 다음 devpack 추천

- v006-a4: 확보된 100건 내외 데이터를 기반으로 public `/onbid` 필터, 정렬, 상세 UX 품질 개선
- v006-b: 운영 스케줄러 등록 전 리허설, 백업/복원 리허설, log retention 기준 수립
- v006-d: 공고목록 API와 national_property/국유재산 전용 API를 별도 범위로 검증

## 23. 종료 git status/log

```text
git status --short
 M run_onbid_fresh_probe.ps1
 M run_onbid_probe.ps1
?? reports/devpacks/devpack_v006_a3_result_bundle.md

git --no-pager log --oneline --decorate -5
894ee0e (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a3 devpack instructions
d16afb2 feat: add official onbid list params and fresh probes v006-a2
10710ce docs: add v006-a2 devpack instructions
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
c7df5b7 docs: add v006 devpack instructions

git diff --name-only
run_onbid_fresh_probe.ps1
run_onbid_probe.ps1
```

종료 상태 확인:

- DB/backup/log/raw 파일은 Git 변경 목록에 없음
- commit/push 미실행
