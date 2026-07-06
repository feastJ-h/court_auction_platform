# Tesseract OCR 무료 설치 안내

이 프로젝트의 무료 OCR 기본 엔진은 Tesseract OCR입니다.

## 1. 설치 방법

Windows에서는 아래 중 하나를 선택합니다.

1. UB Mannheim Windows 빌드 설치
   - Tesseract OCR Windows installer를 설치합니다.
   - 한국어 언어팩 `kor`를 함께 선택합니다.

2. 설치 후 기본 경로 확인
   - 일반 경로: `C:\Program Files\Tesseract-OCR\tesseract.exe`

## 2. 프로젝트 설정

설치 후 `.env`에 필요하면 아래 값을 입력합니다.

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_LANGUAGE=kor+eng
OCR_DPI=220
OCR_MAX_PAGES=8
```

`TESSERACT_CMD`가 비어 있어도 PATH에 `tesseract`가 잡혀 있으면 자동 감지합니다.

## 3. 상태 확인

PowerShell에서:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ocr_worker.ps1 -Limit 1 -DryRun
```

관리자 화면에서도 `Free OCR Engine` 카드에서 사용 가능 여부를 확인할 수 있습니다.

## 4. 실제 OCR 실행

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ocr_worker.ps1 -Limit 1 -Enqueue
```

개발용 mock OCR:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_ocr_worker.ps1 -Limit 1 -Enqueue -Mock
```
