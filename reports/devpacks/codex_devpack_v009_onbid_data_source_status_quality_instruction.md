# Codex Devpack v009 작업지시서
## ONBID 데이터 신뢰성·원문 링크·마감 상태·검증 루프 강화

작성일: 2026-07-10 KST
대상 프로젝트: `court_auction_platform`
권장 작업 브랜치: `codex/devpack-v009-onbid-data-source-status-quality`
기준 브랜치: `codex/devpack-v008-master-review-data-ux-loop`
목표: 공개 UX의 껍데기 개선을 넘어, 실제 리뷰 사이트에서 “볼 만한 데이터가 충분하고, 마감 상태가 정확하며, 원문 확인 흐름이 살아 있는” ONBID 검토 보조 MVP로 끌어올린다.

---

## 0. 이번 devpack의 판단 기준

v008은 다음 성과가 있었다.

- 홈이 “오늘 검토 입구”에 가까워졌다.
- `/onbid`, `/onbid/today`, 자료 확인 필요, 상세 4-Zone, Development Insight CTA, 공유 요약 관리, 관리자 운영 화면이 추가되었다.
- 한글 깨짐(mojibake)과 금지 표현 스캔은 통과했다.
- 주요 script-style 테스트는 PASS했다.

그러나 실제 서비스 체감 기준으로는 아직 부족하다.

이번 v009의 핵심은 신규 기능을 많이 추가하는 것이 아니라, 다음 5개를 반드시 잡는 것이다.

1. ONBID 공개 데이터 수량과 활성 데이터 비율을 늘린다.
2. 마감일/입찰 상태/D-day 계산 오류를 바로잡는다.
3. 원문 보기 또는 원문 확인 경로를 실제 사용 가능한 수준으로 보강한다.
4. 상세 화면의 “상세 정보 없음”과 “상세 정보 있음” 모순을 제거한다.
5. `python -m pytest` 기본 실행이 환경 의존 테스트 때문에 실패하지 않도록 테스트 정책을 정리한다.

---

## 1. 작업 허가 범위

이번 작업에서는 아래 항목을 별도 질의 없이 진행한다.

### 1.1 허용

- 새 작업 브랜치 생성
- Git pull/fetch/status/log/diff 확인
- Python 패키지 설치
- `pytest`/테스트 도구 설치
- 제한적 ONBID API 호출
- 네트워크 접근
- Cloudflare quick tunnel 실행
- 로컬 DB 백업
- derived field repair dry-run 및 조건부 apply
- 비파괴 DB 마이그레이션
- 테스트 실행
- 외부 URL QA
- 작업 브랜치 commit/push

### 1.2 금지

- `main` 직접 push
- API key, secret, token 출력
- raw payload 전체 로그 저장
- raw payload fixture 커밋
- `auction_data.db` 커밋
- `storage/backups/*` 커밋
- `storage/logs/*` 커밋
- 내부 원본 파일 경로 공개
- AI 권리분석 기능 추가
- 위험/안전/추천/수익성/낙찰 가능성 판단 문구 추가
- Archi-Pro 실제 API 연동
- 사용자를 불안하게 만드는 FOMO/경쟁자 알림 추가
- 광고주/전문가를 추천·검증처럼 보이게 하는 문구 추가

---

## 2. 시작 전 필수 확인

