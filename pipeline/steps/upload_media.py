"""Download chosen photos, make JPEG variants, upload to Cloudflare R2, record attribution.

Reads data/photos/<slug>.json (from fetch_photos.py). Per species takes the top N candidates:
1 by default, 4 for slugs listed in data/focus_species.json (a JSON array; created empty if absent).

  originals -> pipeline/cache/media/original/   (gitignored, cached; Commons "original" = 1920px thumb)
  variants  -> pipeline/cache/media/resized/<slug>/<n>-{thumb,medium,large}.jpg
               longest side 400 / 1000 / 1600 px (never upscaled), JPEG q82, EXIF stripped
  R2 keys   -> photos/<slug>/<n>-<size>.jpg  (immutable cache headers; existing keys with the same
               source are skipped via head_object)

Candidates with `kind: "illustration"` (historical plates/artwork) are never used as photo #1 and at
most one is used per species. Credits and species `photos[]` carry `kind`; credits also keep the
original `attribution_raw` when the author was cleaned up.

Right after each species, writes data/credits/<slug>.json (full attribution) and sets `photos` in
data/species/<slug>.json (atomic writes); `photo` (thumb key of photo 1) in data/species_index.json is
rewritten every 50 species and at the end (also on Ctrl-C/SIGTERM). Keys are relative; the site prepends
PUBLIC_MEDIA_BASE_URL.

Order: slugs in data/focus_species.json first, then the rest alphabetically. Progress every 25 species.
Re-running is cheap: when all three R2 keys of a photo already exist with the same `source-url`
metadata, nothing is downloaded (head_object; the large variant's size comes from its `width`/`height`
metadata, or for objects uploaded before that metadata existed from a 64 KB ranged read of its JPEG
header), and the metadata is filled into data/ again. This restores data/ after a lost run and re-applies
`photos` after build_species.py wiped them. Honours MAX_MINUTES (see run.py).

Usage: uv run python steps/upload_media.py [--dry-run] [--only slug ...]
  (slugs can also come from the ONLY_SLUGS env var)
Env: R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (not needed with --dry-run)
"""
from __future__ import annotations

import datetime as dt
import io
import sys
import time
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (  # noqa: E402
    CACHE, DATA, SPECIES_DIR, env, fmt_elapsed, get, log, only_slugs, read_json, sigterm_as_interrupt, time_up,
    write_json,
)

PHOTOS = DATA / "photos"
CREDITS = DATA / "credits"
FOCUS = DATA / "focus_species.json"
RESIZED = CACHE / "media" / "resized"
SIZES = {"thumb": 400, "medium": 1000, "large": 1600}
DEFAULT_N, FOCUS_N = 1, 4
QUALITY = 82
CACHE_CONTROL = "public,max-age=31536000,immutable"
PROGRESS_EVERY = 25
INDEX_EVERY = 50

Image.MAX_IMAGE_PIXELS = 200_000_000


def r2_client():
    from botocore.config import Config
    import boto3

    missing = [k for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if not env(k)]
    if missing:
        sys.exit(f"upload_media: missing env {', '.join(missing)} (set them in .env or use --dry-run)")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
        config=Config(retries={"max_attempts": 5, "mode": "standard"}),
    )


def download(url: str) -> bytes:
    host_interval = 1.1 if "inaturalist" in url else 1.0
    return get(url, kind="media/original", binary=True, min_interval=host_interval)


def make_variants(raw: bytes, slug: str, n: int) -> dict[str, dict]:
    """Return {size: {path, width, height}}; writes JPEGs under cache/media/resized/<slug>/."""
    im = Image.open(io.BytesIO(raw))
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "L"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        rgba = im.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[-1])
        im = bg
    elif im.mode == "L":
        im = im.convert("RGB")
    out = {}
    for size, px in SIZES.items():
        v = im.copy()
        v.thumbnail((px, px), Image.LANCZOS)  # longest side <= px, keeps aspect, never upscales
        path = RESIZED / slug / f"{n}-{size}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        # no exif= / icc_profile= passed -> metadata stripped
        v.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        out[size] = {"path": path, "width": v.width, "height": v.height}
    return out


