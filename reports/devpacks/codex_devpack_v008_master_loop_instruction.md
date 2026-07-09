# Codex Devpack v008 마스터 반복 개발 지시서
## 경·공매 소거형 검토 보조 플랫폼: 데이터 확충 + 공개 UX 완성 + 운영 검증 루프

작성일: 2026-07-10 KST  
대상 저장소: `court_auction_platform`  
권장 작업 브랜치: `codex/devpack-v008-master-review-data-ux-loop`  
기준 브랜치: `codex/devpack-v007-product-ux-safety-analytics`  
목표 모델: Codex 최상위 추론 모델  
작업 방식: 장시간 단일 실행. 중간에 사소한 확인 질문을 하지 말고, 아래 승인 범위 안에서 개발/검증/추가 개발/재검증을 반복한다.

---

## 0. 절대 전제

이 서비스는 경·공매 투자 판단 플랫폼이 아니다.

핵심 정체성:

> 우리는 경·공매 투자 판단 플랫폼이 아니라, 경·공매 후보를 빠르게 거르고 기록하게 만드는 무료 기반 검토 보조 플랫폼이다.

모든 기능과 문구는 다음 원칙을 지켜야 한다.

- 투자 추천 금지
- 권리분석 금지
- 안전/위험 판정 금지
- 수익성 판단 금지
- 낙찰 가능성/입찰가 제시 금지
- 전문가 검증/추천처럼 보이는 표현 금지
- AI가 판단하는 것처럼 보이는 표현 금지
- 원문 확인과 자료 완결성 중심

허용 표현의 기준:

- “원문에서 확인하세요”
- “자료 확인 필요”
- “검토 보조”
- “자료 완결성”
- “가정 기반”
- “최종 판단 전 원문과 관계 서류를 직접 확인하세요”

---

## 1. 이번 v008의 목적

v007은 기반 기능 구현은 있었지만, 실제 리뷰 사이트에서는 아직 제품 체감이 부족했다.

v008의 목적은 다음 네 가지다.

1. 실제 리뷰 사이트에서 발견된 문제를 재현하고 수정한다.
2. ONBID 데이터를 추가 확보하여 public QA와 실제 검토 체감을 개선한다.
3. 홈/오늘 보기/목록/상세/내 검토함/운영 화면을 v13.1 기획에 맞게 정리한다.
4. 개발 → 검증 → 추가 개발 → 검증을 같은 devpack 안에서 반복하여 “완료 선언” 전에 외부 리뷰 URL 기준으로도 확인한다.

---

## 2. 승인 범위

사용자는 이번 작업에 대해 아래 범위를 사전 승인했다.

허용:

- 새 작업 브랜치 생성
- 필요한 패키지 설치
- `pytest` 설치 또는 테스트 환경 정리
- 제한적 외부 네트워크 사용
- 제한적 ONBID API 호출
- Cloudflare quick tunnel 또는 기존 터널 기반 외부 리뷰 QA
- DB 백업
- 비파괴 DB 마이그레이션
- derived field repair Apply 실행: 단, 반드시 최신 백업 + dry-run 영향 요약 + 적용 후 audit 필수
- 테스트 실행
- 커밋
- 원격 브랜치 push
- 결과 리포트 작성

금지:

- `main` 직접 push
- API key/secret 출력
- raw payload 전체 저장/커밋
- DB 파일 커밋
- backup/log/storage/raw 파일 커밋
- 개인정보/원문 전체/OCR 전체를 public에 노출
- AI 권리분석 기능 구현
- 수익성/입찰가/낙찰 가능성 판단 기능 구현
- Archi-Pro 실제 API 연동
- 광고/전문가 추천 기능 구현
- 제한 없는 대량 API 호출

API 호출은 “QA 데이터 확보를 위한 제한적 수집”으로만 수행한다. 과도한 호출이나 무한 루프는 금지한다.

---

## 3. 시작 상태 확인

작업 시작 즉시 아래를 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -8
```

기준 브랜치가 `codex/devpack-v007-product-ux-safety-analytics`인지 확인한다.  
다르면 현재 위치를 기록하고, v007 브랜치를 기준으로 새 브랜치를 만든다.

권장:

```powershell
git fetch origin
git checkout codex/devpack-v007-product-ux-safety-analytics
git pull --ff-only
git checkout -b codex/devpack-v008-master-review-data-ux-loop
```

---

## 4. v007 결과와 실제 리뷰 사이트의 불일치 재현

먼저 코드를 고치기 전에, 현재 상태를 재현하고 기록한다.

검토 대상:

- 로컬: `http://127.0.0.1:8000`
- 외부 리뷰 URL: 기존 URL이 살아 있으면 사용
- 기존 URL이 죽어 있으면 새 Cloudflare quick tunnel 생성

