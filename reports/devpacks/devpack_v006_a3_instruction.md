# devpack_v006_a3_instruction.md

# court_auction_platform v006-a3 작업 지시서
# ONBID 부동산/동산 100건 내외 QA 데이터셋 수집 및 공개 화면 검증

인코딩: UTF-8  
작성 목적: 웹 채팅 복사/붙여넣기로 인한 한글 깨짐을 방지하기 위해, 이 파일 자체를 Codex에 업로드하여 사용한다.

---

## 0. 파일 기반 전달 원칙

이번 지시서는 반드시 파일로 전달한다.

```text
reports/devpacks/devpack_v006_a3_instruction.md
```

웹 화면에서 내용을 복사해서 새 파일을 만들지 마세요.  
한글 인코딩이 깨질 수 있으므로, 이 `.md` 파일 자체를 프로젝트에 저장한 뒤 Codex에 업로드/첨부하여 작업시키세요.

Codex는 이 파일을 UTF-8 문서로 읽고 작업해야 합니다.  
만약 지시서의 한글이 깨져 보이면 작업을 진행하지 말고 즉시 중단하세요.

---

## 1. 매우 중요한 한국어 UI 보존 원칙

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
- 새 사용자 표시 문구의 기본 언어: 한국어 / 영어 / 혼합 / 해당 없음
- 영어가 남아 있는 영역: 코드 식별자 / 환경변수 / API kind / 외부 서비스명 / CLI 출력 / 기타
- 의도치 않은 번역 변경 확인: 완료 / 미완료
- 확인한 템플릿/파일:
  - ...
```

---

## 2. 현재 기준 상태

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

v006 1차 결과 커밋:

```text
405ae5f feat: improve onbid freshness parsing and probe diagnostics v006
```

v006-a2 instruction 기준 커밋:

```text
10710ce docs: add v006-a2 devpack instructions
```

v006-a2 결과는 아직 commit/push 전일 수 있습니다.  
따라서 작업 시작 전 반드시 git 상태를 확인하고, a2 변경분이 커밋되어 있지 않으면 이번 a3 작업을 시작하지 마세요.

---

## 3. v006-a2 결과 요약

v006-a2에서는 공식 ONBID 부동산/동산 물건목록 API의 필수 파라미터를 반영했습니다.

반영된 주요 항목:

```text
serviceKey
pageNo
numOfRows
resultType=json
prptDivCd
pvctTrgtYn
bidPrdYmdStart
bidPrdYmdEnd
```

v006-a2 제한 호출 결과:

```text
real_estate:
  fetched=20
  accepted_fresh=20
  inserted=20
  duplicates=0
  total_count=43811

movable:
  fetched=20
  accepted_fresh=20
  inserted=20
  duplicates=0
  total_count=2246
