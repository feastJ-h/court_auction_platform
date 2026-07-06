# devpack\_v006\_instruction.md

# court\_auction\_platform v006 지시서

## 0\. 매우 중요한 언어/문구 보존 원칙

이번 작업에서 가장 중요한 제한 중 하나는 **기존 한글 UI, 한글 문구, 한글 라벨, 한글 안내문을 영어로 바꾸지 않는 것**입니다.

과거 작업에서 영문 지시서 영향으로 소스와 화면 UI의 한글 문구가 영어로 바뀌는 문제가 있었고, 이를 복구하는 데 큰 비용이 발생했습니다.
따라서 이번 devpack부터 아래 규칙을 항상 지켜야 합니다.

```text
한국어 UI 보존 규칙:

1. 기존 화면에 표시되는 한글 문구를 영어로 번역하거나 교체하지 마세요.
2. 새로 추가하는 사용자 화면 문구는 기본적으로 한국어로 작성하세요.
3. 버튼, 메뉴, 탭, 필터, 배지, 빈 상태 안내, 로그인 안내, 오류 안내, 관리자 안내도 한국어를 우선 사용하세요.
4. 기존 테스트가 영어 문구를 기대하더라도, 실제 서비스 UI가 한국어여야 한다면 테스트를 한국어 기준으로 수정하세요.
5. 단, 코드 식별자, 변수명, 함수명, 클래스명, API kind, 환경변수명, DB 컬럼명, 라우트 경로, 파일명, 패키지명, 외부 서비스명은 기존 영어/기술 명칭을 유지하세요.
6. “사용자에게 보이는 문구”와 “코드 내부 식별자”를 혼동하지 마세요.
7. 영어로 바꿔야 할 특별한 이유가 있다면, 먼저 result bundle에 사유를 적고 실제 변경은 하지 마세요.
```

특히 다음 문구/영역은 영어로 되돌리지 마세요.

```text
- 온비드
- 회생·파산
- 로그인
- 관심
- 감시
- 패스
- 메모
- 로그인 후 분석 확인
- 일정 확인 필요
- 로그인하면 관심감시패스와 메모를 저장할 수 있습니다
- 개인정보처리방침
- 이용약관
- 면책사항
- 전체
- 부동산
- 동산
- 국유재산
- 기타
- 초기화 / 다시 보기 / 검색 / 필터 관련 한국어 문구
```

작업 완료 전 반드시 확인하세요.

```powershell
git diff -- frontend/templates backend tests
```

그리고 result bundle에 아래 항목을 반드시 포함하세요.

```text
한국어 UI 보존 확인:
- 기존 한글 UI를 영어로 바꾼 변경이 있는가? 예/아니오
- 새 사용자 표시 문구는 한국어인가? 예/아니오
- 영어가 남아 있다면 코드 식별자/환경변수/API명/외부서비스명인가? 예/아니오
- 의도치 않은 번역 변경이 없음을 확인했는가? 예/아니오
```

## 1\. 현재 기준 상태

프로젝트:

```text
court\_auction\_platform
```

현재 완료 기준 브랜치:

```text
codex/devpack-v005-product-qa-fresh-data-navigation
```

현재 완료 기준 커밋:

```text
ad6ee38 feat: finalize v005 product qa and review mode
```

현재 기대 상태:

```text
working tree clean
```

v005에서 이미 완료된 중요한 내용:

```text
- public /onbid는 2025-01-01 이후 fresh 데이터 중심으로 표시
- pre-2025, unknown-date, sentinel-date, sample/fixture row는 public 기본 목록에서 숨김
- 공개 UI 한국어화
- 비로그인 ONBID 상세에서 관심/감시/패스/메모 form 숨김
- 비로그인 사용자에게 로그인 CTA 표시
- review mode 보안 헤더와 raw document 차단 유지
- API key, raw payload, 내부 파일 경로, OCR 전문, AI 분석은 public에 노출 금지
```

## 2\. v006의 핵심 목표

v006의 첫 번째 목표는 법무/보안 문구 정리가 아니라 **최신 ONBID 데이터 확보와 공개 목록 가시성 회복**입니다.

현재 우려:

