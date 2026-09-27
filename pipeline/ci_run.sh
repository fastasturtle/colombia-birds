#!/usr/bin/env bash
# CI wrapper: run a command (run.py) in the background and, every FLUSH_MINUTES (default 20) while it
# runs, flush its progress: ci_commit.sh (data/ -> git push, + deploy on main) and cache_sync.py push
# (HTTP cache -> R2). A failed flush only warns and never stops the pipeline; the exit code is the
# command's. The workflow's final steps (if: always()) do the last flush.
#
#   pipeline/ci_run.sh uv run python run.py $STEPS
#
# Env: FLUSH_MINUTES (FLUSH_SECONDS / FLUSH_TICK for tests), plus what ci_commit.sh needs
# (BASE_SHA, BRANCH or GITHUB_REF_NAME, DEPLOY, GH_TOKEN).
set -u
cd "$(dirname "$0")" || exit 1
every=${FLUSH_SECONDS:-$(( ${FLUSH_MINUTES:-20} * 60 ))}
tick=${FLUSH_TICK:-10}   # how often the flusher checks that the command is still running (seconds)

"$@" &
pid=$!
# A background job of a non-interactive shell ignores SIGINT, so forward a cancel to run.py as SIGTERM
# (run.py turns it into KeyboardInterrupt and writes its outputs before exiting).
trap 'kill -TERM "$pid" 2>/dev/null' INT TERM

(
  trap - INT TERM
  while :; do
    waited=0
    while [ "$waited" -lt "$every" ]; do
      kill -0 "$pid" 2>/dev/null || exit 0   # command finished: the final workflow steps flush
      sleep "$tick"
      waited=$((waited + tick))
    done
    echo "::group::progress flush ($(date -u +%H:%M) UTC)"
    ./ci_commit.sh "data: pipeline progress (${STEPS:-$*})" || echo "::warning::progress data push failed (will retry)"
    uv run python cache_sync.py push || echo "::warning::progress cache push failed (will retry)"
    echo "::endgroup::"
  done
) &
flusher=$!

status=0
wait "$pid" || status=$?
# a trapped signal interrupts `wait`: keep waiting until run.py has really exited
while kill -0 "$pid" 2>/dev/null; do wait "$pid" || status=$?; done
wait "$flusher" 2>/dev/null   # lets a flush in progress finish (at most one tick otherwise)
exit "$status"