```

v006-a2 최종 public-visible fresh non-sample 결과:

```text
total: 44
real_estate: 23
movable: 21
```

v006-a2에서 확인된 안전 원칙:

```text
API key 출력 없음
raw payload 전체 출력 없음
한국어 UI 훼손 없음
공고목록 API 호출 없음
national_property/국유재산 전용 API 호출 없음
repair Apply 미실행
Windows Scheduler 영구 등록 미실행
```

---

## 4. 이번 v006-a3의 목표

이번 목표는 “대량 백필”이 아닙니다.

이번 목표는 다음입니다.

```text
부동산/동산 ONBID public-visible fresh non-sample 데이터를 약 100건 내외로 확보하고,
이 데이터를 public /onbid 목록, 카테고리, 필터, 정렬, 상세 QA에 활용할 수 있는 상태로 만든다.
```

현재 기준:

```text
public-visible fresh non-sample total: 44
목표: 90~120건 사이
추가 목표: 약 56건 이상
```

이번 a3의 성공 기준:

```text
1. public-visible fresh non-sample row가 90~120건 수준으로 확보됨
2. 부동산/동산 양쪽 모두 유의미한 row 수를 확보함
3. API key가 출력되지 않음
4. raw payload 전체가 출력되거나 result bundle에 붙지 않음
5. DB 파일, backup 파일, log 파일, raw payload 파일을 Git에 커밋하지 않음
6. 한국어 UI가 영어로 바뀌지 않음
7. 기존 public freshness/security 테스트가 통과함
8. result bundle 하나로 결과가 정리됨
```

---

## 5. 이번 devpack의 범위

허용 범위:

```text
1. 부동산 물건목록 추가 수집
2. 동산 물건목록 추가 수집
3. 부동산/동산 public-visible fresh non-sample count 확인
4. 부동산/동산 상세 API 소량 검증
5. public /onbid 목록/필터/정렬/상세 QA
6. 테스트 또는 QA용 최소 필드 fixture/summary 생성 검토
7. result bundle 작성
```

제외 범위:

```text
1. 공고목록 API
2. national_property/국유재산 전용 API
3. 회생/파산 수집
4. OCR/AI 분석
5. Windows Scheduler 영구 등록
6. repair Apply
7. DB row 삭제
8. destructive migration
9. 대량 백필
10. 외부 알림/이메일/Slack/Discord/webhook
11. AdSense/payment/auction-result 연동
```

---

## 6. 절대 금지 사항

```text
전체 repo 재검토 금지.
API key 출력 금지.
raw payload 전체 출력 금지.
raw payload public 노출 금지.
DB row 삭제 금지.
stale/unknown/pre-2025 데이터 삭제 금지.
destructive migration 금지.
schema 변경 금지.
사용자 승인 없는 repair Apply 금지.
Windows Scheduler 영구 등록 금지.
공고목록 API 호출 금지.
national_property/국유재산 전용 API 호출 금지.
DB 파일 Git 커밋 금지.
storage/backups 파일 Git 커밋 금지.
storage/logs 파일 Git 커밋 금지.
raw payload dump 파일 Git 커밋 금지.
사용자 화면 한글 문구 영어화 금지.
commit/push 금지.
```

이번 devpack에서 commit/push는 하지 않습니다.  
작업 결과 검토 후 사용자가 별도로 승인할 때만 commit/push를 진행합니다.

---

## 7. 작업 시작 전 확인

아래 명령부터 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only
```

기대 상태:

```text
a2 결과 커밋이 완료되어 있고 working tree clean
```

만약 아래처럼 a2 변경분이 남아 있으면 이번 a3 작업을 시작하지 마세요.

```text
M backend/onbid/client.py
M backend/workers/onbid_sync.py
M run_onbid_fresh_probe.ps1
M run_onbid_probe.ps1
M run_onbid_scheduled_sync.ps1
M tests/onbid_module_test.py
?? reports/devpacks/devpack_v006_a2_result_bundle.md
```

이 경우 result bundle에 다음처럼 적고 중단하세요.

```text
v006-a3 중단 사유:
v006-a2 변경분이 아직 커밋되지 않았거나 working tree가 clean이 아니므로,
a3 추가 수집을 진행하지 않음.
```

사용자가 a2 결과를 commit/push한 뒤 다시 실행해야 합니다.

---

## 8. 우선 확인할 파일

필요한 경우에만 아래 파일을 제한적으로 확인하세요.

```text
backend/onbid/client.py
backend/workers/onbid_sync.py
backend/services/auction_items.py
backend/config.py

run_onbid_fresh_probe.ps1
run_onbid_probe.ps1
run_onbid_scheduled_sync.ps1
audit_onbid_freshness.ps1
repair_onbid_derived_fields.ps1
backup_database.ps1

tests/onbid_freshness_policy_test.py
tests/onbid_public_filter_state_test.py
tests/onbid_category_mapping_test.py
tests/sitemap_fresh_public_routes_test.py
tests/onbid_module_test.py
tests/page_response_smoke_test.py
tests/public_access_auth_boundary_test.py
```

템플릿 파일은 기본적으로 수정하지 마세요.