필수 확인 경로:

```text
/
/onbid
/onbid/today
/onbid?category=real_estate
/onbid?category=movable
/onbid?category=national_property
/onbid?data_quality=needs_confirmation
/onbid?closing_within_days=7
/cases
/disclaimer
```

필수 기록:

- status code
- 주요 한국어 문구 존재 여부
- mojibake 존재 여부
- 총 건수/카테고리 건수
- 종료된 항목이 기본 목록 상단에 노출되는지
- 원문 보기 버튼 표시 여부
- 오늘 보기 422 여부
- real_estate 상세 Development Insight CTA 표시 여부
- 금지 표현 존재 여부

금지 표현 검색 패턴:

```text
AI 분석
권리분석
추천 물건
수익률
낙찰 보장
안전한 물건
위험한 물건
알짜
숨은 진주
전문가 보고서
검증 전문가
공식 파트너
```

mojibake 의심 패턴:

```text
�
?먮
?뺤
留
媛
寃
낫
꾩
슂
```

---

## 5. 데이터 확충 계획

### 5.1 데이터 목표

현재 v006-a3 기준 public-visible fresh non-sample은 100건 수준이었다. v008에서는 실제 리뷰 체감을 위해 데이터를 추가 확보한다.

목표:

```text
public-visible fresh non-sample total: 250건 이상
real_estate: 120건 이상
movable: 80건 이상
national_property: 20건 이상 또는 API 한계/무데이터 사유 명확히 보고
active_or_upcoming visible rows: 150건 이상
detail marker real_estate: 60건 이상 또는 visible real_estate의 50% 이상
detail marker movable: 30건 이상 또는 visible movable의 50% 이상
duplicate key count: 0
sample/fixture public 노출: 0
stale/unknown-date public 기본 노출: 0
```

도달하지 못하면 실패가 아니라, 추가 시도와 한계 사유를 결과서에 명확히 적는다. 단, 1회 시도 후 바로 포기하지 말고 최소 2~3개 수집 전략을 시도한다.

### 5.2 수집 전 백업

DB 변경 또는 실제 데이터 수집 전 반드시 백업한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\backup_database.ps1
```

결과서에 기록:

- 백업 경로
- sha256
- source DB
- 복원 테스트 여부

### 5.3 수집 전 audit

```powershell
powershell -ExecutionPolicy Bypass -File .\audit_onbid_freshness.ps1 -MinDate 2025-01-01
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

추가로 서비스 기준 public-visible count를 별도 스크립트 또는 Python snippet으로 기록한다.

필수 count:

- total
- fresh
- stale
- invalid_date
- unknown_date
- public-visible fresh non-sample total
- real_estate
- movable
- national_property
- other
- active/upcoming
- ended
- detail marker counts
- duplicate key count
- sample/fixture count

### 5.4 ONBID 수집 전략

기존 PowerShell wrapper에 `PageNo`가 있으므로 이를 활용한다.

기본 원칙:

- `MinDate=2025-01-01`
- stale/unknown-date 기본 공개 금지 유지
- API key 출력 금지
- raw payload 전체 출력 금지
- raw payload dump 파일 생성 금지
- 호출별 fetched/accepted/inserted/duplicates/dropped를 표로 기록
- throttle 적용
- 중복이 계속 나오면 PageNo/기간/category 전략 변경

권장 수집 범위:

```text
real_estate:
  PageNo 1~10, Limit 20 또는 50
  BidPrdYmdStart: 오늘 기준 -14일
  BidPrdYmdEnd: 오늘 기준 +180일
  IncludeDetails: 단계적으로 확대

movable:
  PageNo 1~10, Limit 20 또는 50
  BidPrdYmdStart: 오늘 기준 -14일
  BidPrdYmdEnd: 오늘 기준 +90일
  IncludeDetails: 단계적으로 확대

national_property:
  전용 API 또는 category 매핑 검증
  PageNo 1~10, Limit 20 또는 50
  데이터가 0이면 API 파라미터/분류 로직/공개 필터 어디에서 0이 되는지 분해 보고

notice/public announcements:
  공고목록 API를 별도 범위로 검증
  실제 item과 연결 가능한 공고인지 확인
```

