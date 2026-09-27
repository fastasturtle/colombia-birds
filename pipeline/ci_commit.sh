#!/usr/bin/env bash
# Commit the pipeline's outputs (data/, docs/research/hotspots-check.md, pipeline/mappings/) on top of
# the remote branch and push, WITHOUT touching the working tree, HEAD or the index of the checkout.
# Safe to run while run.py is still writing: used every 20 minutes during a CI run and once at the end.
#
#   pipeline/ci_commit.sh "commit message"
#
# Env: BASE_SHA   commit the run started from (the checkout); files that differ from it are committed
#      BRANCH     branch to push to (default: $GITHUB_REF_NAME)
#      DEPLOY=1   after a push to main, start deploy.yml (needs GH_TOKEN)
# Exit: 0 pushed or nothing to commit, 1 push failed after 3 attempts.
#
# How: a temporary index is loaded from the fresh remote tip, the paths the run changed relative to
# BASE_SHA (modified, new, deleted) are staged into it from the working tree, and the resulting tree is
# committed with the remote tip as parent. Nothing is rebased, so there are no conflicts with commits
# pushed meanwhile (another queue, an earlier flush of this run); a file changed both by this run and
# upstream takes this run's version. Files are read whole: pipeline writes are atomic (tmp + rename,
# common.atomic_write), so a snapshot never contains a half-written file; *.tmp is gitignored.
set -uo pipefail

msg=${1:?commit message}
branch=${BRANCH:-${GITHUB_REF_NAME:?BRANCH or GITHUB_REF_NAME}}
base=${BASE_SHA:?BASE_SHA}
paths=(data docs/research/hotspots-check.md pipeline/mappings)

cd "$(git rev-parse --show-toplevel)" || exit 1
export GIT_AUTHOR_NAME=colombia-birds-bot GIT_AUTHOR_EMAIL=colombia-birds-bot@users.noreply.github.com
export GIT_COMMITTER_NAME=$GIT_AUTHOR_NAME GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL
idx=$(mktemp); list=$(mktemp)
trap 'rm -f "$idx" "$list"' EXIT

for attempt in 1 2 3; do
  tree=
  if git fetch -q origin "$branch"; then
    remote=$(git rev-parse FETCH_HEAD)
    # paths the run changed: tracked ones differing from BASE_SHA (incl. deletions) + new untracked ones
    { git diff -z --name-only --no-renames "$base" -- "${paths[@]}"
      git ls-files -z --others --exclude-standard -- "${paths[@]}"; } | sort -zu > "$list"
    n=$(tr -cd '\0' < "$list" | wc -c)
    if [ "$n" -eq 0 ]; then
      echo "ci_commit: no data changes"
      exit 0
    fi
    GIT_INDEX_FILE=$idx git read-tree "$remote" &&
      GIT_INDEX_FILE=$idx git update-index --add --remove -z --stdin < "$list" &&
      tree=$(GIT_INDEX_FILE=$idx git write-tree)
    if [ -n "${tree:-}" ]; then
      if [ "$tree" = "$(git rev-parse "$remote^{tree}")" ]; then
        echo "ci_commit: nothing new since the last push ($n changed paths already on $branch)"
        exit 0
      fi
      commit=$(git commit-tree "$tree" -p "$remote" -m "$msg")
      if git push -q origin "$commit:refs/heads/$branch"; then
        echo "ci_commit: pushed $(git rev-parse --short "$commit") to $branch ($n paths changed in this run):"
        git diff --stat "$remote" "$commit" | tail -1
        if [ "${DEPLOY:-}" = 1 ] && [ "$branch" = main ]; then
          gh workflow run deploy.yml --ref main || echo "::warning::could not dispatch deploy.yml"
        fi
        exit 0
      fi
    fi
  fi
  echo "ci_commit: attempt $attempt failed, retrying"
  sleep $((attempt * 10))
done
echo "ci_commit: could not push after 3 attempts"
exit 1
