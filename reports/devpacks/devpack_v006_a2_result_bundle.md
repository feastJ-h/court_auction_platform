# devpack_v006_a2_result_bundle.md

## 1. 작업 메타데이터

- 작업일: 2026-07-07
- 작업 브랜치: `codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal`
- 지시서: `reports/devpacks/devpack_v006_a2_instruction.md`
- 작업 범위: ONBID 부동산/동산 물건목록 및 물건상세 API 파라미터 보강, 제한적 fresh probe 검증
- 제외 범위: 공고목록 API, national_property/국유재산 전용 API, 대량 백필, DB row 삭제, destructive migration, Windows Scheduler 영구 등록, repair Apply, commit/push
- 실제 API key 출력: 없음
- raw payload 전체 출력: 없음

## 2. 시작 git status/log/diff

```text
git status --short
출력 없음

git --no-pager log --oneline --decorate -5
10710ce (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a2 devpack instructions
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
c7df5b7 docs: add v006 devpack instructions
ad6ee38 (origin/codex/devpack-v005-product-qa-fresh-data-navigation, codex/devpack-v005-product-qa-fresh-data-navigation) feat: finalize v005 product qa and review mode
fe883c3 docs: add v005 devpack instructions

git diff --name-only
출력 없음
```

## 3. 참고한 공식 문서 목록

지시서에 첨부 문서로 지정된 아래 ONBID OpenAPI 사용가이드 범위만 기준으로 판단했다.

- `OpenAPI사용가이드_01_온비드_부동산_물건목록_조회서비스.docx`
- `OpenAPI사용가이드_02_온비드_동산_물건목록_조회서비스.docx`
- `OpenAPI사용가이드_04_온비드_부동산_물건상세_조회서비스.docx`
- `OpenAPI사용가이드_05_온비드_동산_물건상세_조회서비스.docx`

## 4. 공식 필수 파라미터 반영 여부

- 목록 API 공통 기본 파라미터 유지: `serviceKey`, `pageNo`, `numOfRows`, `resultType=json`
- 부동산/동산 목록 API에 `prptDivCd`, `pvctTrgtYn` 전달 반영 완료
- 부동산/동산 목록 API에 `bidPrdYmdStart`, `bidPrdYmdEnd` 전달 반영 완료
- optional pass-through 반영: `mdfcnYmdStart`, `mdfcnYmdEnd`, `bidDivCd`, `dspsMthodCd`
- 기본 `prptDivCd`: `0007,0005,0004,0002,0003,0006,0008,0011,0013`
- 기본 `pvctTrgtYn`: `N`
- `bidDivCd`, `dspsMthodCd`는 기본 호출에서 넣지 않고 명시 전달 시에만 통과
- `DetailLimit` 기본값: `1`, 비샘플 실행에서 `1` 초과 금지

## 5. 변경 파일 목록

- `backend/onbid/client.py`
- `backend/workers/onbid_sync.py`
- `run_onbid_fresh_probe.ps1`
- `run_onbid_probe.ps1`
- `run_onbid_scheduled_sync.ps1`
- `tests/onbid_module_test.py`
- `reports/devpacks/devpack_v006_a2_result_bundle.md`

## 6. DB 백업 여부와 백업 경로

- 백업 실행 여부: 실행
- 백업 시각: `20260707_120845`
- 백업 파일: `C:\Users\xogns\Documents\testAuction\court_auction_platform\storage\backups\auction_data_20260707_120845.db`
- 원본 DB: `C:\Users\xogns\Documents\testAuction\court_auction_platform\auction_data.db`
- sha256: `357EACBAAAFD4E8E0D1FD6A68EDF022808F223EFD89064A653FD7B724FCF85A1`
- 복원 테스트: 미실행

## 7. 실행 명령 목록

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only

$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Py -m py_compile backend/onbid/client.py backend/workers/onbid_sync.py backend/services/auction_items.py
& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/onbid_module_test.py

powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01

$BidStart = (Get-Date).ToString("yyyyMMdd")
$BidEnd = (Get-Date).AddDays(60).ToString("yyyyMMdd")
$PrptDivCd = "0007,0005,0004,0002,0003,0006,0008,0011,0013"

powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind real_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -PrptDivCd $PrptDivCd -PvctTrgtYn N -BidPrdYmdStart $BidStart -BidPrdYmdEnd $BidEnd -IncludeDetails -DetailLimit 1
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 -ApiKind movable -Limit 20 -MaxPages 1 -MinDate 2025-01-01 -PrptDivCd $PrptDivCd -PvctTrgtYn N -BidPrdYmdStart $BidStart -BidPrdYmdEnd $BidEnd -IncludeDetails -DetailLimit 1

powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01

& $Py tests/onbid_public_filter_state_test.py
& $Py tests/sitemap_fresh_public_routes_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/public_access_auth_boundary_test.py
```

## 8. 실제 API 호출 목록

허용된 목록 호출만 수행했다. 공고목록 API, national_property/국유재산 전용 API는 호출하지 않았다.

| ApiKind | Limit | MaxPages | MinDate | PrptDivCd | PvctTrgtYn | BidPrdYmdStart | BidPrdYmdEnd | IncludeDetails | DetailLimit |
|---|---:|---:|---|---|---|---|---|---|---:|
| `real_estate` | 20 | 1 | `2025-01-01` | `0007,0005,0004,0002,0003,0006,0008,0011,0013` | `N` | `20260707` | `20260905` | true | 1 |
| `movable` | 20 | 1 | `2025-01-01` | `0007,0005,0004,0002,0003,0006,0008,0011,0013` | `N` | `20260707` | `20260905` | true | 1 |

참고: 최초 부동산 probe는 sandbox 네트워크 제한으로 `WinError 10013`이 발생했고, 승인 후 동일 조건으로 재실행해 성공했다. 그 전에 PowerShell 빈 optional 인자 전달 오류 1건이 있었으며 API 호출 전 래퍼 단계에서 중단되어 수정했다.

## 9. API key 미출력 확인

- 스크립트 출력에는 `serviceKey` 또는 실제 API key가 포함되지 않았다.
- result bundle에도 API key를 기록하지 않았다.

## 10. raw payload 전체 미출력 확인

- probe 결과에는 집계 dict만 출력했다.
- raw payload 전체를 콘솔 또는 result bundle에 출력하지 않았다.
- 상세 검증은 raw 내용 대신 `_raw_detail` marker 존재 여부만 집계했다.

## 11. real_estate 결과

```text
status=SUCCEEDED
run_id=52
fetched=20
accepted_fresh=20
dropped_stale=0
dropped_unknown_date=0
total_count=43811
inserted=20
duplicates=0
used_sample=False
```

`pvctTrgtYn=N`에서 성공했으므로 `Y` 재시도는 수행하지 않았다.

## 12. movable 결과

```text
status=SUCCEEDED
run_id=53
fetched=20
accepted_fresh=20
dropped_stale=0
dropped_unknown_date=0
total_count=2246
inserted=20
duplicates=0
used_sample=False
```

`pvctTrgtYn=N`에서 성공했으므로 `Y` 재시도는 수행하지 않았다.

## 13. 상세 API 검증 결과

- 부동산 상세: `IncludeDetails=true`, `DetailLimit=1` 조건으로 목록 결과 중 최대 1건만 상세 조회
- 동산 상세: `IncludeDetails=true`, `DetailLimit=1` 조건으로 목록 결과 중 최대 1건만 상세 조회
- resultCode/resultMsg: wrapper 집계 결과 기준 실패 없음, 최종 `status=SUCCEEDED`
- 주요 식별자: 목록 row의 `cltrMngNo`, `pbctCdtnNo` 기반으로 상세 요청
- 사진 URL/상세 필드 존재 여부: raw 내용 미출력 조건 때문에 전체 값은 기록하지 않고, DB raw payload 내 `_raw_detail` marker 존재만 집계
- fresh public rows with `_raw_detail` marker: `{"movable": 2, "real_estate": 4}`
- raw payload 전체 미노출: 확인

## 14. fresh audit 전후 비교

### 전

```json
{"by_category":{"all":0,"movable":2,"national_property":1,"other":0,"real_estate":85},"fresh":7,"invalid_date":20,"stale":61,"total":88,"unknown_date":0}
```

### 후

```json
{"by_category":{"all":0,"movable":22,"national_property":1,"other":0,"real_estate":105},"fresh":47,"invalid_date":20,"stale":61,"total":128,"unknown_date":0}
```

## 15. public-visible row 전후 비교

- 최종 public-visible fresh non-sample total: `44`
- 최종 public-visible fresh non-sample by category: `{"movable":21,"real_estate":23}`
- v006-a2 성공 기준인 public-visible non-sample fresh row 1건 이상 확보 완료

## 16. repair Apply 권장 여부

- repair Apply 권장 여부: 아니오
- 권장 사유: fresh public row 확보가 완료되었고, dry-run 결과 `would_update=48`은 남아 있으나 이번 a2에서 repair Apply는 사용자 승인 없이 금지되어 있다.
- 실행 전 필수 조건: 사용자 명시 승인, 백업 확인, 적용 범위 재검토
- 제안 명령:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

## 17. 한국어 UI 보존 확인

- 기존 한국어 UI를 영어로 바꾼 변경: 없음
- 새 사용자 표시 문구의 기본 언어: 해당 없음. PowerShell/CLI 진단 문구만 추가 및 보강
- 영어가 남아 있는 영역: 코드 식별자, 환경변수명, API kind, 내부 서비스명, PowerShell/CLI 진단 출력
- 과도한 번역 변경 확인: 완료
- 확인한 파일:
  - `backend/onbid/client.py`
  - `backend/workers/onbid_sync.py`
  - `run_onbid_fresh_probe.ps1`
  - `run_onbid_probe.ps1`
  - `run_onbid_scheduled_sync.ps1`
  - `tests/onbid_module_test.py`

## 18. 테스트 실행 결과

```text
py_compile: PASS
tests/onbid_freshness_policy_test.py: PASS
tests/onbid_category_mapping_test.py: PASS
tests/onbid_module_test.py: PASS
tests/onbid_public_filter_state_test.py: PASS
tests/sitemap_fresh_public_routes_test.py: PASS
tests/page_response_smoke_test.py: PASS
tests/public_access_auth_boundary_test.py: PASS
```

반복 공통 경고:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## 19. 잔여 리스크

- `repair_onbid_derived_fields.ps1 -DryRun` 결과 `would_update=48`이 남아 있다.
- `repair Apply`는 이번 지시서상 금지되어 실행하지 않았다.
- 복원 리허설은 수행하지 않았다.
- 상세 API 결과의 전체 raw payload는 보안 지침상 출력하지 않았으므로, 상세 필드별 값 검증은 제한적으로만 기록했다.

## 20. 다음 devpack 추천

- repair Apply 승인 여부를 별도 devpack에서 판단
- ONBID v006-a2에서 확보된 fresh row 기반으로 public route 품질과 필터 정렬 검증 확대
- 필요 시 v004/v006 후속에서 공고목록 API와 national_property 계열을 별도 범위로 분리 검증

## 21. 종료 git status/log

```text
git status --short
 M backend/onbid/client.py
 M backend/workers/onbid_sync.py
 M run_onbid_fresh_probe.ps1
 M run_onbid_probe.ps1
 M run_onbid_scheduled_sync.ps1
 M tests/onbid_module_test.py
?? reports/devpacks/devpack_v006_a2_result_bundle.md

git --no-pager log --oneline --decorate -5
10710ce (HEAD -> codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal, origin/codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal) docs: add v006-a2 devpack instructions
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
c7df5b7 docs: add v006 devpack instructions
ad6ee38 (origin/codex/devpack-v005-product-qa-fresh-data-navigation, codex/devpack-v005-product-qa-fresh-data-navigation) feat: finalize v005 product qa and review mode
fe883c3 docs: add v005 devpack instructions
```

참고: PowerShell 스크립트 3개는 Git이 다음 touch 시 LF를 CRLF로 바꿀 수 있다는 line-ending 경고를 표시했다.

commit/push는 수행하지 않았다.
