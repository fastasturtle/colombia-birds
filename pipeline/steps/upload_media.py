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

Then writes data/credits/<slug>.json (full attribution), sets `photos` in data/species/<slug>.json and
`photo` (thumb key of photo 1) in data/species_index.json. Keys are relative; the site prepends
PUBLIC_MEDIA_BASE_URL. Re-running is cheap and also re-applies `photos` after build_species.py wiped them.

Usage: uv run python steps/upload_media.py [--dry-run] [--only slug ...]
  (slugs can also come from the ONLY_SLUGS env var)
Env: R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (not needed with --dry-run)
"""
from __future__ import annotations

import datetime as dt
import io
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import CACHE, DATA, SPECIES_DIR, env, get, log, only_slugs, read_json, write_json  # noqa: E402

PHOTOS = DATA / "photos"
CREDITS = DATA / "credits"
FOCUS = DATA / "focus_species.json"
RESIZED = CACHE / "media" / "resized"
SIZES = {"thumb": 400, "medium": 1000, "large": 1600}
DEFAULT_N, FOCUS_N = 1, 4
QUALITY = 82
CACHE_CONTROL = "public,max-age=31536000,immutable"

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


def upload(s3, bucket: str, key: str, path: Path, source_url: str) -> bool:
    """Upload unless the key already exists with the same source. Returns True if uploaded."""
    from botocore.exceptions import ClientError

    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        if head.get("Metadata", {}).get("source-url") == ascii_meta(source_url):
            return False
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound"):
            raise
    s3.upload_file(
        str(path), bucket, key,
        ExtraArgs={
            "ContentType": "image/jpeg",
            "CacheControl": CACHE_CONTROL,
            "Metadata": {"source-url": ascii_meta(source_url)},
        },
    )
    return True


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
        try:
            raw = download(c["download_url"])
            variants = make_variants(raw, slug, n)
        except Exception as e:
            log(f"  {slug}: skip {c.get('source_url')}: {type(e).__name__}: {str(e)[:150]}")
            continue
        base = f"photos/{slug}/{n}"
        keys = {size: f"{base}-{size}.jpg" for size in SIZES}
        uploaded = 0
        if not dry:
            for size, key in keys.items():
                uploaded += upload(s3, bucket, key, variants[size]["path"], c["source_url"])
        chosen.append({
            "n": n,
            "key_base": base,
            "sizes": keys,
            "width": variants["large"]["width"],
            "height": variants["large"]["height"],
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
            "_uploaded": uploaded,
        })
    return chosen


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    only = only_slugs([a for a in args if a != "--dry-run" and a != "--only"])

    if not FOCUS.exists():
        write_json(FOCUS, [])
    focus = set(read_json(FOCUS, []))

    s3 = None if dry else r2_client()
    bucket = env("R2_BUCKET")

    index_path = DATA / "species_index.json"
    index = read_json(index_path, [])
    by_id = {e["id"]: e for e in index}

    files = sorted(PHOTOS.glob("*.json"))
    n_species = n_photos = n_uploaded = 0
    for f in files:
        rec = read_json(f)
        slug = rec["id"]
        if only and slug not in only:
            continue
        cands = rec.get("candidates") or []
        if not cands:
            continue
        n_wanted = FOCUS_N if slug in focus else DEFAULT_N
        try:
            chosen = process(slug, cands, n_wanted, s3, bucket, dry)
        except Exception as e:  # e.g. R2 hiccup; rerun picks it up
            log(f"  {slug}: {type(e).__name__}: {str(e)[:200]}")
            continue
        if not chosen:
            continue
        n_species += 1
        n_photos += len(chosen)
        n_uploaded += sum(c.pop("_uploaded") for c in chosen)
        if dry:
            log(f"  {slug}: {len(chosen)} photo(s) resized -> {RESIZED / slug}")
            continue

        write_json(CREDITS / f"{slug}.json", {
            "id": slug,
            "updated": dt.date.today().isoformat(),
            "photos": chosen,
        })
        sp_path = SPECIES_DIR / f"{slug}.json"
        sp = read_json(sp_path)
        if sp is not None:
            sp["photos"] = [
                {k: c[k] for k in ("key_base", "sizes", "width", "height", "kind", "author", "license",
                                   "license_url", "source_url", "credit")}
                for c in chosen
            ]
            write_json(sp_path, sp)
        if slug in by_id:
            by_id[slug]["photo"] = chosen[0]["sizes"]["thumb"]

    if not dry:
        write_json(index_path, index)
    log(f"upload: {n_species} species, {n_photos} photos"
        + (" (dry run, nothing uploaded)" if dry else f", {n_uploaded} objects uploaded"))


if __name__ == "__main__":
    main()
