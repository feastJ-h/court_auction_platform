# devpack_v006_a2_instruction.md

# court_auction_platform v006-a2 작업 지시서

## 0. 매우 중요한 한국어 UI 보존 원칙

이번 작업에서도 기존 한글 UI, 한글 문구, 한글 라벨, 한글 안내문을 영어로 바꾸지 마세요.

```text
한국어 UI 보존 규칙:

1. 기존 화면에 표시되는 한글 문구를 영어로 번역하거나 교체하지 마세요.
2. 새로 추가하는 사용자 화면 문구는 기본적으로 한국어로 작성하세요.
3. 버튼, 메뉴, 탭, 필터, 배지, 빈 상태 안내, 로그인 안내, 오류 안내, 관리자 안내도 한국어를 우선 사용하세요.
4. 기존 테스트가 영어 문구를 기대하더라도, 실제 서비스 UI가 한국어여야 한다면 테스트를 한국어 기준으로 수정하세요.
5. 코드 식별자, 변수명, 함수명, 클래스명, API kind, 환경변수명, DB 컬럼명, 라우트 경로, 파일명, 패키지명, 외부 서비스명은 기존 영어/기술 명칭을 유지하세요.
6. 사용자에게 보이는 문구와 코드 내부 식별자를 혼동하지 마세요.
7. 영어로 바꿔야 할 특별한 이유가 있다면 result bundle에 사유만 적고 실제 변경은 하지 마세요.
```

특히 아래 문구는 영어로 되돌리지 마세요.

```text
온비드
회생·파산
로그인
관심
감시
패스
메모
로그인 후 분석 확인
일정 확인 필요
로그인하면 관심감시패스와 메모를 저장할 수 있습니다
개인정보처리방침
이용약관
면책사항
전체
부동산
동산
국유재산
기타
초기화
검색
필터
```

작업 완료 전 result bundle에 반드시 아래 형식으로 확인 결과를 적으세요.

```text
## 한국어 UI 보존 확인

- 기존 한글 UI를 영어로 바꾼 변경: 없음 / 있음
- 새 사용자 표시 문구의 기본 언어: 한국어 / 영어 / 혼합
- 영어가 남아 있는 영역: 코드 식별자 / 환경변수 / API kind / 외부 서비스명 / 기타
- 의도치 않은 번역 변경 확인: 완료 / 미완료
- 확인한 템플릿/파일:
  - ...
```

## 1. 현재 기준 상태

프로젝트:

```text
court_auction_platform
```

현재 작업 브랜치:

```text
codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal
```

v005 기준 커밋:

```text
ad6ee38 feat: finalize v005 product qa and review mode
```

v006 instruction 기준 커밋:

```text
c7df5b7 docs: add v006 devpack instructions
```

v006 1차 작업 결과는 다음 상태를 만들었습니다.

```text
- ONBID freshness 날짜 후보 일부 보강
- national_property unknown-date 일부 원인 확인
- notice 날짜 파라미터 일부 보강
- 그러나 public-visible non-sample fresh row는 아직 0건
- 현재 DB fresh 7건은 sample/fixture라 public 기본 목록에서 숨겨짐
```

이번 v006-a2는 v006의 후속입니다.

## 2. 이번 v006-a2의 목표

이번 작업은 온비드 API 전체가 아니라 **부동산 물건목록/상세**와 **동산 물건목록/상세**만 다룹니다.

공고목록 API와 국유재산/national_property 계열은 이번 devpack에서 분리합니다.

이번 목표:

```text
공식 OpenAPI 활용가이드 기준으로 부동산/동산 물건목록 요청 파라미터를 맞추고,
2025-01-01 이후 public-visible non-sample ONBID row를 최소 1건 이상 확보할 수 있는지 제한적으로 검증한다.
```

가장 중요한 가정:

```text
v006 1차에서 최신 데이터 확보가 실패한 이유는 단순 DB repair 문제가 아니라,
부동산/동산 물건목록 API에 공식 필수 파라미터 또는 입찰기간 검색조건이 충분히 반영되지 않았기 때문일 수 있다.
```

## 3. 첨부 공식 문서 기준 분석 요약

이번 작업은 아래 첨부 문서를 기준으로만 판단합니다.

