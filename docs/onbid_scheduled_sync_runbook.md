# 온비드 공매 수집 스케줄 운영 가이드

## 운영 방향

온비드는 회생/파산 공고보다 데이터량과 상태 변경 빈도가 큽니다. 기본 운영은 목록 중심으로 자주 수집하고, 상세 API와 공고 물건정보 API는 별도 스케줄 또는 수동 실행으로 보강합니다.

권장 스케줄:

```text
목록 수집: 매일 06:30, 08:30, 10:30, 12:30, 14:30, 16:30, 18:30, 20:30, 22:30
공고 상세/물건정보 수집: 매일 23:10 또는 필요 시 수동 실행
회생/파산 수집: 평일 08:10, 15:10 / 주말 09:10
```

기본 목록 수집 옵션:

```text
ApiKind=all
Limit=100
MaxPages=8
IncludeDetails=off
```

공고 수집 옵션:

```text
ApiKind=notice
Limit=100
MaxPages=8
IncludeNoticeDetails=on
IncludeNoticeItems=on
```

`ApiKind=all`은 기존 의미를 유지하며 부동산 목록과 동산 목록만 수집합니다. 공고 API는 `ApiKind=notice`로 명시 실행합니다.

## 수동 점검

프로젝트 폴더로 이동합니다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
```

샘플 물건 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -Sample -ApiKind all -Limit 20 -MaxPages 1
```

샘플 공고, 공고 상세, 공고 물건정보 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

실제 API로 부동산과 동산 목록 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind all -Limit 100 -MaxPages 8
```

부동산 상세 API 포함 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind real_estate -Limit 30 -MaxPages 3 -IncludeDetails
```

동산 상세 API 포함 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind movable -Limit 30 -MaxPages 3 -IncludeDetails
```

공고 상세와 공고 물건정보 포함 수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind notice -Limit 100 -MaxPages 8 -IncludeNoticeDetails -IncludeNoticeItems
```

과거 또는 누락분 재수집:

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType backfill -ApiKind notice -Limit 100 -MaxPages 12 -IncludeNoticeDetails -IncludeNoticeItems
```

## Windows 작업 스케줄러 예시

관리자 PowerShell에서 공통 설정을 먼저 만듭니다.

```powershell
$Project = "C:\Users\xogns\Documents\testAuction\court_auction_platform"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
```

목록 수집 작업:

```powershell
$ListAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Project\run_onbid_scheduled_sync.ps1`" -RunType scheduled -ApiKind all -Limit 100 -MaxPages 8"
$Times = @("06:30", "08:30", "10:30", "12:30", "14:30", "16:30", "18:30", "20:30", "22:30")
foreach ($Time in $Times) {
    $SafeTime = $Time.Replace(":", "")
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time
    Register-ScheduledTask -TaskName "OnbidListSync_$SafeTime" -Action $ListAction -Trigger $Trigger -Settings $Settings -Description "ONBID list sync $Time"
}
```

공고 상세/물건정보 수집 작업:

```powershell
$NoticeAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Project\run_onbid_scheduled_sync.ps1`" -RunType scheduled -ApiKind notice -Limit 100 -MaxPages 8 -IncludeNoticeDetails -IncludeNoticeItems"
$NoticeTrigger = New-ScheduledTaskTrigger -Daily -At 23:10
Register-ScheduledTask -TaskName "OnbidNoticeSync_2310" -Action $NoticeAction -Trigger $NoticeTrigger -Settings $Settings -Description "ONBID notice detail and item sync 23:10"
```

상세 API 보강 작업:

```powershell
$DetailAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Project\run_onbid_scheduled_sync.ps1`" -RunType scheduled -ApiKind real_estate -Limit 30 -MaxPages 3 -IncludeDetails"
$DetailTrigger = New-ScheduledTaskTrigger -Daily -At 23:40
Register-ScheduledTask -TaskName "OnbidDetailSync_2340" -Action $DetailAction -Trigger $DetailTrigger -Settings $Settings -Description "ONBID real estate detail sync 23:40"
```

## 상태 확인

관리자 화면:

```text
http://127.0.0.1:8000/admin/collection
```

온비드 품질 API:

```text
GET /api/admin/onbid-quality
```

로그 경로:

```text
storage/logs/onbid/
```

실행 이력 테이블:

```text
crawl_runs
```

주요 실행 유형:

```text
onbid_scheduled
onbid_manual
onbid_backfill
onbid_sample
```

## 운영 주의사항

- 스크립트는 `storage/onbid_scheduled_sync.lock`으로 중복 실행을 막습니다.
- API 키는 `.env` 또는 운영 환경 변수에서만 관리하고 문서나 로그에 남기지 않습니다.
- `ApiKind=notice`는 공고 목록, 공고 상세, 공고 물건정보 흐름입니다. `-IncludeNoticeItems`를 켜면 `AuctionItem` 저장과 `auction_notice_item_links` 연결까지 수행합니다.
- `MaxPages`를 크게 늘리기 전에는 `/admin/collection`의 실패 횟수, 중복 수, 링크율을 확인합니다.
- 실패 이력은 `/admin/collection`, `/api/admin/onbid-quality`, `storage/logs/onbid/`를 함께 확인합니다.
