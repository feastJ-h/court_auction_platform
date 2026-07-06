# 로그인/개인화/사용자 UI 개선 및 다음 개발 지시서

작성일: 2026-07-05

## 1. 목적

이번 단계의 목적은 사용자가 실제로 경매 물건을 훑어볼 때 피로하지 않도록 사용자 화면을 정리하고, 로그인한 사용자별로 관심 없는 물건을 제외할 수 있는 구조를 추가하는 것이다.

동시에 다음 개발 항목으로 언급된 아래 작업도 이후 루프에 포함한다.

- OCR 큐
- UNKNOWN 날짜 보정
- LOCAL_INGESTED 메타데이터 보강
- 관리자 리뷰 입력 UI
- 라우터 분리

## 2. 핵심 방향

사용자 화면은 분석 운영 화면이 아니다. 사용자는 많은 정보를 전부 읽기보다, 여러 물건 중 괜찮은 후보 한두 개를 빠르게 고르고 싶어 한다.

따라서 사용자 화면은 다음 방향으로 바꾼다.

- 반복되는 물건 정보와 분석 요약을 줄인다.
- 모델 비교는 사용자 화면에서 기본 노출하지 않는다.
- 작업 로그, job 상태, worker 상태는 관리자 화면으로 보낸다.
- 사용자에게는 “볼 만한지”, “왜 주의해야 하는지”, “원문을 볼 수 있는지”만 우선 보여준다.
- 관심 없는 물건은 로그인 사용자별로 “패스” 처리해서 다음 목록에서 숨긴다.

## 3. 로그인 기능

### 3.1 1차 목표

처음부터 복잡한 회원 시스템을 만들지 않는다. 1차는 로컬/소규모 운영에 맞는 간단한 로그인으로 시작한다.

필수 기능:

- 로그인 페이지
- 로그아웃
- 현재 로그인 사용자 식별
- 사용자별 패스 목록 저장
- 관리자 화면 접근 제한 준비

권장 방식:

```text
1차:
  세션 쿠키 기반 간단 로그인
  users 테이블
  password_hash 저장
  관리자/일반 사용자 역할 구분

2차:
  비밀번호 변경
  사용자별 분류/태그
  관리자 계정 관리 화면

3차:
  외부 인증 또는 더 강한 보안 구조 검토
```

### 3.2 권장 테이블

```text
users
  id
  username
  password_hash
  display_name
  role
  is_active
  created_at
  updated_at

user_event_actions
  id
  user_id
  event_id
  action_type
  reason
  created_at
  updated_at
```

`action_type` 예시:

```text
PASSED
BOOKMARKED
WATCHING
ARCHIVED
```

이번 1차에서는 `PASSED`만 구현해도 된다.

## 4. 패스 처리 방식

### 4.1 DB에서 안 가져오는 방식 권장

사용자가 패스한 물건은 “화면에서만 숨기는 방식”보다 “DB 조회 단계에서 제외하는 방식”을 권장한다.

이유:

- 서버가 화면에 보낼 데이터량이 줄어든다.
- 템플릿 렌더링 비용이 줄어든다.
- 사용자 입장에서 페이지네이션이 자연스럽다.
- 이미 숨긴 물건이 API 응답에 섞이지 않는다.
- 나중에 물건 수가 많아질수록 더 유리하다.

단, 소스/DB에 원본 데이터는 그대로 남긴다. 즉, `asset_events`나 `raw_documents`를 삭제하지 않는다.

권장 흐름:

```text
사용자 로그인
-> /user 요청
-> 현재 user_id 확인
-> user_event_actions에서 PASSED event_id 제외
-> DB query에서 제외된 목록만 조회
-> 화면 표시
```

### 4.2 복구 기능

사용자가 실수로 패스할 수 있으므로 복구 경로를 둔다.

권장 화면:

```text
/user/passed
  내가 패스한 물건 목록
  다시 보기 버튼
```

또는 사용자 화면에 필터로 제공:

```text
보기 모드:
  추천/검토 대상
  패스한 물건
  전체
```

1차에서는 `/user/passed` 또는 관리자용 확인 API만 있어도 충분하다.

## 5. 사용자 화면 UI 개선