```text
OpenAPI활용가이드_01_온비드_부동산_물건목록_조회서비스.docx
OpenAPI활용가이드_02_온비드_동산_물건목록_조회서비스.docx
OpenAPI활용가이드_04_온비드_부동산_물건상세_조회서비스.docx
OpenAPI활용가이드_05_온비드_동산_물건상세_조회서비스.docx
```

### 3.1 부동산 물건목록 조회서비스

서비스:

```text
OnbidRlstListSrvc
운영환경:
https://apis.data.go.kr/B010003/OnbidRlstListSrvc2
오퍼레이션:
getRlstCltrList2
```

공식 설명상 이 서비스는 현재 입찰 중이거나 입찰예정인 부동산 공매물건 목록 조회서비스입니다.

요청 필수 파라미터:

```text
serviceKey
pageNo
numOfRows
resultType
prptDivCd
pvctTrgtYn
```

v006-a2에서 우선 반영할 선택 파라미터:

```text
bidPrdYmdStart
bidPrdYmdEnd
mdfcnYmdStart
mdfcnYmdEnd
```

주의:

```text
bidDivCd, dspsMthodCd는 v2.0에서 필수입력값 제외로 변경된 것으로 문서에 표시되어 있으므로 기본값으로 강제하지 마세요.
필요한 경우 명시 옵션으로만 전달하세요.
```

### 3.2 동산 물건목록 조회서비스

서비스:

```text
OnbidMvastListSrvc
운영환경:
https://apis.data.go.kr/B010003/OnbidMvastListSrvc2
오퍼레이션:
getMvastCltrList2
```

공식 설명상 이 서비스는 차량 제외 동산 중 현재 입찰 중이거나 입찰예정인 동산 공매물건 목록 조회서비스입니다.

요청 필수 파라미터:

```text
serviceKey
pageNo
numOfRows
resultType
prptDivCd
pvctTrgtYn
```

v006-a2에서 우선 반영할 선택 파라미터:

```text
bidPrdYmdStart
bidPrdYmdEnd
mdfcnYmdStart
mdfcnYmdEnd
```

주의:

```text
동산 v2.1에서는 무게 데이터 타입이 VARCHAR(200)으로 변경된 이력이 있으므로,
동산 응답의 cltrWt 또는 무게 관련 필드를 숫자로 강제 파싱하지 마세요.
```

### 3.3 부동산/동산 상세 조회서비스

상세 서비스는 목록에서 받은 식별자를 이용한 보강용입니다. 이번 devpack에서 상세 API는 “목록 수집 성공 후 1건 검증” 용도로만 사용하세요.

부동산 상세:

```text
OnbidRlstDtlSrvc
https://apis.data.go.kr/B010003/OnbidRlstDtlSrvc2
getRlstDtlInf2
```

동산 상세:

```text
OnbidMvastDtlSrvc
https://apis.data.go.kr/B010003/OnbidMvastDtlSrvc2
getMvastDtlInf2
```

상세 요청 필수 파라미터:

```text
serviceKey
pageNo
numOfRows
resultType
cltrMngNo
```

상세 요청 선택 파라미터:

```text
pbctCdtnNo
```

중요:

```text
상세 API는 broad discovery용으로 사용하지 마세요.
목록에서 public-visible 후보가 나온 경우, 각 API kind별 최대 1건만 상세 조회하세요.
```

## 4. 절대 금지 사항

```text
전체 repo 재검토 금지.
대량 백필 금지.
API key 출력 금지.
raw payload 전체 출력 금지.
raw payload public 노출 금지.
DB row 삭제 금지.
stale/unknown/pre-2025 데이터 삭제 금지.
destructive migration 금지.
schema 변경 금지.
사용자 승인 없는 repair Apply 금지.
Windows Scheduler 영구 등록 금지.
공고목록 API 수정/호출 금지.
national_property/국유재산 전용 API 수정/호출 금지.
사용자 화면 한글 문구 영어화 금지.
commit/push 금지.
```

이번 devpack에서 공고목록과 국유재산/national_property는 건드리지 마세요.

단, 부동산/동산 목록 응답 안에 `prptDivCd=0010` 국유재산이 섞여 들어오는 경우 기존 national_property mapping은 훼손하지 말고, public category가 국유재산으로 분리되는 기존 정책을 유지하세요.

## 5. 작업 시작 전 확인

