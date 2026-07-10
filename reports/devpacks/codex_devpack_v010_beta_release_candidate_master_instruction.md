# Codex Devpack v010 마스터 작업지시서
## 베타 릴리스 후보(Beta RC) UI/UX·핵심 사용자 흐름·운영 안정성 완성

작성일: 2026-07-10 KST  
대상 저장소: `feastJ-h/court_auction_platform`  
기준 브랜치: `codex/devpack-v009-onbid-data-source-status-quality`  
작업 브랜치: `codex/devpack-v010-beta-release-candidate-ux`  
결과서 경로: `reports/devpacks/devpack_v010_beta_release_candidate_result_bundle.md`

---

# 0. 이번 작업의 성격

이번 devpack은 신규 아이디어를 넓게 추가하는 작업이 아니다.

현재 서비스는 v009를 통해 다음 기반을 확보했다.

- public-visible fresh non-sample ONBID 약 1,076건
- active/upcoming 약 1,016건
- 부동산 약 516건
- 동산 약 560건
- 마감 상태 KST 보정
- 상세 자료 완결성 표현 정리
- 원문 URL 부재 시 직접 확인 정보 제공
- 관리자 데이터 품질 화면
- 기본 pytest 정책 분리

데이터 수량은 베타 UI를 검증하기에 충분하다.  
이번 작업에서는 무리한 추가 대량 수집보다 **사용자가 실제로 탐색·소거·저장·재방문할 수 있는 제품 완성도**를 우선한다.

이번 devpack의 최종 목표는 다음과 같다.

> 외부 베타 사용자 30~50명이 별도 설명 없이 홈 → 온비드 목록 → 카테고리 선택 → 필터 → 상세 → 관심/패스/메모 → 내 검토함 흐름을 사용할 수 있는 베타 릴리스 후보를 만든다.

서비스의 정체성은 계속 유지한다.

> 우리는 경·공매 투자 판단 플랫폼이 아니라, 경·공매 후보를 빠르게 거르고 기록하게 만드는 무료 기반 검토 보조 플랫폼이다.

---

# 1. 현재 사이트 기준 핵심 문제

현재 외부 리뷰 사이트:

```text
https://glen-county-cnet-trunk.trycloudflare.com
```

현재 상태에서 다음 문제를 확인했다.

## 1.1 카테고리 탐색 구조

- `전체 / 부동산 / 동산 / 국유일반재산 / 기타` 탭이 필터 폼 내부의 하단에 위치한다.
- 동일한 카테고리가 상단 `<select>`와 하단 탭으로 중복 제공된다.
- 사용자는 카테고리를 선택하기 전에 지역·자료 상태·가격 입력 폼을 먼저 마주한다.
- 서비스의 핵심 분류보다 보조 필터가 더 앞에 보인다.
- 탭 count가 현재 필터 조건과 관계없는 전체 count로 보일 가능성이 있다.

## 1.2 페이지네이션

- 전체 목록에서 1~54페이지가 한 번에 모두 노출된다.
- 부동산 목록에서도 1~26페이지가 전부 노출된다.
- 모바일에서는 페이지 번호가 여러 줄로 감기며 화면을 과도하게 차지할 수 있다.
- 페이지 링크 생성 시 일부 쿼리 상태만 보존하고, 정렬·마감 조건 등 전체 필터 상태를 잃을 가능성이 있다.
- 현재 구조는 “소거형 검토 보드”보다 오래된 검색 결과 페이지처럼 느껴진다.

## 1.3 카드 정보 밀도

- 카드마다 `원문 링크 확인 필요`가 배지와 액션 영역에서 반복된다.
- 비로그인 사용자에게 `로그인 후 관심/패스`가 모든 카드에 반복된다.
- 로그인 사용자가 목록에서 바로 패스할 수 있는 핵심 소거 UX가 충분히 드러나지 않는다.
- 가격·감정가·마감·상태·자료 부족 정보의 시각적 우선순위가 균일하지 않다.

## 1.4 홈과 오늘 보기의 편중

- 홈 최근 공개 목록이 같은 기관·같은 공고의 유사 물건들로 채워질 수 있다.
- 오늘 보기 20건도 한 공고 또는 한 기관 물건으로 편중될 수 있다.
- 오늘 보기 코드가 실제 오늘 신규 항목이 없을 때 최근 20건으로 조용히 대체될 수 있어 “오늘 신규” 의미가 불명확해질 수 있다.
- 홈의 `오늘 새로 확인된 물건` count가 실제 오늘 최초 수집 건수인지, 현재 활성 건수인지 사용자에게 명확하지 않다.

## 1.5 베타 서비스 표현

- 공개 상단에 `리뷰 모드가 활성화되어 있습니다. 관리자 수정, 실 API 동기화, 개인화 저장은 임시로 비활성화됩니다.`라는 내부 운영 문구가 노출된다.
- 베타 사용자에게는 필요한 안내보다 내부 시스템 상태 설명이 먼저 보인다.
- 현재 review mode에서는 개인화 저장이 막혀 있어 실제 베타 사용자 흐름을 검증하기 어렵다.

## 1.6 테스트와 운영 신뢰

- v009의 `python -m pytest`는 기본 제품 테스트 2건만 수집했다.
- 다수의 핵심 테스트는 별도 script-style 명령으로 실행된다.
- “pytest PASS”만으로 전체 제품 회귀 검증이 되었다고 보기 어렵다.
- 이용약관 화면에는 v005 베타 초안 문구와 과거 기준일이 남아 있다.
- 각 템플릿이 Tailwind CDN과 전체 HTML 구조를 반복하며 일관된 레이아웃 관리가 어렵다.

---

# 2. 자율 실행 권한과 작업 원칙

사용자는 이번 devpack의 정상적인 개발·검증 작업에 대해 별도 확인을 요구하지 않는다.

Codex는 아래 허용 범위에서는 사용자에게 동의를 다시 묻지 말고 계속 진행한다.

## 2.1 별도 확인 없이 허용