호출 상한:

```text
한 devpack 내 목록 API 호출: api kind별 최대 20 page
상세 API 호출: api kind별 최대 100건
동일 page 중복 재호출: 최대 1회
호출 간 대기: 1~2초
```

### 5.5 상세 보강

상세 페이지에 “상세 정보가 없습니다”가 과도하게 나오지 않도록 detail marker를 늘린다.

우선순위:

1. public-visible active/upcoming real_estate
2. public-visible active/upcoming movable
3. 상세 결측이 많은 항목
4. 마감 임박 항목
5. Development Insight CTA 대상 real_estate 토지/단독주택/상가주택

상세가 없으면 없는 상태를 숨기지 말고, “상세 자료 확인 필요”로 표시한다.

### 5.6 repair Apply

`repair_onbid_derived_fields.ps1 -DryRun`에서 derived field 보정이 필요한 경우, 이번 devpack에서는 실행 가능하다.

조건:

1. 최신 DB 백업 완료
2. dry-run 결과 기록
3. 업데이트 대상 필드가 public safety 원칙을 해치지 않음
4. Apply 후 audit 재실행
5. Apply 전/후 count 비교
6. 실패 시 복구 방안 기록

명령 예시:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

---

## 6. 공개 UX 수정 계획

### 6.1 홈

홈은 소개 페이지가 아니라 “오늘 볼 것”의 입구여야 한다.

최상단 4개 카드:

1. 오늘 신규 등록 물건
2. 이번 주 마감 임박 물건
3. 내 지역 신규 물건
4. 가격 정보 있는 1억 이하 물건

비로그인 기본 지역:

- 서울/수도권

로그인 사용자:

- 내 지역 설정 반영

각 카드에는 다음을 표시한다.

- 제목
- 건수
- 짧은 설명
- 이동 버튼
- 비어 있을 때 안전한 empty state

권장 홈 문구:

> 오늘 새로 나온 경·공매 후보를 확인하고, 관심 없는 물건은 패스해 검토 목록을 정리하세요. 최종 판단은 원문과 관계 서류 확인을 기준으로 해야 합니다.

### 6.2 오늘 보기

현재 외부 리뷰 URL에서 `/onbid/today` 클릭 시 422가 발생했다. 반드시 수정한다.

필수 조건:

- 비로그인 GET 200
- 로그인 GET 200
- 저장 form은 비로그인 숨김
- 비로그인에는 로그인 CTA 노출
- 오늘 신규가 없으면 empty state 표시
- 모든 오늘 후보가 관심 또는 패스로 처리되면 “오늘 검토 완료”
- 완료 요약: 신규 n건, 패스 n건, 관심 n건, 메모 n건, 원문 확인 n건
- 외부 터널 URL에서도 422 없음

오늘 보기 기준:

- 우선 `first_seen_at` 또는 수집일 기준 오늘/최근 24시간
- 해당 데이터가 부족하면 “최근 수집 후보” fallback을 명확히 표시
- 종료된 항목보다 active/upcoming 우선
- stale/unknown/sample 제외

### 6.3 ONBID 목록

목록은 검색 결과표가 아니라 소거형 검토 보드다.

필수 수정:

- 한글 깨짐 문구 제거
- `?먮Ц...`, `媛...` 등 mojibake 0건
- 자료 완결성 배지를 한국어로 표시
- “내 검색함” → “내 검토함”
- 기본 목록은 진행중/예정/마감 임박 우선
- 종료된 항목은 기본 상단에서 밀어내거나 `status=ended` 필터로 분리
- 각 카드에 원문 보기/상세 보기 명확히 표시
- 비로그인에게 관심/패스/메모는 로그인 CTA로 표시
- 로그인 사용자에게 관심/패스/메모/감시 액션 표시
- category count와 실제 목록 count 일치
- national_property 0건이면 탭을 비활성 또는 “수집 준비 중” 상태로 명확히 표시

카드 정보 계층:

1. 유형 / 지역
2. 물건명
3. 최저입찰가 / 감정가
4. 마감일 또는 종료 상태
5. 자료 완결성 배지
6. 기관
7. 원문 보기
8. 관심 / 패스 / 메모 / 감시
9. 상세 보기

### 6.4 자료 확인 필요

`/onbid?data_quality=needs_confirmation`는 사용자에게 “기회”처럼 보이면 안 된다.

필수:

