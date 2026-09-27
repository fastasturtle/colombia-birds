"""Select candidate photos per species (Wikimedia Commons + iNaturalist) -> data/photos/<slug>.json

Only freely licensed photos are kept: CC0, public domain, CC BY, CC BY-SA (no NC/ND, no GFDL-only).
Nothing is downloaded here; upload_media.py downloads, resizes and uploads the chosen candidates.

Usage: uv run python steps/fetch_photos.py [slug ...] [--limit N] [--refresh]
       (slugs can also come from the ONLY_SLUGS env var)

Commons: files in Category:<commons category or sci name> plus the Wikidata P18 images.
  Ranked: Quality/Featured first, then P18, then by pixel count. Width >= 800, JPEG/PNG only.
iNaturalist: research-grade observations with CC0/BY/BY-SA photos, ordered by votes, first photo of
  each observation (<= 60 req/min).
Final order: Commons quality/featured, Commons P18, top 2 iNat, remaining Commons by size, remaining iNat,
  then down-ranked Commons photos (zoo/captive/museum/nest hints), then at most one historical
  illustration (plates, BHL scans, artwork, or dated before 1930), which is only kept after >= 1 photo.
  Each candidate has `kind: photo|illustration`. Duplicates (a Commons crop and its original, or a Commons
  import of an iNaturalist photo that iNat also returned) are collapsed, keeping the better-ranked one.
Authors: "(c) Name, some rights reserved (CC BY)" -> "Name"; a URL (e.g. a Flickr profile) -> the user
  name from its path. The original string is kept as `attribution_raw` when it differs.

Wikimedia rate-limits shared IPs hard (403/429). After a few consecutive Commons failures the step stops
asking Commons for the rest of the run; species with a failed source are retried on the next run
(`sources_ok` in the output records which sources answered).
"""
from __future__ import annotations

import datetime as dt
import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, SPECIES_DIR, get_json, log, only_slugs, read_json, write_json  # noqa: E402

PHOTOS = DATA / "photos"
MAX_CANDIDATES = 4
MIN_WIDTH = 800
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia serves a fixed set of thumbnail widths cheaply (…, 1280, 1920, …); other widths are rendered
# on demand and throttled harder. 1920 comfortably covers the 1600px "large" variant.
COMMONS_THUMB_WIDTH = 1920
INAT_API = "https://api.inaturalist.org/v1/observations"
EXT_FIELDS = "License|LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription|DateTimeOriginal|Categories"
# Titles that are almost never a photo of the living bird (skipped unless it is the Wikidata P18 image)
SKIP_TITLE_RE = re.compile(
    r"\b(map|range|distribution|egg|eggs|nest|specimen|skin|skull|skeleton|stamp|museum|naturalis|"
    r"sound|sonogram|spectrogram)\b",
    re.I,
)
# Captive / not-a-living-wild-bird hints: kept, but ranked after every other photo
DOWNRANK_RE = re.compile(
    r"\b(zoo|zoological|captive|captivity|aviary|specimen|museum|egg|eggs|nest)\b|tierpark|dierenpark|vogelpark",
    re.I,
)
# Historical plates, book scans and artwork: at most one per species, ranked after all photos.
# (`plates?(?!-)` so "Plate-billed Mountain-Toucan" is not an illustration.)
ILLUSTRATION_RE = re.compile(
    r"\bpl\.\s*[\dIVXLC]|\bplates?\b(?!-)|\btab\.\s*[\dIVXLC]|\btaf\.\s*\d|\bplanche\b|species novae|\bavium\b|"
    r"biologia centrali|wonders of the bird world|\bBHL\b|biodiversity ?heritage ?library|biodiversitylibrary\.org|"
    r"illustration|lithograph|engraving|drawing|painting|watercolou?r",
    re.I,
)
ILLUSTRATION_BEFORE_YEAR = 1930
YEAR_RE = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")
INAT_PHOTO_RE = re.compile(r"inaturalist\.org/photos/(\d+)|iNaturalist photo (\d+)", re.I)
# "X (cropped)", "X-crop", "X_crop", "X (2)", "X edit" -> "X"
VARIANT_RE = re.compile(r"(?:\s*\((?:cropped|crop|edit|edited|\d)\)|[-_ ](?:cropped|crop|edit|edited))\s*$", re.I)
AUTHOR_PREFIX_RE = re.compile(r"^\s*(?:\(c\)|©|copyright)\s*", re.I)
AUTHOR_SUFFIX_RE = re.compile(r",?\s*(?:some|all|no) rights reserved.*$", re.I)
RANKING_VERSION = 2  # bump when ranking/cleanup changes: records with an older version are re-ranked (from cache)
COMMONS_FAIL_LIMIT = 3