- Git fetch/pull/status/log/diff
- 새 작업 브랜치 생성
- 코드·템플릿·테스트·문서 수정
- 비파괴 DB 마이그레이션
- 작업 전 DB 백업
- Python/Node 테스트 패키지 설치
- Playwright 브라우저 설치
- 네트워크 접근
- 공식 ONBID 페이지 또는 공식 문서의 소량 검증
- 제한적 ONBID 증분 동기화
- 로컬 서버 실행
- Cloudflare quick tunnel 실행
- 로컬·외부 route QA
- Playwright screenshot 생성
- Lighthouse 또는 동등한 품질 점검
- 작업 브랜치 commit/push
- 실패한 테스트의 원인 분석과 재수정
- 구현 → 테스트 → 외부 검증 → 재수정 반복

## 2.2 진행 중 판단 규칙

- 비파괴적이고 범위 내인 선택은 Codex가 보수적으로 결정한다.
- 사소한 UI 선택이나 파일 구조 선택을 사용자에게 질문하지 않는다.
- 특정 패키지나 도구가 실패하면 대체 가능한 도구로 전환한다.
- 외부 자격증명이나 DNS 권한이 없어 진행이 막히면, 안전한 fallback과 실행 스크립트·runbook을 만들고 나머지 작업을 계속한다.
- 일부 목표가 공식 데이터 한계 때문에 불가능하면 가짜 데이터를 만들지 말고, 안전한 대안 UX를 구현한 뒤 결과서에 기록한다.
- 테스트가 실패하면 결과서만 작성하고 끝내지 말고, 원인을 수정한 뒤 다시 실행한다.
- 최소 2회의 전체 개발·검증 루프를 완료한다.

---

# 3. 절대 개발하면 안 되는 항목

아래 항목은 사용자 확인 없이 개발하거나 실행하면 안 된다.

## 3.1 Git·배포·데이터

- `main` 직접 작업 또는 직접 push
- production 배포
- 운영 DNS 변경
- 기존 사용자 데이터 대량 삭제
- 파괴적 DB migration
- 백업 없는 DB 구조 변경
- DB, backup, runtime log, `.env` 커밋
- API key, secret, session token 출력
- raw ONBID payload 전체 저장 또는 커밋
- 원문 파일, OCR 전체문, 내부 경로 공개
- Git history 강제 재작성
- 다른 작업 브랜치 삭제

## 3.2 제품 범위

- AI 권리분석
- 안전/위험 판정
- 추천 물건
- 수익성 평가
- 예상 낙찰가
- 추천 입찰가
- 명도 가능성 판단
- 전문가 추천·검증·매칭
- 결제, Pro 결제, Team 결제
- 광고 네트워크 실제 적용
- 전문가 마켓플레이스
- Archi-Pro 실제 API 연동
- Development Insight 실제 수익 계산
- 사용자 행동 데이터 외부 판매
- 프로그래매틱 SEO 대량 페이지 생성
- FOMO·경쟁자 수·놓치면 손해 등의 다크패턴
- 비공식 크롤링 우회
- 국유일반재산 가짜 fixture 공개
- 검증되지 않은 ONBID 상세 URL 패턴 사용

## 3.3 표현 금지

다음 표현을 public-facing UI에 추가하지 않는다.

```text
AI 분석
권리분석
안전
위험
추천
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
투자 기회
돈 되는 물건
완벽한 분석
```

---

# 4. 시작 절차

