# 백업 및 복구 지침

## DB 백업

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\backup_database.ps1
```

백업 파일은 다음 폴더에 생성된다.

```text
storage\backups
```

파일명 예시:

```text
auction_data_20260705_031500.db
```

## 백업 검증

스크립트는 백업 파일의 SHA-256 해시를 출력한다. 운영 기록에는 다음 세 값을 남긴다.

```text
source
backup
sha256
```

## 복구 절차

1. FastAPI 서버와 분석 워커를 중지한다.
2. 현재 `auction_data.db`를 별도 이름으로 보관한다.
3. 복구할 백업 파일을 `auction_data.db`로 복사한다.
4. FastAPI를 실행한다.
5. `/admin`, `/user`, `/api/local-analysis/status`를 확인한다.

복구 예시:

```powershell
Copy-Item .\auction_data.db .\auction_data.before_restore.db
Copy-Item .\storage\backups\auction_data_YYYYMMDD_HHMMSS.db .\auction_data.db -Force
```

## 파일 보존 정책

- `storage/raw_quarantine`: 최초 다운로드 원본 격리소
- `storage/processed`: 처리 완료 또는 가공 데이터
- `storage/processed/analyzed_documents`: 분석 완료 후 보관되는 원본 문서
- `storage/analysis_jobs`: 분석 job 입력/출력 스냅샷
- `storage/backups`: DB 백업

원본 PDF/HWP는 임의 삭제하지 않는다.
