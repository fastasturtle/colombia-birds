#!/usr/bin/env bash
# One-shot environment setup for a fresh checkout (local or Claude Code cloud session).
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== pipeline (uv)"; (cd pipeline && uv sync -q)
echo "== site (npm)"; (cd site && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD="${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" npm install --silent)
if [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ] && ! (cd site && npx --no playwright --version >/dev/null 2>&1 && ls ~/.cache/ms-playwright 2>/dev/null | grep -q chromium); then
  echo "== playwright chromium"; (cd site && npx playwright install chromium)
fi
echo "done. Try: cd site && npm run build && npm run shots"