## 4.1 Git 확인

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -10
```

기준 브랜치 동기화 후 작업 브랜치를 만든다.

```powershell
git checkout codex/devpack-v009-onbid-data-source-status-quality
git pull --ff-only origin codex/devpack-v009-onbid-data-source-status-quality
git checkout -b codex/devpack-v010-beta-release-candidate-ux
```

브랜치가 이미 존재하면 현재 상태를 확인하고 이어서 진행한다.

## 4.2 작업 전 백업

DB 변경 여부와 관계없이 베타 devpack 시작점 백업을 만든다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

결과서에 기록:

- source DB
- backup 경로
- SHA-256
- 백업 시각
- restore 실행 여부

## 4.3 베이스라인 캡처

변경 전 아래 화면을 desktop/mobile 크기로 캡처한다.

- `/`
- `/onbid`
- `/onbid?category=real_estate`
- `/onbid?category=movable`
- `/onbid/today`
- real_estate 상세 1건
- movable 상세 1건
- `/my/onbid/favorites` 로그인 상태
- `/cases`

권장 viewport:

```text
390 × 844
768 × 1024
1440 × 900
```

스크린샷은 QA 자료로 사용하되 민감 데이터나 세션 쿠키를 커밋하지 않는다.

---

# 5. P0-1: 온비드 카테고리 탭을 최상위 탐색으로 이동

사용자 요청의 최우선 항목이다.

## 5.1 화면 정보 계층

ONBID 목록의 순서를 다음으로 변경한다.

1. 전역 헤더
2. breadcrumb
3. 페이지 제목과 짧은 설명
4. **카테고리 탭**
5. 오늘 보기 / 내 검토함 / 자료 확인 필요 quick actions
6. compact filter bar
7. active filter chips + 결과 수 + 정렬
8. 물건 목록
9. compact pagination

현재 필터 폼 내부 하단에 있는 카테고리 탭을 제거하고 제목 바로 아래로 이동한다.

## 5.2 탭 구성

기본 탭:

```text
전체
부동산
동산
국유일반재산
```

`기타`는 count가 1건 이상일 때만 노출하거나 보조 탭으로 둔다.

각 탭에는 count를 표시한다.

예시:

```text
전체 1,076
부동산 516
동산 560
국유일반재산 0
```

## 5.3 중복 제거

- 필터 폼의 category `<select>`를 제거한다.
- 카테고리 선택 수단은 기본적으로 탭 한 곳으로 통일한다.
- 모바일에서도 별도 select를 중복 제공하지 않고 가로 스크롤 탭을 사용한다.
- 탭은 한 페이지에 한 번만 렌더링한다.

## 5.4 데스크톱 UI

- 제목 바로 아래 충분히 큰 segmented tabs 형태
- 현재 탭은 진한 배경과 `aria-current="page"`
- hover/focus 상태 제공
- 탭 영역은 긴 목록을 스크롤할 때 상단에 sticky 처리할 수 있다.
- sticky 적용 시 전역 nav와 겹치지 않게 높이와 z-index를 검증한다.

## 5.5 모바일 UI

- 한 줄 가로 스크롤
- 스크롤바는 과도하게 강조하지 않는다.
- 각 탭 touch target 최소 44px
- 선택된 탭이 화면 안에 보이도록 한다.
- 페이지 전체에 horizontal overflow가 생기면 안 된다.

## 5.6 count 의미

가능하면 category count를 단순 전체 count가 아니라 **현재 category 이외의 필터가 적용된 faceted count**로 계산한다.

예:

- 지역=서울
- 가격=1억 이하

이 조건에서 탭 count는 해당 조건을 만족하는 전체/부동산/동산 수를 보여준다.

구현 부담이 크면 v010에서는 global count를 유지하되 `전체 공개 기준`이라는 설명을 명확히 표시한다.  
잘못된 faceted count를 만드는 것보다 명시된 global count가 낫다.

## 5.7 필수 테스트

```text
tests/onbid_category_tabs_top_position_test.py
tests/onbid_category_single_control_test.py
tests/onbid_category_tab_state_preservation_test.py
tests/onbid_category_tabs_mobile_overflow_test.py
tests/onbid_category_zero_empty_state_test.py
```

성공 기준:

- 탭이 filter form보다 먼저 렌더링된다.
- category select가 중복 노출되지 않는다.
- 선택 상태가 명확하다.
- category 변경 시 region/price/data quality/sort가 보존된다.
- page는 1로 초기화된다.
- 국유일반재산 0건에서 정확한 empty state가 보인다.

---

# 6. P0-2: 페이지네이션 축약 및 쿼리 상태 보존

## 6.1 데스크톱 페이지네이션

54개 번호를 모두 노출하지 않는다.

권장 예시:

```text
이전  1  …  25  26  [27]  28  29  …  54  다음
```

다음 규칙을 따른다.

- 첫 페이지
- 현재 페이지 기준 앞뒤 2페이지
- 마지막 페이지
- 중간 구간은 ellipsis
- 이전/다음
- 현재 페이지는 `aria-current="page"`
- 비활성 이전/다음은 링크가 아니라 disabled 상태
- 페이지가 7개 이하일 때는 전체 표시 가능

한 화면에 표시되는 숫자/ellipsis를 과도하게 늘리지 않는다.

## 6.2 모바일 페이지네이션

모바일에서는 숫자 목록을 나열하지 않는다.

```text
이전    27 / 54    다음
```

필요하면 `처음`과 `마지막`은 접근성 메뉴나 보조 링크로 제공하되 한 줄을 유지한다.

## 6.3 결과 범위 표시

목록 상단에 다음 형식의 정보를 표시한다.

```text
총 1,076건 · 1–20번째 표시 · 마감 임박순
```

카테고리 선택 시:

```text
동산 560건 · 1–20번째 표시
```

## 6.4 모든 필터 상태 보존

페이지 링크, 이전/다음, 카테고리 탭, 가격 preset, sort 링크에서 다음 상태를 보존한다.

```text
region
category
data_quality
price_min
price_max
closing_within_days
sort
q/keyword
status
agency
usage
has_notice
has_detail
```

필터나 sort가 변경되면 page는 1로 리셋한다.

현재 pagination이 일부 query만 전달하는 구조라면 공통 `query_state` 또는 `build_query_href()` 개선으로 중복을 제거한다.

## 6.5 shared component

ONBID와 회생·파산 목록에서 사용할 공통 pagination partial 또는 helper를 만든다.

권장 파일 예:

```text
frontend/templates/shared/pagination.html
backend/web/pagination.py
```

기존 route 동작을 깨지 않는 범위에서 구현한다.

## 6.6 필수 테스트

```text
tests/pagination_window_algorithm_test.py
tests/onbid_pagination_compact_markup_test.py
tests/onbid_pagination_preserves_all_filters_test.py
tests/onbid_pagination_mobile_shape_test.py
tests/cases_pagination_compact_markup_test.py
tests/pagination_invalid_page_clamp_test.py
```

필수 케이스:

- 1/54
- 2/54
- 27/54
- 53/54
- 54/54
- 전체 1페이지
- 전체 7페이지
- 잘못된 음수/문자/page 초과
- category+region+price+sort 동시 적용 후 page 이동

---

# 7. P0-3: 목록 필터와 결과 헤더 정리

## 7.1 quick actions

카테고리 탭 아래 quick actions:

```text
오늘 보기
내 검토함
자료 확인 필요
```

이 영역은 카테고리 탭보다 시각적으로 한 단계 낮게 보이게 한다.

## 7.2 필터 구조

공개 필터는 복잡해지지 않게 유지한다.

기본 노출:

- 지역
- 가격
- 자료 상태
- 정렬

정렬 옵션:

```text
마감 임박순
최근 수집순
가격 낮은 순
가격 높은 순
```

정렬은 추천이나 투자성 평가가 아니라 객관적 배열임을 유지한다.

## 7.3 가격 필터

현재 최소가/최대가 입력과 preset을 동시에 모두 강조하지 않는다.

권장:

- preset chips를 기본 노출
- `직접 입력`을 누르면 최소/최대 입력 표시
- 모바일에서는 필터 drawer 또는 접힘 영역
- 적용된 가격 조건은 active filter chip으로 표시

## 7.4 active filter chips

적용된 필터를 결과 상단에 명확히 표시한다.

예:

```text
서울 ×
1억 이하 ×
자료 확인 필요 ×
전체 초기화
```

각 chip 삭제 시 다른 필터는 유지하고 page만 1로 리셋한다.

## 7.5 모바일 filter drawer

모바일에서 필터 폼이 세로로 길게 화면을 차지하지 않게 한다.

- `필터` 버튼
- 현재 적용 개수 표시
- 열렸을 때 region/price/data state/sort 제공
- 적용/초기화 버튼
- keyboard focus 관리
- ESC 또는 닫기 지원
- JS가 실패해도 일반 form submit으로 동작하는 progressive enhancement

## 7.6 접근성

- placeholder만 사용하지 말고 label 제공
- select/input에 연결된 `<label>`
- focus ring
- form error text
- 가격 숫자 입력에 적절한 inputmode
- 필터 적용 결과를 live region으로 과도하지 않게 안내

---

# 8. P0-4: 목록 카드 정보 우선순위 개선

## 8.1 데스크톱 카드 계층

다음 순서가 한눈에 보여야 한다.

1. 유형 / 상태 / D-day
2. 물건명
3. 지역과 기관 또는 관리번호
4. 최저입찰가 / 감정가
5. 마감일
6. 자료 완결성 요약
7. 관심 / 패스 / 상세

## 8.2 반복 문구 감소

`원문 링크 확인 필요`를 같은 카드 안에서 여러 번 반복하지 않는다.

원문 URL이 없을 때:

- 카드 상단에 작은 `원문 경로 확인 필요` 상태를 한 번만 표시하거나
- 액션 영역에 `상세에서 확인 방법 보기`를 제공한다.

disabled 버튼처럼 보이는 큰 박스를 매 카드마다 반복하지 않는다.

원문 URL이 있을 때만 `원문 보기`를 명확한 외부 링크로 제공한다.

## 8.3 자료 부족 표현

카드에는 최대 1개의 요약 배지만 표시한다.

```text
자료 일부 확인 필요
```

세부 부족 항목은 상세에서 확인한다.

가격과 소재지가 모두 없는 경우처럼 사용자 검토에 중요한 경우만 보조 텍스트로 표시한다.

## 8.4 비로그인 액션

모든 카드마다 큰 `로그인 후 관심/패스` 버튼을 반복하지 않는다.

권장 구조:

- 상세 보기: 기본 액션
- 로그인 후 저장: 작은 보조 액션
- 목록 상단 또는 첫 카드 부근에 개인화 안내 1회

## 8.5 로그인 액션

로그인 사용자에게 목록 카드에서 다음을 직접 제공한다.

```text
관심
패스
상세
```

패스는 서비스 핵심 액션이므로 관심보다 숨겨지면 안 된다.

## 8.6 카드 클릭 영역

- 물건명은 상세 링크
- 카드 전체를 링크로 만들지 않는다.
- 버튼과 링크 클릭 영역 충돌 방지
- 모바일 touch target 검증

---

# 9. P0-5: 패스 → 카드 제거 → 5초 실행취소

현재 서비스 헌법에 명시된 핵심 UX를 베타에서 실제로 완성한다.

## 9.1 동작

로그인 사용자가 목록 또는 오늘 보기에서 `패스`를 누르면:

1. 카드가 즉시 시각적으로 사라진다.
2. `기본 목록에서 숨겼습니다` 토스트가 나타난다.
3. 토스트에 `실행 취소` 버튼을 표시한다.
4. 토스트는 5초간 유지한다.
5. 실행 취소 시 패스 상태를 되돌리고 카드를 원래 위치에 복원한다.
6. 취소하지 않으면 패스 상태를 유지한다.
7. 패스함에서 복구할 수 있다.

## 9.2 안전성

- 삭제가 아니라 user preference 상태만 변경한다.
- 서버 응답 실패 시 카드를 복원하고 오류 안내한다.
- JS가 비활성화되어도 기존 POST/redirect 방식으로 동작한다.
- CSRF 보호를 유지한다.
- 중복 클릭 방지
- 토스트는 `aria-live="polite"`
- 여러 개를 연속 패스했을 때 토스트 충돌 정책을 정의한다.

## 9.3 관심 동작

관심은 카드가 사라지지 않는다.

- 버튼 상태 변경
- `관심에 저장했습니다`
- 다시 누르면 해제 가능
- 관심 저장 후 내 검토함 링크 제공 가능

## 9.4 테스트

```text
tests/onbid_pass_undo_api_test.py
tests/onbid_pass_undo_ui_contract_test.py
tests/onbid_pass_is_not_delete_test.py
tests/onbid_preference_progressive_fallback_test.py
tests/onbid_preference_csrf_test.py
```

Playwright E2E:

- 로그인
- 목록에서 패스
- 카드 사라짐
- 5초 내 실행취소
- 카드 복원
- 다시 패스
- 내 검토함의 패스함에서 확인
- 복구

---

# 10. P0-6: 오늘 보기의 의미와 편중 문제 수정

## 10.1 “오늘” 기준 명확화

현재 `freshness_date == date.today()`가 실제 최초 수집일인지 확인한다.

오늘 신규 기준은 가능한 경우 다음을 사용한다.

1. `first_seen_at` 또는 최초 DB insert 시각
2. 명확한 수집 등록일
3. 위 값이 없다면 조용히 최근 20건으로 대체하지 않는다.

## 10.2 fallback 금지 또는 명시

오늘 신규가 0건인 경우:

```text
오늘 새로 수집된 항목이 없습니다.
최근 수집 항목 보기
```

최근 항목을 보여주려면 별도 섹션과 정확한 라벨을 쓴다.

```text
최근 수집 기준 · 2026-07-09
```

`오늘 보기` 화면에서 최근 항목을 오늘 신규처럼 보이게 하면 안 된다.

## 10.3 queue 크기

- 기본 queue는 20건
- 오늘 신규가 20건을 넘으면 `오늘 신규 N건 중 우선 20건`을 표시
- 로그인 사용자는 남은 미검토 항목을 이어서 볼 수 있다.
- 완료 상태는 실제 queue를 관심/패스로 분류했을 때만 표시한다.

## 10.4 다양성

홈 preview와 오늘 보기 queue가 하나의 공고 또는 기관으로 채워지지 않게 한다.

권장 selection 규칙:

- 같은 공고 최대 3건
- 같은 기관 최대 6~8건
- 부동산과 동산이 모두 있으면 가능한 범위에서 혼합
- 마감 임박과 최근 수집을 균형 있게 구성
- 데이터 자체를 삭제하거나 합치지 않고 표시 selection에만 적용

공고/기관 식별자가 불안정하면 무리한 grouping을 하지 말고, 제목·기관·공고번호 기준의 보수적 diversity cap만 적용한다.

## 10.5 오늘 보기 UI

- 상단 summary는 로그인 사용자에게 의미 있게 표시
- 비로그인은 `패스 0 / 관심 0` 같은 개인 상태 통계를 과도하게 강조하지 않는다.
- 비로그인은 서비스 사용법과 로그인 이점을 짧게 안내
- 로그인 상태에서는 남은 검토 수를 가장 강조
- 완료 화면은 차분하게 유지

## 10.6 테스트

```text
tests/onbid_today_truthful_queue_basis_test.py
tests/onbid_today_no_silent_recent_fallback_test.py
tests/onbid_today_diversity_cap_test.py
tests/onbid_today_logged_out_summary_test.py
tests/onbid_today_completion_real_queue_test.py
```

---

# 11. P0-7: 홈 화면을 베타 진입점으로 정리

## 11.1 카드 count 의미 수정

4개 카드의 count와 설명이 실제 query와 정확히 일치해야 한다.

권장:

1. 오늘 새로 수집된 물건
2. 7일 이내 마감
3. 서울·수도권 신규
4. 가격 확인된 1억 이하

`오늘 새로 확인된 물건`이 active 전체 count라면 명칭을 `현재 검토 가능한 물건`으로 바꾼다.

실제 오늘 count를 표시할 수 있으면 그 count를 사용한다.

## 11.2 최근 공개 preview

현재 같은 공고의 유사 물건이 4개 연속 보이는 문제를 줄인다.

- 최대 1건 또는 2건/공고
- 가능한 경우 부동산 2건 + 동산 2건
- 지역 다양성
- 마감일 다양성
- “추천”이 아니라 단순 최신·다양화 selection임을 유지

## 11.3 첫 방문 안내

강제 modal을 사용하지 않는다.

홈 또는 ONBID 목록에 짧은 3단계 안내를 제공한다.

```text
1. 오늘 후보를 확인합니다.
2. 관심 없는 후보는 패스합니다.
3. 남은 후보는 원문에서 다시 확인합니다.
```

`패스는 삭제가 아니라 기본 목록 숨김`임을 설명한다.

## 11.4 product name

현재 `Court Auction Platform` 영문 표기는 임시 제품명으로 중앙화한다.

- public title에 한국어 설명을 함께 사용
- 이름 변경이 쉽도록 settings 또는 shared component로 관리
- 임의의 새로운 상표명을 확정하지 않는다.

---

# 12. P1: 상세 화면 모바일·행동 구조 개선

## 12.1 상단 source zone

- 원문 URL 있으면 원문 보기
- 원문 URL 없으면 온비드 공식 사이트에서 직접 확인할 번호와 copy 버튼
- 공식 ONBID 홈페이지 링크는 공식 도메인을 검증한 뒤 제공
- 검증되지 않은 물건 상세 URL을 조합하지 않는다.

## 12.2 copy 기능

원문 URL이 없을 때 복사 가능 항목:

- 온비드 번호
- 공매 번호
- 물건명

복사 후:

```text
온비드 번호를 복사했습니다.
```

analytics에는 전체 문자열이나 URL을 저장하지 않는다.

## 12.3 모바일 action bar

모바일 상세에서 개인 액션이 페이지 최하단에만 묻히지 않게 한다.

로그인:

```text
관심
패스
메모
```

비로그인:

```text
로그인 후 저장
```

원문 링크가 있을 때만 원문 버튼을 포함한다.

sticky bottom action bar 사용 시 본문을 가리거나 브라우저 safe area와 충돌하지 않게 한다.

## 12.4 Development Insight

- real_estate에만 유지
- 화면 최우선 액션으로 올리지 않는다.
- 원문 확인과 개인 정리보다 아래에 둔다.
- 실제 계산/API 연동은 하지 않는다.
- 면책 문구 유지

---

# 13. P1: 내 검토함 베타 완성

로그인 후 핵심 화면을 다음 탭으로 정리한다.

```text
관심
감시
메모
패스
공유
```

## 13.1 요구사항

- 각 탭 count
- empty state
- 정렬: 최근 저장 / 마감 임박
- 패스 복구
- 관심 해제
- 감시 해제
- 메모 수정
- 공유 요약 revoke
- 종료된 항목 표시
- 원문 링크 유무 표시
- private memo public 노출 금지

## 13.2 로그인 전환

비로그인 사용자가 관심/패스를 시도하면:

- 로그인으로 이동
- `next` 경로 보존
- 로그인 후 원래 상세 또는 목록으로 복귀
- 가능하면 사용자가 시도한 액션을 다시 안내
- 오픈 리다이렉트 방지

## 13.3 베타 테스트 계정

실제 비밀번호나 계정을 코드/결과서에 남기지 않는다.

환경변수 또는 테스트 fixture로 로그인 E2E를 수행한다.

---

# 14. P1: 전역 헤더·베타 배너·푸터

## 14.1 review mode와 beta mode 분리

현재 내부 운영 문구를 공개 베타 사용자에게 그대로 노출하지 않는다.

권장 상태:

### Review Mode

- noindex/noarchive
- 관리자 변경 제한
- 개인화 제한 가능
- 내부 테스트용 기술 문구
- 외부 일반 사용자에게 장기 노출하지 않음

### Beta Mode

- compact 사용자 안내
- 로그인 개인화 허용
- 문제 제보 허용
- 관리자 기능은 권한 보호
- 필요하면 noindex 유지
- public banner 예시:

```text
베타 서비스 · 일부 자료는 누락되거나 변경될 수 있습니다. 최종 확인은 원문에서 진행하세요.
```

내부 API 동기화/관리자 제한 설명은 관리자에게만 표시한다.

## 14.2 헤더

- 브랜드/서비스명
- 홈
- 온비드
- 회생·파산
- 로그인 또는 내 검토함
- active state
- 모바일 한 줄 또는 간단한 메뉴
- 링크 wrapping으로 레이아웃이 깨지지 않게 함
- skip to content 링크

## 14.3 푸터

모든 public page에 공통 푸터:

```text
서비스 소개
이용약관
개인정보 처리방침
면책사항
데이터 출처
오류 제보
마지막 업데이트
```

운영자 연락처나 회사 정보가 확정되지 않았으면 임의로 만들지 않는다.  
확정되지 않은 필드는 `준비 중` 또는 설정값으로 둔다.

## 14.4 법적 고지 문서

현재 v005 초안 문구를 베타 기준으로 정리한다.

- 기준일 갱신
- 서비스 제공 범위
- 공개 데이터 출처
- 자료 지연·누락 가능성
- 투자·법률 자문 아님
- 사용자 메모와 공유 기능
- 오류 제보 처리
- 개인정보 최소 수집
- 로그/analytics 범위
- 광고가 아직 없으면 광고 조항을 과도하게 넣지 않음

법적 완전성을 보장한다고 표현하지 않는다.

---

# 15. P1: 회생·파산 화면 UI 일관성

회생·파산은 이번 devpack의 주력 기능 확장이 아니다.

다만 베타 전체 품질을 위해 다음은 적용한다.

- 공통 header/footer/layout
- compact pagination
- 모바일 overflow 방지
- category/filter label 접근성
- 상세 버튼과 원문 보기 우선순위
- 금지 표현 스캔
- no raw AI/OCR 공개
- 로그인 원문 확인 포인트 문구의 보수성 유지

ONBID 소거 UX를 회생·파산에 무리하게 복제하지 않는다.

---

# 16. P1: 디자인 시스템과 템플릿 구조

## 16.1 공통 layout

가능하면 다음 공통 구조를 만든다.

```text
frontend/templates/layouts/public.html
frontend/templates/shared/public_header.html
frontend/templates/shared/public_footer.html
frontend/templates/shared/pagination.html
frontend/templates/shared/onbid_category_tabs.html
frontend/templates/shared/filter_drawer.html
frontend/templates/shared/toast.html
```

모든 페이지를 무리하게 한 번에 재작성하지 말고 public 핵심 화면부터 적용한다.

## 16.2 Tailwind CDN

베타 안정성을 위해 다음 순서로 검토한다.

1. 현재 CDN 방식의 실제 성능과 CSP 문제 확인
2. 안전하면 로컬 static CSS build로 전환
3. 전환으로 작업 범위가 과도하게 커지거나 회귀가 생기면 v010에서는 공통 layout만 완료하고 전환 사유를 결과서에 기록

CDN을 제거하기 위해 UI 전체를 깨뜨리면 안 된다.

## 16.3 시각 원칙

- 지나치게 많은 색상 사용 금지
- zinc 기반 중립색 유지
- emerald: 주요 보조/성공
- amber: 자료 확인 필요
- blue: 일정/D-day
- red는 오류나 파괴 액션에만 제한
- border radius, spacing, button height 통일
- 텍스트 계층 명확화
- shadow 과도 사용 금지

---

# 17. P0: 데이터 품질과 증분 동기화

현재 1,000건 이상 확보되었으므로 목표 수량을 더 키우기 위한 무조건적 bulk fetch는 하지 않는다.

## 17.1 이번 devpack 데이터 원칙

- active/upcoming public-visible 수 유지
- 중복 0 유지
- stale/unknown 공개 차단
- sample/fixture 공개 0
- status conflict 공개 표시 0
- incremental sync 검증
- 마지막 업데이트 시각 제공
- 데이터가 오래되면 public 경고

## 17.2 원문 경로

v009에서 direct original URL coverage는 0%였다.

이번 작업에서:

- 공식 ONBID 상세/검색 URL 패턴을 공식 페이지와 소량 샘플로 검증
- exact detail URL이 검증되지 않으면 생성하지 않음
- 공식 ONBID 홈페이지 링크 + 번호 복사 fallback 개선
- 5~10개 sample에 대해 실제 사용자가 공식 사이트에서 찾을 수 있는지 수동 QA
- API key/query secret이 URL에 들어가지 않게 함

## 17.3 국유일반재산

- 0건을 숨기기 위해 stale 데이터를 공개하지 않는다.
- 탭은 유지하되 명확한 empty state 제공
- official API date normalization을 소량 검토할 수 있음
- 가짜 row 생성 금지

## 17.4 scheduled sync

기존 script를 기반으로 다음을 검증한다.

- 중복 실행 방지
- 실패 exit code
- API key 미출력
- summary log
- rate limit
- active date window
- 실패 후 기존 public 데이터 유지
- 관리자 last sync status
- scheduler registration rehearsal
- 실제 영구 scheduler 등록은 로컬 환경과 사용자 정책에 맞춰 비파괴적으로 진행하거나 runbook 제공

---

# 18. 베타 보안 필수 점검

외부 베타에 가까운 형태이므로 다음을 반드시 검증한다.

## 18.1 세션

- HttpOnly
- SameSite=Lax 또는 더 엄격한 적절한 값
- HTTPS 환경에서 Secure
- session expiration
- session fixation 방지
- logout 후 session 무효화

## 18.2 CSRF

다음 POST에 CSRF 적용 확인:

- 관심/패스/감시/메모
- 패스 undo
- 오류 제보
- 공유 생성/revoke
- 관리자 issue 상태 변경
- 관리자 sync
- Development Insight CTA가 상태 변경을 한다면 해당 POST

## 18.3 rate limit

최소 대상:

- 로그인
- 오류 제보
- 공유 생성
- 원문 redirect endpoint
- admin sync

## 18.4 보안 헤더

- Content-Security-Policy 검토
- X-Content-Type-Options
- Referrer-Policy
- frame-ancestors 또는 X-Frame-Options
- Permissions-Policy
- noindex review/beta 정책
- 공유 링크 noindex/noarchive 유지

## 18.5 오류 페이지

- 404
- 403
- 429
- 500

한국어 사용자 안내를 제공하고 내부 stack trace·경로·secret을 노출하지 않는다.

---

# 19. Analytics 정리

추가 이벤트:

```text
category_tab_click
filter_open
filter_apply
filter_clear
sort_change
pagination_click
view_item_detail
pass_item
undo_pass
favorite_item
unfavorite_item
view_original_fallback
copy_onbid_number
view_my_review
today_queue_complete
```

저장 금지:

- raw memo
- full URL
- API key
- 검색어에 포함될 수 있는 개인정보
- 상세 원문
- 사용자 입력 note 본문
- 세션 쿠키 원문

metadata는 item id, category, page, sort, boolean state 등 최소 정보만 저장한다.

analytics가 실패해도 사용자 액션은 성공해야 한다.

---

# 20. 접근성·반응형·성능 QA

## 20.1 필수 viewport

```text
360 × 800
390 × 844
768 × 1024
1024 × 768
1440 × 900
```

## 20.2 접근성 기준

- 키보드만으로 header, tabs, filter, cards, pagination 사용 가능
- visible focus
- semantic heading 순서
- form label
- button/link 역할 구분
- aria-current
- aria-live toast
- disabled state
- 색상만으로 상태 전달 금지
- touch target 44px 권장
- 가로 스크롤은 category tabs 내부만 허용
- 페이지 전체 horizontal overflow 0

## 20.3 자동 검사

가능하면 axe-core 또는 동등한 자동 검사를 실행한다.

필수 화면:

- 홈
- ONBID 전체
- ONBID category
- 오늘 보기
- 상세
- 로그인
- 내 검토함
- 회생·파산
- 법적 고지

critical/serious 접근성 위반은 0을 목표로 한다.

## 20.4 성능

가능하면 mobile Lighthouse:

```text
Performance >= 75
Accessibility >= 90
Best Practices >= 90
```

review/beta noindex 때문에 SEO 점수가 낮아지는 경우 그 이유를 별도 기록한다.

성능 저하 원인:

- Tailwind CDN
- 중복 script
- 큰 HTML pagination
- 불필요한 JS
- layout shift

를 점검한다.

---

# 21. 테스트 정책 개선

v009의 default pytest 2건만으로 베타 회귀 검증을 완료했다고 보지 않는다.

## 21.1 목표

- 기본 pytest가 실제 제품 테스트를 의미 있게 수집
- script-style 테스트도 단일 beta QA 명령으로 실행
- 외부 네트워크 테스트는 별도 marker
- 결과서에 테스트 개수와 이름을 투명하게 기록

## 21.2 pytest 설정

권장:

```ini
testpaths = tests
python_files = test_*.py *_test.py
markers =
    integration
    external
    visual
