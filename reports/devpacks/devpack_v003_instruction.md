# Codex 개발팩 v003 작업 지시서

## Public Beta Readiness Pack 1

- 작성일: 2026-07-06
- 대상 저장소: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- 원격 저장소: `https://github.com/feastJ-h/court_auction_platform.git`
- 기준 태그: `baseline-v002-20260706`
- 기준 커밋: `48f47c7 baseline after devpack v002`
- 작업 브랜치: `codex/devpack-v003-public-first-personalization`
- 지시서 위치: `reports/devpacks/devpack_v003_instruction.md`
- 최종 결과 bundle 위치: `reports/devpacks/devpack_v003_result_bundle.md`
- 최신 프로젝트 상태 문서: `reports/project-result_current.md`

이 개발팩은 단발성 작은 수정이 아니라 장시간 작업을 전제로 한 v003 통합 개발팩이다. 목표는 현재 내부 MVP 성격의 서비스를 **비로그인 공개 탐색 + 로그인 개인화 + 관리자 운영 유지** 구조로 전환하고, 베타 공개 준비에 필요한 최소 운영/문서/검증 기반을 함께 정리하는 것이다.

---

## 0. 최상위 목표

v003의 최상위 목표는 다음 한 문장으로 정의한다.

```text
로그인하지 않아도 온비드와 회생/파산 기본 정보를 편하게 볼 수 있게 만들고, 로그인하면 관심/패스/메모/회생·파산 AI 분석이 활성화되는 Public-first 베타 준비 구조로 전환한다.
```

서비스 원칙:

```text
Public-first:
  온비드 목록/상세와 회생·파산 기본 목록/상세는 로그인 없이 볼 수 있다.

Login-enhanced:
  로그인하면 관심, 패스, 감시, 메모, 회생·파산 AI 분석을 사용할 수 있다.

Admin-operated:
  관리자는 기존 수집, 분석, 품질, 사용자 관리 기능을 그대로 유지한다.
```

---

## 1. 작업 시작 전 필수 절차

### 1.1 Git 상태 확인

작업 시작 직후 아래 명령을 실행하고 결과를 최종 bundle에 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -5
```

정상 기대값:

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Branch: codex/devpack-v003-public-first-personalization
Remote: https://github.com/feastJ-h/court_auction_platform.git
Base: 48f47c7 또는 baseline-v002-20260706 이후 커밋
```

다음이면 기능 개발을 중단하고 result bundle에 기록한다.

- Git root가 예상 경로가 아니다.
- 현재 브랜치가 `main`이다.
- `git init`이 필요해 보인다.
- `.env`, DB, `storage/`, 로그, runtime 파일이 stage되어 있다.
- 작업 시작 전 사용자 변경분이 있어 덮어쓸 위험이 있다.

### 1.2 AGENTS.md 읽기

repo root의 `AGENTS.md`를 먼저 읽고 따른다. 지시서와 AGENTS.md가 충돌하면 이 v003 지시서가 우선한다. 보안/금지 규칙은 더 엄격한 쪽을 따른다.

### 1.3 작업 중 질문 기준

사소한 판단은 사용자에게 묻지 말고 이 지시서의 기준에 따라 진행한다.

다음 상황은 구현을 멈추지 말고 안전한 대안을 적용하거나 보류 처리 후 result bundle에 기록한다.

- 실제 API 키가 필요한 경우
- 실제 외부 네트워크 호출이 필요한 경우
- 파괴적 DB 변경이 필요한 경우
- 원문 파일/개인정보/AI 분석 노출 위험이 있는 경우
- 기존 테스트를 무력화해야만 진행 가능한 경우
- 국유일반재산 API 응답 필드가 불확실한 경우

---

## 2. 절대 금지 사항

- `git init` 실행 금지
- `main` 브랜치 직접 개발 금지
- `.git` 삭제 금지
- `git reset --hard`, `git clean -fd`, `git clean -fdx` 금지
- `.env`, `*.db`, `*.sqlite`, `storage/`, `logs/`, `runtime_settings.json` 커밋 금지
- DB/storage/raw documents 삭제 금지
- 내부 원문 파일 전체 공개 금지
- 회생/파산 AI 분석 비로그인 공개 금지
- 온비드 전체 물건 AI 분석 자동 적용 금지
- 회생/파산 사건과 온비드 물건 자동 강제 연결 금지
- 국유일반재산 API를 추측 필드로 완전 구현 금지
- Alembic 본격 전환 금지
- 실제 AdSense 송출 강제 금지
- 관리자 기능 대개편 금지
- 테스트 삭제/무력화 금지

