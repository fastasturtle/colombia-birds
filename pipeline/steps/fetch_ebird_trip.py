"""Anya's new checklists from a public eBird Trip Report -> pipeline/sources/ebird/trip_report.csv

The automatic path for the trip sightings (the manual one is `run.py observations --import MyEBirdData.csv`, see
build_observations.py). Runs every 2 hours in .github/workflows/observations.yml, followed by `observations`.

Config: pipeline/sources/ebird/trip_reports.json
  {"user_id": "USER3559161", "reports": [{"id": 579125, "note": "..."}]}
  `user_id` = whose checklists to take (eBird user id of the person in the report's `people` list); `reports` is a list
  because one trip report covers at most 31 days. To take the whole group later, the person filter is the only thing
  to change: every per-person request carries tripReportPersonId.
  For the «Группа» block of /seen/ the step also takes, for every participant and for the whole report, only the
  numbers (species, other taxa, checklists): no checklist ids, locations or species lists of the others.

Sources (no key): the JSON backend of the trip report page, https://ebird.org/tripreport-internal/v1/ (undocumented
and internal: requests are serial, ~0.7 s apart, 20 s timeout, 3 attempts with backoff, browser-like User-Agent; the
HTML page is behind an anti-bot challenge, the JSON is not; responses are no-store, so no HTTP cache):
  people/{id}                                       -> [{tripReportPersonId, userId, userDisplayName, role,
                                                        personBeginDt, personEndDt "YYYY-MM-DDTHH:MM:SS" (only for a
                                                        participant with a personal window; eBird then counts only
                                                        their checklists inside it)}]
  num-species/{id}[?tripReportPersonId=P]           -> [species, other taxa (hybrids, spuhs, slashes)], e.g. [437, 1];
                                                       without the filter: the whole group
  num-checklists/{id}[?tripReportPersonId=P]        -> 58 (checklists; without the filter: the group's, de-duplicated)
  checklists/{id}?tripReportPersonId=P              -> [{subId, numSpecies, obsTime "HH:MM", isoObsDate "YYYY-MM-DD HH:MM",
                                                        loc: {locId, name, latitude, longitude, subnational1Code}}]
  taxon-list/{id}?tripReportPersonId=P              -> [{speciesCode, category, commonName, sciName, numIndividuals,
                                                        numChecklists}] (species and hybrids; no spuhs/slashes)
  taxon-detail/{id}/{speciesCode}?tripReportPersonId=P -> {checklists: [{subId, obsDt, locName, howMany}]}
Always with the person filter: without it the report de-duplicates checklists shared within the group and shows
another participant's subId; with it the subIds are those of Anya's own export.

Per-checklist species rows, two modes:
  - EBIRD_API_KEY set: official eBird API 2.0 `product/checklist/view/{subId}` (header x-ebirdapitoken) for each
    checklist that is new, whose numSpecies changed, or that is dated within RECENT_DAYS days of today (Bogotá) and was
    last fetched more than REFRESH_HOURS ago (edits after submission are common, but an unchanged report must stay at
    a few requests per run). Gives protocol, duration, distance, area, observers, all-obs-reported, checklist and
    observation comments, breeding codes.
  - no key (fallback): `taxon-list` once, then `taxon-detail` only for taxa that are new or whose numChecklists /
    numIndividuals differ from the stored snapshot (a new or edited checklist changes the counts of its taxa); taxa
    gone from the list are dropped. Gives species and counts per checklist only (no protocol, effort, comments).
    A checklist whose stored species are fewer than its numSpecies is logged as a warning.
  A checklist fetched in key mode keeps its key-mode rows when a later run has no key.

Request budget per report and run: people + checklists + 2 x (participants + 1) counts (num-species, num-checklists
per person and for the group; key-independent), plus taxon-list in fallback mode, plus the views / taxon details of
what changed, plus one taxonomy lookup for unknown codes. Unchanged report of 6 people: ~16 requests in key mode,
~17 in fallback mode.

State: pipeline/sources/ebird/trip_report_state.json (committed; the CSV is rebuilt from it on every run)
  {fetched_at (UTC ISO of the last run that changed anything), user_id,
   reports: {<id>: {person_id, checklists: {subId: {date, time, numSpecies, loc_id, loc_name, lat, lng, region}},
                    people: [{person_id, user_id, name, role, begin, end, species, other_taxa, checklists}]
                            (in the report's order; begin / end = personBeginDt / personEndDt as YYYY-MM-DD, null
                            when the person has no personal window, i.e. the whole report),
                    group: {species, other_taxa, checklists}  (the whole report),
                    views: {subId: {fetched, numSpecies, protocolId, durationHrs, allObsReported, numObservers,
                                    effortDistanceKm, effortAreaHa, comments, subnational1Code,
                                    obs: [{code, count, comments, breeding}]}},
                    taxa: {code: {category, sci, en, numChecklists, numIndividuals, detail: [[subId, howMany]]}}}},
   taxonomy: {code: {sci, name, order}}}  names of codes not in data/species (eBird ref/taxonomy, locale=ru, no key)
  Checklists missing from a successful `checklists` answer (deleted on eBird) are dropped with their rows.
  The counts are part of the state: a change in any of them is a change (state and CSV written, fetched_at updated).

Output: pipeline/sources/ebird/trip_report.csv, the same header and value formats as the export
(colombia_2026.csv): Date YYYY-MM-DD, Time "hh:mm AM", Protocol "eBird - Traveling Count" etc. (protocolId P22/P21/
P20/P23/P62 -> names of the export, unknown ids raw; empty in fallback mode), Count = howManyStr or the fallback's
howMany, "X" when absent / 0. Names: data/species/*.json by ebird_code (sci_name, Russian name, else English;
taxon_order), else the eBird taxonomy (state `taxonomy`, fetched only for codes not seen before). Columns the
sources lack (County, ML Catalog Numbers, effort in fallback mode) stay empty.

Writes happen only at the end and only when something changed (atomic, CSV first, state last): a network error, an
API refusal or a missing person exits non-zero with the previous CSV and state untouched.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PIPELINE, ROOT, SPECIES_DIR, USER_AGENT, env, log, read_json, write_json, write_text  # noqa: E402

SRC = PIPELINE / "sources" / "ebird"
CONFIG = SRC / "trip_reports.json"
STATE = SRC / "trip_report_state.json"
OUT_CSV = SRC / "trip_report.csv"

TRIP_API = "https://ebird.org/tripreport-internal/v1"
EBIRD_API = "https://api.ebird.org/v2"
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/129.0.0.0 Safari/537.36")
TZ = ZoneInfo("America/Bogota")
MIN_INTERVAL = 0.7  # s between requests (serial)
TIMEOUT = 20
ATTEMPTS = 3
RECENT_DAYS = 3
REFRESH_HOURS = 12

HEADER = ["Submission ID", "Common Name", "Scientific Name", "Taxonomic Order", "Count", "State/Province", "County",
          "Location ID", "Location", "Latitude", "Longitude", "Date", "Time", "Protocol", "Duration (Min)",
          "All Obs Reported", "Distance Traveled (km)", "Area Covered (ha)", "Number of Observers", "Breeding Code",
          "Observation Details", "Checklist Comments", "ML Catalog Numbers"]
PROTOCOLS = {"P20": "eBird - Casual Observation", "P21": "eBird - Stationary Count", "P22": "eBird - Traveling Count",
             "P23": "eBird - Area Count", "P62": "Historical"}


class FetchError(Exception):
    pass


# ---------- HTTP ----------

class Fetcher:
    """Serial GETs with a pause between requests, short timeout and a few retries; counts requests."""

    def __init__(self, client: httpx.Client | None = None, min_interval: float = MIN_INTERVAL):
        self.client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=True)
        self.min_interval = min_interval
        self.requests = 0
        self._last = 0.0

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None):
        err = ""
        for attempt in range(ATTEMPTS):
            wait = self._last + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.requests += 1
            try:
                r = self.client.get(url, params=params, headers=headers)
                if r.status_code == 200:
                    return r.json()
                err = f"HTTP {r.status_code}"
                if r.status_code < 500 and r.status_code != 429:
                    break  # 4xx: retrying will not help
            except (httpx.HTTPError, ValueError) as e:
                err = f"{type(e).__name__}: {e}"
            if attempt + 1 < ATTEMPTS:
                time.sleep(2 * 2 ** attempt)
        raise FetchError(f"{url}: {err}")

    def trip(self, path: str, params: dict | None = None):
        return self.get_json(f"{TRIP_API}/{path}", params, {"User-Agent": BROWSER_UA, "Accept": "application/json"})

    def ebird(self, path: str, params: dict | None = None, key: str | None = None):
        h = {"User-Agent": USER_AGENT}
        if key:
            h["x-ebirdapitoken"] = key
        return self.get_json(f"{EBIRD_API}/{path}", params, h)


# ---------- pure helpers (tested) ----------

def resolve_person(people: list[dict], user_id: str) -> int:
    for p in people or []:
        if p.get("userId") == user_id:
            return int(p["tripReportPersonId"])
    raise LookupError(f"{user_id} is not among the report's people "
                      f"({', '.join(str(p.get('userId')) for p in people or [])})")


def counts(num_species, num_checklists) -> dict:
    """num-species ([species, other taxa], or a bare number) and num-checklists answers -> the state's counts."""
    ns = num_species if isinstance(num_species, list) else [num_species]
    return {"species": int(ns[0] or 0) if ns else 0, "other_taxa": int(ns[1] or 0) if len(ns) > 1 else 0,
            "checklists": int(num_checklists or 0)}


