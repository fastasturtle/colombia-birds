"""Likely species per route site from GBIF occurrence counts.

For each site in data/sites.json, one GBIF occurrence facet query (class Aves, Colombia, with
coordinates, present) inside a circle of `--radius` km (a 32-gon WKT polygon) returns record counts
per speciesKey. Keys are mapped to our slugs via data/species/*.json `ids.gbif`; the rest are looked
up once via /v1/species/{key} and matched by scientific name (sci_name / sci_name_aco). Keys that
still do not match are written to data/sources/gbif_sites_unmatched.json.

Output data/site_species.json:
  {site_id: {radius_km, total_records, retrieved, species: [{id, n}] sorted by n desc}}
Species with fewer than `--min-count` records (default 3) are dropped.

Usage: uv run python run.py gbif_sites   |   steps/fetch_gbif_sites.py --radius 12 --min-count 3 [--refresh]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
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


def species_lookups() -> tuple[dict[int, str], dict[str, str]]:
    by_key: dict[int, str] = {}
    by_sci: dict[str, str] = {}
    for p in sorted(SPECIES_DIR.glob("*.json")):
        sp = json.loads(p.read_text())
        k = (sp.get("ids") or {}).get("gbif")
        if k:
            by_key[int(k)] = sp["id"]
        for f in ("sci_name", "sci_name_aco"):
            if sp.get(f):
                by_sci.setdefault(norm_sci(sp[f]), sp["id"])
    return by_key, by_sci


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=float, default=12.0, help="km")
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--refresh", action="store_true", help="ignore the HTTP cache for facet queries")
    a = ap.parse_args()

    sites = read_json(DATA / "sites.json")
    by_key, by_sci = species_lookups()
    today = dt.date.today().isoformat()
    out: dict[str, dict] = {}
    unmatched: dict[int, dict] = {}
    resolved_extra: dict[int, str | None] = {}

    for s in sites:
        r = get_json(f"{API}/occurrence/search", {
            "classKey": AVES, "country": "CO", "hasCoordinate": "true", "occurrenceStatus": "PRESENT",
            "geometry": circle_wkt(s["lat"], s["lon"], a.radius),
            "facet": "speciesKey", "facetLimit": 1500, "limit": 0,
        }, kind="gbif", min_interval=1.0, retries=6, refresh=a.refresh)
        counts = r["facets"][0]["counts"] if r.get("facets") else []
        agg: dict[str, int] = {}
        for c in counts:
            key, n = int(c["name"]), int(c["count"])
            if n < a.min_count:
                continue
            sid = by_key.get(key)
            if sid is None:
                if key not in resolved_extra:
                    info = get_json(f"{API}/species/{key}", kind="gbif", min_interval=0.3, retries=6)
                    names = [info.get("canonicalName"), info.get("species")]
                    sid = next((by_sci[norm_sci(x)] for x in names if x and norm_sci(x) in by_sci), None)
                    resolved_extra[key] = sid
                    if sid is None:
                        unmatched[key] = {"key": key, "name": info.get("canonicalName") or info.get("scientificName"),
                                          "status": info.get("taxonomicStatus"), "sites": {}}
                sid = resolved_extra[key]
                if sid is None:
                    unmatched[key]["sites"][s["id"]] = n
                    continue
            agg[sid] = agg.get(sid, 0) + n  # two GBIF keys may map to one of our species
        sp = sorted(({"id": k, "n": v} for k, v in agg.items()), key=lambda x: (-x["n"], x["id"]))
        out[s["id"]] = {"radius_km": a.radius, "total_records": r.get("count", 0), "retrieved": today, "species": sp}
        log(f"  {s['id']:24s} records {r.get('count', 0):7d}  keys {len(counts):4d}  species(n>={a.min_count}) {len(sp):4d}")

    write_json(DATA / "site_species.json", out)
    write_json(SOURCES / "gbif_sites_unmatched.json",
               sorted(unmatched.values(), key=lambda u: -sum(u["sites"].values())))
    ns = sorted(len(v["species"]) for v in out.values())
    log(f"sites: {len(ns)}, species per site min {ns[0]} / median {ns[len(ns)//2]} / max {ns[-1]}; "
        f"extra key lookups {len(resolved_extra)}, unmatched keys {len(unmatched)}")


if __name__ == "__main__":
    main()