---

## 3. 작업 범위 운영 방식

작업은 세 단계로 진행한다.

```text
Core Scope:
  반드시 완료해야 하는 v003 핵심 범위.

Extended Scope:
  Core Scope 완료 후 계속 진행해야 하는 확장 범위.

Stretch Scope:
  Core + Extended가 안정적으로 완료된 후 가능한 범위에서 진행하는 보강 범위.
```

진행 원칙:

- Core Scope 완료 전에는 Extended Scope로 넘어가지 않는다.
- Core Scope가 막히면 안전하게 보류하고 나머지 Core 항목을 진행한다.
- Extended/Stretch 항목은 완료, 부분 완료, 보류, 미진행을 result bundle에 명확히 구분한다.
- 중간 결과 문서를 여러 개 만들지 않는다.
- 최종 결과는 `reports/devpacks/devpack_v003_result_bundle.md` 하나에 통합한다.

---

# Core Scope

---

## 4. Core 1: 공개 온비드 목록/상세

### 4.1 목표

비로그인 사용자가 온비드 공매 물건 목록과 상세를 볼 수 있게 한다.

대표 공개 경로:

```text
GET /onbid
GET /onbid/{auction_item_id}
```

기존 경로:

```text
/auctions
/auctions/{auction_item_id}
```

처리 기준:

- `/onbid`를 공개 대표 경로로 만든다.
- 기존 `/auctions`는 가능하면 유지한다.
- 기존 템플릿 `frontend/templates/auctions/index.html`, `frontend/templates/auctions/detail.html`를 재사용하거나 public-friendly 구조로 개선한다.
- `/auctions`를 `/onbid`로 redirect할지 alias로 둘지는 기존 라우터 구조를 보고 안전한 쪽을 선택한다.
- 기존 링크가 깨지지 않도록 호환성을 유지한다.

### 4.2 비로그인 목록 표시 정보

온비드 목록에서 최소 표시할 정보:

```text
- 물건명
- 부동산/동산 구분
- 소재지
- 기관명
- 감정가
- 최저입찰가
- 할인율
- 입찰 시작일
- 입찰 마감일
- 마감 D-day
- 공고 연결 여부
- 상세 수집 여부
- 원문/온비드 링크 존재 여부
```

비로그인 상태에서도 이 정보는 볼 수 있다.

### 4.3 온비드 목록 UX

기본 UX 목표는 “많은 물건을 쏟아내기”가 아니라 “판단 가능한 물건을 먼저 보여주기”다.

기본 정렬 우선순위:

```text
1. 진행 중 또는 마감 임박
2. 상세 수집 있음
3. 공고 연결 있음
4. 가격/일정/소재지가 비어 있지 않음
5. 할인율 높은 물건
6. 신규 수집 물건
```

빠른 탭 또는 간단 필터:

```text
- 오늘/이번주 마감
- 신규 등록
- 할인율 높은 순
- 부동산
- 동산
- 공고 연결 있음
- 상세정보 있음
```

고급 필터 후보:

```text
- 검색어 q
- 지역/소재지
- 용도
- 기관명
- 가격대
- 입찰 마감일
- 할인율
- 부동산/동산 구분
- 공고 연결 여부
- 상세 수집 여부
```

구현 가능한 범위에서 Core에는 최소 빠른 탭/기본 필터를 넣고, 나머지는 Extended에서 보강한다.

### 4.4 비로그인 관심/패스 버튼

비로그인 목록/상세에도 관심/패스 버튼은 노출할 수 있다. 단, 클릭 시 저장하지 않고 로그인 안내를 제공한다.

문구 예시:

```text
로그인하면 관심 물건으로 저장할 수 있어요.
로그인하면 패스한 물건을 다음부터 숨길 수 있어요.
```

구현 방식:

- 서버 POST는 로그인 필요 상태를 반환한다.
- 화면은 로그인 모달, 안내 배너, 로그인 페이지 redirect 중 기존 UX와 가장 잘 맞는 방식을 선택한다.
- 비로그인 상태에서 DB에 preference를 저장하지 않는다.

---

## 5. Core 2: 공개 온비드 상세 + 공고/원문 링크

### 5.1 목표

온비드 상세 페이지에서 핵심 가격/일정/기관/공고/원문 정보를 명확히 보여준다.

상세 표시 정보:

