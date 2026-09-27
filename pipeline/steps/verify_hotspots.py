"""Verify the eBird hotspot ids in data/sites.json against the eBird API and suggest nearby hotspots.

For every site:
  (a) each listed hotspot id -> GET /v2/ref/hotspot/info/{locId}: API name + coordinates, distance
      (haversine) to the site. Status `ok` (<= 15 km and the names share a meaningful token),
      `suspect` (with reason) or `invalid` (API 400/404/410 or empty answer).
  (b) GET /v2/ref/hotspot/geo?lat&lng&dist=10 (widened to 25/50 km when empty): the 8 nearest hotspots
      with id, name, distance and numSpeciesAllTime.

Only eBird reference data is stored (hotspot ids, names, coordinates, species counts), no observations.
Needs EBIRD_API_KEY (https://ebird.org/api/keygen); run in GitHub Actions (pipeline.yml, steps=hotspots).

Outputs:
  data/sources/hotspots_check.json           full report + summary
  docs/research/hotspots-check.md            human-readable table
  pipeline/mappings/hotspot_suggestions.json {site_id: [{id, name, distance_km, numSpeciesAllTime}]}
data/sites.json is hand-authored and is never modified here: apply suggestions by hand after review.
"""
from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA, PIPELINE, ROOT, SOURCES, env, get, log, read_json, write_json  # noqa: E402

API = "https://api.ebird.org/v2"
OK_KM = 15.0
NEARBY_N = 8
DISTS = (10, 25, 50)  # km, eBird max is 50
OUT_JSON = SOURCES / "hotspots_check.json"
OUT_MD = ROOT / "docs" / "research" / "hotspots-check.md"
OUT_SUGG = PIPELINE / "mappings" / "hotspot_suggestions.json"

STOP = {
    "de", "del", "la", "las", "el", "los", "y", "e", "a", "en", "the", "of", "and", "to", "via", "road",
    "rn", "pnn", "sff", "reserva", "reserve", "natural", "nature", "nacional", "national", "parque", "park",
    "finca", "hotel", "lodge", "center", "centro", "vereda", "km", "alternative", "id", "verify", "nearby",
    "colombia", "municipio", "sector", "general", "area", "zona", "aves", "birding", "bird", "birds",
}


class KeyError_(Exception):
    pass


def tokens(*names: str) -> set[str]:
    out: set[str] = set()
    for n in names:
        n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
        out |= {t for t in re.split(r"[^a-z0-9]+", n) if len(t) >= 3 and t not in STOP and not t.isdigit()}
    return out


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def api(path: str, params: dict | None, key: str):
    """GET an eBird endpoint (cached by URL; the token header is not part of the cache key).
    Returns parsed JSON, or None for 400/404/410 (unknown id). Raises KeyError_ on 401/403."""
    try:
        text = get(f"{API}{path}", params, kind="ebird_hotspots", min_interval=0.6,
                   headers={"X-eBirdApiToken": key})
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code in (401, 403):
            raise KeyError_(f"eBird API refused the key (HTTP {code} on {path})") from None
        if code in (400, 404, 410):
            return None
        raise
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if path.endswith("/geo"):  # geo endpoint may answer CSV if fmt is ignored
            raise
        return None


def check_listed(site: dict, h: dict, key: str) -> dict:
    rec = {"id": h["id"], "name_listed": h.get("name"), "name_api": None, "lat": None, "lng": None,
           "distance_km": None, "numSpeciesAllTime": None, "status": "invalid", "reason": None}
    info = api(f"/ref/hotspot/info/{h['id']}", None, key)
    if isinstance(info, list):
        info = info[0] if info else None
    if not info:
        rec["reason"] = "eBird API: unknown locId (404/empty)"
        return rec
    name = info.get("name") or info.get("locName")
    lat = info.get("latitude", info.get("lat"))
    lng = info.get("longitude", info.get("lng"))
    rec.update(name_api=name, lat=lat, lng=lng, numSpeciesAllTime=info.get("numSpeciesAllTime"))
    if lat is None or lng is None:
        rec.update(status="suspect", reason="no coordinates in API answer")
        return rec
    d = round(haversine(site["lat"], site["lon"], lat, lng), 2)
    rec["distance_km"] = d
    common = tokens(name) & tokens(site.get("name", ""), h.get("name", ""), site.get("name_ru", ""))
    reasons = []
    if d > OK_KM:
        reasons.append(f"{d} km from site (> {OK_KM:g})")
    if not common:
        reasons.append("name shares no token with site/listed name")
    rec["status"] = "suspect" if reasons else "ok"
    rec["reason"] = "; ".join(reasons) or f"{d} km, common: {', '.join(sorted(common))}"
    return rec


def nearby(site: dict, key: str) -> tuple[list[dict], int]:
    for dist in DISTS:
        rows = api("/ref/hotspot/geo", {"lat": site["lat"], "lng": site["lon"], "dist": dist, "fmt": "json"}, key)
        if rows:
            break
    rows = rows or []
    out = []
    for r in rows:
        lat, lng = r.get("lat"), r.get("lng")
        if lat is None or lng is None:
            continue
        out.append({"id": r.get("locId"), "name": r.get("locName") or r.get("name"), "lat": lat, "lng": lng,
                    "distance_km": round(haversine(site["lat"], site["lon"], lat, lng), 2),
                    "numSpeciesAllTime": r.get("numSpeciesAllTime")})
    out.sort(key=lambda x: x["distance_km"])
    return out[:NEARBY_N], dist