_commons_failures = 0


def short_err(e: Exception) -> str:
    resp = getattr(e, "response", None)
    if resp is not None:
        return f"HTTP {resp.status_code} from {resp.request.url.host}"
    return f"{type(e).__name__}: {e}"[:200]


def strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def name_from_url(u: str) -> str | None:
    """https://www.flickr.com/photos/<user>/123 -> <user>; otherwise the last non-numeric path segment."""
    pu = urlparse(u)
    segs = [x for x in pu.path.split("/") if x]
    if "flickr.com" in pu.netloc and len(segs) >= 2 and segs[0] in ("photos", "people"):
        return unquote(segs[1])
    for seg in reversed(segs):
        if not seg.isdigit():
            return unquote(seg)
    return pu.netloc or None


def clean_author(artist: str | None) -> str | None:
    """'(c) Name, some rights reserved (CC BY)' -> 'Name'; a profile URL -> user name."""
    a = AUTHOR_SUFFIX_RE.sub("", AUTHOR_PREFIX_RE.sub("", artist or "")).strip()
    if re.match(r"https?://", a):
        a = name_from_url(a.split()[0]) or ""
    return a or None


def classify(title: str, *texts: str | None, date: str | None = None) -> str:
    """'illustration' for plates, scans and artwork (by keywords or a date before 1930), else 'photo'."""
    blob = " ".join([title, *(t or "" for t in texts)])
    if ILLUSTRATION_RE.search(blob):
        return "illustration"
    m = YEAR_RE.search(date or "")
    if m and int(m.group(1)) < ILLUSTRATION_BEFORE_YEAR:
        return "illustration"
    return "photo"


def dedupe_key(c: dict) -> str:
    """Same iNaturalist photo id, or the same Commons title up to crop/copy suffixes -> same key."""
    if c.get("source") == "inaturalist" and c.get("photo_url"):
        return "inat:" + c["photo_url"].rstrip("/").rsplit("/", 1)[-1]
    m = INAT_PHOTO_RE.search(" ".join(str(c.get(k) or "") for k in ("credit", "title", "description", "attribution_raw")))
    if m:
        return "inat:" + (m.group(1) or m.group(2))
    t = (c.get("title") or "").lower().strip()
    while (t2 := VARIANT_RE.sub("", t)) != t:
        t = t2
    return "title:" + t.strip()


def cc_url(kind: str, version: str) -> str:
    return f"https://creativecommons.org/licenses/{kind}/{version}/"


def normalize_license(code: str, short: str, url: str) -> tuple[str, str] | None:
    """Commons `License` code (+ short name/url) -> (display name, url), or None if not acceptable."""
    c = (code or "").strip().lower()
    sh = (short or "").strip()
    shl = sh.lower()
    if re.search(r"\bn[cd]\b", c) or re.search(r"\bn[cd]\b", shl):
        return None
    if c.startswith("cc0") or shl.startswith("cc0"):
        return "CC0", url or "https://creativecommons.org/publicdomain/zero/1.0/"
    if c.startswith("pd") or "public domain" in shl:
        return "Public domain", url or "https://en.wikipedia.org/wiki/Public_domain"
    m = re.match(r"cc-by(-sa)?-(\d(?:\.\d)?)", c)
    if m:
        sa, ver = m.group(1), m.group(2)
        if "." not in ver:
            ver += ".0"
        kind = "by-sa" if sa else "by"
        return f"CC {kind.upper()} {ver}", url or cc_url(kind, ver)
    return None