```text
- 물건 기본 정보
- 가격 정보: 감정가, 최저입찰가, 보증금, 할인율
- 입찰 일정: 시작, 마감, 개찰
- 소재지
- 기관명
- 용도/분류
- 상세 설명/유의사항
- 연결된 공고 목록
- 공고 제목
- 공고 상태
- 공고 유형
- 입찰 방식
- 담당 부서
- 공고 원문 링크
- 온비드 원문 링크
```

### 5.2 공고 연결 표시

v002에서 추가된 구조를 활용한다.

```text
AuctionNotice
AuctionNoticeItemLink
AuctionItem
```

상세 페이지에 가능한 경우 표시한다.

```text
- 연결 공고
- 같은 공고에 묶인 다른 물건
- 공고 상세 payload 요약
```

공고 데이터가 없으면 조용히 숨긴다. 빈 카드나 깨진 UI를 만들지 않는다.

### 5.3 원문 링크 정책

공개 가능:

```text
- 외부 온비드 원문 URL
- 외부 법원/공고 원문 URL
```

공개 금지:

```text
- storage 내부 파일 경로
- /documents/raw/{raw_doc_id} 직접 다운로드
- OCR 추출 전문
- raw payload 전체
```

링크 태그에는 다음을 사용한다.

```html
target="_blank" rel="noopener noreferrer"
```

---

## 6. Core 3: 공개 회생/파산 목록/기본 상세

### 6.1 목표

비로그인 사용자가 회생/파산 목록과 기본 상세를 볼 수 있게 한다.

대표 공개 경로:

```text
GET /cases
GET /cases/{event_id}
```

기존 `backend/web/routers/cases.py` 구조를 확인하고, 기존 로그인 사용자 기능을 보존하면서 공개 GET 경로를 열어야 한다.

### 6.2 비로그인 공개 범위

비로그인 목록/상세에서 표시 가능:

```text
- 공고 제목
- 법원/기관
- 공고일
- 마감일
- 지역 또는 자산 분류
- 상태
- 외부 원문 링크
- 기본 설명 요약
```

비로그인에게 숨길 것:

```text
- AI 분석 결과
- AI 점수/위험도/환가 가능성 판단
- OCR 추출 전문
- 내부 저장 원문 파일
- 관리자 리뷰
- 사용자 메모
- 사용자별 관심/패스 저장 상태
- 분석 job 내부 상태
```

### 6.3 로그인 사용자 기존 기능 유지

로그인 사용자는 기존 회생/파산 기능을 계속 사용할 수 있어야 한다.

```text
- 관심
- 패스
- 감시
- 메모
- AI 분석 요약/상세 확인
```

기존 `UserEventAction`, `UserEventNote` 구조를 우선 재사용한다.

### 6.4 API/serializer 경계

템플릿에서만 숨기는 것은 부족하다.

- 비로그인 응답에서는 AI 분석 필드를 생성하지 않는다.
- API JSON이 있다면 비로그인 응답에 AI 분석/내부 경로가 포함되지 않게 한다.
- 공개 DTO/helper를 별도로 만들거나, 기존 serializer에 `viewer`/`is_authenticated` 분기를 명확히 둔다.

---

## 7. Core 4: 로그인 온비드 개인화

### 7.1 목표

로그인 사용자가 온비드 물건을 관심/패스/감시/메모로 관리할 수 있게 한다.

추천 신규 모델:

```text
UserAuctionPreference
- id
- user_id
- auction_item_id
- is_favorite
- is_passed
- is_watching
- note
- tags
- created_at
- updated_at
```

모델명은 기존 네이밍과 충돌하면 적절히 조정할 수 있다. 단, result bundle에 실제 명칭과 이유를 기록한다.

### 7.2 상태 정책

```text
관심을 켜면 패스는 자동 해제
패스를 켜면 관심과 감시는 자동 해제
감시는 관심과 함께 사용 가능
메모는 로그인 사용자만 작성 가능
한 사용자당 한 물건에 preference row 하나를 권장
```

### 7.3 서비스/라우터

권장 신규/확장 파일:

```text
backend/services/user_auction_preferences.py
backend/web/routers/auctions.py
frontend/templates/auctions/detail.html
frontend/templates/auctions/index.html
frontend/templates/user/*.html
```

권장 API/POST 후보:

```text
POST /onbid/{auction_item_id}/preference
POST /api/onbid/{auction_item_id}/preference
POST /onbid/{auction_item_id}/note
```

실제 경로는 기존 스타일을 보고 선택한다. 공개 GET은 열고, 상태 변경 POST는 로그인 필수로 둔다.

### 7.4 내 작업공간