- “자료 확인 필요” 탭/필터
- 자료 부족이 투자 안전성/수익성을 의미하지 않는다는 안내
- 가격/일정/위치/면적/원문 링크 결측 유형별 배지
- 해당 필터 결과 count와 전체 count 정합성
- empty state

문구:

> 일부 정보가 충분하지 않아 원문 확인이 필요한 후보입니다. 가격, 일정, 위치, 면적 등 주요 항목을 원문에서 직접 확인하세요.

### 6.5 상세 화면 4-Zone

상세는 반드시 4-Zone 정보 계층으로 정리한다.

Zone 1. 자료 상태 선언

- 자료 완결성 배지
- 수집 시각
- 출처
- 상단 원문 보기 버튼
- 면책 툴팁

Zone 2. 객관적 팩트

- 최저입찰가
- 감정가
- 입찰 마감일
- 소재지
- 면적
- 물건 유형
- 담당 기관

Zone 3. 원문 확인 포인트

- “검색 보조” 명칭 사용 금지
- “원문 확인 포인트” 또는 “검토 보조” 사용
- 판단성 문구 금지
- 원문/관련 서류 확인 유도

Zone 4. 개인화 액션

- 관심
- 패스
- 감시
- 메모
- 공유 요약
- 오류 제보
- 하단 원문 보기 버튼

상세 페이지 필수 문구:

> 아래 정보는 수집된 공개 자료를 바탕으로 정리한 내용입니다. 최종 판단 전 원문과 관계 서류를 직접 확인해야 합니다.

### 6.6 원문 보기

원문 확인은 서비스 철학의 핵심이다.

필수:

- 상세 상단 원문 보기
- 상세 하단 원문 보기
- 목록 카드 원문 보기
- 원문 링크가 없으면 “원문 링크 확인 필요”
- 원문 클릭 analytics 이벤트
- raw URL 전체를 analytics metadata에 저장하지 않음
- 외부 링크는 새 창/새 탭 권장
- 원문이 없는 경우 자료 상태 배지 반영

### 6.7 Development Insight CTA

v007 결과서상 real_estate 상세에 CTA가 구현되었다고 하나, 실제 공개 상세에서 명확히 보이지 않았다. v008에서 반드시 재확인하고 수정한다.

조건:

- real_estate 상세에만 표시
- movable에는 표시하지 않음
- 홈/목록 전면에는 과도하게 노출하지 않음
- 실제 Archi-Pro/API 연동 금지
- 클릭 시 안내/계측용 페이지
- 수익성/사업성/법률 판단 문구 금지

버튼명:

> 개발 가능성 기초 검토

면책 문구:

> 가정 기반 개발비 및 대략적 공간 검토를 돕는 안내입니다. 실제 건축 인허가, 법률 판단, 수익성을 보장하지 않습니다.

금지:

- 이 땅으로 얼마 벌까
- 개발 수익 계산
- 수익성 확인
- 가치 상승 시뮬레이션
- 돈 되는 개발 후보

---

## 7. 운영/관리자 기능 보강

### 7.1 오류 제보 관리자 큐

v007에는 오류 제보 저장은 있으나 관리자 review UI가 없다. v008에서 구현한다.

필수:

- `/admin/onbid-issue-reports`
- pending/reviewed/resolved/ignored 상태
- 유형별 필터
- item 상세 링크
- 제보 생성 시각
- 운영자 메모
- 상태 변경
- 개인정보 노출 의심 flag 우선 표시
- public에 제보 내용 자동 노출 금지

### 7.2 공유 요약 관리

v007에는 공유 생성과 공개 페이지가 있으나 revoke/manage UI가 없다.

필수:

- 내 검토함 또는 `/my/onbid/shared-summaries`
- 공유 목록
- 공개 링크 복사
- 공유 취소/revoke
- 만료 또는 비활성화 상태
- private memo 노출 여부 명확 표시
- public share는 noindex/noarchive 유지

### 7.3 Analytics 관리자 요약

최소 관리자 요약을 만든다.

필수 이벤트:

- today_queue_view
- preference_action
- original_link_click
- issue_report_create
- share_create
- share_open
- share_copy
- development_insight_cta_view
- development_insight_cta_click

관리자 화면:

- `/admin/product-analytics`
- 최근 7일/30일 이벤트 count
- 경로별 이벤트
- 카테고리별 원문 클릭
- 패스/관심/메모/감시 count
- Development Insight CTA 노출/클릭
- raw memo/full URL/raw payload 미표시