def suggest(site: dict, near: list[dict], listed: list[dict]) -> list[dict]:
    """Up to 3 candidates: listed ids confirmed ok, the name-matching nearby ones, the closest and
    the one with the most species all time."""
    if not near:
        return []
    want = tokens(site.get("name", ""), *[h.get("name", "") for h in site.get("ebird_hotspots", [])])
    ok_ids = {x["id"] for x in listed if x["status"] == "ok"}
    picks: list[dict] = []
    picks += [n for n in near if n["id"] in ok_ids]
    picks += [n for n in near if tokens(n["name"]) & want]
    picks.append(near[0])
    picks.append(max(near, key=lambda n: n["numSpeciesAllTime"] or 0))
    seen, out = set(), []
    for n in picks:
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        out.append({k: n[k] for k in ("id", "name", "distance_km", "numSpeciesAllTime")})
    return out[:3]


def write_md(report: dict, sites: list[dict]) -> None:
    s = report["summary"]
    lines = [
        "# Проверка eBird-хотспотов",
        "",
        f"Сгенерировано шагом `hotspots` (`pipeline/steps/verify_hotspots.py`), {report['retrieved']}. "
        "Не редактировать руками. Статус: `ok` — хотспот не дальше 15 км от координат локации и имя "
        "пересекается с названием; `suspect` — не выполнено одно из условий; `invalid` — eBird такого id не знает.",
        "",
        f"Итого: {s['listed']} id, ok {s['ok']}, suspect {s['suspect']}, invalid {s['invalid']}; "
        f"локаций без id: {', '.join(s['sites_without_ids']) or 'нет'}.",
        "",
        "Предложения (ближайший, с наибольшим числом видов, совпадающий по имени) — в "
        "`pipeline/mappings/hotspot_suggestions.json`; `data/sites.json` правится вручную после проверки.",
        "",
        "| Локация | Указанные id | Предложено |",
        "|---|---|---|",
    ]
    for site in sites:
        r = report["sites"][site["id"]]
        listed = "<br>".join(
            f"`{x['id']}` **{x['status']}** {x['name_api'] or x['name_listed'] or ''}"
            + (f" ({x['distance_km']} км)" if x["distance_km"] is not None else "")
            + (f" — {x['reason']}" if x["status"] != "ok" and x["reason"] else "")
            for x in r["listed"]) or "—"
        sugg = "<br>".join(
            f"[`{n['id']}`](https://ebird.org/hotspot/{n['id']}) {n['name']} ({n['distance_km']} км, "
            f"{n['numSpeciesAllTime'] if n['numSpeciesAllTime'] is not None else '?'} видов)"
            for n in report["suggestions"].get(site["id"], [])) or "—"
        cell = lambda t: t.replace("|", "\\|")
        lines.append(f"| {cell(site['name'])} (`{site['id']}`) | {cell(listed)} | {cell(sugg)} |")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    key = (env("EBIRD_API_KEY") or "").strip()
    if not key:
        sys.exit("hotspots: EBIRD_API_KEY is not set. Get a key at https://ebird.org/api/keygen and put it in "
                 ".env (local) or the EBIRD_API_KEY GitHub secret, then run via Actions: pipeline, steps=hotspots.")
    sites = read_json(DATA / "sites.json", [])
    report: dict = {"retrieved": date.today().isoformat(), "ok_km": OK_KM,
                    "note": "eBird reference data only (hotspot ids, names, coordinates, species counts).",
                    "sites": {}, "suggestions": {}}
    try:
        for site in sites:
            listed = [check_listed(site, h, key) for h in site.get("ebird_hotspots", [])]
            near, dist = nearby(site, key)
            by_id = {n["id"]: n for n in near}
            for x in listed:
                if x["numSpeciesAllTime"] is None and x["id"] in by_id:
                    x["numSpeciesAllTime"] = by_id[x["id"]]["numSpeciesAllTime"]
            report["sites"][site["id"]] = {"name": site["name"], "lat": site["lat"], "lng": site["lon"],
                                           "listed": listed, "nearby": near, "nearby_dist_km": dist}
            report["suggestions"][site["id"]] = suggest(site, near, listed)
            log(f"{site['id']}: " + (", ".join(f"{x['id']}={x['status']}" for x in listed) or "no ids")
                + f"; {len(near)} nearby within {dist} km")
    except KeyError_ as e:
        sys.exit(f"hotspots: {e}. Check the EBIRD_API_KEY secret; nothing written.")
    except httpx.HTTPError as e:
        sys.exit(f"hotspots: eBird API error: {e}; nothing written. Re-run later (responses are cached).")

    allx = [x for r in report["sites"].values() for x in r["listed"]]
    report["summary"] = {
        "sites": len(sites), "listed": len(allx),
        **{k: sum(x["status"] == k for x in allx) for k in ("ok", "suspect", "invalid")},
        "sites_without_ids": [s["id"] for s in sites if not s.get("ebird_hotspots")],
        "problems": [f"{sid}:{x['id']}:{x['status']}" for sid, r in report["sites"].items()
                     for x in r["listed"] if x["status"] != "ok"],
    }
    write_json(OUT_JSON, report)
    write_json(OUT_SUGG, report["suggestions"])
    write_md(report, sites)
    s = report["summary"]
    log(f"hotspots: {s['listed']} ids: ok {s['ok']}, suspect {s['suspect']}, invalid {s['invalid']} -> "
        f"{OUT_JSON.relative_to(ROOT)}, {OUT_MD.relative_to(ROOT)}, {OUT_SUGG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
