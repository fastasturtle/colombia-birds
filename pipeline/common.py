"""Shared helpers for pipeline steps: paths, cached HTTP, throttling, slugs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
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
                path.write_bytes(r.content)
                return r.content
            path.write_text(r.text)
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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    tmp.replace(path)


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
            path.write_text(r.text)
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
