"""Tests for steps/fetch_ebird_trip.py on responses captured from the eBird trip report backend (report 579125,
18.10.2026, tests/fixtures/ebird_trip/) and the documented sample of the eBird API `product/checklist/view`.

Run: `cd pipeline && uv run python tests/test_fetch_ebird_trip.py` (plain asserts, no network).
"""
from __future__ import annotations

import copy
import csv
import io
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "steps"))
sys.path.insert(0, str(HERE.parent))
import fetch_ebird_trip as ft  # noqa: E402

FIX = HERE / "fixtures" / "ebird_trip"
NOW = datetime(2026, 10, 18, 18, 0, tzinfo=timezone.utc)
ANYA = "USER3559161"


def fx(name: str):
    return json.loads((FIX / name).read_text())


NAMES = {"grethr1": {"sci": "Turdus fuscater", "name": "Большой дрозд", "order": 28677.0},
         "gwfgoo": {"sci": "Anser albifrons", "name": "Белолобый гусь", "order": 255.0}}


class FakeFetcher(ft.Fetcher):
    """Serves fixtures by path; `fail_on` (substring of the path) raises FetchError like a dead network."""

    def __init__(self, taxon_list=None, fail_on: str | None = None, people=None):
        super().__init__(client=object(), min_interval=0)
        self.taxon_list = taxon_list if taxon_list is not None else fx("taxon_list.json")
        self.people = people if people is not None else fx("people.json")
        self.fail_on = fail_on
        self.paths: list[str] = []

    def get_json(self, url, params=None, headers=None):
        self.requests += 1
        path = url.split("/v1/", 1)[-1].split("/v2/", 1)[-1]
        self.paths.append(path)
        if self.fail_on and self.fail_on in path:
            raise ft.FetchError(f"{url}: ConnectError")
        if path.startswith("people/"):
            return self.people
        if path.startswith("checklists/"):
            assert params == {"tripReportPersonId": 820854}, params  # always person-filtered
            return fx("checklists.json")
        if path.startswith("taxon-list/"):
            assert params == {"tripReportPersonId": 820854}
            return self.taxon_list
        if path.startswith("taxon-detail/"):
            assert params == {"tripReportPersonId": 820854}
            return fx("taxon_detail_grethr1.json") if path.endswith("/grethr1") else {"checklists": [], "assetIds": []}
        if path.startswith("product/checklist/view/"):
            assert headers.get("x-ebirdapitoken") == "KEY"
            v = fx("checklist_view.json")
            v["subId"] = path.rsplit("/", 1)[1]
            return v
        if path.startswith("ref/taxonomy/ebird"):
            known = {"rocpig": ("Columba livia", "Сизый голубь", 1853.0),
                     "x00868": ("Myioborus ornatus x melanocephalus", "Белолицая x Очковая канделита (гибрид)", 34393.0),
                     "gwfgoo2": ("Anser albifrons flavirostris", "Белолобый гусь (Greenland)", 258.0),
                     "cacgoo1": ("Branta hutchinsii", "Малая канадская казарка", 290.0)}
            return [{"speciesCode": c, "sciName": known[c][0], "comName": known[c][1], "taxonOrder": known[c][2]}
                    for c in params["species"].split(",") if c in known]
        raise AssertionError(f"unexpected request {url}")


class Sandbox:
    """Points the step's config/state/CSV paths at a temp dir and fixes the species-file names."""

    def __enter__(self):
        self.td = tempfile.TemporaryDirectory()
        d = Path(self.td.name)
        self.saved = (ft.CONFIG, ft.STATE, ft.OUT_CSV, ft.species_names)
        ft.CONFIG, ft.STATE, ft.OUT_CSV = d / "trip_reports.json", d / "state.json", d / "trip_report.csv"
        ft.CONFIG.write_text(json.dumps({"user_id": ANYA, "reports": [{"id": 579125, "note": "test"}]}))
        ft.species_names = lambda: dict(NAMES)
        return self

    def __exit__(self, *exc):
        ft.CONFIG, ft.STATE, ft.OUT_CSV, ft.species_names = self.saved
        self.td.cleanup()


def read_rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def test_person_resolution():
    people = fx("people.json")
    assert ft.resolve_person(people, ANYA) == 820854
    assert ft.resolve_person(people, "USER2882675") == 820853
    try:
        ft.resolve_person(people, "USER0000000")
    except LookupError as e:
        assert "USER0000000" in str(e)
    else:
        raise AssertionError("missing person must raise")


