# 로그인/개인화/사용자 UI 개선 결과 리포트

작성일: 2026-07-05

## 1. 목표
`login_personalized_user_ui_and_next_work_instruction.md` 기준으로 간단 로그인, 사용자별 패스 목록, 사용자 화면 정보량 축소, 관리자 접근 제한 기반을 구현한다.

## 2. 구현한 내용
- `users` 테이블 추가
- `user_event_actions` 테이블 추가
- PBKDF2-SHA256 기반 비밀번호 해시 저장
- 표준 라이브러리 기반 HMAC 서명 쿠키 로그인 구현
- `/login` 로그인 페이지 추가
- `/logout` 로그아웃 추가
- `/user` 로그인 필요 처리
- `/admin` admin 역할 필요 처리
- 관리자 API 보호:
  - `/api/admin/collection-quality`
  - `/api/admin/analysis-reviews/summary`
  - `/api/admin/analysis-results/{analysis_result_id}/reviews`
- 기본 로컬 관리자 계정 자동 생성
  - username: `admin`
  - password: `admin1234!`
  - `.env`의 `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`로 변경 가능
- 사용자별 `PASSED` 액션 저장
- `/user/events/{event_id}/pass` 패스 처리
- `/user/events/{event_id}/unpass` 패스 취소
- `/user/passed` 패스한 물건 복구 화면 추가
- 사용자 목록 DB 조회 단계에서 로그인 사용자의 `PASSED` 물건 제외
- 사용자 상세 화면에서 모델 비교/작업 로그 탭을 제거하고, `요약`, `가격/일정`, `상세 분석`, `원문 근거` 중심으로 축소

## 3. 수정한 파일
- `backend/config.py`
- `backend/database/models.py`
- `backend/database/session.py`
- `backend/database/crud.py`
- `backend/services/auth.py`
- `backend/services/user_event_actions.py`
- `main_app.py`
- `frontend/templates/auth/login.html`
- `frontend/templates/user/index.html`
- `frontend/templates/user/passed.html`
- `frontend/static/app.js`

## 4. 검증 결과
- Python 문법 검증 통과
- JavaScript 문법 검증 통과
- 로그인 전 `/user` -> `/login?next=/user` 리다이렉트 확인
- 로그인 전 `/admin` -> `/login?next=/admin` 리다이렉트 확인
- 로그인 전 관리자 API 401 확인
- `admin / admin1234!` 로그인 성공
- 로그인 후 `/user` 200
- 로그인 후 `/admin` 200
- 로그인 후 `/user/passed` 200
- 패스 처리 시 `user_event_actions`에 `PASSED` row 생성 확인
- 패스 취소 시 `PASSED` row 삭제 확인
- 원본 `asset_events`, `raw_documents` 삭제 없음
- FastAPI 서버 재시작 후 `/login`, `/user`, `/admin`, `/user/passed` 재확인

## 5. 보안 및 운영 메모
- 현재는 로컬/소규모 운영용 1차 로그인이다.
- 기본 비밀번호는 반드시 `.env`에서 바꾸는 것을 권장한다.
- 쿠키는 HMAC 서명되어 위변조를 방지하지만, 장기 운영 전에는 HTTPS 및 더 강한 세션 저장소를 검토해야 한다.
- 일반 사용자 계정 생성 UI는 아직 없다.

## 6. 다음 작업 권장
1. 관리자 사용자 관리 화면 추가
2. 비밀번호 변경 기능 추가
3. 패스 외 `BOOKMARKED`, `WATCHING` 액션 추가
4. 사용자 화면 카드 추가 축소 및 관심/추천 중심 UX 고도화
5. 관리자 리뷰 입력 UI 구현
6. UNKNOWN 날짜 보정 UI 구현
7. LOCAL_INGESTED 메타데이터 보강 UI 구현
8. OCR job 큐 구현
9. `auth`, `user action` 라우터부터 `backend/api/routes`로 분리