작업 시작 즉시 아래를 실행하고 결과서에 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -8
```

그 다음 기준 브랜치에서 새 브랜치를 만든다.

```powershell
git checkout codex/devpack-v008-master-review-data-ux-loop
git pull --ff-only origin codex/devpack-v008-master-review-data-ux-loop
git checkout -b codex/devpack-v009-onbid-data-source-status-quality
```

이미 브랜치가 존재하면 fetch 후 해당 브랜치에서 이어서 작업하되, 상태를 결과서에 기록한다.

---

## 3. 작업 전 백업

DB를 건드리기 전에 반드시 백업한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

결과서에 아래를 기록한다.

- 백업 파일 경로
- sha256
- source DB 경로
- restore 실행 여부
- restore 미실행이면 미실행 사유

---

## 4. 현재 상태 진단

아래 항목을 코드 또는 스크립트로 계산하여 결과서에 기록한다.

### 4.1 데이터 수량

- 전체 ONBID row 수
- fresh row 수
- public-visible fresh non-sample 수
- category별 public-visible fresh non-sample 수
  - real_estate
  - movable
  - national_property
  - other
- active_or_upcoming 수
- ended 수
- unknown_date 수
- stale 수
- duplicate key count
- sample/fixture public exposure count

### 4.2 원문/상세 품질

- public-visible fresh rows 중 source/original URL 보유 수
- original URL coverage %
- category별 original URL coverage
- 상세 marker 보유 수
- 실제 상세 본문 필드 보유 수
- “상세 정보가 없습니다” 노출 수
- “상세 정보 있음” 배지가 붙었지만 상세 본문이 없는 수

### 4.3 마감 상태 품질

오늘 기준은 KST 기준 현재 날짜/시간을 사용한다.

계산해야 할 항목:

- deadline < now 인데 `입찰진행중`으로 보이는 항목 수
- deadline < now 인데 목록 상단 active 영역에 노출되는 항목 수
- deadline < now 인데 `/onbid/today` 기본 목록에 노출되는 항목 수
- `D+N` 라벨이 혼동되게 표시되는 항목 수
- `/onbid?closing_within_days=7` 결과 수

---

## 5. 최우선 수정 1: 마감 상태/D-day 계산 정리

현재 라이브 리뷰 사이트에서는 2026-07-10 KST 기준 이미 지난 2026-07-07, 2026-07-09 마감 항목이 `입찰진행중` 또는 `D+1`, `D+3` 형태로 보이는 문제가 있다. 이 문제를 최우선 수정한다.

### 5.1 상태 계산 원칙

- `deadline >= now`이면 활성 또는 예정 항목으로 본다.
- `deadline < now`이면 종료 또는 입찰마감 항목으로 본다.
- 날짜/시간은 KST 기준으로 비교한다.
- 시간 정보가 없고 날짜만 있으면 보수적으로 해당일 23:59:59 KST를 기준으로 한다.
- 마감일이 없으면 `일정 확인 필요`로 표시한다.

### 5.2 UI 라벨 원칙

허용:

- `입찰진행중`
- `마감 임박`
- `D-3`
- `오늘 마감`
- `입찰마감`
- `마감 후 3일`
- `일정 확인 필요`
- `종료됨`

금지 또는 수정 필요:

- 이미 지난 항목에 `입찰진행중`
- 이미 지난 항목에 혼동되는 `D+1`, `D+3` 단독 표시
- 마감일이 없는데 활성처럼 보이는 표시
- 종료 항목을 기본 목록 최상단에 우선 노출

### 5.3 목록/홈/오늘 보기 정책

- `/onbid` 기본 정렬은 active/upcoming 우선, ended는 뒤로 보낸다.
- `/onbid/today` 기본 목록은 active/upcoming만 보여준다.
- ended를 오늘 보기에 포함해야 할 특별한 이유가 있으면 별도 접힘 섹션 “이미 마감된 최근 수집 항목”으로 분리한다.
- 홈의 “이번 주 마감 임박” 카드는 active/upcoming 중 7일 이내 마감 항목만 집계한다.
- 0건이면 “현재 공개 가능한 마감 임박 항목이 없습니다”로 표시하고, 사용자가 빈 목록으로 들어가도 자연스러운 empty state를 제공한다.

### 5.4 필수 테스트

새 테스트 또는 기존 테스트 보강:

- `tests/onbid_deadline_status_kst_test.py`
- `tests/onbid_today_excludes_ended_by_default_test.py`
- `tests/onbid_closing_within_days_active_only_test.py`
- `tests/home_closing_card_empty_state_test.py`

테스트해야 할 케이스:

- 과거 마감일
- 오늘 마감
- 7일 이내 마감
- 7일 이후 마감
- 마감일 없음
- 날짜만 있고 시간 없음
- KST 기준 날짜 경계

---

## 6. 최우선 수정 2: ONBID 데이터 추가 수집

v008 결과 기준 public-visible fresh non-sample은 138건이고, v008 목표였던 250건에 미달했다. v009에서는 더 현실적인 QA/리뷰용 데이터셋을 확보한다.

### 6.1 v009 목표 수량

최소 목표:

```text
public-visible fresh non-sample total >= 300
active_or_upcoming >= 200
real_estate >= 130
movable >= 100
national_property >= 20
duplicate_key_count = 0
sample/fixture public exposure = 0
```

단, national_property는 API 특성상 fresh public row 확보가 불가능할 수 있다. 이 경우 실패로 숨기지 말고 다음을 결과서에 기록한다.

- 호출한 API kind
- 호출 파라미터
- fetched
- accepted_fresh
- inserted
- dropped_stale
- dropped_unknown_date
- dropped_invalid_date
- public-visible로 제외된 사유
- 다음 시도 전략

### 6.2 수집 원칙

- `MinDate=2025-01-01` 기준은 유지한다.
- public 노출은 active/upcoming 우선으로 한다.
- stale/unknown/invalid date는 기본 공개에서 제외한다.
- sample/fixture는 공개에서 제외한다.
- 중복 key는 insert하지 않는다.
- API key는 절대 출력하지 않는다.
- raw payload 전체를 저장하거나 커밋하지 않는다.
- 호출별 요약 통계만 결과서에 기록한다.

### 6.3 추천 수집 전략

1. 현재 DB audit
2. real_estate list 수집
   - pageNo 1~10 범위
   - limit 50 또는 100
   - bid period: today KST ~ today + 120일
   - duplicate가 많으면 page range 변경
3. movable list 수집
   - pageNo 1~10 범위
   - limit 50 또는 100
   - bid period: today KST ~ today + 60일 또는 90일
4. national_property 별도 수집
   - 공식 API/기존 client의 분리 파라미터를 확인
   - pageNo 1~10
   - fresh/active row 확보가 안 되면 stale/unknown 제외 사유 기록
5. notice/public announcement 수집
   - ONBID notice/public announcements와 item 연결 가능성 확인
   - item과 연결 가능한 공고 번호/물건 번호/온비드 번호 매칭
6. 상세 API 보강
   - active/upcoming public rows 중 detail/source URL이 없는 항목 우선
   - real_estate와 movable 모두 보강
   - detail limit을 너무 낮게 두지 말고 목표량 기반으로 반복
   - API 호출은 과도하지 않게 sleep/rate-limit 적용

### 6.4 호출 안전장치

- 각 API kind별 최대 호출 수를 제한한다.
- 실패 시 재시도는 1~2회까지만 한다.
- API 응답 본문 전체를 출력하지 않는다.
- 사진 URL 전체 목록을 출력하지 않는다.
- API key가 포함될 수 있는 URL을 로그에 남기지 않는다.
- 결과서에는 요약 통계만 남긴다.

---

## 7. 최우선 수정 3: 원문 링크 / 원문 확인 경로 보강

현재 운영 DB public item에는 원문 detail URL이 연결된 항목이 없어 실제 상세의 `원문 보기` 버튼이 대부분 숨김 또는 확인 필요 상태로 표시된다고 보고되었다. 실제 라이브 사이트에서도 목록과 상세에 `원문 링크 확인 필요`가 반복 노출된다.

이 문제는 서비스 정체성과 직접 연결된다. 우리는 투자 판단을 하지 않고 원문 확인을 유도하는 플랫폼이므로, 원문 경로가 약하면 제품의 핵심이 약해진다.

### 7.1 목표

최소 목표:

```text
public-visible fresh non-sample original_url_coverage >= 70%
active_or_upcoming original_url_coverage >= 80%
top 50 public list original_url_coverage >= 90%
```

달성 불가능하면 다음을 반드시 결과서에 기록한다.

- ONBID API가 원문 URL을 주지 않는지
- 내부적으로 만들 수 있는 URL 패턴이 있는지
- 물건 번호/공고 번호/온비드 번호로 공식 사이트 검색 경로를 제공할 수 있는지
- 임시 UX 대안

### 7.2 원문 링크 생성/보강 전략

다음 순서로 확인한다.

1. API detail payload 안의 원문/detail URL 필드 존재 여부
2. API list payload 안의 source/detail URL 필드 존재 여부
3. ONBID 공식 상세 페이지 URL 패턴 구성 가능 여부
4. 공고번호/물건번호/온비드번호 기반 공식 검색 URL 구성 가능 여부
5. 위 1~4가 모두 불가능할 경우, UI에서 “원문 직접 검색 정보” 제공

### 7.3 UI 원칙

원문 URL이 있을 때:

- 목록 카드에 `원문 보기` 버튼 표시
- 상세 상단과 하단에 `원문 보기` 표시
- 클릭 analytics 기록
- 외부 링크는 새 창 또는 명확한 외부 이동 표시

원문 URL이 없을 때:

- `원문 링크 확인 필요`를 카드마다 중복 강조하지 말고 차분히 표시
- 상세에는 “온비드에서 아래 번호로 직접 확인하세요” 영역 제공
  - 온비드 번호
  - 공매 번호
  - 기관명
  - 물건명
  - 마감일
- `원문 보기`처럼 보이는 가짜 버튼은 금지
- 원문이 없는 항목은 자료 완결성 배지를 `원문 확인 필요`로 유지

### 7.4 analytics 안전

- original link click 이벤트에는 raw full URL을 metadata로 저장하지 않는다.
- item id, category, has_original_url 정도만 저장한다.
- API key나 query secret이 들어갈 가능성이 있는 URL은 절대 analytics에 저장하지 않는다.

### 7.5 필수 테스트

- `tests/onbid_original_url_coverage_test.py`
- `tests/onbid_original_link_fallback_test.py`
- `tests/product_analytics_original_url_safety_test.py`

---

## 8. 최우선 수정 4: 상세 화면 정보 모순 제거

현재 상세 화면에는 `상세 정보가 없습니다. 원문 확인이 필요합니다.`가 보이면서, 바로 아래 원문 확인 포인트에는 `상세 정보 있음`이 같이 표시되는 모순이 있다. 이 문제를 해결한다.

### 8.1 원칙

- 상세 본문이 없으면 `상세 정보 없음` 또는 `상세 정보 확인 필요`로 표시한다.
- 단순히 detail API marker가 있다는 이유만으로 `상세 정보 있음`이라고 표시하지 않는다.
- 실제 사용자에게 의미 있는 detail fields가 일정 수준 이상 있어야 `상세 정보 확인됨`으로 본다.
- 원문 URL이 없으면 `원문 링크 확인 필요`로 표시한다.
- 공고 연결이 있으면 공고 연결 여부와 원문 URL 여부를 분리한다.

### 8.2 원문 확인 포인트 UI 개선

현재처럼 배지 텍스트가 한 줄로 붙는 형태를 피한다.

권장 구조:

```text
원문 확인 포인트