아래 명령부터 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only
```

기대 상태:

```text
v006 1차 변경분이 아직 커밋 전이라면 modified 파일이 있을 수 있습니다.
그 경우 먼저 현재 변경분의 의미를 확인하고, 이번 a2 작업이 이전 변경분을 덮어쓰지 않도록 하세요.
```

만약 사용자가 이미 v006 1차 변경분을 커밋했다면, 로그에 아래와 유사한 커밋이 보여야 합니다.

```text
feat: improve onbid freshness parsing and probe diagnostics v006
```

## 6. 우선 확인할 파일

필요한 경우에만 아래 파일을 제한적으로 확인하세요.

```text
backend/onbid/client.py
backend/workers/onbid_sync.py
backend/services/auction_items.py
backend/config.py

run_onbid_fresh_probe.ps1
run_onbid_scheduled_sync.ps1
audit_onbid_freshness.ps1
repair_onbid_derived_fields.ps1
backup_database.ps1

tests/onbid_freshness_policy_test.py
tests/onbid_category_mapping_test.py
tests/onbid_module_test.py
tests/page_response_smoke_test.py
```

템플릿 파일은 기본적으로 수정하지 마세요.

템플릿 수정이 꼭 필요하다면 한국어 UI 보존 규칙을 먼저 확인하고, 수정 사유를 result bundle에 적으세요.

## 7. 구현 방향

### 7.1 공식 필수 파라미터 반영

부동산/동산 목록 API 호출에 아래 공식 필수 파라미터가 항상 포함되도록 하세요.

```text
serviceKey
pageNo
numOfRows
resultType=json
prptDivCd
pvctTrgtYn
```

기존 코드에서 `serviceKey`, `pageNo`, `numOfRows`, `resultType`만 보내고 있었다면, `prptDivCd`, `pvctTrgtYn`를 추가해야 합니다.

### 7.2 prptDivCd 기본값

이번 a2에서는 국유재산/national_property를 별도 devpack으로 분리합니다.

따라서 부동산/동산 목록 실험용 기본 `prptDivCd`는 국유재산 코드 `0010`을 제외한 값으로 시작하세요.

추천 기본값:

```text
0007,0005,0004,0002,0003,0006,0008,0011,0013
```

코드 의미:

```text
0007 압류재산
0005 기타일반재산
0004 불용품
0002 공유재산
0003 금융권담보재산
0006 유입재산
0008 수탁재산
0011 공공개발재산
0013 파산재산
```

주의:

```text
이 기본값은 이번 a2 실험용입니다.
기존 national_property 분리 정책을 제거하거나 약화하지 마세요.
```

### 7.3 pvctTrgtYn 기본값

`pvctTrgtYn`는 공식 문서상 필수입니다.

우선 `N`으로 호출하세요.

```text
pvctTrgtYn=N
```

첫 호출이 0건이면, 같은 조건에서 `Y`를 1회만 추가 호출할 수 있습니다.

```text
pvctTrgtYn=Y
```

`Y,N` 같은 복수값을 임의로 보내지 마세요. 문서상 CHAR(1)입니다.

### 7.4 입찰기간 조건

기존 v006에서 `MinDate=2025-01-01`만으로는 최신 진행/예정 물건을 안정적으로 가져오지 못했습니다.

이번 a2에서는 API 요청 조건으로 `bidPrdYmdStart`, `bidPrdYmdEnd`를 명시적으로 지원하세요.

PowerShell 실행 시점 기준:

```powershell
$BidStart = (Get-Date).ToString("yyyyMMdd")
$BidEnd = (Get-Date).AddDays(60).ToString("yyyyMMdd")
```

그리고 API 요청에 아래를 전달하세요.

```text
bidPrdYmdStart=$BidStart
bidPrdYmdEnd=$BidEnd
```

중요:

```text
MinDate=2025-01-01은 수신 후 public freshness filter 기준으로 유지합니다.
bidPrdYmdStart/bidPrdYmdEnd는 ONBID API 서버에 보내는 검색조건입니다.
두 개념을 혼동하지 마세요.
```

### 7.5 선택 파라미터 pass-through

아래 파라미터는 코드에서 optional pass-through로 지원해도 됩니다.

```text
bidDivCd
dspsMthodCd
mdfcnYmdStart
mdfcnYmdEnd
```

하지만 이번 a2의 기본 실호출에서는 과도한 필터링을 피하기 위해 `bidDivCd`, `dspsMthodCd`는 기본으로 넣지 마세요.

### 7.6 상세 API 검증

목록 호출에서 public-visible 후보가 나오면, 각 API kind별 최대 1건만 상세 조회하세요.

상세 요청은 목록 row에서 받은 아래 값을 사용하세요.

```text
cltrMngNo
pbctCdtnNo
```

상세 API 필수값:

```text
serviceKey
pageNo=1
numOfRows=1
resultType=json
cltrMngNo
```

`pbctCdtnNo`가 있으면 함께 보내세요.

상세 조회 결과는 전체 raw payload를 result bundle에 붙이지 마세요. 아래 정도만 기록하세요.

```text
- 상세 조회 성공 여부
- resultCode/resultMsg
- 주요 식별자 존재 여부
- 사진 URL/상세 필드 존재 여부
- raw payload 전체 미출력 확인
```

## 8. 스크립트 인터페이스 보강

기존 스크립트에 아래 옵션이 없다면 최소 변경으로 추가하세요.

대상 후보:

```text
run_onbid_fresh_probe.ps1
run_onbid_scheduled_sync.ps1
```

추가 후보 옵션:

```powershell
-PrptDivCd
-PvctTrgtYn
-BidPrdYmdStart
-BidPrdYmdEnd
-MdfcnYmdStart
-MdfcnYmdEnd
-IncludeDetails
-DetailLimit
```

`DetailLimit` 기본값은 0 또는 1로 두세요.  
이번 a2에서는 `DetailLimit=1`을 초과하지 마세요.

스크립트 출력에는 serviceKey를 절대 출력하지 마세요.

출력 가능한 안전한 파라미터 요약:

```text
ApiKind=real_estate
Limit=20
MaxPages=1
PageNo=1
MinDate=2025-01-01
PrptDivCd=0007,0005,0004,0002,0003,0006,0008,0011,0013
PvctTrgtYn=N
BidPrdYmdStart=yyyyMMdd
BidPrdYmdEnd=yyyyMMdd
IncludeDetails=true/false
DetailLimit=1
```

## 9. 실호출 제한

이번 a2의 실제 API 호출은 제한적으로만 수행하세요.

공통 제한:

```text
Limit=20
MaxPages=1
MinDate=2025-01-01
```

이번 devpack 전체에서 목록 API 실호출은 기본 4회 이내로 제한하세요.

허용 목록 호출:

```text
1. real_estate, pvctTrgtYn=N, bid period 60일
2. movable, pvctTrgtYn=N, bid period 60일
3. real_estate가 0건이면 real_estate, pvctTrgtYn=Y, bid period 60일 1회
4. movable이 0건이면 movable, pvctTrgtYn=Y, bid period 60일 1회
```

상세 API 호출은 public-visible 후보가 있을 때만 실행하세요.

```text
부동산 상세 최대 1건
동산 상세 최대 1건
```

이번 a2에서 호출하지 말 것:

```text
notice
national_property
공고목록 API
국유재산 전용 API
```

## 10. DB 백업

실제 API 수집으로 DB write 가능성이 있으므로 호출 전 백업하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

result bundle에 아래를 기록하세요.

```text
백업 실행 여부
백업 시각
백업 파일 경로
sha256 가능 시 기록
복원 미실행 확인
```

## 11. 권장 실행 순서

### Phase 1 — 시작 상태 확인

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only
```

