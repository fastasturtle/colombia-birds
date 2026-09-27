"""Likely species per route site from GBIF occurrence counts.

For each site in data/sites.json, two GBIF occurrence facet queries (class Aves, Colombia, with
coordinates, present) inside a circle of `--radius` km (a 32-gon WKT polygon) return record counts
per speciesKey: all year, and autumn only (`month=9,11`, a GBIF range = Sep-Nov; the trip is in
October, so this is the seasonal signal). Keys are mapped to our slugs via data/species/*.json `ids.gbif`; the rest are looked
up once via /v1/species/{key} and matched by scientific name (sci_name / sci_name_aco). Keys that
still do not match are written to data/sources/gbif_sites_unmatched.json.

Output data/site_species.json:
  {site_id: {radius_km, total_records, total_records_aut, retrieved,
             species: [{id, n, n_aut, freq_aut, level}] sorted by n_aut desc, then n desc}}
freq_aut = n_aut / total_records_aut; level = "common" (freq_aut >= 1%), "uncommon" (0.1-1%),
"rare" (< 0.1% or n_aut < 3). Species with fewer than `--min-count` all-year records (default 3) are dropped. Sites with fewer than
`--min-records` records in total (default 1000) get the radius doubled, up to x4.

Usage: uv run python run.py gbif_sites   |   steps/fetch_gbif_sites.py --radius 7 --min-count 3 [--refresh]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA, SOURCES, SPECIES_DIR, get_json, log, norm_sci, read_json, write_json  # noqa: E402

API = "https://api.gbif.org/v1"
AVES = 212


def circle_wkt(lat: float, lon: float, radius_km: float, n: int = 32) -> str:
    """Counter-clockwise polygon approximating a circle (GBIF wants CCW WKT, lon lat)."""
    dlat = radius_km / 111.32
    dlon = radius_km / (111.32 * math.cos(math.radians(lat)))
    pts = [(lon + dlon * math.cos(2 * math.pi * i / n), lat + dlat * math.sin(2 * math.pi * i / n)) for i in range(n)]
    pts.append(pts[0])
    return "POLYGON((" + ",".join(f"{x:.5f} {y:.5f}" for x, y in pts) + "))"


MAP = Path(__file__).resolve().parent.parent / "mappings" / "gbif_to_species.json"


def stem(epithet: str) -> str:
    """Epithet without the Latin gender ending: murina / murinus -> murin, rufum / rufa -> ruf."""
    return re.sub(r"(us|um|a|is|e|er)$", "", epithet) if len(epithet) > 4 else epithet


def species_lookups() -> tuple[dict[int, str], dict[str, str], dict[tuple[str, str], list[str]]]:
    by_key: dict[int, str] = {}
    by_sci: dict[str, str] = {}
    by_fam_epithet: dict[tuple[str, str], list[str]] = {}
    for p in sorted(SPECIES_DIR.glob("*.json")):
        sp = json.loads(p.read_text())
        k = (sp.get("ids") or {}).get("gbif")
        if k:
            by_key[int(k)] = sp["id"]
        for f in ("sci_name", "sci_name_aco"):
            if sp.get(f):
                by_sci.setdefault(norm_sci(sp[f]), sp["id"])
        fam = ((sp.get("family") or {}).get("sci") or "").lower()
        for e in {stem(norm_sci(sp[f]).split()[-1]) for f in ("sci_name", "sci_name_aco") if sp.get(f)}:
            by_fam_epithet.setdefault((fam, e), []).append(sp["id"])
    return by_key, by_sci, by_fam_epithet


def match_name(info: dict, by_sci: dict[str, str], by_fam_epithet: dict, manual: dict[str, str]) -> tuple[str | None, str]:
    """GBIF species record -> our slug: manual map, exact sci name, then same family + same epithet stem
    (genus moves such as Notiochelidon murina -> Orochelidon murina), only when unambiguous."""
    names = [x for x in (info.get("canonicalName"), info.get("species")) if x]
    for x in names:
        if x in manual:
            return manual[x], "manual"
    for x in names:
        if norm_sci(x) in by_sci:
            return by_sci[norm_sci(x)], "sci"
    fam = (info.get("family") or "").lower()
    if names and fam:
        cands = by_fam_epithet.get((fam, stem(norm_sci(names[0]).split()[-1])), [])
        if len(set(cands)) == 1:
            return cands[0], "family+epithet"
    return None, ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=float, default=7.0, help="km")
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--min-records", type=int, default=1000,
                    help="widen the radius (x2, then x4) for sites with fewer GBIF records than this")
    ap.add_argument("--refresh", action="store_true", help="ignore the HTTP cache for facet queries")
    a = ap.parse_args()

    sites = read_json(DATA / "sites.json")
    by_key, by_sci, by_fam_epithet = species_lookups()
    manual: dict[str, str] = {k: v for k, v in read_json(MAP, {}).items() if not k.startswith("_")}
    how_n: dict[str, int] = {}
    today = dt.date.today().isoformat()
    out: dict[str, dict] = {}
    unmatched: dict[int, dict] = {}
    resolved_extra: dict[int, str | None] = {}

    def facet(s: dict, radius: float, months: str | None = None) -> dict:
        params = {
            "classKey": AVES, "country": "CO", "hasCoordinate": "true", "occurrenceStatus": "PRESENT",
            "geometry": circle_wkt(s["lat"], s["lon"], radius),
            "facet": "speciesKey", "facetLimit": 1500, "limit": 0,
        }
        if months:
            params["month"] = months  # GBIF range syntax "9,11" = Sep..Nov ("9,10,11" is rejected)
        return get_json(f"{API}/occurrence/search", params, kind="gbif", min_interval=1.0, retries=6, refresh=a.refresh)

    def resolve_key(key: int, site_id: str, n: int) -> str | None:
        sid = by_key.get(key)
        if sid is not None:
            return sid
        if key not in resolved_extra:
            info = get_json(f"{API}/species/{key}", kind="gbif", min_interval=0.3, retries=6)
            sid, how = match_name(info, by_sci, by_fam_epithet, manual)
            resolved_extra[key] = sid
            how_n[how or "unmatched"] = how_n.get(how or "unmatched", 0) + 1
            if how == "family+epithet":
                log(f"    {info.get('canonicalName')} -> {sid} (family+epithet)")
            if sid is None:
                unmatched[key] = {"key": key, "name": info.get("canonicalName") or info.get("scientificName"),
                                  "status": info.get("taxonomicStatus"), "sites": {}}
        sid = resolved_extra[key]
        if sid is None:
            unmatched[key]["sites"][site_id] = n
        return sid

    def level(n_aut: int, freq: float) -> str:
        if n_aut < 3 or freq < 0.001:
            return "rare"
        return "common" if freq >= 0.01 else "uncommon"

    for s in sites:
        # sparsely surveyed spots (e.g. km-42): widen the circle (x2, x4) until there is something to show
        radius = a.radius
        r = facet(s, radius)
        while r.get("count", 0) < a.min_records and radius < a.radius * 4:
            radius *= 2
            r = facet(s, radius)
        counts = r["facets"][0]["counts"] if r.get("facets") else []
        agg: dict[str, int] = {}
        for c in counts:
            key, n = int(c["name"]), int(c["count"])
            if n < a.min_count:
                continue
            sid = resolve_key(key, s["id"], n)
            if sid is not None:
                agg[sid] = agg.get(sid, 0) + n  # two GBIF keys may map to one of our species
        ra = facet(s, radius, "9,11")
        total_aut = ra.get("count", 0)
        agg_aut: dict[str, int] = {}
        for c in (ra["facets"][0]["counts"] if ra.get("facets") else []):
            key = int(c["name"])
            sid = by_key.get(key) if key in by_key else resolved_extra.get(key)
            if sid in agg:  # keys already resolved above (all-year n >= n_aut)
                agg_aut[sid] = agg_aut.get(sid, 0) + int(c["count"])
        sp = []
        for k, v in agg.items():
            na = agg_aut.get(k, 0)
            f = na / total_aut if total_aut else 0.0
            sp.append({"id": k, "n": v, "n_aut": na, "freq_aut": round(f, 5), "level": level(na, f)})
        sp.sort(key=lambda x: (-x["n_aut"], -x["n"], x["id"]))
        out[s["id"]] = {"radius_km": radius, "total_records": r.get("count", 0), "total_records_aut": total_aut,
                        "retrieved": today, "species": sp}
        lv = {L: sum(1 for x in sp if x["level"] == L) for L in ("common", "uncommon", "rare")}
        log(f"  {s['id']:24s} r={radius:g}km records {r.get('count', 0):7d} aut {total_aut:6d}  "
            f"species(n>={a.min_count}) {len(sp):4d}  {lv}")

    write_json(DATA / "site_species.json", out)
    write_json(SOURCES / "gbif_sites_unmatched.json",
               sorted(unmatched.values(), key=lambda u: -sum(u["sites"].values())))
    ns = sorted(len(v["species"]) for v in out.values())
    log(f"sites: {len(ns)}, species per site min {ns[0]} / median {ns[len(ns)//2]} / max {ns[-1]}; "
        f"extra key lookups {len(resolved_extra)} {how_n}, unmatched keys {len(unmatched)}")


if __name__ == "__main__":
    main()
