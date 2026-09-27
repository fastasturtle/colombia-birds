# colombia-birds-reports (Cloudflare Worker)

Receives «Сообщить об ошибке» submissions from the site and files GitHub issues in
`fastasturtle/colombia-birds` labelled `report` (+ `species` when a species id is sent).

- `GET /` → `{"ok":true,"service":"colombia-birds-reports"}` (health)
- `OPTIONS /report` → CORS preflight (origins `https://fastasturtle.github.io`, `http://localhost:4321`)
- `POST /report` JSON `{page, species?, heading?, message, honeypot, ua}` → `{ok:true, issue:N}`
  - 403 unknown origin, 400 bad JSON / non-empty honeypot / message empty or > 1000 chars,
    429 more than 5 reports per IP per 10 min (KV `RATE`, TTL 600 s), 502 GitHub error (generic text).

## Deploy

GitHub Actions → **Deploy report Worker** (`.github/workflows/worker.yml`, also runs on push to `main`
touching `worker/**`). It uses GitHub secrets `CLOUDFLARE_WORKERS_TOKEN` and `REPORTS_TOKEN` (stored on the Worker as `GITHUB_REPORTS_TOKEN`): finds or
creates the KV namespace `colombia-birds-reports-RATE` (`scripts/kv-config.mjs` writes
`wrangler.deploy.toml` with its id), deploys, sets the Worker secret, ensures labels `report`/`species`
and prints the Worker URL in the job summary. Then set the repo variable
`PUBLIC_REPORT_URL=https://colombia-birds-reports.<subdomain>.workers.dev/report` and re-run the Pages deploy.

## Local run and smoke test

```bash
cd worker && npm ci
npx tsc --noEmit
npx wrangler dev --local --port 8787     # KV is simulated; no GITHUB_REPORTS_TOKEN -> POST returns 502
```

```bash
W=http://localhost:8787     # or the deployed https://colombia-birds-reports.<subdomain>.workers.dev
O='Origin: http://localhost:4321'; J='Content-Type: application/json'
curl -s $W/                                                             # health
curl -si -X OPTIONS $W/report -H "$O" | grep -i access-control          # CORS headers
curl -s -w ' %{http_code}\n' -X POST $W/report -H "$O" -H "$J" -d '{"message":"x","honeypot":"bot"}'  # 400
curl -s -w ' %{http_code}\n' -X POST $W/report -H "$O" -H "$J" -d '{"message":""}'                    # 400
curl -s -w ' %{http_code}\n' -X POST $W/report -H "$O" -H "$J" \
  -d '{"page":"https://fastasturtle.github.io/colombia-birds/species/grallaria-milleri/","species":"grallaria-milleri","heading":"Brown-banded Antpitta","message":"test report, please close","ua":"curl"}'
# 200 {"ok":true,"issue":N} with a token (local: put GITHUB_REPORTS_TOKEN=... in worker/.dev.vars), else 502.
# Repeat the last call 6 times: the 6th within 10 minutes returns 429.
```

A real test against production creates a real issue: close it afterwards.