INAT_LICENSES = {
    "cc0": ("CC0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    "cc-by": ("CC BY 4.0", cc_url("by", "4.0")),
    "cc-by-sa": ("CC BY-SA 4.0", cc_url("by-sa", "4.0")),
}


def commons_category(sp: dict) -> str:
    url = (sp.get("links") or {}).get("commons_category")
    if url and "Category:" in url:
        return unquote(url.split("Category:", 1)[1]).replace("_", " ")
    return sp["sci_name"]


def p18_titles(sp: dict) -> list[str]:
    out = []
    for u in sp.get("wikidata_images") or []:
        if "Special:FilePath/" in u:
            out.append("File:" + unquote(u.split("Special:FilePath/", 1)[1]).replace("_", " "))
    return out


def commons_query(params: dict) -> list[dict]:
    """Run a Commons imageinfo query, following `continue`. Raises on HTTP errors."""
    base = {
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": COMMONS_THUMB_WIDTH,
        "iiextmetadatafilter": EXT_FIELDS,
        "format": "json",
        "formatversion": 2,
        "maxlag": 5,
        **params,
    }
    pages: list[dict] = []
    cont: dict = {}
    for _ in range(10):
        data = get_json(COMMONS_API, {**base, **cont}, kind="commons", min_interval=1.0)
        if "error" in data:
            raise RuntimeError(f"commons api: {data['error'].get('code')}: {data['error'].get('info')}")
        pages += data.get("query", {}).get("pages", [])
        if "continue" not in data:
            break
        cont = data["continue"]
    return pages


def commons_candidates(sp: dict, today: str) -> list[dict]:
    cat = commons_category(sp)
    pages = commons_query({
        "generator": "categorymembers",
        "gcmtitle": f"Category:{cat}",
        "gcmtype": "file",
        "gcmlimit": 50,
    })
    p18 = p18_titles(sp)
    have = {p.get("title") for p in pages}
    missing = [t for t in p18 if t not in have]
    if missing:
        pages += commons_query({"titles": "|".join(missing[:50])})

    seen: set[str] = set()
    out = []
    for p in pages:
        title = p.get("title", "")
        if title in seen or p.get("missing"):
            continue
        seen.add(title)
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if (ii.get("width") or 0) < MIN_WIDTH:
            continue
        is_p18 = title in p18
        if not is_p18 and SKIP_TITLE_RE.search(title):
            continue
        em = {k: (v or {}).get("value", "") for k, v in (ii.get("extmetadata") or {}).items()}
        lic = normalize_license(strip_html(em.get("License")), strip_html(em.get("LicenseShortName")),
                                strip_html(em.get("LicenseUrl")))
        if not lic:
            continue
        cats = em.get("Categories", "")
        artist_raw = strip_html(em.get("Artist")) or None
        credit = strip_html(em.get("Credit")) or None
        description = strip_html(em.get("ImageDescription"))[:300] or None
        date_taken = strip_html(em.get("DateTimeOriginal")) or None
        author = clean_author(artist_raw)
        if not author and credit and not re.match(r"https?://", credit) and credit.lower() != "own work":
            author = credit
        kind = classify(title, description, credit, artist_raw, cats, date=date_taken)
        quality = [q for q in ("Featured pictures", "Quality images", "Valued images") if q in cats]
        if quality and quality[0] != "Valued images":
            tier, reason = 0, f"commons {quality[0].lower()}"
        elif is_p18:
            tier, reason = 1, "wikidata P18"
        else:
            tier, reason = 3, "commons by size"
        out.append({
            "source": "commons",
            "source_url": ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}",
            "download_url": ii.get("thumburl") or ii.get("url"),
            "original_url": ii.get("url"),
            "width": ii.get("width"),
            "height": ii.get("height"),
            "license": lic[0],
            "license_url": lic[1],
            "author": author,
            "attribution_raw": artist_raw if artist_raw != author else None,
            "credit": credit,
            "title": title.removeprefix("File:").rsplit(".", 1)[0],
            "description": description,
            "date_taken": date_taken,
            "kind": kind,
            "rank_reason": reason,
            "retrieved": today,
            "_down": bool(DOWNRANK_RE.search(title)),
            "_tier": tier,
            "_pixels": (ii.get("width") or 0) * (ii.get("height") or 0),
        })
    out.sort(key=lambda c: (c["_tier"], -c["_pixels"]))
    return out


