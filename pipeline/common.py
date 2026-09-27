"""Shared helpers for pipeline steps: paths, cached HTTP, throttling, slugs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
CACHE = PIPELINE / "cache"
DATA = ROOT / "data"
SOURCES = DATA / "sources"
SPECIES_DIR = DATA / "species"

load_dotenv(ROOT / ".env")

USER_AGENT = (
    "colombia-birds-pipeline/0.1 "
    "(https://github.com/fastasturtle/colombia-birds; dima.kozhevnikov@gmail.com)"
)

_last_call: dict[str, float] = {}


def throttle(host: str, min_interval: float) -> None:
    """Sleep so that consecutive calls to `host` are at least `min_interval` seconds apart."""
    now = time.monotonic()
    prev = _last_call.get(host)
    if prev is not None and now - prev < min_interval:
        time.sleep(min_interval - (now - prev))
    _last_call[host] = time.monotonic()


def _cache_path(kind: str, key: str, ext: str) -> Path:
    h = hashlib.sha1(key.encode()).hexdigest()
    p = CACHE / kind / h[:2] / f"{h}.{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


_client = httpx.Client(
    headers={"User-Agent": USER_AGENT, "Api-User-Agent": USER_AGENT},
    timeout=httpx.Timeout(120, connect=30),
    follow_redirects=True,
)


def get(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    kind: str = "http",
    min_interval: float = 0.5,
    retries: int = 4,
    headers: dict[str, str] | None = None,
    binary: bool = False,
    refresh: bool = False,
) -> bytes | str:
    """GET with on-disk cache (keyed by final URL) and polite retry on 429/5xx."""
    req = _client.build_request("GET", url, params=params, headers=headers)
    key = str(req.url)
    path = _cache_path(kind, key, "bin" if binary else "txt")
    if path.exists() and not refresh:
        return path.read_bytes() if binary else path.read_text()
    host = req.url.host
    delay = 2.0
    for attempt in range(retries + 1):
        throttle(host, min_interval)
        try:
            r = _client.send(req)
        except httpx.HTTPError as e:
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2
            continue
        if r.status_code == 200:
            if binary:
                atomic_write(path, r.content)
                return r.content
            write_text(path, r.text)
            return r.text
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            wait = float(r.headers.get("Retry-After") or delay)
            time.sleep(min(wait, 120))
            delay *= 2
            continue
        r.raise_for_status()
    raise RuntimeError(f"unreachable: {url}")


def get_json(url: str, params: dict[str, Any] | None = None, **kw) -> Any:
    return json.loads(get(url, params, **kw))


def atomic_write(path: Path, data: bytes) -> None:
    """Write via tmp file + rename: readers (and the CI commit/cache-sync loop running beside the
    pipeline) see either the old or the new file, never a half-written one; an interrupted run leaves
    no stray .tmp file (`*.tmp` is also gitignored and skipped by cache_sync.py)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(data)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_text(path: Path, text: str) -> None:
    """Atomic Path.write_text (UTF-8)."""
    atomic_write(path, text.encode())