로그인 사용자가 본인 관심/패스 목록을 관리할 수 있게 한다.

권장 경로:

```text
/my
/my/onbid/favorites
/my/onbid/passed
/my/cases/favorites
/my/cases/passed
```

기존 사용자 화면이 `/user` 중심이면 `/user` 경로를 유지하고 `/my`를 alias/redirect로 둘 수 있다. 기존 사용성을 깨지 않는 선택을 한다.

표시 대상:

```text
- 관심 온비드
- 패스한 온비드
- 메모한 온비드
- 관심 회생/파산
- 패스한 회생/파산
- AI 분석 확인 가능 회생/파산
```

---

## 8. Core 5: AI 분석 노출 경계

### 8.1 정책

```text
비로그인:
  회생/파산 AI 분석 미노출
  AI 분석 존재 여부 정도만 안내 가능
  예: "AI 분석은 로그인 후 확인할 수 있어요."

로그인:
  회생/파산 AI 분석 요약/상세 표시

관리자:
  분석 job, raw result, review, 재분석 기능 표시

온비드:
  AI 분석 자동 적용하지 않음
```

### 8.2 구현 요구사항

- 템플릿 조건 처리
- 라우터/serializer 조건 처리
- API 응답 필드 검증
- 테스트에서 비로그인 응답에 AI 분석 키워드/필드가 없는지 확인

금지:

- CSS로만 숨기기
- 프론트에서만 제거하기
- 비로그인 API 응답에 AI 분석 JSON을 내려주고 화면에서만 숨기기

---

## 9. Core 6: 권한 경계 테스트

v003의 핵심은 권한 경계다. 테스트를 반드시 추가/수정한다.

권장 테스트 파일:

```text
tests/public_access_auth_boundary_test.py
```

또는 기존 파일 확장:

```text
tests/page_response_smoke_test.py
tests/router_boundary_test.py
tests/isolated_operations_test.py
```

필수 검증:

```text
비로그인:
- GET /onbid 200
- GET /onbid/{id} 200
- GET /cases 200
- GET /cases/{id} 200
- 회생/파산 AI 분석 미노출
- 온비드 관심/패스/메모 POST는 로그인 필요
- 회생/파산 관심/패스/메모 POST는 로그인 필요
- /admin/* 접근 불가
- /api/admin/* 접근 불가
- 내부 원문 파일 접근 불가

로그인:
- 온비드 관심/패스/메모 가능
- 회생/파산 관심/패스/메모 가능
- 회생/파산 AI 분석 표시
- 내 관심/패스 목록 표시

관리자:
- /admin/collection 접근 가능
- /api/admin/onbid-quality 접근 가능
```

기존 테스트가 사용하는 isolated DB 패턴을 재사용한다.

---

# Extended Scope

Core Scope를 완료하고 핵심 테스트가 통과하면 아래를 계속 진행한다.

---

## 10. Extended 1: 온비드 필터/정렬 고도화

### 10.1 목표

공개 온비드 목록이 “많은 물건을 무작정 보여주는 화면”이 아니라 “찾고 싶은 물건을 빠르게 찾는 화면”이 되게 한다.

### 10.2 구현 후보

쿼리 파라미터 후보:

```text
q
region
asset_type
usage
agency
price_min
price_max
bid_deadline_from
bid_deadline_to
closing_within_days
min_discount_rate
has_notice
has_detail
sort
```

정렬 후보:

```text
closing_soon
newest
discount_desc
price_asc
price_desc
updated_desc
```

템플릿:

- 빠른 탭은 항상 보인다.
- 고급 필터는 접을 수 있게 한다.
- 필터 적용 상태를 badge로 보여준다.
- 결과가 없으면 친절한 empty state를 보여준다.

---

## 11. Extended 2: 온비드 상세 공고 요약/같은 공고 물건

### 11.1 목표

온비드 상세에서 공고 연결성을 더 잘 보여준다.

표시 후보:

```text
- 연결 공고 목록
- 공고 제목
- 공고 상태
- 공고 유형
- 공고일
- 입찰 기간
- 담당 부서
- 공고 상세 요약
- 같은 공고의 다른 물건
```

구현 기준:

- `AuctionNoticeItemLink`를 통해 같은 공고의 다른 `AuctionItem`을 찾는다.
- 너무 많은 경우 상위 N개만 보여주고 전체 보기 링크를 둔다.
- 데이터가 비어 있으면 숨긴다.

---

## 12. Extended 3: 공개 랜딩 페이지 정리

### 12.1 목표

첫 화면에서 서비스 정체성이 명확해야 한다.