def inat_candidates(sp: dict, today: str) -> list[dict]:
    params = {
        "quality_grade": "research",
        "photo_license": "cc0,cc-by,cc-by-sa",
        "order_by": "votes",
        "per_page": 10,
        "photos": "true",
    }
    tid = (sp.get("ids") or {}).get("inaturalist")
    if tid:
        params["taxon_id"] = tid
    else:
        params["taxon_name"] = sp["sci_name"]
    data = get_json(INAT_API, params, kind="inaturalist", min_interval=1.1)
    out = []
    for obs in data.get("results", []):
        for ph in obs.get("photos") or []:
            lic = INAT_LICENSES.get((ph.get("license_code") or "").lower())
            if not lic or ph.get("hidden"):
                continue
            dims = ph.get("original_dimensions") or {}
            w, h = dims.get("width"), dims.get("height")
            if w and max(w, h or 0) < MIN_WIDTH:
                continue
            url = ph.get("url") or ""
            login = (obs.get("user") or {}).get("login")
            name = (obs.get("user") or {}).get("name") or login
            out.append({
                "source": "inaturalist",
                "source_url": obs.get("uri") or f"https://www.inaturalist.org/observations/{obs['id']}",
                "download_url": url.replace("/square.", "/original."),
                "reference_url": url.replace("/square.", "/large."),
                "photo_url": f"https://www.inaturalist.org/photos/{ph['id']}",
                "width": w,
                "height": h,
                "license": lic[0],
                "license_url": lic[1],
                "author": name,
                "credit": ph.get("attribution"),
                "title": f"{sp['sci_name']}, iNaturalist observation {obs['id']}",
                "observation_id": obs["id"],
                "observer_login": login,
                "date_taken": obs.get("observed_on"),
                "kind": "photo",
                "rank_reason": "inaturalist votes",
                "retrieved": today,
                "_tier": 2,
                "_down": False,
                "_pixels": (w or 0) * (h or 0),
            })
            break  # one photo per observation keeps the candidates diverse
    return out


def merge(commons: list[dict], inat: list[dict]) -> list[dict]:
    photos = [c for c in commons if c.get("kind", "photo") == "photo"]
    illustrations = [c for c in commons if c.get("kind") == "illustration"]
    top_commons = [c for c in photos if c["_tier"] <= 1 and not c["_down"]]
    rest_commons = [c for c in photos if c["_tier"] > 1 and not c["_down"]]
    down = [c for c in photos if c["_down"]]
    ordered = top_commons + inat[:2] + rest_commons + inat[2:] + down
    seen: set[str] = set()
    picked: list[dict] = []
    for c in ordered:
        key = dedupe_key(c)
        if key in seen:
            continue
        seen.add(key)
        picked.append(c)
        if len(picked) >= MAX_CANDIDATES:
            break
    # one historical illustration as the last extra image, never as the only/first one
    if picked and len(picked) < MAX_CANDIDATES and illustrations:
        picked.append(illustrations[0])
    return [{k: v for k, v in c.items() if not k.startswith("_") and v is not None} for c in picked]