### 5.1 제거하거나 접을 정보

사용자 화면 기본 목록에서 아래 정보는 숨기거나 상세 안으로 넣는다.

- 작업 로그
- 분석 job 진행률
- worker 상태
- 모델별 전체 비교
- Gemini/ChatGPT 세부 차이
- 원문 전체 텍스트
- 같은 내용이 반복되는 물건 설명/요약
- 너무 긴 분석 Markdown

이 정보들은 관리자 화면 또는 상세 펼침에서만 본다.

### 5.2 기본 카드에 남길 정보

사용자 카드에는 다음만 우선 노출한다.

```text
사건번호
제목
지역/주소 요약
물건 유형
최저가
입찰일 또는 마감일
D-day
핵심 위험 한 줄
추천/주의 등급
분석 완료 여부
원문 보기
상세 보기
패스 버튼
관심 버튼
```

### 5.3 상세 보기 구조

상세 보기에는 다음 정도만 남긴다.

```text
요약
  이 물건을 볼지 말지 판단하는 핵심 요약

가격/일정
  최저가
  입찰일
  마감일

주의 사항
  권리 위험
  점유/명도
  추가 확인 필요

원문 근거
  짧은 근거 발췌
  원문 파일 열기
```

모델 비교 탭은 기본 사용자 화면에서는 제거하거나 접는다. 필요하면 관리자 화면에서 본다.

### 5.4 정렬

사용자 목록 정렬은 다음을 권장한다.

```text
1. 로그인 사용자가 PASSED 하지 않은 물건
2. 분석 완료 물건
3. 추천/검토 가치가 높은 물건
4. 입찰일 또는 마감일이 가까운 물건
5. 법원 등록일 최신순
```

단, 너무 복잡하면 1차는 아래로 충분하다.

```text
1. PASSED 제외
2. 분석 완료 우선
3. 법원 등록일 최신순
```

## 6. 관리자 화면과 역할 분리

사용자 화면에서 줄이는 정보는 관리자 화면에서 유지하거나 강화한다.

관리자 화면에 남길 정보:

- 분석 job 상태
- worker 상태
- 실패 원인
- 모델별 결과
- Gemini/ChatGPT/Codex 비교
- OCR 필요 여부
- UNKNOWN 날짜 항목
- LOCAL_INGESTED 항목
- 관리자 리뷰 입력

즉, 사용자 화면은 판단용, 관리자 화면은 운영용으로 역할을 분리한다.

## 7. 다음 개발 항목 포함 지시

### 7.1 OCR 큐

목표:

```text
텍스트가 비어 있는 PDF/HWP를 AI 분석 실패로 처리하지 않고 OCR 대기 상태로 보낸다.
```

작업:

- `OCR_REQUIRED` 상태 정의
- OCR job 테이블 또는 기존 job_type 확장
- 관리자 화면에 OCR 필요 문서 표시
- OCR 완료 후 분석 대기열로 넘기는 흐름 설계

### 7.2 UNKNOWN 날짜 보정

목표:

```text
notice_date, expire_date가 UNKNOWN인 항목을 관리자에서 확인하고 보정할 수 있게 한다.
```

작업:

- UNKNOWN 날짜 항목 필터
- 상세 페이지 텍스트나 파일명에서 날짜 재추출
- 수동 보정 UI
- 보정 이력 저장

### 7.3 LOCAL_INGESTED 메타데이터 보강

목표:

```text
로컬에서 인입한 파일도 출처, 날짜, 사건번호, 파일명 근거를 가능한 범위에서 보강한다.
```

작업:

- 파일명 기반 사건번호/날짜 추출
- 원본 경로 보존
- 관리자 화면에서 메타데이터 수정
- LOCAL_INGESTED와 실제 법원 수집 데이터 구분 표시

### 7.4 관리자 리뷰 입력 UI

목표:

```text
관리자가 분석 결과 품질을 평가하고, 나중에 모델/프롬프트 개선에 활용한다.
```

권장 테이블:

```text
analysis_reviews
  id
  analysis_result_id
  reviewer_user_id
  price_score
  date_score
  risk_score
  evidence_score
  hallucination_score
  note
  created_at
```

관리자 화면 항목:

- 가격 정확도
- 날짜 정확도
- 위험 판단 정확도
- 원문 근거 충분성
- 환각 의심 여부
- 메모

### 7.5 라우터 분리

목표:

```text
main_app.py에 몰린 route와 화면 준비 로직을 기능별로 분리한다.
```

권장 구조:

```text
backend/api/routes/auth.py
backend/api/routes/user.py
backend/api/routes/admin.py
backend/api/routes/jobs.py
backend/api/routes/documents.py
backend/api/routes/settings.py

backend/view_models/user_events.py
backend/view_models/admin_dashboard.py
backend/services/local_analysis_status.py
backend/services/user_event_actions.py
```

주의:

- URL은 유지한다.
- 기능 변경과 리팩토링을 한 번에 크게 섞지 않는다.
- 먼저 auth와 user action처럼 작은 route부터 분리한다.

## 8. 개발 순서

### Loop 1. 로그인 최소 구현

- `users` 테이블 추가
- 비밀번호 hash 저장
- 로그인/로그아웃 route 추가
- 세션 기반 현재 사용자 확인
- 기본 관리자 계정 생성 방식 마련
- `/user` 접근 시 로그인 필요 처리

완료 기준:

- 로그인 전 `/user` 접근 시 로그인 화면으로 이동
- 로그인 후 `/user` 접근 가능
- 로그아웃 가능

### Loop 2. 사용자별 패스 기능

- `user_event_actions` 테이블 추가
- 패스 API 추가
- 패스 취소 API 추가
- 사용자 목록 쿼리에서 PASSED 제외
- 카드에 패스 버튼 추가
- 패스한 물건 복구 화면 또는 필터 추가

완료 기준:

- A 사용자가 패스한 물건은 A 목록에서 사라진다.
- B 사용자에게는 그대로 보인다.
- DB 원본 데이터는 삭제되지 않는다.

### Loop 3. 사용자 화면 정보량 축소

- 카드 기본 정보 축소
- 반복 요약 제거
- 모델 비교 기본 노출 제거
- 작업 로그 제거
- 상세 보기 구조 단순화
- 관심/패스 중심 액션 배치

완료 기준:

- 목록에서 한 카드가 너무 길지 않다.
- 사용자가 빠르게 넘겨볼 수 있다.
- 원문과 상세 분석은 필요할 때만 연다.

### Loop 4. 관리자 운영 정보 강화

- 사용자 화면에서 제거한 작업 상태 정보는 관리자 화면에 유지
- OCR 필요, UNKNOWN 날짜, LOCAL_INGESTED 필터 추가
- 관리자 리뷰 입력 UI 준비

완료 기준:

- 운영자는 관리자 화면에서 상태를 충분히 볼 수 있다.
- 사용자는 불필요한 운영 정보를 보지 않는다.

### Loop 5. 라우터 분리

- auth route 분리
- user route 분리
- user action service 분리
- 기존 URL 유지
- TestClient로 회귀 검증

완료 기준:

- `/user`, `/admin`, 로그인, 패스 API가 모두 동작한다.
- `main_app.py`가 작아지기 시작한다.

## 9. 권장 검증

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
python -m py_compile main_app.py backend/database/models.py backend/database/crud.py backend/jobs/service.py
```

웹 확인:

```text
/login
/logout
/user
/user/passed
/admin
```

기능 확인:

```text
1. 로그인 전 사용자 화면 차단
2. 로그인 후 사용자 화면 표시
3. 패스 버튼 클릭
4. 목록에서 사라짐
5. 패스 목록에서 복구
6. 복구 후 다시 목록에 표시
7. 관리자 화면에는 원본 데이터 계속 표시
```

## 10. 중요한 결정

패스한 물건은 DB에서 삭제하지 않는다.

권장 방식:

```text
원본 데이터 유지
사용자별 action 기록
목록 조회 시 PASSED 제외
필요하면 패스 목록에서 복구
```

이 방식이 화면에서만 숨기는 것보다 서버와 사용자 경험 양쪽에서 더 좋다. 특히 물건 수가 늘어날수록 DB 조회 단계에서 제외하는 편이 렌더링과 전송량을 줄일 수 있다.