랜딩 구성 후보:

```text
- 온비드 공매 바로보기
- 회생/파산 공고 바로보기
- 오늘/이번주 마감 물건
- 신규 공고
- 로그인하면 관심/패스/AI 분석 사용 가능 안내
```

기존 `/`가 관리자/로그인 중심이면 공개 서비스 소개/탐색 중심으로 조정한다. 관리자 접근은 별도 메뉴/경로로 유지한다.

---

## 13. Extended 4: 광고 슬롯 feature flag

### 13.1 목표

실제 AdSense 송출은 하지 않고, 나중에 붙일 수 있는 구조만 만든다.

설정 후보:

```text
ADSENSE_ENABLED=false
ADSENSE_CLIENT_ID=
ADSENSE_FOOTER_SLOT_ID=
```

위치:

```text
- 공개 온비드 목록 하단
- 공개 온비드 상세 하단
- 공개 회생/파산 목록 하단
- 공개 회생/파산 상세 하단
```

금지:

- 관리자 페이지 광고 표시
- 버튼/원문 링크 근처에 오인 클릭 유도 배치
- 실제 client id/slot id 하드코딩
- 정책 위반을 유도하는 문구

구현:

- `backend/config.py` settings에 옵션 추가 가능
- 템플릿 partial 예: `frontend/templates/shared/ad_slot.html`
- 기본값은 disabled

---

## 14. Extended 5: SEO/공유 메타/robots/sitemap 초안

### 14.1 목표

공개 페이지가 검색/공유에 대응할 수 있는 최소 구조를 만든다.

구현 후보:

```text
- 공통 title/description block
- Open Graph meta 기본값
- canonical URL helper 또는 template 변수
- GET /robots.txt
- GET /sitemap.xml 또는 최소 sitemap route
```

sitemap에는 우선 정적 공개 경로를 포함한다.

```text
/
/onbid
/cases
/about
/disclaimer
```

동적 물건/사건 sitemap은 데이터량과 URL 정책을 고려해 Stretch 또는 v004로 보류 가능하다.

---

## 15. Extended 6: 법적 고지/AI 책임 안내 초안

### 15.1 목표

베타 공개 전 최소 고지 페이지를 만든다.

추천 경로:

```text
/about
/disclaimer
/privacy-draft
```

내용 방향:

```text
- 본 서비스는 공공데이터 조회 편의 제공 서비스
- 원문 공고 확인 권장
- AI 분석은 참고자료이며 최종 판단 근거가 아님
- 입찰/투자 판단 책임은 사용자에게 있음
- 공공 API 데이터 지연/오류 가능성 있음
- 개인정보 처리방침은 베타 공개 전 정식화 예정
```

주의:

- 법률 자문처럼 단정하지 않는다.
- 과장 광고 문구를 넣지 않는다.
- 실제 개인정보 처리방침 완성본처럼 보이지 않게 `draft`임을 표시한다.

---

## 16. Extended 7: UTF-8 문구 1차 정리

### 16.1 목표

사용자/공개 화면 중심으로 깨진 한글 문구를 정리한다.

대상:

```text
frontend/templates/
tests/
reports/devpacks/devpack_v003_result_bundle.md
```

기준:

- 대량 포맷팅 금지
- 기능과 무관한 전체 reformat 금지
- 테스트 기대 문구가 바뀌면 실제 화면 문구와 함께 수정
- 관리자 collection 화면은 v002에서 정리되었으므로 중복 작업하지 않는다.

---

# Stretch Scope

Core + Extended 완료 후 시간이 남으면 아래 우선순위대로 진행한다.

---

## 17. Stretch 1: 관리자 관찰성 2차 강화

v002의 `/api/admin/onbid-quality`와 `/admin/collection`을 확장한다.

추가 지표 후보:

```text
- API 종류별 성공/실패
- 최근 24시간/7일 신규/갱신/중복 추이
- 상세 payload 누락률
- 공고 연결률
- 공고-물건 링크 생성률
- 마지막 성공 시각
- 마지막 실패 시각
- 최근 실패 메시지 분류
```

기존 관리자 인증 경계를 유지한다.

---

## 18. Stretch 2: 실제 API 소량 점검 도구 준비

### 18.1 목표

실제 API 키가 있는 운영 환경에서 소량 점검할 수 있는 probe 구조를 준비한다. Codex는 실제 키를 출력하거나 보고서에 쓰지 않는다.

후보 파일:

```text
run_onbid_probe.ps1
backend/workers/onbid_probe.py
```