☑ 가격 정보: 확인됨
☑ 소재지: 확인됨
☑ 입찰 일정: 확인됨
☐ 원문 링크: 확인 필요
☐ 상세 설명: 확인 필요

위 항목은 자료 완결성 상태입니다. 법률·투자 판단을 의미하지 않습니다.
```

### 8.3 필수 테스트

- `tests/onbid_detail_data_consistency_test.py`
- `tests/onbid_detail_checklist_readability_test.py`
- `tests/onbid_detail_no_false_detail_available_test.py`

---

## 9. UX 보완: 홈 / 목록 / 오늘 보기

### 9.1 홈

홈 4개 카드가 실제 집계와 맞아야 한다.

- 오늘 새로 확인된 물건: active/upcoming public-visible 기준 우선
- 이번 주 마감 임박: active/upcoming + 7일 이내
- 내 지역 신규 물건: 기본 서울/수도권, 단 active/upcoming 우선
- 가격 정보 있는 1억 이하: active/upcoming 우선, ended는 뒤로

0건 카드의 문구:

```text
현재 공개 가능한 항목이 없습니다. 조건을 바꾸거나 전체 목록을 확인해 보세요.
```

### 9.2 목록

- 기본 정렬은 active/upcoming 먼저
- ended는 뒤로
- category count는 전체 count인지 현재 필터 count인지 명확히 표시
- 국유일반재산 0건이면 “현재 공개 가능한 국유일반재산 항목이 없습니다” empty state 제공
- `자료 확인 필요` 필터는 정보 부족을 기회처럼 포장하지 않는다.

### 9.3 오늘 보기

- 비로그인도 200 유지
- 비로그인은 저장 form 없이 로그인 CTA만 표시
- 기본 목록은 active/upcoming
- 마감된 최근 수집 항목은 별도 접힘 섹션으로 분리하거나 기본 제외
- 완료 UX는 로그인 사용자에게만 저장 기반으로 표시
- “오늘 검토 완료”는 투자 검토 완료가 아니라 후보 정리 완료로 표현한다.

---

## 10. 관리자/운영 대시보드 보강

v008에서 관리자 운영 화면이 추가되었다. v009에서는 데이터 품질 운영 지표를 추가한다.

### 10.1 `/admin/onbid-data-quality`

새 화면 또는 기존 admin 화면 확장.

표시 항목:

- public-visible fresh non-sample total
- active_or_upcoming
- ended
- category count
- original URL coverage
- detail body coverage
- source API kind별 count
- missing original URL count
- missing price count
- missing address count
- missing deadline count
- false detail available count
- national_property fresh 확보 실패 사유 요약
- last sync time
- last detail enrichment time

### 10.2 운영 액션

- issue report pending/resolved/ignored 처리
- original URL missing 항목 목록
- detail missing 항목 목록
- ended인데 active로 보이는 의심 항목 목록
- derived field repair dry-run 결과 보기

단, 운영 액션은 public에 노출하지 않는다.

---

## 11. pytest 기본 정책 정리

v008에서는 `python -m pytest`가 5개를 수집했고 4개가 실패했다. 실패 원인은 기존 환경 의존/실통신 테스트였다.

v009에서는 기본 pytest가 제품 테스트 기준으로 통과하도록 정리한다.

### 11.1 목표

```powershell
python -m pytest
```

기본 실행이 PASS해야 한다.

### 11.2 정책

- 실통신/외부 사이트 의존 테스트는 기본 pytest에서 제외한다.
- Playwright/court website/network tests는 `integration` 또는 `external` marker로 분리한다.
- OCR/PDF fixture가 로컬 환경에 의존하는 테스트는 fixture를 안정화하거나 기본 제외한다.
- provider default 차이로 실패하는 AI 테스트는 환경변수 또는 fixture로 고정한다.
- 테스트를 삭제하지 말고, 목적에 맞게 marker/pytest.ini로 정리한다.

### 11.3 산출물

- `pytest.ini` 또는 `pyproject.toml` pytest 설정
- integration marker 문서화
- 기본 pytest 결과
- integration pytest 별도 실행 가능 명령

예시:

```powershell
python -m pytest
python -m pytest -m integration
python -m pytest -m external
```

---

## 12. 보수적 문구 안전성 유지

아래 표현은 public-facing UI에 나오면 안 된다.

```text
AI 분석
권리분석
위험
안전
추천 물건
알짜
숨은 진주
저평가
수익률
수익성 높음
낙찰 보장
명도 쉬움
전문가 보고서
검증 전문가
공식 파트너
이 물건 담당 전문가
돈 되는
투자 기회
```

허용 방향:

```text
원문 확인 포인트
자료 확인 필요
자료 완결성
검토 보조
공개 자료 기준 정리
가정 기반 계산
최종 판단 전 원문과 관계 서류 확인
```

필수 스캔:

```powershell
Get-ChildItem -Path frontend\templates\public,frontend\templates\auctions,frontend\templates\cases -Recurse -File |
  Select-String -Pattern "AI 분석|권리분석|위험|안전|추천 물건|알짜|숨은 진주|저평가|수익률|낙찰 보장|명도 쉬움|전문가 보고서|검증 전문가|공식 파트너|이 물건 담당 전문가|돈 되는|투자 기회"
