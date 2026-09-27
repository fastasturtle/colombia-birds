---
name: error-reports
description: Build and operate the "сообщить об ошибке" feedback loop (site form → Cloudflare Worker → GitHub issue → agent fix). Use when asked to set up the report button/Worker, or to triage and fix reported content errors.
---

# Error reports: build and triage

Two modes. Read AGENTS.md first. Never print secret values; never commit them.

## Mode A: build the feature (one-time)

Goal: any device, no login, can report a mistake on any page. Reports become GitHub issues labelled `report`.

1. **Worker** in `worker/` (Cloudflare Workers, free tier, TypeScript, `wrangler`):
   - `POST /report` with JSON `{page, species?, message, honeypot, ua}`; CORS allow-origin
     `https://fastasturtle.github.io` and `http://localhost:4321`; reject if `honeypot` non-empty,
     `message` empty or > 1000 chars, or > 5 reports per IP per 10 minutes (Workers KV or Durable Object
     counter; simplest: KV with TTL).
   - Creates an issue via GitHub REST (`POST /repos/fastasturtle/colombia-birds/issues`) using secret
     `GITHUB_REPORTS_TOKEN` (fine-grained, Issues: write only). Title: `[report] <species en or page path>`;
     body: page URL, species id, message, user-agent, timestamp; labels: `report` (+ `species` if species id).
   - Returns `{ok: true, issue: <number>}`; on GitHub error returns 502 with a generic message.
   - `wrangler.toml` with `name = "colombia-birds-reports"`, `compatibility_date`, KV binding `RATE`.
   - Built: `worker/` (see `worker/README.md`). Cloud sessions have no Cloudflare/GitHub secrets, so deploy
     only via Actions → **Deploy report Worker** (`.github/workflows/worker.yml`): uses secrets
     `CLOUDFLARE_WORKERS_TOKEN` (Workers Scripts + KV Storage: Edit) and `REPORTS_TOKEN` (GitHub forbids the `GITHUB_` prefix for secrets; inside the Worker it becomes `GITHUB_REPORTS_TOKEN`), finds or
     creates KV `colombia-birds-reports-RATE` (`worker/scripts/kv-config.mjs` → `wrangler.deploy.toml`),
     `wrangler secret put`s the token, creates labels, prints the URL in the job summary.
   - Put `<worker url>/report` into GitHub variable `PUBLIC_REPORT_URL` (read by `deploy.yml`) and, for local
     builds, `site/.env` (Astro reads `site/.env`, not the root one).
   - Local test without secrets: `npx wrangler dev --local` works offline for KV; POST returns 502 (no token).
2. **Site**: `site/src/components/ReportButton.svelte`, rendered in `Base.astro` footer (all pages);
   species pages pass `species={sp.id}` to `Base`. The form also sends the page `<h1>` as `heading`
   (issue title on species pages). Small button «Сообщить об ошибке» → inline form (textarea, hidden
   honeypot input, send). Prefill page URL. Show «Спасибо, записали» on success, a retry hint on failure.
   Disabled (hidden) when `PUBLIC_REPORT_URL` is not set. Mobile first, ≥ 40 px tap target.
3. Verify: `cd site && npm run build`, screenshots via `npm run shots`, and a real POST with curl to the
   Worker (expect an issue to appear). Add the `report` label to the repo if missing (GitHub API).
4. Document in README (one paragraph) and tick the TODO item.

## Mode B: triage reports (recurring)

1. List open issues with label `report` (GitHub MCP `list_issues`, or `search_issues`
   `repo:fastasturtle/colombia-birds is:open label:report`).
2. For each: open the page it refers to, reproduce the problem against `data/`, `content/` and the
   pipeline. Decide: data bug (fix pipeline/mapping and re-run the step), content error (fix the
   `content/` file), site bug (fix `site/`), or not an error (explain).
3. Fix in the working branch, build, commit with message `fix(report #N): ...`, push; when merged to
   `main`, comment on the issue in one or two sentences (what changed, link to the page) and close it.
   Follow the AGENTS.md rule: do not commit secrets, keep licenses intact.
4. If a report reveals a systematic problem (e.g. many wrong Russian names), open one umbrella issue,
   add it to `docs/TODO.md`, and ask the owner before mass changes (staged rollout rule).