기능 후보:

```text
- Sample 모드 지원
- 실제 API 키가 있으면 Limit=5, MaxPages=1 수준으로 소량 호출
- DB 저장 없이 dry-run 가능
- 응답 필드명 요약
- normalizer 후보 키 비교
- raw payload 전체는 Git commit하지 않음
```

결과 파일이 필요하면 `storage/` 또는 ignored local path에 저장한다. Git에 올리지 않는다.

국유일반재산 API는 완전 구현하지 않고, 샘플 확인/설계 준비 수준에 둔다.

---

## 19. Stretch 3: 백업/복원 리허설 문서

가능하면 기존 문서에 통합하거나 result bundle에 섹션으로 정리한다.

내용 후보:

```text
- DB 백업 명령
- storage 백업 범위
- 복원 순서
- 복원 후 테스트 명령
- Windows 작업 스케줄러 중지/재개 절차
```

새 문서를 꼭 만들어야 한다면:

```text
docs/backup_restore_runbook.md
```

하지만 문서 파일 수를 늘리지 않는 것이 원칙이므로 가능하면 result bundle 또는 기존 runbook에 통합한다.

---

## 20. Stretch 4: AGENTS.md/Codex CLI 운영 규칙 보강

작업 중 반복 규칙이 추가로 필요하다고 판단되면 `AGENTS.md`를 보강한다.

보강 후보:

```text
- /clear, /goal 사용 방식
- result bundle 단일화 규칙
- approval mode 권장
- 작업 전/후 Git 확인 명령
- 금지 명령
```

AGENTS.md를 수정하면 result bundle에 이유와 변경 요약을 기록한다.

---

# v004 이후 참고 로드맵

이 섹션은 구현 범위가 아니라 방향 참고다. Core/Extended/Stretch를 모두 끝내기 전에는 v004 항목을 구현하지 않는다.

## v004 후보: 온비드 데이터 품질/실제 API 보강

```text
- 실제 온비드 공고 API 응답 샘플 10~50건 수집
- normalizer 후보 필드 보강
- 공고 상세 payload 요약 고도화
- 국유일반재산 API 응답 샘플 확보
- 온비드 필터/검색 성능 개선
```

## v005 후보: 운영 안정화

```text
- 백업/복원 리허설
- Windows 작업 스케줄러 실제 등록 점검
- 실패 알림
- API 호출량 정책
- 로그 보관 정책
```

## v006 후보: 베타 출시 polish

```text
- 법적 고지 정식화
- 개인정보 처리방침 정식화
- AI 분석 책임 고지 강화
- AdSense 실제 연동
- SEO/sitemap 고도화
- 배포 인프라 검토
```

---

# 구현 세부 지침

---

## 21. 라우터 설계 지침

기존 라우터:

```text
backend/web/routers/auctions.py
backend/web/routers/cases.py
backend/web/routers/admin_operations.py
backend/web/routers/documents.py
```

지침:

- 공개 GET 경로와 로그인 필요 POST 경로를 명확히 분리한다.
- 관리자 API는 기존 인증을 유지한다.
- `documents.py`의 내부 원문 접근 경계를 풀지 않는다.
- 로그인 사용자 판별은 기존 dependency/session 방식을 재사용한다.
- 비로그인 GET에서 예외가 나지 않도록 optional user helper가 필요하면 만든다.
- 라우터 중복 등록을 만들지 않는다.

---

## 22. 템플릿 설계 지침

기존 템플릿을 최대한 재사용한다.

```text
frontend/templates/auctions/index.html
frontend/templates/auctions/detail.html
frontend/templates/user/index.html
frontend/templates/user/action_list.html
frontend/templates/user/passed.html
frontend/templates/auth/login.html
```

필요 시 신규 partial을 만든다.

```text
frontend/templates/shared/ad_slot.html
frontend/templates/shared/public_notice.html
frontend/templates/shared/seo_meta.html
```

신규 public 페이지 후보:

```text
frontend/templates/public/about.html
frontend/templates/public/disclaimer.html
frontend/templates/public/privacy_draft.html
```

주의:

- 대규모 디자인 리뉴얼은 하지 않는다.
- 공개 UX에 필요한 정보 구조 개선에 집중한다.
- 관리자 화면 스타일과 사용자 화면 스타일을 불필요하게 섞지 않는다.

---

## 23. 서비스 계층 지침

신규/확장 서비스 후보:

```text
backend/services/auction_items.py
backend/services/user_auction_preferences.py
backend/services/onbid_observability.py
backend/services/user_event_actions.py
backend/services/user_event_notes.py
```

