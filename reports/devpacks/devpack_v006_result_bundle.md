# devpack_v006_result_bundle.md

## 1. 작업 메타데이터

- 작업일: 2026-07-07 KST
- 브랜치: `codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal`
- 기준 커밋: `c7df5b7 docs: add v006 devpack instructions`
- v005 기준: `ad6ee38 feat: finalize v005 product qa and review mode`
- 중심 목표: 2025-01-01 이후 실제 ONBID 데이터를 제한적으로 확인하고 public `/onbid` 표시 가능성을 검증

## 2. 시작 Git 상태

```text
git status --short
(출력 없음)

git --no-pager log --oneline --decorate -5
c7df5b7 (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006 devpack instructions
ad6ee38 (origin/codex/devpack-v005-product-qa-fresh-data-navigation, codex/devpack-v005-product-qa-fresh-data-navigation) feat: finalize v005 product qa and review mode
fe883c3 docs: add v005 devpack instructions
913aece (origin/codex/devpack-v004-real-onbid-operations, codex/devpack-v004-real-onbid-operations) feat: implement real onbid operations v004
999f04d docs: add v004 devpack instructions

git diff --name-only
(출력 없음)
```

추가 시작 확인:

```text
git rev-parse --show-toplevel
C:/Users/xogns/Documents/testAuction/court_auction_platform

git branch --show-current
codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal

git remote -v
origin https://github.com/feastJ-h/court_auction_platform.git
```

## 3. 확인한 파일 목록

- `reports/devpacks/devpack_v006_instruction.md`
- `backend/workers/onbid_sync.py`
- `backend/services/auction_items.py`
- `backend/onbid/client.py`
- `backend/config.py`
- `backend/web/routers/documents.py`
- `run_onbid_fresh_probe.ps1`
- `run_onbid_probe.ps1`
- `run_onbid_scheduled_sync.ps1`
- `audit_onbid_freshness.ps1`
- `repair_onbid_derived_fields.ps1`
- `backup_database.ps1`
- `check_scheduled_tasks.ps1`
- `tests/onbid_freshness_policy_test.py`
- `tests/onbid_category_mapping_test.py`
- `tests/page_response_smoke_test.py`

## 4. DB 백업

- 백업 실행: 수행
- 백업 실행 시각: 2026-07-07 08:51:01 KST
- 백업 파일: `C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260707_085101.db`
- source: `C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db`
- sha256: `245718079ECC2561CF9588416B3E88955876501823E5B1C1168BC257FD187EE0`
- 복원 실행: 수행하지 않음