TIER_BY_REASON = {"commons featured pictures": 0, "commons quality images": 0, "wikidata P18": 1}


def process(sp: dict, prev: dict, today: str) -> dict:
    global _commons_failures
    ok = dict(prev.get("sources_ok") or {})
    commons: list[dict] = []
    inat: list[dict] = []

    if _commons_failures < COMMONS_FAIL_LIMIT:
        try:
            commons = commons_candidates(sp, today)
            ok["commons"] = True
            _commons_failures = 0
        except Exception as e:
            _commons_failures += 1
            ok["commons"] = False
            log(f"  {sp['id']} commons: {short_err(e)}")
            if _commons_failures >= COMMONS_FAIL_LIMIT:
                log(f"  commons: {COMMONS_FAIL_LIMIT} consecutive failures, skipping Commons for the rest of this run")
    else:
        ok["commons"] = False
    if not ok["commons"]:
        # keep Commons candidates from an earlier run rather than losing them to a transient block
        commons = []
        for c in prev.get("candidates", []):
            if c.get("source") != "commons":
                continue
            raw = c.get("attribution_raw") or c.get("author")
            author = clean_author(raw)
            commons.append({
                **c,
                "author": author,
                "attribution_raw": raw if raw != author else None,
                "kind": c.get("kind") or classify(c.get("title") or "", c.get("description"), c.get("credit"),
                                                  raw, date=c.get("date_taken")),
                "_tier": TIER_BY_REASON.get(c.get("rank_reason"), 3),
                "_down": bool(DOWNRANK_RE.search(c.get("title") or "")),
                "_pixels": (c.get("width") or 0) * (c.get("height") or 0),
            })

    try:
        inat = inat_candidates(sp, today)
        ok["inaturalist"] = True
    except Exception as e:
        ok["inaturalist"] = False
        log(f"  {sp['id']} inaturalist: {short_err(e)}")

    return {
        "id": sp["id"],
        "sci_name": sp["sci_name"],
        "commons_category": commons_category(sp),
        "sources_ok": ok,
        "ranking": RANKING_VERSION,
        "candidates": merge(commons, inat),
        "retrieved": today,
    }


def main() -> None:
    args = sys.argv[1:]
    limit = None
    refresh = "--refresh" in args
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i:i + 2]
    only = only_slugs(args)
    today = dt.date.today().isoformat()

    files = sorted(SPECIES_DIR.glob("*.json"))
    done = 0
    for f in files:
        sp = read_json(f)
        if only and sp["id"] not in only:
            continue
        out_path = PHOTOS / f"{sp['id']}.json"
        prev = read_json(out_path, {})
        if (not refresh and not only and prev and prev.get("ranking") == RANKING_VERSION
                and all((prev.get("sources_ok") or {}).get(s) for s in ("commons", "inaturalist"))):
            continue  # complete from an earlier run (older ranking versions are redone; HTTP is cached)
        if limit is not None and done >= limit:
            break
        try:
            rec = process(sp, prev, today)
        except Exception as e:  # never let one species stop the run
            log(f"  {sp['id']}: {e}")
            continue
        write_json(out_path, rec)
        done += 1
        if done % 50 == 0:
            log(f"photos: {done} species processed")

    # summary over everything on disk
    total = with_any = 0
    by_source = {"commons": 0, "inaturalist": 0}
    for p in PHOTOS.glob("*.json"):
        rec = read_json(p)
        total += 1
        srcs = {c["source"] for c in rec.get("candidates", [])}
        with_any += bool(srcs)
        for s in srcs:
            by_source[s] = by_source.get(s, 0) + 1
    log(f"photos: processed {done} this run; {with_any}/{total} species have >=1 candidate "
        f"(commons {by_source['commons']}, inaturalist {by_source['inaturalist']})")


if __name__ == "__main__":
    main()