---

## 8. 테스트 계획

### 8.1 패키지와 테스트 실행

`pytest`가 없으면 설치한다.

```powershell
python -m pip install pytest
```

기본 실행:

```powershell
python -m py_compile backend\database\models.py backend\database\session.py backend\services\auction_items.py backend\services\product_engagement.py backend\web\routers\auctions.py
python -m pytest
```

### 8.2 기존 필수 테스트

반드시 실행:

```text
tests/onbid_freshness_policy_test.py
tests/onbid_public_filter_state_test.py
tests/onbid_category_mapping_test.py
tests/sitemap_fresh_public_routes_test.py
tests/onbid_module_test.py
tests/page_response_smoke_test.py
tests/public_access_auth_boundary_test.py
tests/router_boundary_test.py
tests/isolated_operations_test.py
```

### 8.3 v007 테스트 유지

반드시 실행:

```text
tests/product_copy_safety_test.py
tests/onbid_today_review_completion_test.py
tests/onbid_data_quality_needed_filter_test.py
tests/onbid_data_issue_report_test.py
tests/onbid_review_summary_share_test.py
tests/product_analytics_events_test.py
tests/development_insight_cta_safety_test.py
```

### 8.4 v008 신규 테스트 추가

아래 테스트를 추가한다.

```text
tests/no_mojibake_public_copy_test.py
tests/home_curation_cards_test.py
tests/onbid_today_route_external_shape_test.py
tests/onbid_default_active_priority_test.py
tests/onbid_original_link_prominence_test.py
tests/onbid_detail_four_zone_test.py
tests/development_insight_cta_visibility_test.py
tests/onbid_admin_issue_queue_test.py
tests/onbid_shared_summary_manage_test.py
tests/product_analytics_admin_summary_test.py
tests/onbid_dataset_quality_threshold_test.py
```

각 테스트의 핵심:

- public template에 mojibake 패턴 없음
- 홈 4개 카드 존재
- `/onbid/today` 200
- 기본 목록에서 ended가 상단을 점령하지 않음
- 목록/상세에 원문 보기 표시
- 상세 4-Zone 존재
- real_estate에는 Development Insight CTA 표시, movable에는 미표시
- issue report admin queue 존재
- shared summary revoke/manage 가능
- analytics admin summary raw 민감정보 노출 없음
- public-visible 데이터 threshold 검증

### 8.5 외부 리뷰 URL QA

로컬 테스트만으로 완료 선언하지 않는다.

서버 실행 후 외부 터널을 열고 QA한다.

예시:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
cloudflared.exe tunnel --url http://127.0.0.1:8000
```

외부 URL에서 아래를 확인한다.

```text
/
/onbid
/onbid/today
/onbid?category=real_estate
/onbid?category=movable
/onbid?category=national_property
/onbid?data_quality=needs_confirmation
/onbid?closing_within_days=7
/cases
/disclaimer
```

필수 통과:

- status 200
- `/onbid/today` 422 없음
- mojibake 없음
- 금지 표현 없음
- 홈 4개 카드 확인
- ONBID count 250건 이상 또는 한계 사유
- real_estate/movable count 표시
- 원문 보기 확인
- real_estate detail Development Insight CTA 확인
- movable detail Development Insight CTA 없음
- public share noindex/noarchive
- review mode 안내 정상

---

## 9. 반복 개발 루프

이번 devpack은 한 번 고치고 끝내지 않는다.

반복 루프:

```text
Loop 1: 상태 재현
  - 사이트/테스트/DB 상태를 기록한다.

Loop 2: 데이터 확충
  - 제한 수집 → audit → repair 필요 검토 → 상세 보강 → audit.

Loop 3: 공개 UX 수정
  - 홈/오늘 보기/목록/상세/문구/한글 깨짐 수정.

Loop 4: 운영 UI 보강
  - issue admin queue/shared summary manage/analytics admin summary.

Loop 5: 테스트
  - py_compile → 기존 테스트 → 신규 테스트 → pytest 전체.

Loop 6: 외부 리뷰 QA
  - Cloudflare URL로 직접 확인.

Loop 7: 부족 항목 재개발
  - 실패 항목을 고치고 Loop 5~6 반복.

Loop 8: 결과서 작성
  - 완료/미완료/다음 과제를 구분해 기록한다.