## 5. 실행 명령 목록

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only
git rev-parse --show-toplevel
git branch --show-current
git remote -v
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind movable -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\check_scheduled_tasks.ps1
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind real_estate -Limit 20 -PageNo 2 -MaxPages 1 -MinDate 2025-01-01 -IncludeDetails
```

테스트 명령은 17번 섹션에 별도 기록.

## 6. 실제 API 호출 목록

API key 출력: 없음. raw payload 전체 출력: 없음. 진단 출력은 필드명과 날짜 샘플 값만 제한 출력.

| ApiKind | Limit | MaxPages | PageNo | MinDate | 결과 |
|---|---:|---:|---:|---|---|
| `real_estate` | 20 | 1 | 1 | 2025-01-01 | 최초 샌드박스 네트워크 실패 후 재시도에서 ONBID HTTP 502 |
| `real_estate` | 20 | 1 | 1 | 2025-01-01 | 재시도 성공, fetched 20, accepted_fresh 0, dropped_unknown_date 20 |
| `real_estate` | 20 | 1 | 2 | 2025-01-01 | 수동 sync, fetched 20, accepted_fresh 0, dropped_unknown_date 20 |
| `movable` | 20 | 1 | 1 | 2025-01-01 | fetched 0, total_count 0 |
| `national_property` | 20 | 1 | 1 | 2025-01-01 | 수정 전 fetched 20, dropped_unknown_date 20 |
| `national_property` | 20 | 1 | 1 | 2025-01-01 | 날짜 매핑 수정 후 fetched 20, dropped_stale 20, dropped_unknown_date 0 |
| `notice` | 20 | 1 | 1 | 2025-01-01 | 수정 전 fetched notices 20, dropped_stale 20 |
| `notice` | 20 | 1 | 1 | 2025-01-01 | `opbdDtStart` 전달 후 dropped_stale 2, dropped_unknown_date 18 |
| `notice` | 20 | 1 | 1 | 2025-01-01 | 날짜 후보 보강 후 dropped_stale 20, dropped_unknown_date 0 |

1건 제한 진단:

- `national_property`: 날짜 후보 `FRST_BID_SLCTN_YMD`, 샘플 형태 `20030711`
- `real_estate`: 날짜 후보 `cltrBidBgngDt`, `cltrBidEndDt`, 샘플 형태 `299912301000`
- `notice`: 날짜 후보 `cltrBidBgngDt`, `cltrBidEndDt`, `cltrOpbdDt`, `pbancYmd`, 샘플 형태 `201711081100`, `202712311600`, `20171101`

## 7. fresh audit 전/후 비교

초기 read-only audit:

```json
{"by_category":{"all":0,"movable":2,"national_property":1,"other":0,"real_estate":85},"fresh":7,"invalid_date":20,"stale":60,"total":88,"unknown_date":1}
```

최종 audit:

```json
{"by_category":{"all":0,"movable":2,"national_property":1,"other":0,"real_estate":85},"fresh":7,"invalid_date":20,"stale":61,"total":88,"unknown_date":0}
```

해석:

- `national_property`의 unknown-date 1건은 날짜 매핑 보강으로 stale로 분류됨.
- fresh 7건은 모두 sample/fixture marker가 있는 row로 확인됨.
- 실제 non-sample fresh row는 확보되지 않음.

## 8. public-visible row 전/후 비교

최종 현재 DB 기준:

```text
public_counts: all 0, real_estate 0, movable 0, national_property 0, other 0
all_counts: all 88, real_estate 85, movable 2, national_property 1, other 0
fresh/sample 집계: ('fresh','sample') 7, ('invalid_date','real') 20, ('stale','real') 61
```

`/onbid` 응답 확인:

```text
status_code: 200
온비드 문구 포함: True
영문 Reset 포함: False
한국어 초기화 포함: True
AI 분석 있음 public 노출: False
```

## 9. real_estate 수집 결과

- `run_onbid_fresh_probe.ps1` 최초 실행은 샌드박스 네트워크 제한으로 실패했고, escalated 재시도는 ONBID HTTP 502로 실패.
- 이후 재시도는 성공했으나 fetched 20, accepted_fresh 0, dropped_unknown_date 20.
- 1건 제한 날짜 진단에서 첫 페이지 응답은 `cltrBidBgngDt=299912301000` 같은 sentinel future 계열 날짜가 확인됨.
- `PageNo=2` 수동 sync도 fetched 20, accepted_fresh 0, dropped_unknown_date 20.
- 결론: v006 제한 범위 내에서는 실제 public-visible real_estate fresh row를 확보하지 못함.

## 10. movable 0건 원인 진단

- endpoint: `https://apis.data.go.kr/B010003/OnbidMvastListSrvc2/getMvastCltrList2`
- 파라미터: `pageNo`, `numOfRows`, `resultType=json`, `serviceKey`
- `MinDate`는 API 요청 파라미터가 아니라 수신 후 freshness 필터 기준.
- 제한 호출 결과: fetched 0, total_count 0.
- 원인 후보: 현재 기본 movable list endpoint/기본 조건에서 반환 데이터가 없거나, ONBID 동산 API가 추가 필터를 요구할 가능성.
- 이번 devpack에서는 재시도 반복하지 않음.

## 11. national_property 날짜 매핑 결과