### Phase 2 — 코드/스크립트 최소 수정

공식 필수 파라미터와 입찰기간 파라미터를 real_estate/movable list 호출에 반영하세요.

필요 시 관련 테스트를 추가/수정하세요.

### Phase 3 — 컴파일과 단위 테스트

```powershell
& $Py -m py_compile backend/onbid/client.py backend/workers/onbid_sync.py backend/services/auction_items.py

& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/onbid_module_test.py
```

### Phase 4 — DB 백업

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

### Phase 5 — baseline audit

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

### Phase 6 — 제한 real_estate 호출

```powershell
$BidStart = (Get-Date).ToString("yyyyMMdd")
$BidEnd = (Get-Date).AddDays(60).ToString("yyyyMMdd")
$PrptDivCd = "0007,0005,0004,0002,0003,0006,0008,0011,0013"

powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind real_estate `
  -Limit 20 `
  -MaxPages 1 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd `
  -IncludeDetails `
  -DetailLimit 1
```

0건이면 1회만 Y로 재시도할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind real_estate `
  -Limit 20 `
  -MaxPages 1 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn Y `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd `
  -IncludeDetails `
  -DetailLimit 1
```

### Phase 7 — 제한 movable 호출

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind movable `
  -Limit 20 `
  -MaxPages 1 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd `
  -IncludeDetails `
  -DetailLimit 1