```text
public /onbid 목록이 0건 또는 너무 적게 보일 수 있음.
주요 원인은 기존 취합 데이터가 오래된 데이터, 예를 들어 온비드 등록일 기준 2003년 인근 데이터일 가능성이 큼.
```

따라서 v006 목표는 다음입니다.

```text
2025-01-01 이후 실제 ONBID 데이터를 제한적으로 수집하고,
public /onbid에 fresh 데이터가 표시될 수 있는 상태를 만든다.
```

## 3\. 이번 devpack의 범위

이번 v006은 다음 범위로 제한합니다.

```text
1. 현재 DB의 freshness 상태 확인
2. 오래된 데이터가 public에서 숨겨지는지 확인
3. 제한적 실제 ONBID fresh 수집
4. real\_estate 중심의 최신 데이터 확보
5. movable API 0건 원인 진단
6. national\_property unknown-date 원인 진단 및 최소 수정
7. notice stale drop 원인 진단
8. 수동 one-shot scheduled sync 리허설
9. derived-field repair Apply 필요 여부 판단
10. 한국어 UI 보존 검증
```

## 4\. 절대 금지 사항

```text
전체 repo 재검토 금지.
대량 백필 금지.
API key 출력 금지.
raw payload 전체 출력 금지.
DB row 삭제 금지.
stale/unknown/pre-2025 데이터 삭제 금지.
destructive migration 금지.
schema 변경 금지. 단, 정말 필요한 경우 먼저 result bundle에 제안만 하고 실제 변경하지 마세요.
commit/push 금지.
Windows Scheduler 영구 등록 금지.
사용자 화면 한글 문구를 영어로 변경 금지.
기존 한국어 UI/라벨/안내문을 영어로 번역 금지.
```

## 5\. 먼저 실행할 Git 확인

작업 시작 시 아래만 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git diff --name-only
```

전체 소스 탐색을 하지 말고, 변경이 필요한 관련 파일만 확인하세요.

## 6\. 우선 확인할 파일

필요할 때만 아래 파일을 제한적으로 확인하세요.

```text
backend/workers/onbid\_sync.py
backend/services/auction\_items.py
backend/web/routers/auctions.py
backend/database/models.py
backend/database/session.py
main\_app.py

run\_onbid\_fresh\_probe.ps1
run\_onbid\_scheduled\_sync.ps1
audit\_onbid\_freshness.ps1
repair\_onbid\_derived\_fields.ps1
backup\_database.ps1
check\_scheduled\_tasks.ps1

frontend/templates/auctions/index.html
frontend/templates/auctions/detail.html
frontend/templates/shared/onbid\_category\_tabs.html
frontend/templates/shared/filter\_chips.html
frontend/templates/shared/empty\_state.html
frontend/templates/shared/public\_nav.html

tests/onbid\_freshness\_policy\_test.py
tests/onbid\_public\_filter\_state\_test.py
tests/onbid\_category\_mapping\_test.py
tests/sitemap\_fresh\_public\_routes\_test.py
tests/public\_route\_visual\_smoke\_test.py
tests/navigation\_active\_state\_test.py
```

## 7\. 현재 알려진 v005 데이터 상태

v005 기준 실제 ONBID fresh probe 요약:

```text
real\_estate:
  fetched 20
  accepted fresh 20

movable:
  fetched 0

notice:
  fetched 20 notices
  accepted fresh 0
  dropped stale 20

national\_property:
  fetched 20
  accepted fresh 0
  dropped unknown date 20
```

현재 DB freshness audit 기준:

```text
Total ONBID rows: 88
Fresh: 27
Stale: 60
Unknown date: 1
Derived-field repair dry run: checked 88, would update 62, updated 0
```

중요 해석:

```text
repair\_onbid\_derived\_fields.ps1 -Apply는 오래된 2003년대/pre-2025 데이터를 최신 데이터로 만들어주지 않습니다.

이 스크립트는 public\_category, freshness\_date, freshness\_status, public\_visible 같은 저장된 파생 필드를 갱신할 뿐입니다.

따라서 이번 v006에서는 먼저 최신 2025+ ONBID 데이터를 제한적으로 확보하는 것이 우선입니다.
```

## 8\. Phase 1 — 현재 상태 read-only audit

먼저 DB 변경 없이 현재 상태를 확인하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\audit\_onbid\_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\\repair\_onbid\_derived\_fields.ps1 -DryRun -MinDate 2025-01-01
```