```

완료 선언 금지 조건:

- `/onbid/today`가 외부 URL에서 422
- mojibake 패턴이 public 화면에 남음
- 금지 표현이 public 화면에 남음
- 원문 보기 버튼이 상세에 없음
- real_estate detail CTA가 없음
- full pytest를 시도하지 않음
- 데이터 확충을 1회만 시도하고 포기
- API key/raw payload/DB/backup/log가 Git 변경 목록에 포함
- 결과서에 외부 URL QA가 없음

---

## 10. 결과 리포트 작성

작업 완료 후 반드시 다음 파일을 만든다.

```text
reports/devpacks/devpack_v008_master_loop_result_bundle.md
reports/project-result_current.md
```

결과 리포트 필수 목차:

1. 작업 메타데이터
2. 시작 git status/log
3. 기준 브랜치와 새 브랜치
4. 백업 정보와 sha256
5. 변경 파일 목록
6. v007 결과서 대비 반영/미반영 표
7. 외부 리뷰 사이트 재현 결과
8. 데이터 수집 호출 표
9. DB audit 전/후 비교
10. public-visible 데이터셋 규모
11. detail marker 전/후 비교
12. national_property/공고목록 API 검증 결과
13. repair Apply 실행 여부와 결과
14. 구현 기능 요약
15. 공개 UX 수정 사항
16. 운영/관리자 기능
17. 개인정보/secret/raw payload 노출 점검
18. 금지 표현/mojibake 검색 결과
19. public route QA 결과
20. 외부 Cloudflare URL QA 결과
21. 테스트 실행 결과
22. 남은 리스크
23. 다음 devpack 추천
24. 종료 git status/log
25. commit/push 결과

결과서에는 “성공한 것”과 “아직 부족한 것”을 명확히 분리한다.

---

## 11. 커밋/푸시

작업이 끝나고 테스트와 외부 QA를 마친 뒤 커밋한다.

예시:

```powershell
git status --short
git add backend frontend tests docs reports scripts
git commit -m "feat: improve public review ux and onbid data readiness v008"
git push -u origin codex/devpack-v008-master-review-data-ux-loop
```

주의:

- DB 파일 add 금지
- storage/backups add 금지
- storage/logs add 금지
- raw payload add 금지
- `.env` add 금지
- API key 포함 파일 add 금지

커밋 전 확인:

```powershell
git status --short
git diff --cached --name-only
```

---

## 12. 최종 통과 기준

v008 완료 기준:

```text
[ ] public-visible fresh non-sample total 250건 이상 또는 한계 사유 명확
[ ] active/upcoming visible rows 150건 이상 또는 한계 사유 명확
[ ] real_estate 120건 이상 또는 한계 사유 명확
[ ] movable 80건 이상 또는 한계 사유 명확
[ ] national_property 수집/검증 완료
[ ] detail marker real_estate/movable 보강
[ ] /onbid/today 외부 URL 200
[ ] 홈 4개 큐레이션 카드 표시
[ ] ONBID 목록 mojibake 0건
[ ] “내 검색함” → “내 검토함”
[ ] 목록/상세 원문 보기 명확
[ ] 상세 4-Zone 정리
[ ] real_estate Development Insight CTA 표시
[ ] movable Development Insight CTA 미표시
[ ] 자료 확인 필요 필터 정상
[ ] issue report admin queue 구현
[ ] shared summary manage/revoke 구현
[ ] analytics admin summary 구현
[ ] 금지 표현 0건
[ ] API key/raw payload/DB/backup/log 커밋 0건
[ ] py_compile PASS
[ ] 기존 테스트 PASS
[ ] v007 테스트 PASS
[ ] v008 신규 테스트 PASS
[ ] python -m pytest PASS 또는 실패 사유와 대체 전체 실행 명확
[ ] 외부 Cloudflare URL QA 결과 포함
[ ] 결과 리포트 작성
[ ] 브랜치 push 완료
```

이 기준을 충족하지 못하면 완료로 쓰지 말고, “부분 완료”로 명확히 보고한다.

---

## 13. 마지막 주의

기능을 많이 넣는 것보다 더 중요한 것은 사용자가 첫 화면에서 다음을 바로 느끼게 하는 것이다.

> 오늘 새로 볼 후보가 있고, 관심 없는 것은 패스할 수 있으며, 남긴 후보는 원문 중심으로 다시 검토할 수 있다.

v008의 목표는 거창한 확장이 아니라, 이 기본 경험을 실제 리뷰 사이트에서 설득력 있게 보이게 만드는 것이다.