```

0건이면 1회만 Y로 재시도할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind movable `
  -Limit 20 `
  -MaxPages 1 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn Y `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd `
  -IncludeDetails `
  -DetailLimit 1
```

### Phase 8 — 후속 audit

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

### Phase 9 — public 검증 테스트

```powershell
& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_public_filter_state_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/sitemap_fresh_public_routes_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/public_access_auth_boundary_test.py
```

템플릿을 수정했다면 추가로 실행하세요.

```powershell
& $Py tests/navigation_active_state_test.py
& $Py tests/public_route_visual_smoke_test.py
```

## 12. 결과 판단 기준

### 성공

```text
real_estate 또는 movable 중 하나 이상에서 public-visible non-sample fresh row가 최소 1건 이상 확보됨.
API key가 출력되지 않음.
raw payload가 public/result bundle에 전체 출력되지 않음.
기존 한국어 UI가 영어로 바뀌지 않음.
테스트가 통과함.
```

### 부분 성공

```text
fresh row 확보는 실패했지만,
공식 필수 파라미터가 요청에 반영되었고,
API resultCode/resultMsg 기준으로 실패 원인이 명확히 정리됨.
```

### 실패

```text
resultCode=10 또는 11이 반복되며 공식 필수 파라미터가 여전히 잘못됨.
API key 또는 raw payload가 출력됨.
한국어 UI가 영어로 바뀜.
기존 public freshness/security 테스트가 실패함.
```

## 13. repair Apply 정책

이번 a2에서도 `repair_onbid_derived_fields.ps1 -Apply`는 실행하지 마세요.

fresh non-sample public-visible row가 확보된 뒤에도, Apply는 별도 사용자 승인 후 수행합니다.

이번 a2 result bundle에는 아래만 적으세요.

```text
repair Apply 권장 여부: 예/아니오
권장 사유:
실행 전 필수 조건:
제안 명령:
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

## 14. result bundle 작성

결과는 하나의 파일로만 작성하세요.

```text
reports/devpacks/devpack_v006_a2_result_bundle.md
```

반드시 포함할 항목:

```text
1. 작업 메타데이터
2. 시작 git status/log/diff
3. 참고한 공식 문서 목록
4. 공식 필수 파라미터 반영 여부
5. 변경 파일 목록
6. DB 백업 여부와 백업 경로
7. 실행 명령 목록
8. 실제 API 호출 목록
   - ApiKind
   - Limit
   - MaxPages
   - MinDate
   - PrptDivCd
   - PvctTrgtYn
   - BidPrdYmdStart
   - BidPrdYmdEnd
   - IncludeDetails
   - DetailLimit
9. API key 미출력 확인
10. raw payload 전체 미출력 확인
11. real_estate 결과
12. movable 결과
13. 상세 API 검증 결과
14. fresh audit 전/후 비교
15. public-visible row 전/후 비교
16. repair Apply 권장 여부
17. 한국어 UI 보존 확인
18. 테스트 실행 결과
19. 남은 리스크
20. 다음 devpack 추천
21. 종료 git status/log
```

## 15. 종료 전 확인

종료 전 반드시 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
```

commit/push는 하지 마세요.

## 16. 성공 기준 요약

이번 v006-a2는 아래 중 하나를 만족하면 의미 있는 진전입니다.

```text
1. 부동산 또는 동산에서 public-visible non-sample fresh row를 최소 1건 확보한다.
2. 확보하지 못하더라도 공식 필수 파라미터 반영 후의 resultCode/resultMsg와 totalCount를 근거로 다음 원인을 좁힌다.
3. 공고목록과 국유재산/national_property는 건드리지 않는다.
4. 기존 한국어 UI를 보존한다.
5. API key/raw payload를 노출하지 않는다.
6. result bundle 하나로 정리한다.
```
