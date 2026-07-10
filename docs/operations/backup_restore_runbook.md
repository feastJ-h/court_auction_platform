# Backup and restore runbook

백업은 앱 중지 또는 쓰기 부하가 낮을 때 `backup_database.ps1`로 생성하고 SHA-256과 주요 table count를 기록한다. 복원 리허설은 원본 DB가 아닌 `storage/restore-rehearsal` 아래 임시 사본에서 수행한다.

```powershell
./test_restore_rehearsal.ps1
```

리허설은 SQLite integrity check, 주요 table count, 새 코드의 additive migration/idempotence와 smoke query를 확인한다. 실제 복원은 앱을 중지하고 손상/오염 기준이 충족될 때만 `restore_database.ps1`를 사용한다. 원본과 실패 DB는 삭제하지 않고 별도 보존한다.
