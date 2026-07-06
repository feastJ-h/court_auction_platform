# 온비드 자동 매칭 및 관리자 화면 분리 스프린트 리포트

## 1. 구현된 주요 기능
- 공매 물건과 회생·파산 사건의 자동 연결 후보 계산 기능을 추가했습니다.
- 후보 점수 기준:
  - 주소 유사성
  - 물건명/공고명 유사성
  - 공고문/원문 내 사건번호 포함 여부
  - 자산 유형 일치 여부
- 공매 상세 화면에 `자동 연결 후보` 영역을 추가했습니다.
- 후보를 `candidate` 상태로 저장할 수 있게 했습니다.
- 관리자 화면을 목적별로 1차 분리했습니다.
  - `/admin/assets`
  - `/admin/analysis`
  - `/admin/reviews`
  - 기존 `/admin/collection` 유지
- 양방향 후보 API를 추가했습니다.
  - `GET /api/admin/auctions/{auction_item_id}/link-candidates`
  - `GET /api/cases/{case_id}/auction-link-candidates`
- 장시간 개발 계획 문서 `long_running_onbid_development_plan.md`를 작성했습니다.

## 2. 보안 및 예외 처리
- 후보 계산은 확정 연결을 만들지 않고, 관리자가 명시적으로 저장해야 DB에 반영됩니다.
- 후보 저장 API는 관리자 권한이 필요합니다.
- 원문 전문은 후보 계산에 내부적으로만 사용하고 사용자 화면에 노출하지 않습니다.
- 실제 온비드 API 키 없이도 샘플 데이터 기반으로 기능 검증이 가능합니다.

## 3. 테스트 결과
- 문법 검사 통과:
  - `main_app.py`
  - `backend/services/auction_items.py`
  - `tests/onbid_module_test.py`
- 격리 DB 테스트 통과:
  - 샘플 온비드 수집
  - 공매 목록/상세 렌더링
  - 자동 연결 후보 API
  - 사건 기준 후보 API
  - 후보/수동 연결 저장
  - `/admin/assets`, `/admin/analysis`, `/admin/reviews` 렌더링

## 4. 다음 단계
- 사용자가 온비드 API 키를 준비하면 `backend/onbid/client.py`의 실제 엔드포인트 매핑을 진행합니다.
- 사건 상세 화면에 `공매 연결` 탭을 붙여 사건 기준 워크플로우를 완성합니다.
- 연결 상태 변경 UI와 알림 테이블을 추가합니다.