```

`backend/**/test_*.py`와 root 실통신 테스트가 기본 suite에 들어오지 않도록 testpaths/marker를 명시한다.

script-style 파일이 pytest 함수가 아니라면:

- 핵심 테스트는 pytest function으로 전환하거나
- adapter/wrapper test를 추가한다.

테스트를 삭제해 PASS를 만들지 않는다.

## 21.3 목표 수집량

기본:

```powershell
python -m pytest -m "not integration and not external and not visual"
```

최소 25개 이상의 의미 있는 제품 test case가 수집되도록 한다.

별도:

```powershell
python -m pytest -m integration
python -m pytest -m external
python -m pytest -m visual
```

외부 환경 때문에 실행하지 못한 suite는 이유를 기록한다.

## 21.4 beta QA runner

다음과 같은 단일 실행점을 만든다.

```text
run_beta_qa.ps1
```

포함:

1. py_compile
2. default pytest
3. legacy/script tests
4. banned copy scan
5. mojibake scan
6. route smoke
7. optional visual QA
8. sensitive staged-file scan

실패 시 non-zero exit code.

---

# 22. Playwright E2E 필수 시나리오

## 22.1 비로그인

1. 홈 접속
2. ONBID 이동
3. 카테고리 탭이 첫 viewport에 노출
4. 부동산 선택
5. 서울 + 1억 이하 적용
6. sort 변경
7. page 이동
8. 필터 유지 확인
9. 상세 이동
10. 원문 fallback 확인
11. 로그인 CTA 확인

## 22.2 로그인

1. 로그인
2. 오늘 보기
3. 관심 저장
4. 패스
5. 카드 제거
6. undo
7. 재패스
8. 내 검토함
9. 패스함 복구
10. 메모 작성/수정
11. 관심 해제
12. 로그아웃

## 22.3 모바일

- category tab horizontal scroll
- filter drawer
- compact pagination
- card button touch
- detail action bar
- no body overflow
- toast undo

## 22.4 관리자

- 비로그인 admin route 보호
- 일반 user admin 접근 차단
- issue queue
- data quality dashboard
- product analytics
- sync control CSRF/rate limit
- public에 관리자 정보 미노출

---

# 23. 개발·검증 반복 루프

최소 2회, 필요 시 3회 수행한다.

## Loop 1: 구조 개선

1. baseline screenshot
2. category tabs 이동
3. pagination window 구현
4. filter/query state 정리
5. list card 정리
6. unit tests
7. local smoke
8. 모바일 screenshot

## Loop 2: 핵심 행동 완성

1. pass/undo
2. today semantics
3. home diversity
4. my review flow
5. beta banner/header/footer
6. legal copy update
7. security checks
8. Playwright E2E
9. Cloudflare external QA

## Loop 3: 부족분 수정

다음 중 하나라도 실패하면 추가 수정한다.

- category tabs가 필터 아래에 있음
- category control 중복
- 페이지 번호 전체 노출
- 모바일 pagination 줄바꿈
- filter state 손실
- pass undo 실패
- today silent fallback
- 홈 preview 동일 공고 편중
- body horizontal overflow
- critical accessibility issue
- default pytest 25개 미만
- beta QA runner 실패
- external route 500
- 금지 표현/mojibake 발견
- private memo/raw data 노출
- 로그인 후 next 복귀 실패

---

# 24. 로컬·외부 검증 경로

## 24.1 로컬

```text
/
 /onbid
 /onbid?category=real_estate
 /onbid?category=movable
 /onbid?category=national_property
 /onbid?region=서울&price_max=100000000&sort=closing_soon
 /onbid?category=real_estate&page=2
 /onbid/today
 /onbid/{real_estate_id}
 /onbid/{movable_id}
 /my/onbid/favorites
 /my/onbid/passed
 /my/onbid/notes
 /my/onbid/shared-summaries
 /cases
 /terms
 /privacy
 /disclaimer
 /admin/onbid-data-quality
 /admin/onbid-issue-reports
 /admin/product-analytics