```

출력 결과가 있으면 문맥을 검토하고, 사용자 노출 금지 표현이면 수정한다.

---

## 13. 개발/검증 반복 루프

이번 작업은 한 번 구현하고 끝내지 않는다. 반드시 최소 2회 루프를 돈다.

### Loop 1

1. 현재 상태 audit
2. 마감 상태/D-day 수정
3. 원문 링크 보강 1차
4. ONBID 추가 수집 1차
5. 상세 모순 제거
6. 테스트 실행
7. 로컬 route QA
8. 결과 기록

### Loop 2

1. Loop 1 결과에서 미달 항목 확인
2. 추가 수집/상세 보강 2차
3. active/upcoming 부족 시 파라미터 조정
4. 원문 URL coverage 부족 시 대안 경로 구현
5. 외부 Cloudflare URL QA
6. 테스트 재실행
7. 최종 결과 기록

### 필요 시 Loop 3

다음 중 하나라도 미달이면 추가 루프를 진행한다.

- public-visible fresh non-sample total < 300
- active_or_upcoming < 200
- original URL coverage < 목표치
- 과거 마감 항목이 active처럼 보임
- `/onbid/today`에 종료 항목이 기본 노출됨
- detail consistency test 실패
- 기본 `python -m pytest` 실패
- live URL에서 mojibake 또는 금지 표현 발견

---

## 14. 로컬 QA

로컬 서버를 띄워 다음을 확인한다.

```powershell
python -m uvicorn main_app:app --host 127.0.0.1 --port 8000
```

필수 확인 route:

```text
/
/onbid
/onbid/today
/onbid?category=real_estate
/onbid?category=movable
/onbid?category=national_property
/onbid?data_quality=needs_confirmation
/onbid?closing_within_days=7
/onbid?price_max=100000000
/cases
/disclaimer
/admin/onbid-issue-reports
/admin/product-analytics
/admin/onbid-data-quality
```

상세 확인:

- active real_estate 3건
- active movable 3건
- ended item 2건
- original URL 보유 item 3건
- original URL 미보유 item 3건

검증 항목:

- status 200
- mojibake 없음
- 금지 표현 없음
- 과거 마감 항목 active 표시 없음
- 원문 URL 있으면 원문 보기 표시
- 원문 URL 없으면 직접 검색 정보 표시
- 상세 정보 있음/없음 모순 없음
- Development Insight CTA는 real_estate에만 표시
- movable에는 Development Insight CTA 미표시
- 공유 summary noindex/noarchive 유지
- issue report는 public에 자동 노출되지 않음

---

## 15. Cloudflare 외부 QA

Cloudflare quick tunnel을 열어 실제 외부 URL에서 검증한다.

```powershell
cloudflared.exe tunnel --url http://127.0.0.1:8000
```

외부 URL이 생성되면 같은 route를 요청한다.

결과서에 반드시 기록:

- Cloudflare URL
- route별 status
- mojibake 여부
- 금지 표현 여부
- `/onbid` 총 건수
- `/onbid/today` 종료 항목 기본 노출 여부
- `/onbid?closing_within_days=7` 결과 수
- 상세 real_estate CTA 표시 여부
- movable CTA 미표시 여부
- original URL coverage sample
- 원문 URL 없는 항목의 fallback 표시 여부

QA 후 uvicorn/cloudflared 프로세스 종료 여부도 기록한다.

---

## 16. 필수 테스트 목록

기존 필수 테스트:

```powershell
python tests/onbid_freshness_policy_test.py
python tests/onbid_public_filter_state_test.py
python tests/onbid_category_mapping_test.py
python tests/sitemap_fresh_public_routes_test.py
python tests/onbid_module_test.py
python tests/page_response_smoke_test.py
python tests/public_access_auth_boundary_test.py
python tests/router_boundary_test.py
python tests/isolated_operations_test.py
```

v007/v008 계열 테스트:

```powershell
python tests/product_copy_safety_test.py
python tests/onbid_today_review_completion_test.py
python tests/onbid_data_quality_needed_filter_test.py
python tests/onbid_data_issue_report_test.py
python tests/onbid_review_summary_share_test.py
python tests/product_analytics_events_test.py
python tests/development_insight_cta_safety_test.py
python tests/admin_readiness_dashboard_test.py
python tests/no_mojibake_public_copy_test.py
python tests/home_curation_cards_test.py
python tests/onbid_today_route_external_shape_test.py
python tests/onbid_default_active_priority_test.py
python tests/onbid_original_link_prominence_test.py
python tests/onbid_detail_four_zone_test.py
python tests/development_insight_cta_visibility_test.py
python tests/onbid_admin_issue_queue_test.py
python tests/onbid_shared_summary_manage_test.py
python tests/product_analytics_admin_summary_test.py
python tests/onbid_dataset_quality_threshold_test.py
```

v009 신규/보강 테스트:

```powershell
python tests/onbid_deadline_status_kst_test.py
python tests/onbid_today_excludes_ended_by_default_test.py
python tests/onbid_closing_within_days_active_only_test.py
python tests/home_closing_card_empty_state_test.py
python tests/onbid_original_url_coverage_test.py
python tests/onbid_original_link_fallback_test.py
python tests/product_analytics_original_url_safety_test.py
python tests/onbid_detail_data_consistency_test.py
python tests/onbid_detail_checklist_readability_test.py
python tests/onbid_detail_no_false_detail_available_test.py
python tests/onbid_admin_data_quality_dashboard_test.py
python tests/pytest_default_collection_policy_test.py
```

pytest:

```powershell
python -m pytest
```

기본 pytest가 실패하면 이번 devpack은 완료로 보지 않는다. 단, 실패가 통제 불가능한 외부 네트워크 때문이면 marker 정책으로 기본 pytest에서 제외하고 별도 integration 명령으로 분리한다.

---

## 17. 성공 기준

v009 성공 기준은 다음이다.

### 17.1 데이터

```text
public-visible fresh non-sample total >= 300
active_or_upcoming >= 200
real_estate >= 130
movable >= 100
national_property >= 20 또는 fresh 확보 불가 사유 명확히 기록
duplicate_key_count = 0
sample/fixture public exposure = 0
```

### 17.2 원문/상세

```text
active_or_upcoming original URL coverage >= 80% 또는 공식 API 한계/대안 명확히 기록
top 50 list original URL coverage >= 90% 또는 대안 표시 완료
false detail available count = 0
상세 정보 있음/없음 모순 = 0
```

### 17.3 상태/UX

```text
과거 마감 항목 active 표시 = 0
/onbid/today 기본 목록에 ended 노출 = 0
/onbid?closing_within_days=7은 active/upcoming만 표시
홈 4개 카드가 실제 집계와 일치
mojibake = 0
금지 표현 = 0
```

### 17.4 테스트

```text
필수 script-style tests PASS
v009 신규 tests PASS
python -m pytest PASS
Cloudflare 외부 route QA PASS
```

---

## 18. 결과서 작성 형식

결과서는 아래 경로에 작성한다.

```text
reports/devpacks/devpack_v009_onbid_data_source_status_quality_result_bundle.md
```

반드시 포함:

1. 작업 메타데이터
2. 시작 git status/log
3. 백업 정보
4. v008 결과 반영 요약
5. 작업 전 audit
6. API 호출 목록 요약
7. 데이터 수집 전/후 비교
8. original URL coverage 전/후 비교
9. deadline/status 오류 전/후 비교
10. 상세 정보 모순 전/후 비교
11. 구현 변경 파일 목록
12. 개인정보/secret/raw payload 노출 점검
13. local QA 결과
14. Cloudflare 외부 QA 결과
15. 테스트 결과
16. `python -m pytest` 결과
17. 남은 리스크
18. 다음 devpack 추천
19. 종료 git status/log
20. commit hash/push 결과

API 호출 표에는 다음 컬럼을 포함한다.

```text
ApiKind | PageNo | Limit | MaxPages | DateRange | fetched | accepted_fresh | inserted | duplicates | dropped_stale | dropped_unknown_date | dropped_invalid_date | detail_attempted | detail_succeeded
```

---

## 19. 커밋/푸시

민감 파일 제외 확인 후 커밋한다.

```powershell
git status --short
git diff --name-only
```

커밋 대상에 포함하면 안 되는 것:

```text
auction_data.db
storage/backups/*
storage/logs/*
raw payload dump
API key 포함 파일
.env
```

커밋 메시지 예시:

```text
feat: improve onbid data source status quality v009
```

푸시:

```powershell
git push -u origin codex/devpack-v009-onbid-data-source-status-quality
```

---

## 20. 최종 주의

이번 작업은 “기능 추가”보다 “서비스 신뢰성 복구”가 우선이다.

특히 다음 3개는 반드시 해결하거나, 해결 불가 사유를 투명하게 기록한다.

1. 마감된 물건이 진행 중처럼 보이는 문제
2. 원문 링크가 대부분 없는 문제
3. 공개 데이터 수량과 활성 데이터 부족 문제

서비스의 정체성은 계속 유지한다.

**우리는 경·공매 투자 판단 플랫폼이 아니라, 경·공매 후보를 빠르게 거르고 기록하게 만드는 무료 기반 검토 보조 플랫폼이다.**