def ascii_meta(s: str) -> str:
    return quote(s or "", safe=":/?&=%#+,;@()!*'~.-_")[:1024]


class Stats:
    uploaded = 0        # objects put to R2
    skipped = 0         # objects already in R2 with the same source
    bytes = 0           # bytes uploaded
    restored = 0        # photos filled in from R2 without downloading


def head(s3, bucket: str, key: str) -> dict | None:
    """head_object, or None if the key does not exist."""
    from botocore.exceptions import ClientError

    try:
        return s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound"):
            raise
        return None


def upload(s3, bucket: str, key: str, path: Path, source_url: str, width: int, height: int) -> bool:
    """Upload unless the key already exists with the same source. Returns True if uploaded."""
    h = head(s3, bucket, key)
    if h is not None and h.get("Metadata", {}).get("source-url") == ascii_meta(source_url):
        Stats.skipped += 1
        return False
    s3.upload_file(
        str(path), bucket, key,
        ExtraArgs={
            "ContentType": "image/jpeg",
            "CacheControl": CACHE_CONTROL,
            "Metadata": {"source-url": ascii_meta(source_url), "width": str(width), "height": str(height)},
        },
    )
    Stats.uploaded += 1
    Stats.bytes += path.stat().st_size
    return True


def existing_size(s3, bucket: str, keys: dict[str, str], source_url: str) -> tuple[int, int] | None:
    """(width, height) of the large variant if every size is already in R2 from `source_url`, else None.
    No download: head_object per key, plus a 64 KB ranged read of the large JPEG only when it predates
    the width/height metadata."""
    want = ascii_meta(source_url)
    heads = {}
    for size, key in keys.items():
        h = head(s3, bucket, key)
        if h is None or h.get("Metadata", {}).get("source-url") != want:
            return None
        heads[size] = h
    meta = heads["large"].get("Metadata", {})
    if meta.get("width") and meta.get("height"):
        return int(meta["width"]), int(meta["height"])
    body = s3.get_object(Bucket=bucket, Key=keys["large"], Range="bytes=0-65535")["Body"].read()
    try:
        return Image.open(io.BytesIO(body)).size
    except Exception:
        return None  # header not readable from the prefix: fall back to download + re-check


def process(slug: str, cands: list[dict], n_wanted: int, s3, bucket: str | None, dry: bool) -> list[dict]:
    chosen = []
    for c in cands:
        if len(chosen) >= n_wanted:
            break
        kind = c.get("kind", "photo")
        # a historical illustration is only an extra: never photo #1, at most one per species
        if kind == "illustration" and (not chosen or any(x["kind"] == "illustration" for x in chosen)):
            continue
        n = len(chosen) + 1
        base = f"photos/{slug}/{n}"
        keys = {size: f"{base}-{size}.jpg" for size in SIZES}
        size_wh = None if dry else existing_size(s3, bucket, keys, c["source_url"])
        if size_wh:  # already uploaded from this source: just restore the metadata
            width, height = size_wh
            Stats.skipped += len(keys)
            Stats.restored += 1
        else:
            try:
                raw = download(c["download_url"])
                variants = make_variants(raw, slug, n)
            except Exception as e:
                log(f"  {slug}: skip {c.get('source_url')}: {type(e).__name__}: {str(e)[:150]}")
                continue
            width, height = variants["large"]["width"], variants["large"]["height"]
            if not dry:
                for size, key in keys.items():
                    upload(s3, bucket, key, variants[size]["path"], c["source_url"],
                           variants[size]["width"], variants[size]["height"])
        chosen.append({
            "n": n,
            "key_base": base,
            "sizes": keys,
            "width": width,
            "height": height,
            "source": c["source"],
            "source_url": c["source_url"],
            "download_url": c["download_url"],
            "kind": kind,
            "author": c.get("author"),
            "attribution_raw": c.get("attribution_raw"),
            "credit": c.get("credit"),
            "license": c["license"],
            "license_url": c.get("license_url"),
            "title": c.get("title"),
            "original_width": c.get("width"),
            "original_height": c.get("height"),
            "retrieved": c.get("retrieved"),
            "modifications": "resized and re-encoded as JPEG; metadata stripped",
        })
    return chosen