가능하면 public `/onbid`에서 실제로 몇 건이 보이는지 확인하세요.

확인할 항목:

```text
1. total row 수
2. fresh row 수
3. stale row 수
4. unknown-date row 수
5. public\_visible true row 수
6. public /onbid 표시 가능 row 수
7. category별 fresh/public-visible 수
8. sample/fixture/sentinel 때문에 숨겨지는 row 수
```

## 9\. Phase 2 — DB 백업

실제 ONBID API 수집 또는 DB write 가능성이 있는 작업 전에는 반드시 백업하세요.

기본 명령:

```powershell
powershell -ExecutionPolicy Bypass -File .\\backup\_database.ps1
```

백업 스크립트 사용법이 다르면 스크립트를 확인한 뒤 가장 안전한 방식으로 실행하세요.

result bundle에 반드시 기록하세요.

```text
- 백업 실행 여부
- 백업 파일 경로
- 백업 실행 시각
```

복원은 실행하지 마세요.

## 10\. Phase 3 — 제한적 real\_estate 최신 데이터 수집

real\_estate는 v005에서 2025+ fresh accepted가 성공했던 API kind입니다.
따라서 real\_estate부터 작게 확장하세요.

기본 제한:

```text
Limit=20
MaxPages=1
MinDate=2025-01-01
```

명령 예시:

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_fresh\_probe.ps1 -ApiKind real\_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

실행 후 즉시 audit:

```powershell
powershell -ExecutionPolicy Bypass -File .\\audit\_onbid\_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\\repair\_onbid\_derived\_fields.ps1 -DryRun -MinDate 2025-01-01
```

첫 실행이 안전하고 API key가 출력되지 않았으며, 결과가 전부 duplicate이면 한 번만 더 넓혀도 됩니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_fresh\_probe.ps1 -ApiKind real\_estate -Limit 20 -MaxPages 2 -MinDate 2025-01-01
```

이번 devpack에서는 절대 아래를 초과하지 마세요.

```text
Limit=20
MaxPages=3
```

## 11\. Phase 4 — movable 0건 원인 진단

v005에서 movable은 fetched 0이었습니다.

무작정 반복 호출하지 말고 먼저 코드에서 parameter 구성을 확인하세요.

확인할 항목:

```text
1. movable endpoint가 올바른가
2. movable API kind 매핑이 올바른가
3. 날짜 파라미터 이름이 real\_estate와 다른가
4. MinDate가 실제 API에 적용되는 방식이 맞는가
5. pagination 파라미터가 올바른가
6. 실제 데이터가 없어서 0건인지, 요청 파라미터 문제인지
```

필요 시 한 번만 제한 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_fresh\_probe.ps1 -ApiKind movable -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

0건이면 재시도하지 말고 원인 후보와 다음 조치만 result bundle에 정리하세요.

## 12\. Phase 5 — national\_property 날짜 매핑 진단

v005에서 national\_property는 20건 fetch됐지만 20건 모두 unknown-date로 drop되었습니다.

이는 데이터가 없다는 뜻이 아니라 **날짜 필드 매핑이 부족할 가능성**이 큽니다.

목표:

```text
national\_property payload에서 freshness\_date로 사용할 수 있는 날짜 필드 후보를 찾는다.
```

주의:

```text
raw payload 전체를 result bundle에 붙이지 마세요.
public 화면에 raw payload를 노출하지 마세요.
API key를 출력하지 마세요.
필드명과 간단한 샘플 날짜 형태만 기록하세요.
```

명확한 날짜 필드가 확인되면, 최소 수정만 허용합니다.

수정 후보:

```text
backend/services/auction\_items.py
```

테스트 추가/수정 후보:

```text
tests/onbid\_freshness\_policy\_test.py
tests/onbid\_category\_mapping\_test.py
```

수정 후 실행:

```powershell
\& $Py tests/onbid\_freshness\_policy\_test.py
\& $Py tests/onbid\_category\_mapping\_test.py
```

그 다음 한 번만 제한 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_fresh\_probe.ps1 -ApiKind national\_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

실행 후 audit:

```powershell
powershell -ExecutionPolicy Bypass -File .\\audit\_onbid\_freshness.ps1 -MinDate 2025-01-01
```

## 13\. Phase 6 — notice stale drop 원인 진단

v005에서 notice는 20건 fetch됐지만 20건 모두 stale로 drop되었습니다.

확인할 항목:

```text
1. notice API에 MinDate가 실제로 적용되는가
2. notice 날짜 필드가 올바르게 매핑되어 있는가
3. noticeDate, pbancDt, opbdDt 계열 중 어떤 필드를 쓰는가
4. 2025+ 조건을 줬는데도 2003년대 데이터가 오는 이유가 있는가
```

한 번만 제한 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_fresh\_probe.ps1 -ApiKind notice -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

결과에는 raw payload를 붙이지 말고 아래만 기록하세요.

```text
- fetched count
- accepted fresh
- dropped stale
- dropped unknown date
- 파싱된 날짜의 최소/최대 범위
- 의심되는 필드명
- 다음 수정 제안
```

## 14\. Phase 7 — 수동 scheduled sync 리허설

이번 devpack에서는 Windows Scheduler 영구 등록을 하지 않습니다.

대신 기존 scheduled sync script를 수동 one-shot으로 실행하는 것은 허용합니다.

먼저 scheduler 현재 상태를 확인하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\check\_scheduled\_tasks.ps1
```