```

실제 route 명칭이 다르면 현재 구조에 맞추되 결과서에 기록한다.

## 24.2 Cloudflare

외부 QA를 위해 quick tunnel을 실행한다.

```powershell
cloudflared.exe tunnel --url http://127.0.0.1:8000
```

가능하면 beta mode로 실행한다.

결과서에:

- 외부 URL
- beta/review mode
- route별 status
- desktop/mobile screenshot
- category tabs 위치
- pagination 모양
- pass/undo E2E
- 로그인 저장 여부
- original fallback
- noindex 상태
- process 종료 여부

를 기록한다.

## 24.3 고정 베타 URL

Cloudflare named tunnel 자격증명이 이미 있고 비파괴적으로 설정 가능하면 고정 staging/beta URL을 준비할 수 있다.

자격증명이 없으면:

- 사용자에게 질문하며 멈추지 않는다.
- named tunnel setup runbook을 작성한다.
- quick tunnel로 QA를 완료한다.
- DNS나 계정을 임의 생성하지 않는다.

---

# 25. Beta RC 성공 기준

## 25.1 ONBID 탐색

```text
카테고리 탭이 제목 바로 아래에 위치
category control 중복 0
탭 모바일 overflow 정상
현재 category 명확
국유일반재산 0건 empty state 정상
```

## 25.2 페이지네이션

```text
54개 번호 전체 노출 0
desktop windowed pagination
mobile 이전 / 현재-전체 / 다음
모든 filter/sort 상태 보존
ONBID와 cases 공통 적용
```

## 25.3 소거 UX

```text
로그인 목록에서 패스 가능
패스 후 카드 제거
5초 undo
패스는 삭제 아님
패스함 복구 가능
관심 저장 가능
메모 저장 가능
```

## 25.4 오늘 보기

```text
오늘 queue 기준 명확
silent recent fallback 0
완료 상태 실제 queue 기준
동일 공고 편중 제한
비로그인/로그인 상태 구분
```

## 25.5 베타 운영

```text
beta mode에서 개인화 저장 가능
public technical review banner 제거
header/footer/legal links
최신 기준일
마지막 데이터 업데이트 표시
404/403/429/500 사용자 안전
```

## 25.6 품질

```text
mojibake 0
금지 표현 0
body horizontal overflow 0
critical/serious accessibility issue 0 또는 명확한 미해결 사유
default product pytest >= 25 case PASS
run_beta_qa.ps1 PASS
Playwright core E2E PASS
Cloudflare external QA PASS
```

## 25.7 데이터/보안

```text
public active data 유지
duplicate key 0
sample exposure 0
stale/unknown 기본 공개 0
raw payload 노출 0
private memo 공유 노출 0
secret staged 0
CSRF/session/rate limit 검증
```

---

# 26. 결과 보고서 형식

결과 파일:

```text
reports/devpacks/devpack_v010_beta_release_candidate_result_bundle.md
```

반드시 포함:

1. 작업 메타데이터
2. 시작 Git 상태
3. 백업 정보
4. v009 carry-forward
5. 변경 전 라이브 UI audit
6. 화면별 변경 요약
7. category tabs 전/후
8. pagination 전/후
9. filter/query state 검증
10. card UX 변경
11. pass/undo 검증
12. today queue 기준 및 diversity
13. home count/preview 검증
14. 내 검토함 E2E
15. beta/review mode 분리
16. header/footer/legal 업데이트
17. security 점검
18. 데이터 sync/원문 fallback 점검
19. 접근성 결과
20. responsive viewport 결과
21. Lighthouse 또는 성능 결과
22. pytest 수집 수와 결과
23. script/legacy test 결과
24. Playwright E2E 결과
25. Cloudflare 외부 URL QA
26. 개인정보/secret/raw exposure 점검
27. 변경 파일 목록
28. 남은 리스크
29. 베타 오픈 가능/조건부 가능/불가 판정
30. 다음 devpack 추천
31. 종료 Git 상태
32. commit hash/push 결과

베타 판정은 과장하지 않는다.

```text
베타 오픈 가능
조건부 베타 오픈 가능
베타 오픈 보류
```

중 하나를 근거와 함께 선택한다.

---

# 27. 커밋·푸시

작업 중 논리적 checkpoint commit을 만들 수 있다.

권장 예:

```text
refactor: improve public list navigation and pagination
feat: add pass undo and beta review flow
test: add beta rc responsive and e2e coverage
docs: add v010 beta rc result bundle
```

최종 확인:

```powershell
git status --short
git diff --check
git diff --name-only
```

금지 파일 확인:

```text
.env
*.db
storage/backups/*
storage/logs/*
raw payload
screenshots containing secrets
session files
browser profile
API key files
```

푸시:

```powershell
git push -u origin codex/devpack-v010-beta-release-candidate-ux
```

`main`에는 merge하거나 push하지 않는다.

---

# 28. 최종 실행 지시

이번 devpack에서는 작업 중 일반적인 개발 선택을 사용자에게 묻지 않는다.

다음 순서로 끝까지 진행한다.

```text
분석
→ 백업
→ 구현
→ unit test
→ UI screenshot
→ Playwright E2E
→ 외부 Cloudflare 검증
→ 실패 항목 수정
→ 전체 재검증
→ 결과 보고서
→ 작업 브랜치 commit/push
```

작업 시간이 길어져도 기능을 반쯤 구현한 채 질문으로 종료하지 않는다.

안전하게 완료하지 못한 항목은:

1. 가능한 fallback 구현
2. 나머지 범위 계속 진행
3. 결과서에 정확한 원인과 재현 절차 기록

의 순서로 처리한다.

이번 devpack의 최우선 결과는 다음 두 가지다.

> 카테고리 탭과 필터 구조가 한눈에 이해되고, 54개 페이지 번호가 더 이상 화면을 점유하지 않는 것.

> 사용자가 실제로 후보를 패스하고 실행취소하며, 관심·메모·패스함으로 검토 흐름을 관리할 수 있는 것.