def write_species(slug: str, chosen: list[dict]) -> None:
    """Credits + species `photos` for one species, written as soon as it is uploaded (atomic writes)."""
    cr_path = CREDITS / f"{slug}.json"
    prev = read_json(cr_path, {})
    if prev.get("photos") != chosen:  # unchanged credits keep their date (no git noise on re-runs)
        write_json(cr_path, {"id": slug, "updated": dt.date.today().isoformat(), "photos": chosen})
    sp_path = SPECIES_DIR / f"{slug}.json"
    sp = read_json(sp_path)
    if sp is not None:
        photos = [
            {k: c[k] for k in ("key_base", "sizes", "width", "height", "kind", "author", "license",
                               "license_url", "source_url", "credit")}
            for c in chosen
        ]
        if sp.get("photos") != photos:
            sp["photos"] = photos
            write_json(sp_path, sp)


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    only = only_slugs([a for a in args if a != "--dry-run" and a != "--only"])
    sigterm_as_interrupt()

    if not FOCUS.exists():
        write_json(FOCUS, [])
    focus_list = read_json(FOCUS, [])
    focus = set(focus_list)

    s3 = None if dry else r2_client()
    bucket = env("R2_BUCKET")

    index_path = DATA / "species_index.json"
    index = read_json(index_path, [])
    by_id = {e["id"]: e for e in index}

    # focus species first (in focus_species.json order), then everything else alphabetically
    have = {f.stem for f in PHOTOS.glob("*.json")}
    order = [s for s in dict.fromkeys(focus_list) if s in have] + sorted(have - focus)
    if only:
        order = [s for s in order if s in only]
    total = len(order)

    t0 = time.monotonic()
    seen = n_species = n_photos = 0
    index_dirty = False

    def save_index() -> None:
        nonlocal index_dirty
        if index_dirty and not dry:
            write_json(index_path, index)
            index_dirty = False

    def progress() -> None:
        log(f"upload: {seen}/{total} species, {Stats.uploaded} files uploaded, {Stats.skipped} skipped-existing, "
            f"{Stats.bytes / 1e6:.0f} MB, elapsed {fmt_elapsed()} (step {(time.monotonic() - t0) / 60:.0f}m)")

    try:
        for slug in order:
            if time_up("upload"):
                break
            seen += 1
            rec = read_json(PHOTOS / f"{slug}.json") or {}
            cands = rec.get("candidates") or []
            chosen = []
            if cands:
                n_wanted = FOCUS_N if slug in focus else DEFAULT_N
                try:
                    chosen = process(slug, cands, n_wanted, s3, bucket, dry)
                except Exception as e:  # e.g. R2 hiccup; rerun picks it up
                    log(f"  {slug}: {type(e).__name__}: {str(e)[:200]}")
            if chosen:
                n_species += 1
                n_photos += len(chosen)
                if dry:
                    log(f"  {slug}: {len(chosen)} photo(s) resized -> {RESIZED / slug}")
                else:
                    write_species(slug, chosen)
                    if slug in by_id and by_id[slug].get("photo") != chosen[0]["sizes"]["thumb"]:
                        by_id[slug]["photo"] = chosen[0]["sizes"]["thumb"]
                        index_dirty = True
            if seen % INDEX_EVERY == 0:
                save_index()
            if seen % PROGRESS_EVERY == 0:
                progress()
    finally:
        # also on Ctrl-C / SIGTERM: the index gets the photo of every species whose files were written
        save_index()

    progress()
    log(f"upload: {n_species} species, {n_photos} photos"
        + (" (dry run, nothing uploaded)" if dry else
           f", {Stats.uploaded} objects uploaded, {Stats.restored} photos restored from R2 without download"))


if __name__ == "__main__":
    main()