def checklist_meta(c: dict) -> dict:
    loc = c.get("loc") or {}
    iso = c.get("isoObsDate") or ""
    return {"date": iso[:10], "time": c.get("obsTime") or iso[11:16] or None, "numSpecies": c.get("numSpecies"),
            "loc_id": c.get("locId") or loc.get("locId"), "loc_name": loc.get("name") or loc.get("locName"),
            "lat": loc.get("latitude", loc.get("lat")), "lng": loc.get("longitude", loc.get("lng")),
            "region": loc.get("subnational1Code")}


def plan_views(checklists: dict[str, dict], views: dict[str, dict], now: datetime) -> list[str]:
    """subIds to (re)fetch with checklist/view: new, numSpecies changed, or recent and not fetched for REFRESH_HOURS."""
    today = now.astimezone(TZ).date()
    out = []
    for sid, c in checklists.items():
        v = views.get(sid)
        if v is None or v.get("numSpecies") != c.get("numSpecies"):
            out.append(sid)
            continue
        recent = c.get("date") and date.fromisoformat(c["date"]) >= today - timedelta(days=RECENT_DAYS)
        fetched = datetime.fromisoformat((v.get("fetched") or "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
        if recent and now - fetched >= timedelta(hours=REFRESH_HOURS):
            out.append(sid)
    return out


def plan_taxa(taxon_list: list[dict], taxa: dict[str, dict]) -> list[str]:
    """speciesCodes whose taxon-detail must be (re)fetched: new taxa or changed counts."""
    out = []
    for t in taxon_list:
        old = taxa.get(t["speciesCode"])
        if old is None or old.get("numChecklists") != t.get("numChecklists") \
                or old.get("numIndividuals") != t.get("numIndividuals"):
            out.append(t["speciesCode"])
    return out


def view_entry(v: dict, num_species, fetched: str) -> dict:
    """What we keep of a checklist/view answer."""
    obs = []
    for o in v.get("obs") or []:
        breeding = next((a.get("value") for a in o.get("obsAux") or [] if a.get("fieldName") == "breeding_code"), None)
        obs.append({"code": o["speciesCode"], "count": o.get("howManyStr"), "comments": o.get("comments"),
                    "breeding": breeding})
    return {"fetched": fetched, "numSpecies": num_species,
            **{k: v.get(k) for k in ("protocolId", "durationHrs", "allObsReported", "numObservers", "effortDistanceKm",
                                     "effortAreaHa", "comments", "subnational1Code")},
            "obs": obs}


def fmt_time(t: str | None) -> str:
    """'06:19' -> '06:19 AM', '13:05' -> '01:05 PM', '00:05' -> '12:05 AM' (the export's format)."""
    if not t:
        return ""
    h, m = int(t[:2]), t[3:5]
    return f"{(h % 12) or 12:02d}:{m} {'AM' if h < 12 else 'PM'}"


def fmt_num(x, digits: int | None = 3) -> str:
    """Number as the export writes it: no trailing '.0', no leading zero ('.741', '-.5')."""
    if x is None or x == "":
        return ""
    x = float(x) if digits is None else round(float(x), digits)
    s = str(int(x)) if x == int(x) else str(x)
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def count_str(x) -> str:
    """howManyStr / howMany -> the export's Count ('X' when only present)."""
    if x is None:
        return "X"
    s = str(x).strip()
    return "X" if s in ("", "0", "X", "x") else s


def species_names() -> dict[str, dict]:
    """ebird_code -> {sci, name (ru, else en), order} from data/species/*.json."""
    out = {}
    for f in glob.glob(str(SPECIES_DIR / "*.json")):
        d = json.loads(Path(f).read_text())
        if d.get("ebird_code"):
            n = d.get("names") or {}
            out[d["ebird_code"]] = {"sci": d.get("sci_name"), "name": n.get("ru") or n.get("en") or "",
                                    "order": d.get("taxon_order")}
    return out


def build_rows(rep: dict, names: dict[str, dict]) -> list[dict]:
    """CSV rows (dicts over HEADER) of one report's state."""
    by_cl: dict[str, list[tuple[str, dict]]] = {}
    for code, t in (rep.get("taxa") or {}).items():
        for sid, how in t.get("detail") or []:
            by_cl.setdefault(sid, []).append((code, {"count": count_str(how)}))
    rows = []
    for sid, c in rep["checklists"].items():
        v = (rep.get("views") or {}).get(sid)
        base = {k: "" for k in HEADER}
        base.update({"Submission ID": sid, "State/Province": c.get("region") or "", "Location ID": c.get("loc_id") or "",
                     "Location": c.get("loc_name") or "",
                     "Latitude": fmt_num(c.get("lat"), None), "Longitude": fmt_num(c.get("lng"), None),
                     "Date": c.get("date") or "", "Time": fmt_time(c.get("time"))})
        if v:
            pid = v.get("protocolId") or ""
            base.update({
                "State/Province": v.get("subnational1Code") or base["State/Province"],
                "Protocol": PROTOCOLS.get(pid, pid),
                "Duration (Min)": str(round(v["durationHrs"] * 60)) if v.get("durationHrs") is not None else "",
                "All Obs Reported": "" if v.get("allObsReported") is None else str(int(bool(v["allObsReported"]))),
                "Distance Traveled (km)": fmt_num(v.get("effortDistanceKm")),
                "Area Covered (ha)": fmt_num(v.get("effortAreaHa")),
                "Number of Observers": fmt_num(v.get("numObservers")),
                "Checklist Comments": v.get("comments") or "",
            })
            items = [(o["code"], {"count": count_str(o.get("count")), "details": o.get("comments") or "",
                                  "breeding": o.get("breeding") or ""}) for o in v.get("obs") or []]
        else:
            items = by_cl.get(sid, [])
        for code, o in items:
            n = names.get(code) or {}
            t = (rep.get("taxa") or {}).get(code) or {}
            order = n.get("order")
            rows.append(((c.get("date") or "", c.get("time") or "", sid, float(order) if order is not None else 1e9),
                         {**base, "Common Name": n.get("name") or t.get("en") or "",
                          "Scientific Name": n.get("sci") or t.get("sci") or code,
                          "Taxonomic Order": fmt_num(order), "Count": o["count"],
                          "Breeding Code": o.get("breeding", ""), "Observation Details": o.get("details", "")}))
    rows.sort(key=lambda x: (x[0], x[1]["Scientific Name"]))  # date, 24 h time, checklist, taxonomic order
    return [r for _, r in rows]


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


# ---------- run ----------

def update_report(f: Fetcher, rid: int, user_id: str, old: dict, key: str | None, now: datetime, stats: dict) -> dict:
    """Fetch what changed for one report; returns its new state (old is not modified)."""
    people = f.trip(f"people/{rid}")
    person = resolve_person(people, user_id)
    pf = {"tripReportPersonId": person}
    listing = f.trip(f"checklists/{rid}", pf)
    checklists = {c["subId"]: checklist_meta(c) for c in listing}
    old_cl = old.get("checklists") or {}
    stats["checklists"] += len(checklists)
    stats["new"] += sum(1 for s in checklists if s not in old_cl)
    stats["changed"] += sum(1 for s, c in checklists.items() if s in old_cl and old_cl[s].get("numSpecies") != c["numSpecies"])
    stats["gone"] += sum(1 for s in old_cl if s not in checklists)
    fetched = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    views = {s: v for s, v in (old.get("views") or {}).items() if s in checklists}
    taxa = json.loads(json.dumps(old.get("taxa") or {}))
    if key:
        todo = plan_views(checklists, views, now)
        for sid in todo:
            views[sid] = view_entry(f.ebird(f"product/checklist/view/{sid}", None, key), checklists[sid]["numSpecies"], fetched)
        stats["views"] += len(todo)
    else:
        # a key-mode view of a checklist edited since then is stale: its taxon-detail rows take over
        views = {s: v for s, v in views.items() if v.get("numSpecies") == checklists[s]["numSpecies"]}
        tl = f.trip(f"taxon-list/{rid}", pf)
        todo = plan_taxa(tl, taxa)
        current = {t["speciesCode"] for t in tl}
        for code in [c for c in taxa if c not in current]:
            del taxa[code]
        by_code = {t["speciesCode"]: t for t in tl}
        for i, code in enumerate(todo, 1):
            d = f.trip(f"taxon-detail/{rid}/{code}", pf)
            t = by_code[code]
            taxa[code] = {"category": t.get("category"), "sci": t.get("sciName"), "en": t.get("commonName"),
                          "numChecklists": t.get("numChecklists"), "numIndividuals": t.get("numIndividuals"),
                          "detail": sorted([c["subId"], c.get("howMany")] for c in d.get("checklists") or [])}
            if i % 50 == 0:
                log(f"  taxon-detail {i}/{len(todo)}")
        stats["details"] += len(todo)
        covered: dict[str, int] = {}
        for t in taxa.values():
            if t.get("category") == "species":
                for sid, _ in t["detail"]:
                    covered[sid] = covered.get(sid, 0) + 1
        for sid, c in checklists.items():
            if sid not in views and (c["numSpecies"] or 0) > covered.get(sid, 0):
                log(f"  warning: {sid} ({c['date']}) has {c['numSpecies']} species, rows for {covered.get(sid, 0)}")
    # numbers only for the «Группа» block: every participant, then the whole report
    group_people = []
    for p in people:
        q = {"tripReportPersonId": int(p["tripReportPersonId"])}
        group_people.append({"person_id": q["tripReportPersonId"], "user_id": p.get("userId"),
                             "name": p.get("userDisplayName") or "", "role": p.get("role"),
                             "begin": (p.get("personBeginDt") or "")[:10] or None,
                             "end": (p.get("personEndDt") or "")[:10] or None,
                             **counts(f.trip(f"num-species/{rid}", q), f.trip(f"num-checklists/{rid}", q))})
    group = counts(f.trip(f"num-species/{rid}"), f.trip(f"num-checklists/{rid}"))
    stats["group"].append(f"group {group['species']} species / {group['checklists']} checklists, "
                          f"{len(group_people)} people")
    return {"person_id": person, "checklists": checklists, "views": views, "taxa": taxa,
            "people": group_people, "group": group}


def strip_times(state: dict) -> dict:
    """State without run timestamps (to tell whether anything changed)."""
    s = json.loads(json.dumps(state))
    s.pop("fetched_at", None)
    return s


def run(f: Fetcher, key: str | None, now: datetime) -> dict:
    """The whole step; writes nothing until every request has succeeded. Returns a summary."""
    cfg = read_json(CONFIG)
    if not cfg or not cfg.get("user_id") or not cfg.get("reports"):
        raise SystemExit(f"ebird_trip: {CONFIG} needs user_id and reports")
    old = read_json(STATE) or {}
    if old.get("user_id") not in (None, cfg["user_id"]):
        old = {}  # another person: start over
    stats = {"checklists": 0, "new": 0, "changed": 0, "gone": 0, "views": 0, "details": 0, "group": []}
    reports = {}
    for r in cfg["reports"]:
        rid = str(r["id"])
        reports[rid] = update_report(f, int(r["id"]), cfg["user_id"], (old.get("reports") or {}).get(rid) or {},
                                     key, now, stats)
    names = species_names()
    taxonomy = dict(old.get("taxonomy") or {})
    codes = {o["code"] for rep in reports.values() for v in rep["views"].values() for o in v["obs"]} \
        | {c for rep in reports.values() for c in rep["taxa"]}
    missing = sorted(c for c in codes if c not in names and c not in taxonomy)
    if missing:
        for i in range(0, len(missing), 100):
            for t in f.ebird("ref/taxonomy/ebird", {"species": ",".join(missing[i:i + 100]), "fmt": "json", "locale": "ru"}):
                taxonomy[t["speciesCode"]] = {"sci": t.get("sciName"), "name": t.get("comName"), "order": t.get("taxonOrder")}
    taxonomy = {c: v for c, v in taxonomy.items() if c in codes}
    new_state = {"user_id": cfg["user_id"], "reports": reports, "taxonomy": dict(sorted(taxonomy.items()))}
    rows = [row for rep in reports.values() for row in build_rows(rep, {**taxonomy, **names})]
    seen, uniq = set(), []
    for row in rows:  # two reports overlapping by a day: keep the first copy of a checklist
        k = (row["Submission ID"], row["Scientific Name"])
        if k not in seen:
            seen.add(k)
            uniq.append(row)
    text = to_csv(uniq)
    changed = strip_times(new_state) != strip_times(old) or not OUT_CSV.exists() or OUT_CSV.read_text() != text
    if changed:
        new_state["fetched_at"] = now.isoformat(timespec="seconds").replace("+00:00", "Z")
        write_text(OUT_CSV, text)
        write_json(STATE, new_state)
    return {**stats, "requests": f.requests, "rows": len(uniq), "wrote": changed,
            "mode": "key" if key else "taxon-list", "unknown_codes": len(missing)}


def main() -> None:
    key = (env("EBIRD_API_KEY") or "").strip() or None
    t0 = time.monotonic()
    f = Fetcher()
    try:
        s = run(f, key, datetime.now(timezone.utc))
    except LookupError as e:
        sys.exit(f"ebird_trip: {e}; nothing written")
    except FetchError as e:
        sys.exit(f"ebird_trip: request failed after {f.requests} requests ({e}); nothing written, "
                 f"{OUT_CSV.relative_to(ROOT)} and the state left as they were")
    log(f"ebird_trip ({s['mode']}): {s['checklists']} checklists in the report(s), {s['new']} new, {s['changed']} changed, "
        f"{s['gone']} gone; {s['views']} checklist views, {s['details']} taxon details, {s['unknown_codes']} codes looked up "
        f"in the taxonomy; {'; '.join(s['group'])}; {s['requests']} requests in {time.monotonic() - t0:.0f}s; "
        + (f"{s['rows']} rows -> {OUT_CSV.relative_to(ROOT)}" if s["wrote"] else "nothing changed, files untouched"))


if __name__ == "__main__":
    main()