그 다음, 백업이 완료된 상태에서 아래 중 하나를 수동 실행할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_scheduled\_sync.ps1 -ApiKind real\_estate -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

national\_property 날짜 매핑이 수정되고 테스트가 통과한 경우에만 아래를 추가로 실행할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\\run\_onbid\_scheduled\_sync.ps1 -ApiKind national\_property -Limit 20 -MaxPages 1 -MinDate 2025-01-01
```

result bundle에는 아래를 명확히 구분해 쓰세요.

```text
수동 scheduled sync script 실행: 수행/미수행
Windows Scheduler 영구 등록: 수행하지 않음
```

## 15\. Phase 8 — derived-field repair Apply 판단

fresh 데이터 수집 후 다시 dry-run을 실행하세요.

```powershell
powershell -ExecutionPolicy Bypass -File .\\repair\_onbid\_derived\_fields.ps1 -DryRun -MinDate 2025-01-01
```

이번 devpack에서는 기본적으로 Apply를 실행하지 마세요.

Apply가 필요하다고 판단되면 result bundle에 아래 형식으로 제안만 하세요.

```text
repair Apply 권장 여부: 예/아니오

권장 사유:
- ...

실행 전 필수 조건:
1. DB 백업 완료
2. 백업 경로 확인
3. 테스트 통과
4. public /onbid 표시 기준 확인
5. 사용자 승인

