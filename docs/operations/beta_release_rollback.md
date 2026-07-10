# Beta release rollback

1. `stop_beta_review.ps1`로 app/tunnel을 중지한다.
2. 현재 commit, health 응답, 오류 request ID를 기록하고 이전 검증 commit을 새 rollback 브랜치에서 checkout한다. history force rewrite는 금지한다.
3. additive column/table은 이전 코드와 공존하므로 기본적으로 DB rollback을 하지 않는다. 데이터 손상·오염이 확인된 경우에만 사전 백업 SHA/count를 검증해 복원한다.
4. named/quick tunnel 대상은 이전 정상 app으로 되돌리고 DNS 소유권·credential을 변경하지 않는다.
5. app을 단일 worker로 시작하고 live/ready/version/onbid 및 외부 category E2E를 3회 확인한다.

SQLite column 제거는 지원하지 않으며 destructive migration rollback은 별도 승인 작업이다.