def write_json(path: Path, obj: Any) -> None:
    """Atomic JSON write (see atomic_write)."""
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def slugify(sci_name: str) -> str:
    """'Grallaria milleri' -> 'grallaria-milleri'."""
    s = unicodedata.normalize("NFKD", sci_name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def norm_sci(name: str) -> str:
    """Normalise a scientific name for matching across taxonomies."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", name).strip().lower()


def log(msg: str) -> None:
    print(msg, flush=True)


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def r2_client(who: str = "upload_media"):
    """boto3 S3 client for the Cloudflare R2 bucket (env R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY; bucket name in R2_BUCKET). Exits with a message when any is missing."""
    from botocore.config import Config
    import boto3

    missing = [k for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if not env(k)]
    if missing:
        raise SystemExit(f"{who}: missing env {', '.join(missing)} (set them in .env or use --dry-run)")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
        config=Config(retries={"max_attempts": 5, "mode": "standard"}, max_pool_connections=32),
    )


# ---- Time budget for long per-species steps ----
# MAX_MINUTES (env; run.py --max-minutes sets it) is a budget for the whole process, counted from the
# first import of this module, so with run.py it spans all steps of the run. Per-species steps call
# time_up() before each species: when it is true they finish nothing new, write their outputs and
# return normally, so the CI commit step always gets consistent data well before the hard timeout.
_START = time.monotonic()
_stop_logged: set[str] = set()


def elapsed_min() -> float:
    return (time.monotonic() - _START) / 60


def fmt_elapsed() -> str:
    m = elapsed_min()
    return f"{m:.0f}m" if m < 60 else f"{int(m // 60)}h{int(m % 60):02d}m"


def sigterm_as_interrupt() -> None:
    """Turn SIGTERM (CI cancel/timeout) into KeyboardInterrupt so `finally` blocks run."""
    import signal

    def _raise(signum, frame):
        raise KeyboardInterrupt(f"signal {signum}")

    try:
        signal.signal(signal.SIGTERM, _raise)
    except ValueError:  # not in the main thread
        pass


def time_up(step: str) -> bool:
    """True once MAX_MINUTES has passed; logs the stop line once per step."""
    limit = os.environ.get("MAX_MINUTES")
    if not limit or elapsed_min() < float(limit):
        return False
    if step not in _stop_logged:
        _stop_logged.add(step)
        status(step, None, None, f"{step}: stopped early after {limit} minutes (MAX_MINUTES), resume by re-running")
    return True


# ---- Live status file for watching a run from outside (CI logs only appear after the job ends) ----
# status() prints a progress line (like log) and rewrites pipeline/cache/status.json atomically: a few
# hundred bytes, only at progress lines (every 25-100 species), so it costs nothing. The file never
# leaves the machine from here: in CI, ci_run.sh uploads it every 60 s via `cache_sync.py status` to R2
# `status/pipeline.json` (public: https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev/status/pipeline.json).
# Locally just `cat pipeline/cache/status.json`. cache_sync.py push/pull skip it.
STATUS_PATH = CACHE / "status.json"
_STARTED_AT = datetime.now(timezone.utc)
_history: deque[str] = deque(maxlen=20)


def _iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds").replace("+00:00", "Z")


def status(step: str, done: int | None, total: int | None, message: str, *, echo: bool = True) -> None:
    """Log `message` (unless echo=False) and record it in STATUS_PATH with the step's done/total counts."""
    if echo:
        log(message)
    now = datetime.now(timezone.utc)
    _history.append(f"{now:%H:%M:%S} {message}")
    try:
        write_json(STATUS_PATH, {
            "run_id": os.environ.get("GITHUB_RUN_ID") or "local",
            "steps": os.environ.get("STEPS", ""),
            "step": step,
            "done": done,
            "total": total,
            "message": message,
            "elapsed": fmt_elapsed(),
            "started": _iso(_STARTED_AT),
            "updated": _iso(now),
            "history": list(_history),
        })
    except OSError:  # a status file must never break the pipeline
        pass


def post_form(
    url: str,
    data: dict[str, Any],
    *,
    kind: str = "http",
    min_interval: float = 1.0,
    retries: int = 4,
    headers: dict[str, str] | None = None,
    refresh: bool = False,
) -> str:
    """POST application/x-www-form-urlencoded with the same on-disk cache and retry policy as get()."""
    key = url + "\n" + json.dumps(data, sort_keys=True)
    path = _cache_path(kind, key, "txt")
    if path.exists() and not refresh:
        return path.read_text()
    host = httpx.URL(url).host
    delay = 2.0
    for attempt in range(retries + 1):
        throttle(host, min_interval)
        try:
            r = _client.post(url, data=data, headers=headers)
        except httpx.HTTPError:
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2
            continue
        if r.status_code == 200:
            write_text(path, r.text)
            return r.text
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            time.sleep(min(float(r.headers.get("Retry-After") or delay), 120))
            delay *= 2
            continue
        r.raise_for_status()
    raise RuntimeError(f"unreachable: {url}")


def only_slugs(args: list[str] | None = None) -> set[str]:
    """Species ids to restrict a step to: positional `args` plus the ONLY_SLUGS env var
    (whitespace/comma separated; set by run.py --only and the CI workflow). Empty set = all species."""
    out = {a for a in (args or []) if a and not a.startswith("-")}
    out |= {s for s in re.split(r"[\s,]+", os.environ.get("ONLY_SLUGS", "")) if s}
    return out


# ---- Likelihood of seeing a species at a route site (GBIF autumn frequency within the site radius) ----
# One place for the thresholds: steps gbif_sites and study use these; the site reads the resulting `state`.
SURE_FREQ = 0.01    # freq_aut >= 1%  -> "sure"  («Точно увидим»)
MAYBE_FREQ = 0.001  # freq_aut >= 0.1% -> "maybe" («Возможно»); below, or n_aut < MIN_N_AUT -> "unlikely" («Вряд ли»)
MIN_N_AUT = 3
STATES = ("sure", "maybe", "unlikely")
STATE_RANK = {"sure": 2, "maybe": 1, "unlikely": 0}


def likelihood(n_aut: int, freq_aut: float) -> str:
    """State of a species at a site from its autumn GBIF records: sure / maybe / unlikely."""
    if n_aut < MIN_N_AUT or freq_aut < MAYBE_FREQ:
        return "unlikely"
    return "sure" if freq_aut >= SURE_FREQ else "maybe"
