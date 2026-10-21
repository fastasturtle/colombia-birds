"""Hidden page /igor-500/: derived plan data for one trip participant's push to N species -> data/igor500.json

Runs every 2 hours in .github/workflows/observations.yml after `ebird_trip observations` (continue-on-error: a failed
refresh must not block the observations commit). Manual: `uv run python run.py igor500`.

Config: pipeline/mappings/igor500.json
  {report, person (substring of the participant's userDisplayName), person_ru, goal,
   sites: [site ids of data/site_species.json, in page order],
   reserve: [sites that get candidate lists but are left out of sure_total / likely_total / reachable_missed
             (la-florida: the optional Bogotá day after the programme)]}

Sources: the eBird trip report JSON backend through fetch_ebird_trip.Fetcher (same User-Agent, serial requests,
retries; no key), 4 requests per run:
  people/{report}                          -> the person whose userDisplayName contains `person` (exactly one)
  taxon-list/{report}?tripReportPersonId=P -> the person's taxa
  taxon-list/{report}                      -> the whole group's taxa
  checklists/{report}?tripReportPersonId=P -> only the count and the latest isoObsDate (as_of)
Species are matched to data/species_index.json by scientific name (eBird/Clements 2025, the site's canon); only
category "species" counts; unmatched names are logged as a warning.

Privacy (owner decision): nothing but the derived structure below is written anywhere. The person's species list,
the group's list and all checklists / locations stay in memory; no state file, no CSV.

Output: data/igor500.json
  {person, person_ru, species, checklists, as_of "YYYY-MM-DD HH:MM", goal, group_species, missed_in_group,
   sure_total, likely_total, fetched (UTC ISO of the last run that changed anything),
   sites: {site: [{id, sci, en, ru, family, n_aut, n, tier, group}]}   candidate species the person does not have
     (data/site_species.json rows with n_aut >= 1; tier sure n_aut >= 20 / likely 5-19 / chance 1-4; group = the
     group's list has it), sorted by n_aut desc,
   reachable_missed: [{id, sci, en, ru, sites: {site: n_aut}}]  in the group's list, not the person's, n_aut >= 3 at
     one of the non-reserve sites (only those listed); sorted by max n_aut desc}
  sure_total = distinct candidates "sure" at a non-reserve site; likely_total = distinct candidates "likely" at a
  non-reserve site and "sure" at none.
Deterministic: when nothing but `fetched` would change, the file is left untouched (so ci_commit.sh commits nothing).
A network error or a missing person exits non-zero with data/igor500.json untouched.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, PIPELINE, ROOT, log, read_json, write_json  # noqa: E402
from fetch_ebird_trip import FetchError, Fetcher  # noqa: E402

CONFIG = PIPELINE / "mappings" / "igor500.json"
OUT = DATA / "igor500.json"
SURE, LIKELY, REACHABLE = 20, 5, 3
KEYS = {"person", "person_ru", "species", "checklists", "as_of", "goal", "group_species", "missed_in_group",
        "sure_total", "likely_total", "fetched", "sites", "reachable_missed"}


def tier(n_aut: int) -> str:
    return "sure" if n_aut >= SURE else "likely" if n_aut >= LIKELY else "chance"


def find_person(people: list[dict], name: str) -> dict:
    hits = [p for p in people or [] if name.lower() in (p.get("userDisplayName") or "").lower()]
    if len(hits) != 1:
        raise LookupError(f"{len(hits)} people in the report match {name!r}")
    return hits[0]


def species_sci(taxa: list[dict]) -> set[str]:
    return {t["sciName"] for t in taxa or [] if t.get("category") == "species" and t.get("sciName")}


def compute(cfg: dict, person: dict, person_taxa: list[dict], group_taxa: list[dict], checklists: list[dict],
            index: list[dict], site_species: dict) -> tuple[dict, list[str]]:
    """The derived output (without `fetched`) and the scientific names not found in the species index."""
    by_sci = {s["sci"]: s for s in index}
    by_id = {s["id"]: s for s in index}
    mine_sci, group_sci = species_sci(person_taxa), species_sci(group_taxa)
    unmatched = sorted((mine_sci | group_sci) - by_sci.keys())
    mine = {by_sci[s]["id"] for s in mine_sci if s in by_sci}
    group = {by_sci[s]["id"] for s in group_sci if s in by_sci}

    def names(sid: str) -> dict:
        s = by_id[sid]
        return {"id": sid, "sci": s["sci"], "en": s["en"], "ru": s.get("ru")}

    sites, aut = {}, {}
    for site in cfg["sites"]:
        rows = (site_species.get(site) or {}).get("species") or []
        aut[site] = {r["id"]: r["n_aut"] for r in rows if r["id"] in by_id}
        cand = [{**names(r["id"]), "family": by_id[r["id"]].get("family"), "n_aut": r["n_aut"], "n": r["n"],
                 "tier": tier(r["n_aut"]), "group": r["id"] in group}
                for r in rows if r.get("n_aut", 0) >= 1 and r["id"] in by_id and r["id"] not in mine]
        sites[site] = sorted(cand, key=lambda c: (-c["n_aut"], c["en"], c["id"]))

    ahead = [s for s in cfg["sites"] if s not in set(cfg.get("reserve") or [])]  # the reserve day is not counted
    best: dict[str, set[str]] = {}
    for site in ahead:
        for c in sites[site]:
            best.setdefault(c["id"], set()).add(c["tier"])
    reachable = []
    for sid in group - mine:
        where = {site: aut[site][sid] for site in ahead if aut[site].get(sid, 0) >= REACHABLE}
        if where:
            reachable.append({**names(sid), "sites": where})
    reachable.sort(key=lambda m: (-max(m["sites"].values()), m["en"], m["id"]))

    dates = [c.get("isoObsDate") or "" for c in checklists or []]
    out = {
        "person": person.get("userDisplayName"), "person_ru": cfg.get("person_ru"),
        "species": len(mine_sci), "checklists": len(checklists or []), "as_of": max(dates)[:16] if dates else None,
        "goal": cfg["goal"], "group_species": len(group_sci), "missed_in_group": len(group_sci - mine_sci),
        "sure_total": sum("sure" in t for t in best.values()),
        "likely_total": sum("likely" in t and "sure" not in t for t in best.values()),
        "sites": sites, "reachable_missed": reachable,
    }
    return out, unmatched


def fetch(f: Fetcher, cfg: dict) -> tuple[dict, list, list, list]:
    rid = cfg["report"]
    person = find_person(f.trip(f"people/{rid}"), cfg["person"])
    pid = {"tripReportPersonId": person["tripReportPersonId"]}
    return (person, f.trip(f"taxon-list/{rid}", pid), f.trip(f"taxon-list/{rid}"), f.trip(f"checklists/{rid}", pid))


def write_if_changed(out: dict, now: datetime, path: Path = OUT) -> bool:
    old = read_json(path) or {}
    if {k: v for k, v in old.items() if k != "fetched"} == out and old.get("fetched"):
        return False
    write_json(path, {**out, "fetched": now.isoformat(timespec="seconds").replace("+00:00", "Z")})
    return True


def run(f: Fetcher, now: datetime, path: Path = OUT, cfg: dict | None = None, index: list | None = None,
        site_species: dict | None = None) -> dict:
    """The whole step (inputs default to the repo files); writes only after every request has succeeded."""
    cfg = cfg or read_json(CONFIG)
    person, mine, group, checklists = fetch(f, cfg)
    if not species_sci(mine):
        raise LookupError("the person's taxon list is empty (API glitch?)")
    out, unmatched = compute(cfg, person, mine, group, checklists, index or read_json(DATA / "species_index.json"),
                             site_species or read_json(DATA / "site_species.json"))
    if unmatched:
        log(f"igor500: warning: {len(unmatched)} names not in data/species_index.json: {', '.join(unmatched)}")
    return {**out, "wrote": write_if_changed(out, now, path), "requests": f.requests}


def main() -> None:
    t0 = time.monotonic()
    f = Fetcher()
    try:
        s = run(f, datetime.now(timezone.utc))
    except LookupError as e:
        sys.exit(f"igor500: {e}; {OUT.relative_to(ROOT)} left as it was")
    except FetchError as e:
        sys.exit(f"igor500: request failed after {f.requests} requests ({e}); {OUT.relative_to(ROOT)} left as it was")
    log(f"igor500: {s['species']} species, {s['checklists']} checklists (as of {s['as_of']}); group {s['group_species']}; "
        f"{s['sure_total']} sure, {s['likely_total']} likely, {len(s['reachable_missed'])} reachable missed; "
        f"{s['requests']} requests in {time.monotonic() - t0:.0f}s; "
        + (f"-> {OUT.relative_to(ROOT)}" if s["wrote"] else "nothing changed, file untouched"))


if __name__ == "__main__":
    main()
