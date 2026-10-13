"""Our own sightings on the trip: Anya's eBird checklists -> data/observations.json.

Two modes:

  uv run python run.py observations --import <path/to/MyEBirdData.csv>
      Reads the raw eBird "Download my data" export (worldwide, personal: never committed) and writes the
      committed inputs under pipeline/sources/ebird/:
        colombia_2026.csv           the export's rows with State/Province CO-* dated on or after the trip start
                                    (first date of data/itinerary.json), all columns, same header
        life_list_before_trip.json  {"before", "exported" (max Date of the export), "species": [sorted
                                    scientific names seen anywhere before the trip start, normalised]}
      then builds as below. (Also: `uv run python steps/build_observations.py --import <path>`.)

  uv run python run.py observations
      Builds data/observations.json and data/sources/observations_report.md from those committed sources only.

Matching:
- taxon -> species slug: the scientific name with parentheticals ("Columba livia (Feral Pigeon)") and bracketed
  groups ("Cyanocorax yncas [yncas Group]") stripped, a trinomial cut to its binomial, then exact match against
  data/species_index.json `sci`. Generic taxa (spuhs "sp.", hybrids " x ", slashes "/") and names not in the index
  go to `unmatched`.
- checklist -> site (data/sites.json):
    1. its Location ID is one of the site's `ebird_hotspots`;
    2. else a site of that itinerary day (day sites + overnight site) whose name (a part of it without generic words,
       e.g. "chicaque", "finca discosura") occurs in the location name, within NAME_KM (site coordinates are
       sometimes approximate: Finca Discosura's point is Mocoa, 30 km from the farm);
    3. else the nearest site of any day within NEAR_KM.
  A wider plain radius mis-assigns (El Dorado airport -> La Florida at 3 km, Humedal Soacha -> Campo Tangara at
  7 km, Bogotá city parks -> Jardín Botánico at 6 km), so it stays small; unmatched checklists keep their location.
- checklist -> day: the itinerary day with that date, else null.
- passing: a checklist matched to a site by name or distance (not by the site's hotspot id) on a date that is not
  one of that site's itinerary days (days whose `sites` include it, or whose overnight_site it is), e.g. the roadside
  stop «Vereda La Palestina» 1 km from El Escondite on 7 Oct, a week before the visit. The match is kept (its species
  count for the site); the site shows it as «проездом». A hotspot match off the planned day is a real visit on a
  shifted day (La Drymophila on 6 Oct instead of 5 Oct) or at the lodge (El Encanto on 5 Oct), so it is not passing.
- lifer: the normalised name is not in life_list_before_trip.json.

data/observations.json:
  {observer, source, exported, trip_start,
   checklists: [{id, date, time, site, day, location, location_id, lat, lon, protocol, duration_min, distance_km,
                 observers, comments, n_species, passing (only when true)}]  sorted by date, time
   species: {slug: {first, lifer, n_checklists, sites, days, obs: [{cl, date, time, site, count, details}]}}
   unmatched: [{sci, name, n, dates}]
   stats: {species, lifers, checklists, observations, days,
           by_day: {date: {species, new, lifers, checklists, observations}},
           by_site: {site: {species, new, lifers, checklists, observations, passing_checklists (only when > 0)}},
           off_site: {...same, checklists with no site...} or null}}
  `new` = species first seen on the trip that day / at that site (earliest checklist by date and time).
  `lifers` = lifers among `new` only (counted on the day / at the site of the trip's first sighting), so the
  by_day `new` and `lifers` columns add up to stats.species and stats.lifers. `species` is everything seen there.
"""
from __future__ import annotations

import csv
import io
import math
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA, PIPELINE, SOURCES, log, norm_sci, read_json, write_json, write_text  # noqa: E402

SRC = PIPELINE / "sources" / "ebird"
TRIP_CSV = SRC / "colombia_2026.csv"
LIFE_JSON = SRC / "life_list_before_trip.json"
OUT = DATA / "observations.json"
REPORT = SOURCES / "observations_report.md"

OBSERVER = "Аня"
SOURCE = "eBird, личная выгрузка"
NEAR_KM = 2.0
NAME_KM = 50.0
PROTOCOLS = {"traveling count": "traveling", "stationary count": "stationary", "casual observation": "casual",
             "historical": "historical", "area count": "area", "incidental": "incidental"}
