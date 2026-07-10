# Named tunnel setup

권장 이름은 `court-auction-beta`다. 기존 Cloudflare 계정·도메인·credential 소유권이 확인된 경우에만 named tunnel을 만든다. 임의 도메인 구매나 DNS 소유권 변경은 하지 않는다.

credential이 없는 환경에서는 `start_beta_review.ps1 -QuickTunnel`로 일회성 QA를 수행하고 URL을 운영 기록에만 남긴다. named tunnel은 hostname → `http://127.0.0.1:8000`, ingress 마지막 규칙 → 404로 제한한다. credential JSON은 저장소 밖에 두고 commit scan에서 확인한다.

릴리스 gate는 DNS 3회, live/ready/onbid 각 3회, `run_external_beta_e2e.ps1` 통과다. 502/503 발생 시 app PID·8000 listener·app stderr·cloudflared stderr 순서로 확인한다.