원칙:

- DB query 로직을 라우터에 과도하게 넣지 않는다.
- 개인화 상태 토글 정책은 service 함수로 분리한다.
- serializer/helper에서 viewer 권한에 따른 필드 제한을 명확히 한다.
- 비로그인 공개 DTO와 로그인 상세 DTO를 구분할 수 있으면 구분한다.

---

## 24. DB 변경 지침

Core에서 온비드 개인화 모델을 구현하려면 신규 테이블이 필요할 가능성이 높다.

추천 테이블:

```text
user_auction_preferences
```

추천 필드:

```text
id INTEGER PRIMARY KEY
user_id INTEGER NOT NULL
auction_item_id INTEGER NOT NULL
is_favorite BOOLEAN NOT NULL DEFAULT 0
is_passed BOOLEAN NOT NULL DEFAULT 0
is_watching BOOLEAN NOT NULL DEFAULT 0
note TEXT NOT NULL DEFAULT ''
tags TEXT NOT NULL DEFAULT ''
created_at DATETIME
updated_at DATETIME
```

권장 unique:

```text
user_id + auction_item_id
```

추가 작업:

- `backend/database/models.py` 모델 추가
- `backend/database/session.py` SQLite 비파괴 create/ensure 보강
- `docs/migration_ledger.md` 업데이트
- 테스트에 migration 확인 포함

금지:

- 기존 온비드 unique 기준 변경
- 기존 사용자 action/note 테이블 삭제/변경
- 기존 데이터 삭제

---

## 25. 보안/노출 경계 점검 목록

반드시 확인한다.

```text
비로그인 /cases 응답에 AI 분석 텍스트가 없는가?
비로그인 /cases 상세에 OCR 전문이 없는가?
비로그인 /cases 상세에 내부 storage 경로가 없는가?
비로그인 /documents/raw 접근이 막히는가?
비로그인 관심/패스/메모 POST가 저장되지 않는가?
비로그인 /api/admin/onbid-quality 접근이 막히는가?
로그인 사용자는 본인 preference만 수정하는가?
관리자 화면은 기존처럼 보호되는가?
```

---

## 26. 테스트 실행 지침

기본 Python은 의존성이 부족할 수 있다. 번들 Python을 우선 사용한다.

```powershell
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

필수 테스트:

```powershell
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
```

v003에서 추가/수정한 테스트:

```powershell
& $Py tests/public_access_auth_boundary_test.py
```

파일명이 다르면 실제 추가한 테스트명을 result bundle에 기록한다.

온비드 샘플:

```powershell
.\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

가능하면 `py_compile`도 실행한다.

```powershell
& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/services/auction_items.py
```

신규 파일이 있으면 포함한다.

---

## 27. 결과 bundle 작성 지침

최종 결과 파일:

```text
reports/devpacks/devpack_v003_result_bundle.md
```

이 파일 하나에 모든 결과를 통합한다. 중간 결과서를 여러 개 만들지 않는다.

반드시 포함할 목차:

```markdown
# Codex 개발 결과 Bundle v003

## 1. 작업 메타데이터
- Git root:
- Branch:
- Base commit:
- Final commit(s):
- Remote:
- 작업 시작 status:
- 작업 종료 status:

## 2. 한줄 결과 요약

## 3. Core Scope 결과
### 3.1 공개 온비드 목록/상세
### 3.2 공개 온비드 상세/공고/원문 링크
### 3.3 공개 회생·파산 목록/기본 상세
### 3.4 로그인 온비드 개인화
### 3.5 회생·파산 AI 노출 경계
### 3.6 권한 경계 테스트

## 4. Extended Scope 결과
### 4.1 온비드 필터/정렬
### 4.2 온비드 공고 요약/같은 공고 물건
### 4.3 공개 랜딩 페이지
### 4.4 광고 슬롯 feature flag
### 4.5 SEO/robots/sitemap
### 4.6 고지/AI 책임 안내
### 4.7 UTF-8 정리

## 5. Stretch Scope 결과
### 5.1 관리자 관찰성 2차
### 5.2 실제 API probe 준비
### 5.3 백업/복원 문서
### 5.4 AGENTS.md 보강

## 6. 변경 파일 목록
| 파일 | 변경 요약 | 위험도 | 비고 |

## 7. DB/마이그레이션 변경
- 신규 테이블:
- 신규 컬럼:
- 비파괴 여부:
- migration ledger 업데이트 여부:
- rollback 방법:

## 8. 권한 경계 표
| 사용자 상태 | 접근 가능 | 접근 불가 | 검증 방법 |

## 9. 테스트 결과
| 명령 | 결과 | 비고 |

## 10. 미완료/보류/리스크
| 항목 | 상태 | 이유 | 다음 조치 |

## 11. v004 추천 작업

## 12. Codex CLI 운영 메모
- 사용한 /goal:
- approval 관련 특이사항:
- 사용한 Python:
- 긴 로그 위치:
```

