# Beta launch runbook

1. `backup_database.ps1`를 실행하고 경로·SHA-256을 별도 운영 기록에 남긴다.
2. `APP_ENV=beta`, 32자 이상의 무작위 `APP_SECRET_KEY`, 비기본 관리자 bootstrap 값, 실제 DB 경로를 설정한다. `LOCAL_DEV_LOGIN_HINT=false`를 확인한다.
3. `python -m backend.cli.bootstrap_admin`를 한 번만 실행하고 임시 자격 증명을 환경에서 제거한다.
4. `start_beta_review.ps1`로 단일 worker를 시작한다. quick tunnel은 `-QuickTunnel`을 명시한 검토 세션에만 사용한다.
5. `/health/live`, `/health/ready`, `/health/version`, `/onbid`를 각각 3회 확인하고 `run_external_beta_e2e.ps1`를 통과시킨다.
6. 종료는 `stop_beta_review.ps1`, 상태 확인은 `status_beta_review.ps1`를 사용한다. stale PID는 status 결과가 `running=false`일 때만 제거한다.

예상치 못한 종료는 Task Scheduler가 `start_beta_review.ps1`를 재실행하도록 구성할 수 있으나, 실제 운영 자동 등록은 관리자 검토 후 수행한다. 로그는 `storage/logs`에 두고 외부로 복사하지 않는다.
