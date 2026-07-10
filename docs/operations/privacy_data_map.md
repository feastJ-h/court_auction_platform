# Privacy data map

| 영역 | 최소 데이터 | 접근 | 기본 보존/처리 |
|---|---|---|---|
| 계정 | username, 표시명, password hash, 상태·동의 버전 | 본인/관리자 | 비활성 후 정책 기간 보존 |
| 세션/폐기 | 서명 cookie, 해시된 session ID | 시스템 | 최대 12시간+정리 |
| rate limit | keyed IP hash, scope/count | 시스템/운영자 | window 만료 즉시 정리 |
| 관심·패스·감시·메모 | user/item/action, 개인 메모 | 본인/관리자 최소권한 | 계정 요청 시 export/delete workflow |
| analytics | allowlist event, 내부 item/user ID | 관리자 | raw URL·검색어·메모 금지 |
| audit | actor ID, action, 대상, 안전한 metadata | 관리자 | 운영·보안 감사 기간 |
| issue report | 유형, 선택 메모, 개인정보 포함 표시 | 제출자/관리자 | 해결 후 정책 기간 |
| share | 무작위 token, 공개 요약, revoke 시각 | 링크 보유자/소유자 | revoke 즉시 차단 |

관리자 요청 workflow는 계정 비활성화 → 사용자 데이터 export → preference/memo 삭제 검토 → 공유 revoke → audit 기록 순서다. 공개 serializer는 memo, raw payload, 내부 파일 경로를 포함하지 않는다.