제안 명령:
powershell -ExecutionPolicy Bypass -File .\\repair\_onbid\_derived\_fields.ps1 -Apply -MinDate 2025-01-01
```

사용자 승인 없이 Apply를 실행하지 마세요.

## 16\. Phase 9 — 공개 화면과 한국어 UI 검증

작업 후 public 화면에서 아래가 유지되는지 확인하세요.

```text
1. public /onbid는 fresh 데이터만 기본 표시
2. pre-2025 데이터는 삭제하지 않고 숨김
3. unknown-date 데이터는 삭제하지 않고 숨김
4. sentinel-date 데이터는 숨김
5. sample/fixture 데이터는 기본 숨김
6. sitemap.xml은 fresh public item만 포함
7. 비로그인 ONBID 상세에서는 관심/감시/패스/메모 form이 보이지 않음
8. 비로그인 사용자는 한국어 로그인 CTA를 봄
9. 기존 한글 메뉴/탭/버튼/배지가 영어로 바뀌지 않음
10. “일정 확인 필요” 같은 한글 fallback 문구가 유지됨
```

권장 테스트:

```powershell
\& $Py tests/onbid\_freshness\_policy\_test.py
\& $Py tests/onbid\_public\_filter\_state\_test.py
\& $Py tests/onbid\_category\_mapping\_test.py
\& $Py tests/sitemap\_fresh\_public\_routes\_test.py
\& $Py tests/onbid\_module\_test.py
\& $Py tests/page\_response\_smoke\_test.py
\& $Py tests/public\_access\_auth\_boundary\_test.py
\& $Py tests/navigation\_active\_state\_test.py
\& $Py tests/public\_route\_visual\_smoke\_test.py
```

한국어 UI 회귀 확인을 위해 가능하면 아래 관점도 확인하세요.

```text
- 공개 화면에 의도치 않은 영어 제목이 생겼는가
- Reset 같은 영어 버튼이 다시 생겼는가
- Recovery and Bankruptcy Notices 같은 영어 제목이 다시 생겼는가
- ONBID Public Auction 같은 영어 제목이 다시 생겼는가
- AI 분석 있음 문구가 public에 다시 노출되는가
```

테스트가 없다면 최소한 result bundle에 수동 확인 결과를 쓰세요.

## 17\. 변경 허용 범위

허용되는 변경:

```text
- ONBID freshness/date extraction의 최소 수정
- national\_property 날짜 매핑의 최소 수정
- movable/notice parameter 진단에 필요한 최소 수정
- 관련 테스트 추가/수정
- result bundle 작성
```

주의가 필요한 변경:

```text
- frontend/templates 수정 시 한글 UI 보존 필수
- tests 수정 시 영어 문구 기준으로 되돌리지 말 것
- backend/services/auction\_items.py 수정 시 한글 category label/token alias 훼손 금지
```

금지되는 변경:

```text
- 전체 UI 개편
- 대량 번역
- 한글 문구 영어화
- schema 변경
- destructive migration
- DB row 삭제
- raw payload public 노출
- API key 로그 출력
- commit/push
```

## 18\. result bundle 작성

작업 결과는 하나의 파일로만 작성하세요.

```text
reports/devpacks/devpack\_v006\_result\_bundle.md
```

여러 문서로 나누지 마세요.

반드시 포함할 항목:

```text
1. 작업 메타데이터
2. 시작 git status/log
3. 확인한 파일 목록
4. DB 백업 여부와 백업 경로
5. 실행한 명령 목록
6. 실제 API 호출 목록
   - ApiKind
   - Limit
   - MaxPages
   - MinDate
   - API key 미출력 확인
7. fresh audit 전/후 비교
8. public-visible row 전/후 비교 가능 시 포함
9. real\_estate 수집 결과
10. movable 0건 원인 진단
11. national\_property 날짜 매핑 결과
12. notice stale drop 원인 진단
13. 수동 scheduled sync script 실행 결과
14. Windows Scheduler 영구 등록 여부
15. repair Apply 권장 여부
16. 한국어 UI 보존 확인
17. 실행한 테스트와 결과
18. 변경 파일 목록
19. 남은 리스크
20. 다음 devpack 추천
21. 종료 git status/log
```

한국어 UI 보존 확인 섹션은 반드시 아래 형식으로 작성하세요.

```text
## 한국어 UI 보존 확인

- 기존 한글 UI를 영어로 바꾼 변경: 없음 / 있음
- 새 사용자 표시 문구의 기본 언어: 한국어 / 영어 / 혼합
- 영어가 남아 있는 영역: 코드 식별자 / 환경변수 / API kind / 외부 서비스명 / 기타
- 의도치 않은 번역 변경 확인: 완료 / 미완료
- 확인한 템플릿/파일:
  - ...
- 비고:
  - ...
```

## 19\. 종료 전 확인

종료 전 반드시 실행하세요.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
```

commit/push는 하지 마세요.

## 20\. 성공 기준

이번 v006 devpack은 아래 조건을 만족하면 성공입니다.

```text
1. 2025+ real ONBID 데이터 수집 경로가 제한적으로 검증됨
2. public /onbid에 fresh 데이터가 표시될 수 있는 근거가 생김
3. 오래된 pre-2025 데이터는 삭제하지 않고 숨김 유지
4. API key가 출력되지 않음
5. raw payload가 public에 노출되지 않음
6. scheduler는 영구 등록하지 않고 수동 one-shot 리허설만 수행
7. repair Apply는 사용자 승인 없이 실행하지 않음
8. 기존 한글 UI가 영어로 바뀌지 않음
9. 결과는 devpack\_v006\_result\_bundle.md 하나로 정리됨
```