def test_formats():
    assert ft.fmt_time("06:19") == "06:19 AM" and ft.fmt_time("13:05") == "01:05 PM"
    assert ft.fmt_time("00:05") == "12:05 AM" and ft.fmt_time("12:30") == "12:30 PM" and ft.fmt_time(None) == ""
    assert ft.count_str(3) == "3" and ft.count_str(None) == "X" and ft.count_str(0) == "X" and ft.count_str("X") == "X"
    assert ft.fmt_num(0.9385913, None) == ".9385913" and ft.fmt_num(-77.9582592, None) == "-77.9582592"
    assert ft.fmt_num(0.7414) == ".741" and ft.fmt_num(2.0) == "2" and ft.fmt_num(None) == ""
    m = ft.checklist_meta(fx("checklists.json")[0])
    assert set(m) == {"date", "time", "numSpecies", "loc_id", "loc_name", "lat", "lng", "region"}
    assert m["date"].startswith("2026-10-1") and len(m["time"]) == 5 and m["region"].startswith("CO-")


def test_plan_taxa():
    tl = fx("taxon_list.json")
    assert sorted(ft.plan_taxa(tl, {})) == ["grethr1", "rocpig", "x00868"]
    stored = {t["speciesCode"]: {"numChecklists": t["numChecklists"], "numIndividuals": t["numIndividuals"]} for t in tl}
    assert ft.plan_taxa(tl, stored) == []
    tl2 = copy.deepcopy(tl)
    next(t for t in tl2 if t["speciesCode"] == "grethr1")["numIndividuals"] += 1
    assert ft.plan_taxa(tl2, stored) == ["grethr1"]


def test_plan_views():
    cls = {"S1": {"date": "2026-10-18", "numSpecies": 5}, "S2": {"date": "2026-10-10", "numSpecies": 7},
           "S3": {"date": "2026-10-10", "numSpecies": 4}, "S4": {"date": "2026-10-17", "numSpecies": 3},
           "S5": {"date": "2026-10-16", "numSpecies": 2}}
    views = {"S2": {"numSpecies": 7, "fetched": "2026-10-11T00:00:00Z"},   # old, unchanged: skip
             "S3": {"numSpecies": 3, "fetched": "2026-10-18T17:00:00Z"},   # numSpecies changed: refetch
             "S4": {"numSpecies": 3, "fetched": "2026-10-18T10:00:00Z"},   # recent but fetched 8 h ago: skip
             "S5": {"numSpecies": 2, "fetched": "2026-10-17T12:00:00Z"}}   # recent, fetched 30 h ago: refetch
    assert ft.plan_views(cls, views, NOW) == ["S1", "S3", "S5"]


def test_key_mode_rows():
    v = fx("checklist_view.json")
    e = ft.view_entry(v, 3, "2026-10-18T18:00:00Z")
    assert e["protocolId"] == "P21" and e["durationHrs"] == 1.0 and e["allObsReported"] is False and e["numObservers"] == 1
    assert [o["code"] for o in e["obs"]] == ["gwfgoo", "gwfgoo2", "cacgoo1"]
    assert e["obs"][2]["breeding"] == "C4" and e["obs"][0]["count"] == "1"
    rep = {"checklists": {"S29893687": {"date": "2018-01-04", "time": "23:29", "numSpecies": 3, "loc_id": "L99381",
                                        "loc_name": "Somewhere", "lat": 0.5, "lng": -77.25, "region": "US-NY"}},
           "views": {"S29893687": e}, "taxa": {}}
    names = {**NAMES, "cacgoo1": {"sci": "Branta hutchinsii", "name": "Малая канадская казарка", "order": 290.0}}
    rows = ft.build_rows(rep, names)
    assert [r["Scientific Name"] for r in rows] == ["Anser albifrons", "Branta hutchinsii", "gwfgoo2"]  # unknown code kept raw
    r = rows[0]
    assert list(r) == ft.HEADER and len(ft.HEADER) == 23
    assert r["Common Name"] == "Белолобый гусь" and r["Taxonomic Order"] == "255" and r["Count"] == "1"
    assert (r["Date"], r["Time"], r["Protocol"], r["Duration (Min)"]) == ("2018-01-04", "11:29 PM", "eBird - Stationary Count", "60")
    assert (r["All Obs Reported"], r["Number of Observers"], r["Latitude"], r["Longitude"]) == ("0", "1", ".5", "-77.25")
    assert rows[1]["Breeding Code"] == "C4" and r["County"] == "" and r["ML Catalog Numbers"] == ""


