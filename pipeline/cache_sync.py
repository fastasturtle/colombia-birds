"""Sync the HTTP response cache (pipeline/cache/, without media/) with the R2 bucket, prefix cache/http/.

  uv run python cache_sync.py pull     # download cached responses missing locally
  uv run python cache_sync.py push     # upload new/changed local files, update the manifest
  uv run python cache_sync.py status   # upload pipeline/cache/status.json to status/pipeline.json
  uv run python cache_sync.py status --note "(finished)"   # ... with the note appended to `message`
  add --dry-run to print the plan without transferring anything (works without R2 credentials:
  the remote side is then assumed empty)

`status` publishes the live run status written by common.status() (ci_run.sh calls it every 60 s):
public URL https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev/status/pipeline.json. The local file
is never modified; pull/push skip it.

The remote manifest cache/http/_manifest.json maps relpath -> {"sha1", "size"}, so neither command
lists thousands of keys; if it is missing, pull/push fall back to list_objects_v2 once (sha1 then
unknown, size is compared instead) and push writes a fresh manifest.
The cache only grows (keys are URL hashes), so nothing is ever deleted, locally or remotely; pull
never overwrites a file that exists locally. Local files are hashed once: (size, mtime_ns) -> sha1
is remembered in pipeline/cache/.sync_hashes.json. Skipped: media/, dotfiles, *.tmp (atomic-write
temps of a running pipeline, see common.atomic_write).

Two runs pushing at once (heavy + light queue) may race on the manifest: push re-reads it just before
writing and merges, so at worst an entry goes missing and that file is re-uploaded by the next push.

NOTE: the bucket is public (r2.dev), so everything under cache/http/ is world-readable. It holds only
bodies of public API responses (file names are sha1 hashes of the request URL, so API keys passed in
URLs are not exposed); never store anything secret or private under pipeline/cache/.

Env: R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (.env locally, secrets in CI).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CACHE, STATUS_PATH, atomic_write, env, log, r2_client  # noqa: E402

PREFIX = "cache/http/"
MANIFEST_KEY = PREFIX + "_manifest.json"
HASHES = CACHE / ".sync_hashes.json"
SKIP_TOP = {"media", STATUS_PATH.name}  # status.json is published by `status`, not cached
STATUS_KEY = "status/pipeline.json"
WORKERS = 32


def local_files(root: Path = CACHE) -> dict[str, Path]:
    out = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if rel.parts[0] in SKIP_TOP or any(x.startswith(".") for x in rel.parts) or p.name.endswith(".tmp"):
            continue
        if p.is_file():
            out[rel.as_posix()] = p
    return out


def sha1_of(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_missing(e: Exception) -> bool:
    from botocore.exceptions import ClientError

    return isinstance(e, ClientError) and e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound")


def list_remote(s3, bucket: str) -> dict[str, dict]:
    out = {}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=PREFIX):
        for o in page.get("Contents", []):
            rel = o["Key"][len(PREFIX):]
            if rel and o["Key"] != MANIFEST_KEY:
                out[rel] = {"sha1": None, "size": o["Size"]}
    return out


def remote_manifest(s3, bucket: str, fallback_list: bool = True) -> tuple[dict[str, dict], bool]:
    """(manifest, found). Without a manifest object, lists the prefix (if fallback_list)."""
    if s3 is None:
        return {}, False
    try:
        body = s3.get_object(Bucket=bucket, Key=MANIFEST_KEY)["Body"].read()
        return json.loads(body), True
    except Exception as e:
        if not is_missing(e):
            raise
    if not fallback_list:
        return {}, False
    log("cache_sync: no manifest, listing objects")
    return list_remote(s3, bucket), False


def client(dry: bool):
    if dry and not all(env(k) for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")):
        log("cache_sync: no R2 credentials, dry run against an empty remote")
        return None
    return r2_client("cache_sync")


def pull(s3, bucket: str, dry: bool, root: Path = CACHE) -> int:
    t0 = time.monotonic()
    manifest, _ = remote_manifest(s3, bucket)
    have = local_files(root)
    todo = sorted(rel for rel in manifest if rel not in have)
    size = sum(manifest[r].get("size") or 0 for r in todo)
    log(f"cache_sync pull: {len(manifest)} remote, {len(have)} local, {len(todo)} to download ({size / 1e6:.1f} MB)")
    if dry or not todo:
        return 0
    failed = []

    def fetch(rel: str) -> None:
        try:
            body = s3.get_object(Bucket=bucket, Key=PREFIX + rel)["Body"].read()
            atomic_write(root / rel, body)
        except Exception as e:  # one bad object must not stop the rest
            failed.append(f"{rel}: {type(e).__name__}: {str(e)[:120]}")

    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(fetch, todo))
    for f in failed[:10]:
        log(f"  failed {f}")
    log(f"cache_sync pull: downloaded {len(todo) - len(failed)}, failed {len(failed)} in {time.monotonic() - t0:.0f}s")
    return 1 if failed else 0


def push(s3, bucket: str, dry: bool, root: Path = CACHE) -> int:
    t0 = time.monotonic()
    hashes_path = root / HASHES.name
    try:
        hashes = json.loads(hashes_path.read_text())
    except (OSError, ValueError):
        hashes = {}
    manifest, found = remote_manifest(s3, bucket)
    have = local_files(root)
    local: dict[str, dict] = {}
    for rel, p in have.items():
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        h = hashes.get(rel)
        if not (h and h[0] == st.st_size and h[1] == st.st_mtime_ns):
            h = [st.st_size, st.st_mtime_ns, sha1_of(p)]
            hashes[rel] = h
        local[rel] = {"sha1": h[2], "size": h[0]}

    def changed(rel: str) -> bool:
        r = manifest.get(rel)
        if r is None:
            return True
        if r.get("sha1") is None:  # entry from a listing: only the size is known
            return r.get("size") != local[rel]["size"]
        return r["sha1"] != local[rel]["sha1"]

    todo = sorted(rel for rel in local if changed(rel))
    size = sum(local[r]["size"] for r in todo)
    log(f"cache_sync push: {len(local)} local, {len(manifest)} in manifest, {len(todo)} to upload ({size / 1e6:.1f} MB)")
    if dry:
        return 0
    done, failed = [], []

    def put(rel: str) -> None:
        try:
            s3.put_object(Bucket=bucket, Key=PREFIX + rel, Body=(root / rel).read_bytes(),
                          ContentType="application/octet-stream")
            done.append(rel)
        except Exception as e:
            failed.append(f"{rel}: {type(e).__name__}: {str(e)[:120]}")

    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(put, todo))
    atomic_write(hashes_path, json.dumps(hashes, separators=(",", ":")).encode())
    # Manifest: entries we know are in the bucket (uploaded now, or unchanged and matching), merged into
    # the latest remote manifest (another run may have pushed meanwhile).
    need_write = bool(done) or not found or any(manifest[r].get("sha1") is None for r in local if r in manifest)
    if need_write:
        latest, _ = remote_manifest(s3, bucket, fallback_list=False)
        merged = {**manifest, **latest}
        for rel in local:
            if rel in done or (rel in manifest and not changed(rel)):
                merged[rel] = local[rel]
        s3.put_object(Bucket=bucket, Key=MANIFEST_KEY, ContentType="application/json",
                      Body=json.dumps(merged, separators=(",", ":"), sort_keys=True).encode())
        log(f"cache_sync push: manifest {len(merged)} entries")
    for f in failed[:10]:
        log(f"  failed {f}")
    log(f"cache_sync push: uploaded {len(done)} ({size / 1e6:.1f} MB planned), failed {len(failed)} "
        f"in {time.monotonic() - t0:.0f}s")
    return 1 if failed else 0


def status(s3, bucket: str, dry: bool, note: str = "") -> int:
    """Upload STATUS_PATH (with `note` appended to its message) to STATUS_KEY. No file: nothing to do."""
    try:
        st = json.loads(STATUS_PATH.read_text())
    except FileNotFoundError:
        log(f"cache_sync status: no {STATUS_PATH.name} yet")
        return 0
    if note:
        st["message"] = f"{st.get('message', '')} {note}".strip()
    body = json.dumps(st, ensure_ascii=False, indent=1).encode()
    if dry:
        log(f"cache_sync status: would upload {len(body)} bytes to {STATUS_KEY}:\n{body.decode()}")
        return 0
    s3.put_object(Bucket=bucket, Key=STATUS_KEY, Body=body, ContentType="application/json",
                  CacheControl="no-cache")
    log(f"cache_sync status: {st.get('message', '')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["pull", "push", "status"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--note", default="", help="status: text appended to the uploaded message")
    a = ap.parse_args()
    if a.command == "status" and a.dry_run:
        return status(None, "", True, a.note)  # no R2 needed to show the payload
    s3 = client(a.dry_run)
    bucket = env("R2_BUCKET")
    if a.command == "status":
        return status(s3, bucket, a.dry_run, a.note)
    return (pull if a.command == "pull" else push)(s3, bucket, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
