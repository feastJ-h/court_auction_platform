# 회생·파산 정기 수집 운영 가이드

## 1. 운영 방향

회생·파산 공고 수집은 AI 분석의 원천 데이터 확보가 목적입니다. 온비드보다 데이터 변동량이 적고 분석 비용이 뒤따르기 때문에, 초기 운영은 간헐적인 수집을 권장합니다.

권장 스케줄:

```text
평일 08:10, 15:10
주말 09:10
보정 수집은 수동 실행
```

기본 실행 옵션:

```text
Limit=40
MaxPages=8
DaysBack=7
```

## 2. 수동 검증

프로젝트 폴더:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
```

DryRun 검증:

```powershell
.\run_scheduled_crawl.ps1 -DryRun
```

최근 7일 기준 실제 수집:

```powershell
.\run_scheduled_crawl.ps1 -RunType scheduled -Limit 40 -MaxPages 8 -DaysBack 7
```

특정 시작일 이후 보정 수집:

```powershell
.\run_scheduled_crawl.ps1 -RunType backfill -StartDate 2026-06-15 -Limit 50 -MaxPages 15
```

## 3. Windows 작업 스케줄러 등록 예시

관리자 PowerShell에서 공통 액션을 만듭니다.

```powershell
$Project = "C:\Users\xogns\Documents\testAuction\court_auction_platform"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Project\run_scheduled_crawl.ps1`" -RunType scheduled -Limit 40 -MaxPages 8 -DaysBack 7"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
```

평일 08:10:

```powershell
$TriggerWeekdayMorning = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 08:10
Register-ScheduledTask -TaskName "RecoveryBankruptcyCrawl_Weekday_0810" -Action $Action -Trigger $TriggerWeekdayMorning -Settings $Settings -Description "Recovery and bankruptcy crawl weekday 08:10"
```

평일 15:10:

```powershell
$TriggerWeekdayAfternoon = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 15:10
Register-ScheduledTask -TaskName "RecoveryBankruptcyCrawl_Weekday_1510" -Action $Action -Trigger $TriggerWeekdayAfternoon -Settings $Settings -Description "Recovery and bankruptcy crawl weekday 15:10"
```

주말 09:10:

```powershell
$TriggerWeekend = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday,Sunday -At 09:10
Register-ScheduledTask -TaskName "RecoveryBankruptcyCrawl_Weekend_0910" -Action $Action -Trigger $TriggerWeekend -Settings $Settings -Description "Recovery and bankruptcy crawl weekend 09:10"
```

## 4. 상태 확인

관리자 화면:

```text
http://127.0.0.1:8000/admin/collection
```

로그:

```text
storage/logs/crawl_runs/
```

DB 이력:

```text
crawl_runs
```

## 5. 운영 주의사항

- `storage/scheduled_crawl.lock`으로 중복 실행을 막습니다.
- 분석 비용이 생길 수 있으므로 회생·파산 수집은 온비드보다 적게 돌리는 구성을 권장합니다.
- 보정 수집은 정기 수집과 같은 시간에 겹치지 않게 수동으로 실행합니다.
- 실패가 발생해도 성공적으로 저장된 데이터는 유지됩니다. 실패 상세는 `/admin/collection`과 로그 파일에서 확인합니다.