def test_fallback_run_and_incremental():
    with Sandbox():
        f = FakeFetcher()
        s = ft.run(f, None, NOW)
        assert s["wrote"] and s["mode"] == "taxon-list" and s["checklists"] == 3 and s["new"] == 3
        # people, checklists, taxon-list, 3 taxon-details, 1 taxonomy lookup (rocpig, x00868 not in the species files)
        assert s["requests"] == 7 and s["details"] == 3 and s["unknown_codes"] == 2, s
        assert sorted(f.paths[3:6]) == ["taxon-detail/579125/grethr1", "taxon-detail/579125/rocpig", "taxon-detail/579125/x00868"]
        text = ft.OUT_CSV.read_text()
        rows = read_rows(text)
        assert list(rows[0]) == ft.HEADER
        # grethr1 detail lists 5 checklists, only the 2 in the (sliced) checklist list become rows
        assert [(r["Submission ID"], r["Count"]) for r in rows] == [("S402636312", "1"), ("S402635896", "2")]
        r = rows[0]
        assert (r["Common Name"], r["Scientific Name"], r["Taxonomic Order"]) == ("Большой дрозд", "Turdus fuscater", "28677")
        assert r["Date"] == "2026-10-15" and r["Time"] == "09:50 AM" and r["Protocol"] == "" and r["State/Province"].startswith("CO-")
        state = json.loads(ft.STATE.read_text())
        assert state["fetched_at"] == "2026-10-18T18:00:00Z" and state["reports"]["579125"]["person_id"] == 820854
        assert set(state["taxonomy"]) == {"rocpig", "x00868"}

        # unchanged report: people + checklists + taxon-list, nothing written
        f2 = FakeFetcher()
        s2 = ft.run(f2, None, datetime(2026, 10, 18, 20, 0, tzinfo=timezone.utc))
        assert s2["requests"] == 3 and not s2["wrote"] and s2["details"] == 0
        assert ft.OUT_CSV.read_text() == text and json.loads(ft.STATE.read_text())["fetched_at"] == "2026-10-18T18:00:00Z"

        # one taxon's counts changed: only its detail is fetched again; a taxon gone from the list is dropped
        tl = [t for t in fx("taxon_list.json") if t["speciesCode"] != "x00868"]
        next(t for t in tl if t["speciesCode"] == "grethr1")["numIndividuals"] += 1
        f3 = FakeFetcher(taxon_list=tl)
        s3 = ft.run(f3, None, NOW)
        assert s3["requests"] == 4 and f3.paths[-1] == "taxon-detail/579125/grethr1" and s3["wrote"]
        assert "x00868" not in json.loads(ft.STATE.read_text())["reports"]["579125"]["taxa"]


def test_key_mode_run():
    with Sandbox():
        s = ft.run(FakeFetcher(), "KEY", NOW)
        # people, checklists, 3 checklist views, 1 taxonomy lookup (gwfgoo2, cacgoo1); no taxon-list in key mode
        assert s["mode"] == "key" and s["views"] == 3 and s["requests"] == 6, s
        rows = read_rows(ft.OUT_CSV.read_text())
        assert len(rows) == 9 and {r["Protocol"] for r in rows} == {"eBird - Stationary Count"}
        # the 18 Oct checklist is recent: fetched again only after REFRESH_HOURS
        s2 = ft.run(FakeFetcher(), "KEY", datetime(2026, 10, 18, 20, 0, tzinfo=timezone.utc))
        assert s2["requests"] == 2 and not s2["wrote"]
        s3 = ft.run(FakeFetcher(), "KEY", datetime(2026, 10, 19, 7, 0, tzinfo=timezone.utc))
        assert s3["views"] == 1 and s3["requests"] == 3 and s3["wrote"]  # only its `fetched` changed
        # a later run without the key keeps the key-mode rows (numSpecies unchanged)
        s4 = ft.run(FakeFetcher(), None, NOW)
        assert {r["Protocol"] for r in read_rows(ft.OUT_CSV.read_text())} == {"eBird - Stationary Count"}
        assert s4["details"] == 3


def test_no_write_on_failure():
    with Sandbox():
        ft.run(FakeFetcher(), None, NOW)
        csv_before, state_before = ft.OUT_CSV.read_text(), ft.STATE.read_text()
        tl = copy.deepcopy(fx("taxon_list.json"))
        for t in tl:
            t["numChecklists"] += 1  # everything changed
        for fail in ("taxon-detail/579125/rocpig", "taxon-list/", "ref/taxonomy"):
            f = FakeFetcher(taxon_list=tl + ([{"speciesCode": "newsp1", "category": "species", "sciName": "Nova avis",
                                               "commonName": "New", "numIndividuals": 1, "numChecklists": 1}]
                                             if fail == "ref/taxonomy" else []), fail_on=fail)
            try:
                ft.run(f, None, NOW)
            except ft.FetchError:
                pass
            else:
                raise AssertionError(f"failure in {fail} must propagate")
            assert ft.OUT_CSV.read_text() == csv_before and ft.STATE.read_text() == state_before, fail
        # the person left the report: nothing written either
        try:
            ft.run(FakeFetcher(people=[p for p in fx("people.json") if p["userId"] != ANYA]), None, NOW)
        except LookupError:
            pass
        else:
            raise AssertionError("missing person must raise")
        assert ft.OUT_CSV.read_text() == csv_before and ft.STATE.read_text() == state_before


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print(f"ok {name}")
    print(f"{n} tests passed")
