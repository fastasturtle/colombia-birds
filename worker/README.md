# colombia-birds-reports (Cloudflare Worker)

Receives «Сообщить об ошибке» submissions from the site and files GitHub issues in
`fastasturtle/colombia-birds` labelled `report` (+ `species` when a species id is sent).

- `GET /` → `{"ok":true,"service":"colombia-birds-reports"}` (health)
- `OPTIONS /report` → CORS preflight (origins `https://fastasturtle.github.io`, `http://localhost:4321`)
- cron triggers dispatch GitHub workflows (see «Cron: запуск workflow» below)
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

## Cron: запуск workflow

Расписания GitHub под нагрузкой опаздывают на часы (19.10: `observations` раз в 5–7 часов вместо 2), а cron
Cloudflare срабатывает в ту же минуту. Поэтому Worker сам запускает workflow через GitHub REST API
(`POST /repos/fastasturtle/colombia-birds/actions/workflows/<file>/dispatches`, ветка `main`), обработчик
`scheduled` в `src/index.ts`, расписания в `[triggers]` `wrangler.toml` (UTC):

| cron | workflow | inputs |
|---|---|---|
| `47 */2 * * *` | `observations.yml` | `scheduled: "true"`: шаг «Still on the trip?» останавливает прогоны после поездки, как у cron GitHub |
| `13 10 * * *` | `weather.yml` | нет (после поездки шаг сам не трогает `data/weather.json`) |

Имена файлов и ветка лежат в `[vars]` (`OBSERVATIONS_WORKFLOW`, `WEATHER_WORKFLOW`, `DISPATCH_REF`); строки cron
должны совпадать с `CRON_*` в `src/index.ts` (`event.cron` приходит дословно из `wrangler.toml`). Cron GitHub в
самих workflow остались запасными (`observations` в :17, `weather` в 10:13); двойной прогон безвреден: второй ничего
нового не находит и ничего не коммитит. Ручной «Run workflow» у `observations` (по умолчанию `scheduled = false`)
работает всегда.

`kv-config.mjs` при деплое заменяет в `wrangler.toml` только id KV, так что `[triggers]` и `[vars]` попадают в
`wrangler.deploy.toml` как есть. Worker передеплоивает `.github/workflows/worker.yml` при пуше в `main`, если
изменились `worker/**` или сам workflow.

**Токен.** Тот же секрет `REPORTS_TOKEN` (в Worker `GITHUB_REPORTS_TOKEN`), что создаёт issues. Для dispatch ему
нужны права:
- fine-grained PAT: на репозиторий `fastasturtle/colombia-birds` кроме **Issues: Read and write** ещё
  **Actions: Read and write**. Без него dispatch отвечает 403. Поправить права на
  https://github.com/settings/personal-access-tokens (Edit у токена); при смене одних прав значение токена не
  меняется, перевыпускать и переписывать секрет не нужно;
- classic PAT: scope `repo` покрывает и issues, и `workflow_dispatch` (scope `workflow` нужен только для правки
  файлов workflow, здесь не нужен).

**Проверка.** Логи cron: Cloudflare dashboard → Workers → colombia-birds-reports → Logs / Cron events (строка
`dispatch observations.yml main 204`; при ошибке `dispatch failed <status> <начало ответа>`, и вызов помечен как
упавший). В GitHub: Actions → observations, прогон с event `workflow_dispatch` в xx:47 UTC от владельца токена
(actor). Локально: `npx wrangler dev --local --test-scheduled`, затем
`curl "http://localhost:8787/__scheduled?cron=47+*/2+*+*+*"` (без токена в `.dev.vars` получится 401 в логе;
с настоящим токеном это запустит настоящий workflow).

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
