# 온비드 공매 통합 조회 MVP 스프린트 리포트

## 1. 구현된 주요 기능
- 첨부 지시서의 1차 범위를 기준으로 온비드 공매 정보 MVP 기반을 추가했습니다.
- 공매 DB 테이블을 추가했습니다.
  - `auction_items`
  - `auction_item_snapshots`
  - `auction_notices`
  - `auction_results`
  - `case_auction_links`
  - `auction_alerts`
- API 키 없이도 개발/검증 가능한 온비드 샘플 클라이언트를 추가했습니다.
- 온비드 샘플 수집 실행기를 추가했습니다.
  - `backend/workers/onbid_sync.py`
  - `run_onbid_sync.ps1`
- 사용자/관리자 공매 조회 화면을 추가했습니다.
  - `/auctions`
  - `/auctions/{auction_item_id}`
- 관리자용 샘플 수집 API를 추가했습니다.
  - `POST /api/admin/auctions/onbid/sync?sample=true`
- 회생·파산 사건과 공매 물건 수동 연결 API를 추가했습니다.
  - `POST /api/admin/auctions/{auction_item_id}/links`
- 공매 분석 기초 계산을 추가했습니다.
  - 감정가 대비 최저가율
  - 저감률
  - D-day
  - 보수/기준/낙관 예상 회수액
  - 룰 기반 환가 가능성 점수

## 2. 보안 및 예외 처리
- 온비드 API 원문 데이터는 사용자 화면에 그대로 노출하지 않고 `raw_payload`에 JSON 문자열로 저장합니다.
- 관리자만 온비드 수집과 사건 연결 API를 호출할 수 있습니다.
- 실제 온비드 API 키가 없는 경우 외부 네트워크 호출 없이 샘플 데이터로 동작합니다.
- 사건 연결은 자동 확정하지 않고 관리자 수동 연결 흐름으로 구현했습니다.
- 수집 이력은 기존 `crawl_runs`에 `onbid_sample` 또는 `onbid_sync` 유형으로 남깁니다.

## 3. 테스트 결과
- 문법 검사 통과:
  - `main_app.py`
  - `backend/config.py`
  - `backend/database/models.py`
  - `backend/services/auction_items.py`
  - `backend/onbid/client.py`
  - `backend/workers/onbid_sync.py`
  - `tests/onbid_module_test.py`
- 격리 DB 테스트 통과:
  - `tests/onbid_module_test.py`
  - 샘플 수집 3건 적재
  - `/auctions` 목록 렌더링 확인
  - `/auctions/{id}` 상세 렌더링 확인
  - 공매 물건과 회생·파산 사건 수동 연결 확인
- 기존 운영 격리 테스트 통과:
  - `tests/isolated_operations_test.py`
- 로컬 운영 DB 준비:
  - `run_onbid_sync.ps1 -Sample -Limit 20` 실행 성공
  - 샘플 온비드 공매 3건 적재
- 웹 검증:
  - `/auctions` HTTP 200
  - 목록에 `서울 종로구 숭인동 오피스텔 공매` 표시 확인
  - 상세 화면에 `환가 분석`, `사건 연결` 표시 확인

## 4. 관리자 준비 사항
- 실제 온비드 API 연동 전 필요한 값:
  - `ONBID_API_KEY`
  - 실제 엔드포인트 매핑이 필요한 경우 `ONBID_API_BASE_URL`
- 현재 빌드는 API 키가 없으면 샘플 데이터로 동작합니다.
- 온비드 실제 API 스펙이 확정되면 `backend/onbid/client.py`의 `fetch_real_estate_items`를 실제 호출로 교체하면 됩니다.

## 5. 다음 스프린트 큐
- 실제 온비드 API 명세 확인 및 목록/상세/결과 엔드포인트 연결.
- `/admin/assets`, `/admin/analysis`, `/admin/reviews` 관리자 화면 실제 분리.
- 주소/법인명 정규화 기반 자동 연결 후보 추천 구현.
- `case_auction_links` 연결 상태 변경 UI 구현: 후보, 확인중, 연결완료, 연결제외, 매각완료, 환가포기.
- 입찰 결과 수집과 상태 변경 알림 기초 구현.
- 사건 상세 화면에 `공매 연결` 탭 추가.