- 수정 전: fetched 20, dropped_unknown_date 20.
- 날짜 후보 확인: `FRST_BID_SLCTN_YMD`, `YYYYMMDD` 형태.
- 수정: `backend/services/auction_items.py`의 `ONBID_DATE_KEYS`에 `FRST_BID_SLCTN_YMD` 추가.
- 수정 후: fetched 20, dropped_stale 20, dropped_unknown_date 0.
- 결론: unknown-date 원인은 날짜 필드 매핑 부족이 맞았고, fresh 데이터 부족이 아니라 오래된 2003년대 데이터가 응답되는 상태임.

## 12. notice stale drop 원인 진단

- 수정 전: notice fetched 20, dropped_stale 20.
- 원인 1: worker가 `MinDate`를 notice API의 `opbdDtStart`로 전달하지 않았음.
- 수정: `backend/workers/onbid_sync.py`에서 `MinDate`를 `YYYYMMDD`로 변환해 `opbdDtStart`에 전달.
- 원인 2: notice 응답에 `pbancYmd`, `cltrOpbdDt` 등 추가 날짜 필드가 있음.
- 수정: `ONBID_DATE_KEYS`에 `pbancYmd`, `cltrOpbdDt` 추가.
- 원인 3: 일부 응답은 시작일이 오래되고 종료/개찰일이 미래인 구조임. 날짜 후보 중 처음 값만 쓰면 stale/unknown 판단이 왜곡될 수 있음.
- 수정: plausible한 날짜 후보 중 가장 최신 날짜를 freshness date로 선택. sentinel future는 계속 invalid/hidden 처리.
- 최종 제한 호출: fetched notices 20, accepted_fresh 0, dropped_stale 20, dropped_unknown_date 0.
- 결론: unknown은 제거했지만, 현재 첫 페이지 notice는 여전히 public-visible fresh item으로 연결되지 않음.

## 13. 수동 scheduled sync script 실행 결과

- 수동 scheduled sync script 실행: 수행
- Windows Scheduler 영구 등록: 수행하지 않음
- scheduler 상태 확인:

```text
MISSING CourtAuction-Onbid-List
MISSING CourtAuction-Onbid-Notice
MISSING CourtAuction-Court-Crawl
Dry-run only. Register tasks manually after reviewing command lines.
```

실행 결과:

```text
ONBID scheduled sync finished. ExitCode=0 Log=storage\logs\onbid\onbid_scheduled_20260707_090935.log
result: real_estate fetched 20, accepted_fresh 0, dropped_unknown_date 20, inserted 0

ONBID scheduled sync finished. ExitCode=0 Log=storage\logs\onbid\onbid_manual_20260707_110058.log
result: real_estate PageNo=2 fetched 20, accepted_fresh 0, dropped_unknown_date 20, inserted 0
```

## 14. Windows Scheduler 영구 등록 여부

- 수행하지 않음.

## 15. repair Apply 권장 여부

repair Apply 권장 여부: 아니오

권장하지 않는 이유:

- dry-run 최종 결과는 `checked 88, would_update 48, updated 0`.
- 하지만 public-visible fresh non-sample row는 0건이며, Apply를 실행해도 오래된 데이터가 최신 데이터가 되지는 않음.
- 이번 devpack 제한상 사용자 승인 없이 Apply 실행 금지.

실행 전 필수 조건:

1. DB 백업 완료
2. 백업 경로 확인
3. 테스트 통과
4. public /onbid 표시 기준 확인
5. 사용자 승인

제안 명령:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

## 한국어 UI 보존 확인

- 기존 한글 UI를 영어로 바꾼 변경: 없음
- 새 사용자 표시 문구의 기본 언어: 한국어
- 영어가 남아 있는 영역: 코드 식별자 / 환경변수 / API kind / 외부 서비스명
- 의도치 않은 번역 변경 확인: 완료
- 확인한 템플릿/파일:
  - `frontend/templates` diff 없음
  - `backend/services/auction_items.py`
  - `backend/workers/onbid_sync.py`
  - `tests/onbid_freshness_policy_test.py`
  - `tests/page_response_smoke_test.py`
- 비고:
  - 사용자 화면 템플릿은 수정하지 않음.
  - `/onbid` 확인에서 `Reset` 미포함, `초기화` 포함, `AI 분석 있음` public 미노출 확인.