# words that do not identify a place on their own (stripped from site names before the name match)
GENERIC = {"pnn", "rn", "parque", "natural", "nacional", "reserva", "nature", "reserve", "lodge", "bird", "birding",
           "center", "centre", "hotel", "road", "the", "de", "del", "la", "el", "las", "los", "y", "and", "&"}


# ---------- names ----------

def strip_name(sci: str) -> str:
    """'Columba livia (Feral Pigeon)' -> 'Columba livia'; 'Cyanocorax yncas [yncas Group]' -> 'Cyanocorax yncas'."""
    s = re.sub(r"\s*\([^)]*\)", "", sci)
    s = re.sub(r"\s*\[[^\]]*\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def is_generic(sci: str) -> bool:
    """Spuh, slash or hybrid: not a species."""
    s = strip_name(sci)
    return " sp." in f" {s}" or s.endswith(" sp") or "/" in s or " x " in s or " × " in s


def species_name(sci: str) -> str | None:
    """Normalised species-level name ('Genus species'), or None for a generic taxon."""
    if not sci or is_generic(sci):
        return None
    parts = strip_name(sci).split()
    if len(parts) < 2:
        return None
    return f"{parts[0]} {parts[1]}"  # trinomial (subspecies) -> binomial


# ---------- geometry / places ----------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def name_keys(site: dict) -> list[str]:
    """Identifying phrases of a site name: each '/'-part, parentheses dropped, generic words removed."""
    out = []
    for part in re.split(r"/", re.sub(r"\([^)]*\)", "", site.get("name") or "")):
        words = [w for w in norm_text(part).split() if w not in GENERIC]
        key = " ".join(words)
        if len(key) >= 5:
            out.append(key)
    return out


def match_site(cl: dict, sites: list[dict], day: dict | None) -> str | None:
    """Site id of a checklist (location_id, location, lat, lon), see the module docstring; None when none fits."""
    for s in sites:
        if cl["location_id"] and any(h.get("id") == cl["location_id"] for h in s.get("ebird_hotspots") or []):
            return s["id"]
    lat, lon = cl.get("lat"), cl.get("lon")
    if lat is None or lon is None:
        return None
    if day:
        day_ids = list(day.get("sites") or []) + ([day["overnight_site"]] if day.get("overnight_site") else [])
        loc = f" {norm_text(cl.get('location') or '')} "
        for s in sites:
            if s["id"] in day_ids and any(f" {k} " in loc for k in name_keys(s)) \
                    and haversine(lat, lon, s["lat"], s["lon"]) <= NAME_KM:
                return s["id"]
    best = min(sites, key=lambda s: haversine(lat, lon, s["lat"], s["lon"]), default=None)
    if best and haversine(lat, lon, best["lat"], best["lon"]) <= NEAR_KM:
        return best["id"]
    return None


# ---------- parsing ----------

def parse_time(t: str | None) -> str | None:
    """'06:14 AM' -> '06:14', '12:26 PM' -> '12:26', '02:00 PM' -> '14:00'; '' -> None."""
    t = (t or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})(?:\s*([AaPp])\.?[Mm]\.?)?$", t)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").lower()
    if ap == "p" and h < 12:
        h += 12
    if ap == "a" and h == 12:
        h = 0
    return f"{h:02d}:{mi:02d}"