---

## 28. 최신 프로젝트 상태 문서 업데이트

다음 파일을 새로 만들거나 업데이트한다.

```text
reports/project-result_current.md
```

내용:

```text
- 현재 서비스 한줄 요약
- v003 후 공개/로그인/관리자 기능 상태
- 주요 라우트
- 주요 DB 모델
- 주요 테스트
- 남은 리스크
- v004 우선순위
```

기존 `reports/project-result_v002.md`는 변경하지 않아도 된다. v003부터 최신 상태는 `project-result_current.md`를 우선 사용한다.

---

## 29. 커밋 지침

가능하면 논리 커밋으로 나눈다.

예시:

```text
feat: expose public onbid and case pages
feat: add onbid user preferences
feat: improve public filters seo and notices
test: add public auth boundary coverage
docs: add v003 result bundle and current status
```

단, 커밋 수보다 안전성과 결과 bundle 정확성이 중요하다.

커밋 전 필수 검사:

```powershell
git diff --cached --name-only | Select-String -Pattern '(^|/|\\)(\.env|storage|logs)(/|\\|$)|\.(db|sqlite|sqlite3)$|runtime_settings\.json|\.git\.bad-init'
git status --short
```

민감 파일이 stage되어 있으면 커밋하지 않는다.

최종 push는 사용자가 승인했거나 실행 환경에서 명시 지시가 있을 때만 수행한다.

---

## 30. 완료 기준

v003는 아래 조건을 만족하면 완료로 본다.

```text
1. 비로그인 사용자가 /onbid, /onbid/{id}, /cases, /cases/{id}를 볼 수 있다.
2. 비로그인에게 회생/파산 AI 분석과 내부 원문 파일이 노출되지 않는다.
3. 로그인 사용자는 온비드 관심/패스/감시/메모를 사용할 수 있다.
4. 로그인 사용자는 회생/파산 관심/패스/메모/AI 분석을 사용할 수 있다.
5. 내 관심/패스 목록이 정리된다.
6. 온비드 목록/상세가 필터, 공고 연결, D-day 중심으로 개선된다.
7. 공개 페이지에 광고 슬롯 feature flag, SEO/고지 초안이 준비된다.
8. 관리자 수집/분석/품질 기능은 기존처럼 보호된다.
9. 권한 경계 테스트와 기존 핵심 테스트가 통과한다.
10. docs/migration_ledger.md가 schema 변경에 맞게 업데이트된다.
11. reports/devpacks/devpack_v003_result_bundle.md가 작성된다.
12. reports/project-result_current.md가 작성/업데이트된다.
```

---

## 31. Codex CLI 실행용 /goal 문구

Codex CLI 세션에서 아래 goal을 사용한다.

```text
/goal Implement reports/devpacks/devpack_v003_instruction.md on branch codex/devpack-v003-public-first-personalization. Complete Core Scope first, then Extended Scope, then Stretch Scope as far as safely possible. Preserve public/auth/admin security boundaries, do not expose AI analysis or internal raw files to anonymous users, do not commit secrets or runtime data, and produce one consolidated result bundle at reports/devpacks/devpack_v003_result_bundle.md plus reports/project-result_current.md.
```

---

## 32. Codex에게 처음 보낼 메시지 예시

```markdown
현재 repo는 `C:\Users\xogns\Documents\testAuction\court_auction_platform`입니다.
현재 작업 브랜치는 `codex/devpack-v003-public-first-personalization`입니다.

먼저 아래를 실행해 Git 상태를 확인하고 결과를 최종 bundle에 기록하세요.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -5
```

그 다음 `AGENTS.md`와 `reports/devpacks/devpack_v003_instruction.md`를 읽고 v003를 진행하세요.

사소한 질문은 하지 말고 지시서의 판단 기준에 따라 진행하세요.
단, `git init`, main 직접 작업, DB/storage 삭제, `.env` 노출, 파괴적 migration, 내부 원문 파일 공개, 비로그인 AI 분석 노출이 필요해 보이면 즉시 중단하고 result bundle에 기록하세요.
```