## 17. 실행한 테스트와 결과

```text
& $Py tests/onbid_freshness_policy_test.py
PASS - ONBID freshness policy hides stale and unknown-date public rows

& $Py tests/onbid_category_mapping_test.py
PASS - ONBID stored category mapping and counts

& $Py tests/onbid_public_filter_state_test.py
PASS - ONBID public filter state

& $Py tests/sitemap_fresh_public_routes_test.py
PASS - sitemap includes only fresh public ONBID items

& $Py tests/onbid_module_test.py
PASS - ONBID item, notice, observability, and case link

& $Py tests/page_response_smoke_test.py
PASS - page response smoke test

& $Py tests/public_access_auth_boundary_test.py
PASS - public access and auth boundary

& $Py tests/navigation_active_state_test.py
PASS - navigation active state markers

& $Py tests/public_route_visual_smoke_test.py
PASS - public route HTML smoke
```

공통 경고:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## 18. 변경 파일 목록

```text
backend/services/auction_items.py
backend/workers/onbid_sync.py
tests/onbid_freshness_policy_test.py
tests/page_response_smoke_test.py
reports/devpacks/devpack_v006_result_bundle.md
```

변경 요약:

- ONBID freshness 날짜 후보에 `FRST_BID_SLCTN_YMD`, `cltrOpbdDt`, `pbancYmd` 추가.
- 날짜 후보가 여러 개일 때 public 기준상 plausible한 최신 날짜를 선택하도록 수정.
- notice API 호출에 `MinDate`를 `opbdDtStart=YYYYMMDD`로 전달.
- freshness 테스트에 국유재산 날짜 필드와 장기 진행 물건 케이스 추가.
- page smoke test에서 review mode raw document 403 차단을 허용하도록 조정.

## 19. 남은 리스크

- v006 제한 범위 내 실제 public-visible fresh non-sample ONBID row는 확보하지 못함.
- 현재 DB의 fresh 7건은 sample/fixture라 public 기본 목록에서 숨겨짐.
- real_estate 첫 페이지와 PageNo=2는 sentinel future 계열 날짜로 public hidden 처리됨.
- notice는 날짜 파라미터와 필드 매핑을 보강했지만 첫 페이지가 stale로 분류됨.
- movable 기본 호출은 total_count 0.
- national_property는 날짜 매핑은 개선됐지만 응답이 2003년대 stale 중심.
- `repair_onbid_derived_fields.ps1 -Apply`는 미수행 상태이므로 저장된 파생 필드 일부는 dry-run 기준 업데이트 필요.

## 20. 다음 devpack 추천

1. ONBID API별 서버측 날짜/정렬 파라미터를 공식 문서 기준으로 재확인.
2. real_estate에서 sentinel future가 아닌 실제 진행 일정 row를 가져오기 위한 검색 조건 또는 정렬 조건 추가.
3. notice `opbdDtStart` 외 종료일/공고일 기준 필터 가능 여부 확인.
4. national_property bid target API의 최신순/날짜조건 파라미터 확인.
5. fresh non-sample 1건 이상 확보 후 사용자 승인하에 repair Apply 여부 재판단.

## 21. 종료 Git 상태

```text
git status --short
 M backend/services/auction_items.py
 M backend/workers/onbid_sync.py
 M tests/onbid_freshness_policy_test.py
 M tests/page_response_smoke_test.py
?? reports/devpacks/devpack_v006_result_bundle.md

git --no-pager log --oneline --decorate -5
c7df5b7 (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006 devpack instructions
ad6ee38 (origin/codex/devpack-v005-product-qa-fresh-data-navigation, codex/devpack-v005-product-qa-fresh-data-navigation) feat: finalize v005 product qa and review mode
fe883c3 docs: add v005 devpack instructions
913aece (origin/codex/devpack-v004-real-onbid-operations, codex/devpack-v004-real-onbid-operations) feat: implement real onbid operations v004
999f04d docs: add v004 devpack instructions
```

