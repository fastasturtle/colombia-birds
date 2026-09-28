#!/usr/bin/env python3
"""3-way merge of species JSON for ci_commit.sh (stdlib only; runs outside the uv env).

Two CI runs that start from the same commit both rewrite data/species/<slug>.json and
data/species_index.json (e.g. `build` on the light queue, `upload` on the heavy one). Taking either run's
whole file drops the other's changes, so for these paths ci_commit.sh asks this script for a merged blob:

  species file  start from the remote version, apply the top-level keys this run changed vs BASE_SHA
                (changed, added or removed); everything else keeps the remote value
  index list    per `id` entry, the same per field; entries this run added or removed are added/removed;
                the order is the run's when the run changed the id sequence (build), else the remote's

A key/field changed on both sides takes this run's value (as before for whole files).

  python3 pipeline/ci_merge_json.py BASE_SHA REMOTE_SHA < paths (NUL-separated, relative to the repo root)

For each path that matches the patterns above, exists in the working tree and differs between BASE_SHA and
REMOTE_SHA (changed upstream), writes the merged blob to the object store (`git hash-object -w`) and prints
an `git update-index --index-info` line. Other paths print nothing and keep ci_commit.sh's default (this
run's whole file, or its deletion). A path that fails to parse is skipped the same way (warning on stderr).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SPECIES_RE = re.compile(r"^data/species/[^/]+\.json$")
INDEX = "data/species_index.json"
_MISSING = object()


def dumps(obj: Any) -> str:
    """Same format as common.write_json, so merged files diff cleanly against pipeline output."""
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def merge_dict(base: dict, remote: dict, run: dict) -> dict:
    """Remote + the top-level keys `run` changed relative to `base` (added, modified or removed)."""
    out = dict(remote)
    for k in base.keys() | run.keys():
        b, r = base.get(k, _MISSING), run.get(k, _MISSING)
        if b == r:
            continue
        if r is _MISSING:
            out.pop(k, None)
        else:
            out[k] = r
    return out


def merge_index(base: list, remote: list, run: list) -> list:
    """Per-`id` merge of the species index (see module docstring)."""
    b_by = {e["id"]: e for e in base}
    r_by = {e["id"]: e for e in remote}
    run_by = {e["id"]: e for e in run}
    run_ids, base_ids = [e["id"] for e in run], [e["id"] for e in base]
    primary = run_ids if run_ids != base_ids else [e["id"] for e in remote]

    out: dict[str, dict] = {}
    for i in primary:
        if i in run_by:
            if i in b_by:
                if i not in r_by and run_by[i] == b_by[i]:
                    continue  # deleted upstream, untouched by this run
                out[i] = merge_dict(b_by[i], r_by.get(i, b_by[i]), run_by[i])
            else:  # added by this run (and maybe upstream too)
                out[i] = merge_dict({}, r_by.get(i, {}), run_by[i])
        elif i not in b_by:
            out[i] = r_by[i]  # added upstream only (primary is the remote order here)
        # else: in base but not in this run: this run removed it
    # entries added upstream that the run's order does not know: after their remote predecessor
    result = [out[i] for i in primary if i in out]
    ids = [e["id"] for e in result]
    for pos, e in enumerate(remote):
        i = e["id"]
        if i in out or i in b_by or i in run_by:
            continue
        prev = next((remote[j]["id"] for j in range(pos - 1, -1, -1) if remote[j]["id"] in ids), None)
        at = ids.index(prev) + 1 if prev else 0
        result.insert(at, e)
        ids.insert(at, i)
        out[i] = e
    return result


def merge(path: str, base: Any, remote: Any, run: Any) -> Any:
    if path == INDEX:
        return merge_index(base or [], remote or [], run)
    return merge_dict(base or {}, remote or {}, run)


def git_json(rev: str, path: str) -> Any:
    """JSON of `path` at `rev`, None when the path does not exist there."""
    p = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True)
    return json.loads(p.stdout) if p.returncode == 0 else None


def blob(rev: str, path: str) -> str | None:
    p = subprocess.run(["git", "rev-parse", "-q", "--verify", f"{rev}:{path}"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def main() -> int:
    base_rev, remote_rev = sys.argv[1], sys.argv[2]
    paths = [p for p in sys.stdin.buffer.read().decode().split("\0") if p]
    n = 0
    for path in paths:
        if not (SPECIES_RE.match(path) or path == INDEX) or not Path(path).is_file():
            continue
        if blob(base_rev, path) == blob(remote_rev, path):
            continue  # not changed upstream: the run's file is already the merge
        try:
            run = json.loads(Path(path).read_text())
            merged = merge(path, git_json(base_rev, path), git_json(remote_rev, path), run)
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            print(f"ci_merge_json: {path}: {type(e).__name__}: {e}; taking this run's version", file=sys.stderr)
            continue
        sha = subprocess.run(["git", "hash-object", "-w", "--stdin"], input=dumps(merged).encode(),
                             capture_output=True, check=True).stdout.decode().strip()
        sys.stdout.write(f"100644 {sha}\t{path}\n")
        n += 1
    if n:
        print(f"ci_merge_json: merged {n} file(s) changed both in this run and upstream", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