템플릿 수정이 꼭 필요하다면 한국어 UI 보존 원칙을 먼저 확인하고, 수정 사유를 result bundle에 적으세요.

---

## 9. 수집 기준 파라미터

이번 a3에서도 v006-a2에서 성공한 파라미터를 유지합니다.

공통 파라미터:

```text
Limit=20
MaxPages=1
MinDate=2025-01-01
PrptDivCd=0007,0005,0004,0002,0003,0006,0008,0011,0013
PvctTrgtYn=N
BidPrdYmdStart=오늘 yyyyMMdd
BidPrdYmdEnd=오늘+60일 yyyyMMdd
```

PowerShell 예시:

```powershell
$BidStart = (Get-Date).ToString("yyyyMMdd")
$BidEnd = (Get-Date).AddDays(60).ToString("yyyyMMdd")
$PrptDivCd = "0007,0005,0004,0002,0003,0006,0008,0011,0013"
```

국유재산 분리 원칙:

```text
이번 a3에서는 실험용 prptDivCd 기본값에서 0010을 제외합니다.
부동산/동산 목록 응답 안에 0010이 섞여 들어오면 기존 public category 분리 정책은 유지하되,
national_property 전용 API나 공고목록 API는 호출하지 마세요.
```

---

## 10. PageNo 지원 확인

이번 a3는 기존 page 1을 반복 호출하지 않고 page 2부터 추가 수집하는 것이 핵심입니다.

따라서 먼저 `run_onbid_fresh_probe.ps1`가 `-PageNo`를 지원하는지 확인하세요.

지원한다면 그대로 사용하세요.

지원하지 않는다면 최소 변경으로 `-PageNo` 옵션을 추가하세요.

요구사항:

```text
1. 기본 PageNo는 1이어야 함
2. 기존 호출과 호환되어야 함
3. PageNo는 list API 요청의 pageNo로 전달되어야 함
4. MaxPages=1이면 지정한 PageNo 한 페이지만 수집해야 함
5. API key를 출력하지 말 것
6. 기존 tests/onbid_module_test.py 또는 관련 테스트를 깨뜨리지 말 것
```

`run_onbid_scheduled_sync.ps1`에는 기존에 `-PageNo` 형태가 있을 수 있으므로, 필요한 경우 해당 구현을 참고하세요.  
하지만 Windows Scheduler 영구 등록은 하지 마세요.

---

## 11. DB 백업

실제 API 수집은 DB write를 발생시킬 수 있으므로 호출 전 반드시 백업하세요.

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

---

## 12. baseline audit

수집 전 현재 상태를 확인하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

가능하면 다음 값도 확인하세요.

```text
public-visible fresh non-sample total
public-visible fresh non-sample by category
real_estate public-visible fresh non-sample count
movable public-visible fresh non-sample count
sample/fixture row count
duplicates count
```

새 read-only helper가 꼭 필요하면 최소 범위로 작성할 수 있습니다.  
단, 새 helper를 만들었다면 result bundle에 이유와 파일명을 기록하세요.

---

## 13. 1차 추가 수집 계획

v006-a2에서 page 1은 이미 수집했습니다.  
따라서 page 2부터 시작합니다.

### 13.1 real_estate PageNo=2

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind real_estate `
  -Limit 20 `
  -MaxPages 1 `
  -PageNo 2 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd
```

### 13.2 movable PageNo=2

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind movable `
  -Limit 20 `
  -MaxPages 1 `
  -PageNo 2 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd
```

1차 수집 후 audit:

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

판단:

```text
public-visible fresh non-sample total >= 90 이면 추가 수집 중단을 검토하세요.
public-visible fresh non-sample total >= 100 이면 목록 수집을 중단하세요.
```

---

## 14. 2차 추가 수집 계획

1차 수집 후 public-visible fresh non-sample total이 100건 미만이면 2차 수집을 진행할 수 있습니다.

우선 균형 있게 부족한 카테고리를 선택하세요.

예시:

```text
real_estate가 movable보다 적으면 real_estate PageNo=3 우선
movable이 real_estate보다 적으면 movable PageNo=3 우선
둘 다 비슷하면 real_estate PageNo=3부터
```

### 14.1 선택 카테고리 PageNo=3

real_estate가 필요한 경우:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind real_estate `
  -Limit 20 `
  -MaxPages 1 `
  -PageNo 3 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd
```

movable이 필요한 경우:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_fresh_probe.ps1 `
  -ApiKind movable `
  -Limit 20 `
  -MaxPages 1 `
  -PageNo 3 `
  -MinDate 2025-01-01 `
  -PrptDivCd $PrptDivCd `
  -PvctTrgtYn N `
  -BidPrdYmdStart $BidStart `
  -BidPrdYmdEnd $BidEnd
```

2차 수집 후 다시 audit하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
```

### 14.2 추가 수집 상한

이번 devpack 전체에서 추가 목록 수집은 최대 80건 수준까지만 허용합니다.

즉, 아래를 초과하지 마세요.

```text
real_estate 추가 목록 호출 최대 2회
movable 추가 목록 호출 최대 2회
각 호출 Limit=20, MaxPages=1
총 추가 수집 후보 최대 80건
```

목표가 100건 내외이므로, public-visible fresh non-sample total이 100건 이상이 되면 즉시 목록 수집을 멈추세요.

---

## 15. 상세 API 검증 제한

100건 전체에 대해 상세 API를 호출하지 마세요.

상세 API는 QA 샘플 검증용으로만 사용합니다.

허용 범위:

```text
부동산 상세 최대 3~5건
동산 상세 최대 3~5건
```

이미 v006-a2에서 `_raw_detail` marker가 일부 존재합니다.  
따라서 이번 a3에서는 상세 API를 많이 늘릴 필요가 없습니다.

상세 검증의 목적:

```text
1. 상세 API 요청이 성공하는지 확인
2. 목록의 cltrMngNo, pbctCdtnNo로 상세가 연결되는지 확인
3. 사진 URL/상세 필드 존재 여부를 boolean/집계 수준으로 확인
4. raw payload 전체를 출력하지 않고도 상세 보강 여부를 검증
```

상세 결과를 result bundle에 기록할 때는 아래 수준만 기록하세요.

```text
real_estate detail attempted: N
real_estate detail succeeded: N
movable detail attempted: N
movable detail succeeded: N
fresh public rows with _raw_detail marker: {...}
raw payload 전체 미출력: 확인
```

상세 raw payload, 사진 URL 전체 목록, 내부 파일 경로, API response body 전체를 result bundle에 붙이지 마세요.

---

## 16. QA 데이터셋 / 테스트 fixture 정책

이번 a3의 “100건 수집”은 기본적으로 로컬 DB에 쌓는 QA용 데이터입니다.

아래는 Git에 커밋하지 마세요.

```text
auction_data.db
storage/backups/*
storage/logs/*
raw payload dump
외부 API response body 전체
```

### 16.1 로컬 QA 데이터셋

수집된 약 100건 데이터는 로컬 DB에서 public route QA에 사용합니다.

확인할 것:

```text
/onbid 기본 목록 표시
/onbid?category=real_estate
/onbid?category=movable
가격 필터
지역 필터
카테고리 탭 count
sitemap fresh item 포함
상세 페이지 접근
비로그인 상세의 CTA 유지
```

### 16.2 Git 추적 fixture 생성 여부

테스트 fixture를 만들 필요가 있다면, raw payload 전체를 fixture로 만들지 마세요.

허용되는 fixture 형태:

```text
tests/fixtures/onbid_public_fresh_minimal_v006_a3.json
```

허용 필드 예시:

```json
{
  "generated_for": "v006-a3 public ONBID QA",
  "min_public_date": "2025-01-01",
  "items": [
    {
      "source": "onbid",
      "public_category": "real_estate",
      "freshness_date": "2026-07-15",
      "freshness_status": "fresh",
      "public_visible": true,
      "region_sido": "경기도",
      "price_bucket": "under_100m",
      "has_detail": true,
      "has_thumbnail": false
    }
  ]
}
```

금지 필드:

```text
serviceKey
API key
raw_payload
_raw_detail 전체
내부 파일 경로
storage path
OCR 전문
AI 분석 전문
사용자 개인정보
로그인 사용자 메모
외부 URL 전체 목록
```

fixture는 최대 100건까지 가능하지만, 꼭 필요하지 않다면 생성하지 마세요.  
fixture를 생성했다면 반드시 result bundle에 아래를 기록하세요.

```text
fixture 생성 여부
fixture 파일명
fixture row 수
raw payload 제외 확인
API key 제외 확인
private/internal path 제외 확인
```

---

## 17. public route QA

수집 후 public route가 실제로 쓸 수 있는지 확인하세요.

가능하면 기존 테스트를 우선 사용하세요.

권장 테스트:

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

### 17.1 로컬 DB 기반 수동 QA

테스트가 isolated DB를 사용해 실제 수집 DB를 보지 않는다면, 로컬 DB 기반 수동 QA도 별도로 기록하세요.

확인 항목:

```text
/onbid status 200
/onbid 목록 row 존재
/onbid?category=real_estate status 200
/onbid?category=movable status 200
real_estate category active 유지
movable category active 유지
초기화 문구 유지
Reset 문구 미노출
AI 분석 있음 public 미노출
비로그인 상세에서 관심/감시/패스/메모 form 미노출
비로그인 상세에서 로그인 CTA 노출
```

수동 QA를 위해 dev server를 켜야 한다면 review mode 원칙을 지키세요.

```powershell
$env:REVIEW_MODE="true"
$env:LOCAL_DEV_LOGIN_HINT="false"
Remove-Item Env:REVIEW_SHOW_SAMPLE -ErrorAction SilentlyContinue
powershell -ExecutionPolicy Bypass -File .\run_review_server.ps1 -Port 8000
```

터널은 이번 a3에서 열지 마세요.

---

## 18. repair Apply 정책

이번 a3에서도 `repair_onbid_derived_fields.ps1 -Apply`는 실행하지 마세요.

fresh public row가 100건 내외로 확보되더라도 Apply는 별도 사용자 승인 후 수행합니다.

이번 a3 result bundle에는 아래만 적으세요.

```text
repair Apply 권장 여부: 예/아니오
권장 사유:
실행 전 필수 조건:
제안 명령:
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

판단 기준:

```text
1. public 목록은 fallback 계산으로 이미 정상 표시되는가?
2. stored public_visible/freshness_date/public_category와 fallback 간 차이가 있는가?
3. dry-run would_update가 계속 남아 있는가?
4. Apply가 admin QA나 sitemap count에 실질적으로 필요한가?
5. 백업이 존재하는가?
```

사용자 승인 없이 Apply하지 마세요.

---

## 19. 실패/중단 기준

아래 중 하나라도 발생하면 즉시 중단하고 result bundle에 기록하세요.

```text
API key가 출력됨
raw payload 전체가 출력됨
resultCode=10 또는 11이 반복됨
공고목록 API를 호출해야 할 것 같음
national_property/국유재산 전용 API를 호출해야 할 것 같음
DB schema 변경이 필요해 보임
한국어 UI가 영어로 바뀜
기존 public/security 테스트가 실패함
수집 row가 모두 duplicate로만 나옴
PageNo 지원 수정이 기존 수집 스크립트를 깨뜨림
```

실패 로그를 result bundle에 붙일 때는 30~80줄 정도만 요약하세요.  
긴 PowerShell 로그 전체를 붙이지 마세요.

---

## 20. result bundle 작성

결과는 하나의 파일로만 작성하세요.

```text
reports/devpacks/devpack_v006_a3_result_bundle.md
```

반드시 포함할 항목:

```text
1. 작업 메타데이터
2. 시작 git status/log/diff
3. v006-a2 기준 상태 확인
4. a2 변경분 commit 여부 확인
5. 변경 파일 목록
6. PageNo 지원 여부 및 수정 여부
7. DB 백업 여부와 백업 경로
8. baseline audit
9. 실행한 API 호출 목록
   - ApiKind
   - PageNo
   - Limit
   - MaxPages
   - MinDate
   - PrptDivCd
   - PvctTrgtYn
   - BidPrdYmdStart
   - BidPrdYmdEnd
   - IncludeDetails 여부
   - DetailLimit
10. API key 미출력 확인
11. raw payload 전체 미출력 확인
12. real_estate 추가 수집 결과
13. movable 추가 수집 결과
14. 상세 API 검증 결과
15. fresh audit 전/후 비교
16. public-visible fresh non-sample 전/후 비교
17. 최종 QA 데이터셋 규모
18. fixture 생성 여부
19. Git에 커밋하면 안 되는 파일 확인
20. public route QA 결과
21. repair Apply 권장 여부
22. 한국어 UI 보존 확인
23. 테스트 실행 결과
24. 남은 리스크
25. 다음 devpack 추천
26. 종료 git status/log
```

---

## 21. result bundle의 API 호출 표 형식

result bundle에는 아래 표를 반드시 포함하세요.

```markdown
| ApiKind | PageNo | Limit | MaxPages | MinDate | PrptDivCd | PvctTrgtYn | BidPrdYmdStart | BidPrdYmdEnd | fetched | accepted_fresh | inserted | duplicates | dropped_stale | dropped_unknown_date |
|---|---:|---:|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| real_estate | 2 | 20 | 1 | 2025-01-01 | ... | N | ... | ... | ... | ... | ... | ... | ... | ... |
| movable | 2 | 20 | 1 | 2025-01-01 | ... | N | ... | ... | ... | ... | ... | ... | ... | ... |
```

---

## 22. result bundle의 최종 데이터셋 요약 형식

아래 형식으로 최종 결과를 적으세요.

```text
최종 public-visible fresh non-sample total:
최종 public-visible fresh non-sample real_estate:
최종 public-visible fresh non-sample movable:

최종 DB total:
최종 fresh:
최종 stale:
최종 invalid_date:
최종 unknown_date:

sample/fixture row count:
detail marker count real_estate:
detail marker count movable:
```

---

## 23. 종료 전 확인

종료 전 반드시 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
```

commit/push는 하지 마세요.

---

## 24. 성공 기준 요약

이번 v006-a3는 아래 조건을 만족하면 성공입니다.

```text
1. 부동산/동산 public-visible fresh non-sample row가 90~120건 수준으로 확보된다.
2. PageNo 기반 추가 수집이 가능해진다.
3. 부동산/동산 양쪽 모두 QA에 쓸 수 있는 row 수가 확보된다.
4. API key가 출력되지 않는다.
5. raw payload 전체가 출력되지 않는다.
6. DB/backup/log/raw 파일이 Git에 포함되지 않는다.
7. 기존 한국어 UI가 영어로 바뀌지 않는다.
8. 공고목록 API와 national_property/국유재산 전용 API는 건드리지 않는다.
9. repair Apply는 실행하지 않는다.
10. result bundle 하나로 정리된다.
```

---

## 25. 다음 단계 예상

v006-a3 이후 예상되는 다음 단계는 아래 중 하나입니다.

```text
v006-a4:
수집된 100건 내외 데이터를 기반으로 public /onbid 필터, 정렬, 상세 UX 품질 개선

v006-b:
운영 스케줄러 등록 전 리허설, 백업/복원 리허설, log retention 적용 기준 수립

v006-c:
보안/법무/모바일 접근성 QA

v006-d:
공고목록 API와 national_property/국유재산 전용 API를 별도 범위로 검증
```

이번 a3에서는 다음 단계 중 무엇을 할지 결정하지 말고, result bundle에 추천만 적으세요.
