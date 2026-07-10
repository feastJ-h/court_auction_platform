# Incident response

- SEV-1: 개인정보·secret 노출 또는 데이터 손상. 즉시 외부 접근 차단, 세션 폐기, 증거 보존, 소유자 통지.
- SEV-2: 로그인/ONBID 전체 장애, 잘못된 상태 대량 노출. 배포 중단, 이전 버전 복귀 판단, 30분 단위 상태 기록.
- SEV-3: category/filter 등 특정 핵심 기능 장애. beta 오픈 보류, 재현 테스트 추가 후 수정.
- SEV-4: 문구·경미한 레이아웃. backlog로 기록하고 정상 배포 흐름에서 처리.

모든 사고 기록에는 KST 시각, request ID, 영향 범위, 완화, 원인, 재발 방지 항목을 포함한다. 로그에 cookie/token/memo/raw URL을 복사하지 않는다.
