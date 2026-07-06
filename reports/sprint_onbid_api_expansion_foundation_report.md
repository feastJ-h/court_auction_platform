# 온비드 API 확장 기반 스프린트 리포트

## 1. 목표
- 기존 부동산 목록 API 중심 구조를 정리하고, 추가 예정인 부동산 상세 API와 동산 API를 받을 수 있는 확장 기반을 만들었습니다.
- 실제 추가 API 명세가 확정되기 전에도 샘플 데이터로 저장, 목록, 상세, 사건 연결 흐름을 검증할 수 있게 했습니다.

## 2. 구현 내용
- 온비드 클라이언트 호출 공통화를 진행했습니다.
  - 부동산 목록: 기존 `getRlstCltrList2` 유지
  - 부동산 상세: `ONBID_REAL_ESTATE_DETAIL_BASE_URL`, `ONBID_REAL_ESTATE_DETAIL_OPERATION` 설정 자리 추가
  - 동산 목록: `ONBID_MOVABLE_API_BASE_URL`, `ONBID_MOVABLE_LIST_OPERATION` 설정 자리 추가
- 샘플 데이터를 확장했습니다.
  - 부동산 상세 샘플 3건
  - 동산 샘플 2건
- 수집 실행기에 API 종류 옵션을 추가했습니다.
  - `api_kind=real_estate`
  - `api_kind=movable`
  - `api_kind=all`
  - `include_details=true`
- 관리자 온비드 수집 API도 동일 옵션을 받도록 확장했습니다.
- 온비드 목록 화면에서 동산 필터와 샘플 수집 버튼을 추가했습니다.

## 3. 보안/운영 메모
- API 키 원문은 코드와 리포트에 기록하지 않습니다.
- 실제 상세/동산 API 엔드포인트는 `.env` 설정으로만 주입하도록 준비했습니다.
- 동산 API 명세가 오기 전까지 실제 동산 호출은 설정 미완료 오류를 내고, 샘플 모드는 정상 동작합니다.

## 4. 검증 결과
- 문법 검사: 통과
- `tests/onbid_module_test.py`: 통과
- `tests/router_boundary_test.py`: 통과
- `tests/page_response_smoke_test.py`: 통과

## 5. 다음 작업
- 실제 부동산 상세 API 명세 수령 후 파라미터명과 응답 필드 매핑 보정
- 실제 동산 API 명세 수령 후 엔드포인트/필수 파라미터/상세 필드 매핑
- 온비드 상세 화면에서 부동산/동산별 필드 그룹 분리
- 수집 실패 재시도 큐와 API 호출 제한 대응