def num(s: str | None, kind=float):
    s = (s or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return int(v) if kind is int else round(v, 3)


def protocol(p: str | None) -> str:
    p = (p or "").strip()
    p = re.sub(r"^eBird\s*-\s*", "", p, flags=re.I).lower()
    return PROTOCOLS.get(p, re.sub(r"[^a-z0-9]+", "-", p).strip("-") or "unknown")


def read_csv(text: str) -> tuple[list[str], list[dict]]:
    r = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    return list(r.fieldnames or []), list(r)


# ---------- import ----------

def rel(p: Path) -> str:
    return str(p.relative_to(PIPELINE.parent)) if p.is_relative_to(PIPELINE.parent) else str(p)


def import_export(path: Path, trip_start: str) -> None:
    """Raw export -> committed sources (Colombia trip rows; life list before the trip)."""
    header, rows = read_csv(path.read_text(encoding="utf-8"))
    need = {"Submission ID", "Scientific Name", "State/Province", "Date"}
    if not need <= set(header):
        sys.exit(f"{path}: not an eBird 'Download my data' CSV (missing {sorted(need - set(header))})")
    trip = [r for r in rows if (r.get("State/Province") or "").startswith("CO-") and (r.get("Date") or "") >= trip_start]
    life = sorted({n for r in rows if (r.get("Date") or "") < trip_start
                   for n in [species_name(r.get("Scientific Name") or "")] if n})
    exported = max((r.get("Date") or "" for r in rows), default="")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in sorted(trip, key=lambda r: (r["Date"], parse_time(r.get("Time")) or "", r["Submission ID"], r.get("Taxonomic Order") or "")):
        w.writerow({k: (v if v is not None else "") for k, v in r.items() if k in header})
    write_text(TRIP_CSV, buf.getvalue())
    write_json(LIFE_JSON, {"before": trip_start, "exported": exported, "species": life})
    log(f"import: {len(rows)} rows in the export (up to {exported}); {len(trip)} Colombia trip rows -> {rel(TRIP_CSV)}; "
        f"{len(life)} species before {trip_start} -> {rel(LIFE_JSON)}")


# ---------- build ----------

def build(rows: list[dict], life: set[str], index: list[dict], sites: list[dict], itinerary: list[dict],
          trip_start: str, exported: str) -> dict:
    by_sci = {norm_sci(s["sci"]): s["id"] for s in index}
    days = {d["date"]: d for d in itinerary}
    site_days: dict[str, set[str]] = {}
    for d in itinerary:
        for sid in list(d.get("sites") or []) + ([d["overnight_site"]] if d.get("overnight_site") else []):
            site_days.setdefault(sid, set()).add(d["date"])
    hotspots = {s["id"]: {h.get("id") for h in s.get("ebird_hotspots") or []} for s in sites}

    checklists: dict[str, dict] = {}
    for r in rows:
        cid = r["Submission ID"]
        if cid in checklists:
            continue
        date = r["Date"]
        cl = {
            "id": cid, "date": date, "time": parse_time(r.get("Time")),
            "location": (r.get("Location") or "").strip(), "location_id": (r.get("Location ID") or "").strip() or None,
            "lat": num(r.get("Latitude")), "lon": num(r.get("Longitude")),
            "protocol": protocol(r.get("Protocol")), "duration_min": num(r.get("Duration (Min)"), int),
            "distance_km": num(r.get("Distance Traveled (km)")), "observers": num(r.get("Number of Observers"), int),
            "comments": (r.get("Checklist Comments") or "").strip() or None,
        }
        if cl["lat"] is not None:
            cl["lat"] = round(cl["lat"], 5)
        if cl["lon"] is not None:
            cl["lon"] = round(cl["lon"], 5)
        cl["day"] = date if date in days else None
        cl["site"] = match_site(cl, sites, days.get(date))
        if cl["site"] and date not in site_days.get(cl["site"], set()) and cl["location_id"] not in hotspots[cl["site"]]:
            cl["passing"] = True
        checklists[cid] = cl
    order = sorted(checklists.values(), key=lambda c: (c["date"], c["time"] or "", c["id"]))

    species: dict[str, dict] = {}
    unmatched: dict[str, dict] = {}
    taxa_per_cl: dict[str, set[str]] = {c["id"]: set() for c in order}
    for r in rows:
        cl = checklists[r["Submission ID"]]
        raw = (r.get("Scientific Name") or "").strip()
        name = species_name(raw)
        slug = by_sci.get(norm_sci(name)) if name else None
        if name:
            taxa_per_cl[cl["id"]].add(name)
        if not slug:
            u = unmatched.setdefault(raw, {"sci": raw, "name": (r.get("Common Name") or "").strip(), "n": 0, "dates": set()})
            u["n"] += 1
            u["dates"].add(cl["date"])
            continue
        cnt = (r.get("Count") or "").strip()
        sp = species.setdefault(slug, {"lifer": name not in life, "obs": []})
        sp["obs"].append({"cl": cl["id"], "date": cl["date"], "time": cl["time"], "site": cl["site"],
                          "count": int(cnt) if cnt.isdigit() else None,
                          "details": (r.get("Observation Details") or "").strip() or None})
    rank = {c["id"]: i for i, c in enumerate(order)}
    for sp in species.values():
        sp["obs"].sort(key=lambda o: rank[o["cl"]])
        sp["first"] = sp["obs"][0]["date"]
        sp["first_cl"] = sp["obs"][0]["cl"]
        sp["n_checklists"] = len({o["cl"] for o in sp["obs"]})
        sp["sites"] = list(dict.fromkeys(o["site"] for o in sp["obs"] if o["site"]))
        sp["days"] = list(dict.fromkeys(o["date"] for o in sp["obs"] if o["date"] in days))
    for c in order:
        c["n_species"] = len(taxa_per_cl[c["id"]])

    def group_stats(key) -> dict:
        """Per group (key(checklist) -> group id or None): species, new (first seen there), lifers (among new),
        checklists, observations."""
        out: dict = {}
        for c in order:
            g = key(c)
            if g is None:
                continue
            e = out.setdefault(g, {"species": set(), "new": set(), "lifers": set(), "checklists": 0, "observations": 0})
            e["checklists"] += 1
        for slug, sp in species.items():
            for o in sp["obs"]:
                g = key(checklists[o["cl"]])
                if g is None:
                    continue
                e = out[g]
                e["species"].add(slug)
                e["observations"] += 1
                if o["cl"] == sp["first_cl"]:
                    e["new"].add(slug)
                    if sp["lifer"]:
                        e["lifers"].add(slug)
        return {g: {k: (len(v) if isinstance(v, set) else v) for k, v in e.items()} for g, e in out.items()}

    by_day = group_stats(lambda c: c["date"])
    by_site = group_stats(lambda c: c["site"])
    for c in order:
        if c.get("passing"):
            e = by_site[c["site"]]
            e["passing_checklists"] = e.get("passing_checklists", 0) + 1
    off = group_stats(lambda c: "_" if c["site"] is None else None).get("_")
    for sp in species.values():
        del sp["first_cl"]
    return {
        "observer": OBSERVER, "source": SOURCE, "exported": exported, "trip_start": trip_start,
        "checklists": order,
        "species": species,
        "unmatched": sorted(({**u, "dates": sorted(u["dates"])} for u in unmatched.values()), key=lambda u: u["sci"]),
        "stats": {
            "species": len(species), "lifers": sum(1 for s in species.values() if s["lifer"]),
            "checklists": len(order), "observations": sum(len(s["obs"]) for s in species.values()),
            "days": len({c["date"] for c in order}),
            "by_day": by_day,
            "by_site": by_site,
            "off_site": off,
        },
    }


def plural(n: int, one: str, few: str, many: str) -> str:
    m10, m100 = n % 10, n % 100
    return one if m10 == 1 and m100 != 11 else few if 2 <= m10 <= 4 and not 12 <= m100 <= 14 else many


def report(obs: dict, sites: list[dict], itinerary: list[dict]) -> str:
    name = {s["id"]: s.get("name_ru") or s["name"] for s in sites}
    st = obs["stats"]
    lines = [
        "# Наблюдения (eBird, чеклисты Ани)", "",
        f"Выгрузка от {obs['exported']}, тур с {obs['trip_start']}. Шаг `observations` (`pipeline/steps/build_observations.py`).", "",
        f"- Видов (сопоставлено с базой сайта): {st['species']}, из них новых для Ани (лайферов): {st['lifers']}",
        f"- Чеклистов: {st['checklists']}, дней: {st['days']}, записей: {st['observations']}; "
        f"проездом (у локации не в её день маршрута): {sum(1 for c in obs['checklists'] if c.get('passing'))}",
        f"- Не сопоставлено таксонов: {len(obs['unmatched'])}", "",
        "## По дням", "",
        "Видов: всё, что видели в этот день / на этой локации. Впервые в туре: виды, впервые встреченные в туре именно "
        "здесь; лайферы считаются только среди них (в день и на локации первой встречи), поэтому столбцы «Впервые в "
        "туре» и «из них лайферов» по дням складываются в итог тура.", "",
        "| Дата | Видов | Впервые в туре | из них лайферов | Чеклистов |", "|---|---|---|---|---|",
    ]
    for d, e in sorted(st["by_day"].items()):
        lines.append(f"| {d} | {e['species']} | {e['new']} | {e['lifers']} | {e['checklists']} |")
    lines.append(f"| **итого** | {st['species']} | {sum(e['new'] for e in st['by_day'].values())} | "
                 f"{sum(e['lifers'] for e in st['by_day'].values())} | {st['checklists']} |")
    lines += ["", "## По локациям", "", "| Локация | Видов | Впервые в туре | из них лайферов | Чеклистов |", "|---|---|---|---|---|"]
    for s, e in sorted(st["by_site"].items(), key=lambda x: -x[1]["species"]):
        pc = f" (из них {e['passing_checklists']} проездом)" if e.get("passing_checklists") else ""
        lines.append(f"| {name.get(s, s)} (`{s}`) | {e['species']} | {e['new']} | {e['lifers']} | {e['checklists']}{pc} |")
    if st["off_site"]:
        e = st["off_site"]
        lines.append(f"| вне локаций маршрута | {e['species']} | {e['new']} | {e['lifers']} | {e['checklists']} |")
    lines += ["", "## Не сопоставлено с базой сайта", ""]
    lines += [f"- *{u['sci']}* ({u['name']}): {u['n']} {plural(u['n'], 'запись', 'записи', 'записей')}, {', '.join(u['dates'])}" for u in obs["unmatched"]] or ["Нет."]
    lines += ["", "## Чеклисты проездом", "",
              "Сопоставлены с локацией по названию или расстоянию (ближе 2 км), но в этот день локации нет в маршруте: "
              "виды засчитаны локации, на сайте чеклист помечен «проездом».", ""]
    route_days = {s: sorted(d["date"] for d in itinerary if s in (d.get("sites") or [])) for s in name}
    lines += [f"- {c['date']} {c['time'] or ''} [{c['id']}](https://ebird.org/checklist/{c['id']}): {c['location']} -> "
              f"{name.get(c['site'], c['site'])} (`{c['site']}`, в маршруте: {', '.join(route_days.get(c['site']) or []) or 'нет'})"
              for c in obs["checklists"] if c.get("passing")] or ["Нет."]
    lines += ["", "## Чеклисты без локации маршрута", ""]
    no_site = [c for c in obs["checklists"] if c["site"] is None]
    lines += [f"- {c['date']} {c['time'] or ''} [{c['id']}](https://ebird.org/checklist/{c['id']}): {c['location']} ({c['n_species']} {plural(c['n_species'], 'вид', 'вида', 'видов')})"
              for c in no_site] or ["Нет."]
    return "\n".join(lines) + "\n"


def trip_start_date(itinerary: list[dict]) -> str:
    dates = sorted(d["date"] for d in itinerary)
    if not dates:
        sys.exit("data/itinerary.json is empty: no trip start")
    return dates[0]


def main() -> None:
    args = sys.argv[1:]
    imp = os.environ.get("EBIRD_IMPORT")
    if "--import" in args:
        i = args.index("--import")
        if i + 1 >= len(args):
            sys.exit("--import needs a path to MyEBirdData.csv")
        imp = args[i + 1]
    itinerary = read_json(DATA / "itinerary.json", [])
    trip_start = trip_start_date(itinerary)
    if imp:
        import_export(Path(imp).expanduser().resolve(), trip_start)
    if not TRIP_CSV.exists() or not LIFE_JSON.exists():
        sys.exit(f"no {TRIP_CSV} / {LIFE_JSON}: run `run.py observations --import <MyEBirdData.csv>` first")
    _, rows = read_csv(TRIP_CSV.read_text(encoding="utf-8"))
    life_doc = read_json(LIFE_JSON)
    if life_doc.get("before") != trip_start:
        log(f"warning: life list is 'before {life_doc.get('before')}', the itinerary starts {trip_start}; re-import the export")
    obs = build(rows, set(life_doc["species"]), read_json(DATA / "species_index.json"), read_json(DATA / "sites.json"),
                itinerary, trip_start, life_doc.get("exported") or "")
    write_json(OUT, obs)
    write_text(REPORT, report(obs, read_json(DATA / "sites.json"), itinerary))
    st = obs["stats"]
    log(f"observations: {st['species']} species ({st['lifers']} lifers), {st['checklists']} checklists on {st['days']} days, "
        f"{len(obs['unmatched'])} unmatched taxa, {sum(1 for c in obs['checklists'] if c['site'] is None)} checklists without a site, "
        f"{sum(1 for c in obs['checklists'] if c.get('passing'))} passing -> {rel(OUT)}")


if __name__ == "__main__":
    main()
