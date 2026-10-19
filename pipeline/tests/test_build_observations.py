"""Tests for steps/build_observations.py on an invented export (tests/fixtures/observations/MyEBirdData.csv).

Run: `cd pipeline && uv run python tests/test_build_observations.py` (plain asserts, no pytest needed).
"""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "steps"))
sys.path.insert(0, str(HERE.parent))
import build_observations as bo  # noqa: E402

FIX = HERE / "fixtures" / "observations" / "MyEBirdData.csv"

INDEX = [
    {"id": "columba-livia", "sci": "Columba livia"},
    {"id": "avis-prima", "sci": "Avis prima"},
    {"id": "avis-secunda", "sci": "Avis secunda"},
    {"id": "avis-tertia", "sci": "Avis tertia"},
]
SITES = [
    {"id": "alpha", "name": "Alpha Reserve", "lat": 4.0, "lon": -74.0, "ebird_hotspots": [{"id": "L100", "name": "Hotspot Alpha"}]},
    # gamma is the nearest point to checklist S3, but S3's location names Betaville, a site of the same day
    {"id": "gamma", "name": "Gamma Birding & Coffee", "lat": 4.011, "lon": -74.104, "ebird_hotspots": []},
    {"id": "betaville", "name": "Parque Natural Betaville", "lat": 4.02, "lon": -74.12, "ebird_hotspots": []},
]
ITIN = [
    {"date": "2026-10-02", "sites": ["alpha"], "overnight_site": None},
    {"date": "2026-10-03", "sites": ["gamma", "betaville"], "overnight_site": None},
    {"date": "2026-10-04", "sites": [], "overnight_site": None},
]


def test_names():
    assert bo.species_name("Columba livia (Feral Pigeon)") == "Columba livia"
    assert bo.species_name("Cyanocorax yncas [yncas Group]") == "Cyanocorax yncas"
    assert bo.species_name("Turdus fuscater gigas") == "Turdus fuscater"
    for g in ("Avis sp.", "Avis prima/secunda", "Avis prima x secunda", "Avis prima x Avis secunda (hybrid)"):
        assert bo.is_generic(g) and bo.species_name(g) is None, g
    assert bo.parse_time("06:14 AM") == "06:14" and bo.parse_time("12:26 PM") == "12:26"
    assert bo.parse_time("02:00 PM") == "14:00" and bo.parse_time("12:05 AM") == "00:05" and bo.parse_time("") is None
    assert bo.protocol("eBird - Traveling Count") == "traveling" and bo.protocol("eBird - Casual Observation") == "casual"
    assert bo.num(".75") == 0.75 and bo.num("") is None and bo.num("238", int) == 238


def test_site_matching():
    day3 = ITIN[1]
    cl = {"location_id": "L555", "location": "Camino de entrada a Betaville", "lat": 4.012, "lon": -74.105}
    assert bo.match_site(cl, SITES, day3) == "betaville"  # name of a day site beats the nearer point
    assert bo.match_site({**cl, "location": "Some trail"}, SITES, day3) == "gamma"  # nearest within NEAR_KM
    assert bo.match_site({**cl, "location_id": "L100"}, SITES, day3) == "alpha"  # hotspot id wins
    assert bo.match_site({"location_id": "L1", "location": "Roadside", "lat": 5.0, "lon": -75.0}, SITES, day3) is None
    # the name match only counts for the day's sites
    assert bo.match_site({**cl, "lat": 4.3, "lon": -74.3}, SITES, ITIN[0]) is None


def test_import_and_build():
    with tempfile.TemporaryDirectory() as td:
        bo.TRIP_CSV, bo.LIFE_JSON = Path(td) / "colombia_2026.csv", Path(td) / "life.json"
        bo.import_export(FIX, "2026-10-01")
        life = json.loads(bo.LIFE_JSON.read_text())
        assert life == {"before": "2026-10-01", "exported": "2026-10-04", "species": ["Avis prima", "Columba livia"]}
        header, rows = bo.read_csv(bo.TRIP_CSV.read_text())
        assert header[0] == "Submission ID" and len(header) == 23
        assert {r["Submission ID"] for r in rows} == {"S2", "S3", "S4", "S5"}  # no pre-trip, no non-Colombia rows
    obs = bo.build(rows, set(life["species"]), INDEX, SITES, ITIN, "2026-10-01", life["exported"])
    sp = obs["species"]
    assert set(sp) == {"columba-livia", "avis-prima", "avis-secunda", "avis-tertia"}
    assert not sp["columba-livia"]["lifer"] and not sp["avis-prima"]["lifer"]
    assert sp["avis-secunda"]["lifer"] and sp["avis-tertia"]["lifer"]
    b = sp["avis-secunda"]
    assert b["first"] == "2026-10-02" and b["n_checklists"] == 2 and b["sites"] == ["alpha", "betaville"]
    assert b["obs"][0] == {"cl": "S2", "date": "2026-10-02", "time": "06:14", "site": "alpha", "count": 2, "details": "Voice"}
    assert sp["columba-livia"]["obs"][0]["count"] is None  # «X»
    assert [u["sci"] for u in obs["unmatched"]] == ["Avis prima/secunda", "Avis sp.", "Ignota ignota"]
    cls = {c["id"]: c for c in obs["checklists"]}
    assert [c["id"] for c in obs["checklists"]] == ["S2", "S3", "S4", "S5"]
    assert cls["S2"]["site"] == "alpha" and cls["S3"]["site"] == "betaville" and cls["S4"]["site"] is None
    assert cls["S5"]["site"] == "alpha" and cls["S5"]["time"] == "00:05" and cls["S5"]["day"] == "2026-10-04"
    # S5 is 0.5 km from alpha (no hotspot id) on 2026-10-04, a day without alpha: passing
    assert [c["id"] for c in obs["checklists"] if c.get("passing")] == ["S5"]
    assert cls["S2"]["n_species"] == 2 and cls["S2"]["comments"] == "Ранний выход" and cls["S2"]["observers"] == 3
    st = obs["stats"]
    assert (st["species"], st["lifers"], st["checklists"], st["days"]) == (4, 2, 4, 3)
    # lifers are counted among `new` only: avis-secunda (first on 10-02 at alpha) is seen again on 10-03 and off-site,
    # but counts as a lifer only for 10-02 / alpha; avis-tertia (first on 10-03 at betaville) for 10-03 / betaville
    assert st["by_day"]["2026-10-02"] == {"species": 2, "new": 2, "lifers": 1, "checklists": 1, "observations": 2}
    assert st["by_day"]["2026-10-03"] == {"species": 2, "new": 1, "lifers": 1, "checklists": 2, "observations": 3}
    assert st["by_day"]["2026-10-04"] == {"species": 1, "new": 1, "lifers": 0, "checklists": 1, "observations": 1}
    assert st["by_site"]["alpha"] == {"species": 3, "new": 3, "lifers": 1, "checklists": 2, "observations": 3,
                                      "passing_checklists": 1}
    assert st["by_site"]["betaville"] == {"species": 2, "new": 1, "lifers": 1, "checklists": 1, "observations": 2}
    assert st["off_site"] == {"species": 1, "new": 0, "lifers": 0, "checklists": 1, "observations": 1}
    # per-day columns add up to the trip totals
    assert sum(e["new"] for e in st["by_day"].values()) == st["species"]
    assert sum(e["lifers"] for e in st["by_day"].values()) == st["lifers"]


def test_passing():
    """A checklist matched by distance on a day its site is not on the route is «passing»; stats keep counting it."""
    head = ["Submission ID", "Common Name", "Scientific Name", "Count", "Location ID", "Location", "Latitude", "Longitude",
            "Date", "Time", "Protocol"]
    def row(sid, sci, loc_id, loc, lat, lon, date):
        return dict(zip(head, [sid, "", sci, "1", loc_id, loc, str(lat), str(lon), date, "07:00 AM", "eBird - Stationary Count"]))
    rows = [
        row("P1", "Avis prima", "L900", "Roadside", 4.012, -74.105, "2026-10-02"),   # near gamma, gamma is on 10-03 -> passing
        row("P2", "Avis secunda", "L900", "Roadside", 4.012, -74.105, "2026-10-03"),  # same spot on gamma's day -> not
        row("P3", "Avis tertia", "L100", "Hotspot Alpha", 4.0, -74.0, "2026-10-04"),  # alpha's hotspot off its day -> not
        row("P4", "Avis tertia", "L901", "Lodge garden", 4.012, -74.105, "2026-10-04"),  # gamma is the overnight site -> not
    ]
    itin = [*ITIN[:2], {"date": "2026-10-04", "sites": [], "overnight_site": "gamma"}]
    obs = bo.build(rows, set(), INDEX, SITES, itin, "2026-10-01", "2026-10-04")
    cls = {c["id"]: c for c in obs["checklists"]}
    assert cls["P1"]["site"] == "gamma" and cls["P1"]["passing"] is True
    assert [k for k, c in cls.items() if c.get("passing")] == ["P1"]
    g = obs["stats"]["by_site"]["gamma"]
    assert g["checklists"] == 3 and g["species"] == 3 and g["passing_checklists"] == 1
    assert "passing_checklists" not in obs["stats"]["by_site"]["alpha"]
    assert obs["species"]["avis-prima"]["sites"] == ["gamma"]
    rep = bo.report(obs, SITES, itin)
    assert "| 3 (из них 1 проездом) |" in rep
    assert "[P1]" in rep.split("## Чеклисты проездом")[1].split("##")[0]


def test_hybrid_with_entry():
    """A hybrid with its own index entry (mappings/hybrids.json) is matched as written; other hybrids stay unmatched."""
    head = ["Submission ID", "Common Name", "Scientific Name", "Count", "Location ID", "Location", "Latitude", "Longitude",
            "Date", "Time", "Protocol"]
    def row(sid, sci):
        return dict(zip(head, [sid, "", sci, "1", "L100", "Hotspot Alpha", "4.0", "-74.0", "2026-10-02", "07:00 AM", "eBird - Stationary Count"]))
    index = [*INDEX, {"id": "avis-prima-x-secunda", "sci": "Avis prima x secunda", "source": "hybrid"}]
    rows = [row("H1", "Avis prima x secunda"), row("H1", "Avis prima x tertia"), row("H1", "Avis prima")]
    obs = bo.build(rows, {"Avis prima"}, index, SITES, ITIN, "2026-10-01", "2026-10-02")
    assert set(obs["species"]) == {"avis-prima", "avis-prima-x-secunda"}
    assert obs["species"]["avis-prima-x-secunda"]["lifer"] and not obs["species"]["avis-prima"]["lifer"]
    assert [u["sci"] for u in obs["unmatched"]] == ["Avis prima x tertia"]
    assert obs["checklists"][0]["n_species"] == 2  # the hybrid with an entry counts as a taxon of the checklist


def test_merge_trip_report():
    """Export rows win per Submission ID; trip-report rows add missing checklists; a re-submitted copy is skipped."""
    head = ["Submission ID", "Common Name", "Scientific Name", "Count", "Location ID", "Location", "Latitude", "Longitude",
            "Date", "Time", "Protocol", "Checklist Comments"]
    def row(sid, sci, count, loc_id, date, time, protocol="", comments=""):
        return dict(zip(head, [sid, "", sci, count, loc_id, "Hotspot Alpha", "4.0", "-74.0", date, time, protocol, comments]))
    export = [row("E1", "Avis prima", "2", "L100", "2026-10-02", "06:14 AM", "eBird - Traveling Count", "Из выгрузки"),
              row("E1", "Avis secunda", "1", "L100", "2026-10-02", "06:14 AM", "eBird - Traveling Count", "Из выгрузки"),
              row("E2", "Avis tertia", "1", "L100", "2026-10-03", "10:25 AM", "eBird - Stationary Count")]
    trip = [row("E1", "Avis prima", "5", "L100", "2026-10-02", "06:14 AM"),     # same id: the export's rows win
            row("E1", "Avis tertia", "1", "L100", "2026-10-02", "06:14 AM"),
            row("T1", "Avis tertia", "X", "L100", "2026-10-04", "07:00 AM"),    # only in the trip report: added
            row("T1", "Avis prima", "3", "L100", "2026-10-04", "07:00 AM"),
            row("T2", "Avis tertia", "1", "L100", "2026-10-03", "10:25 AM")]    # E2 under a new id: skipped
    rows, info = bo.merge_sources(export, trip)
    assert info == {"checklists": 3, "added": ["T1"], "duplicates": [{"id": "T2", "same_as": "E2"}]}
    assert [(r["Submission ID"], r["_source"]) for r in rows] == [("E1", "export"), ("E1", "export"), ("E2", "export"),
                                                                ("T1", "trip_report"), ("T1", "trip_report")]
    obs = bo.build(rows, {"Avis prima"}, INDEX, SITES, ITIN, "2026-10-01", "2026-10-03")
    cls = {c["id"]: c for c in obs["checklists"]}
    assert list(cls) == ["E1", "E2", "T1"]
    assert cls["E1"]["source"] == "export" and cls["E1"]["comments"] == "Из выгрузки" and cls["E1"]["n_species"] == 2
    assert cls["T1"]["source"] == "trip_report" and cls["T1"]["protocol"] == "unknown" and cls["T1"]["site"] == "alpha"
    sp = obs["species"]
    assert [o["count"] for o in sp["avis-prima"]["obs"]] == [2, 3]  # E1 keeps the export's count, not the report's 5
    assert sp["avis-tertia"]["first"] == "2026-10-03" and sp["avis-tertia"]["n_checklists"] == 2
    assert obs["stats"]["checklists"] == 3
    # only a trip report (no export yet): every checklist from it
    rows2, info2 = bo.merge_sources([], trip)
    assert info2["added"] == ["E1", "T1", "T2"] and {r["_source"] for r in rows2} == {"trip_report"}
    # report lines on the trip report's share
    obs["sources"] = {"export": {"exported": "2026-10-03", "checklists": 2},
                      "trip_report": {"ids": [579125], "fetched": "2026-10-18T18:00:00Z", **info}}
    rep = bo.report(obs, SITES, ITIN)
    assert "отчёт 579125, обновлён 2026-10-18T18:00:00Z): 3 чеклиста Ани, из них только в отчёте (нет в выгрузке) 1: T1" in rep
    assert "T2 = E2" in rep


def test_group_block():
    """Several reports: checklists summed, species the largest per report; reports without counts are skipped."""
    p = lambda uid, sp, cl: {"person_id": 0, "user_id": uid, "name": uid.lower(), "role": "editor", "species": sp,
                             "other_taxa": 0, "checklists": cl}
    state = {"fetched_at": "T", "user_id": "B", "reports": {
        "1": {"people": [p("A", 10, 3), p("B", 12, 4)], "group": {"species": 15, "other_taxa": 1, "checklists": 6}},
        "2": {"people": [p("B", 20, 2)], "group": {"species": 20, "other_taxa": 0, "checklists": 2}},
        "3": {"checklists": {}}}}
    g = bo.group_block(state)
    assert g["report_ids"] == [1, 2] and g["total"] == {"species": 20, "other_taxa": 1, "checklists": 8}
    assert [(e["name"], e["species"], e["checklists"], e.get("me")) for e in g["people"]] == [("b", 20, 6, True), ("a", 10, 3, None)]
    assert bo.group_block({"reports": {"1": {}}}) is None and bo.group_block(None) is None


def test_main_writes_sources_and_fetched():
    """main(): both CSVs merged, `fetched` from the trip-report state, `sources` block, per-checklist `source`."""
    saved = (bo.TRIP_CSV, bo.LIFE_JSON, bo.TRIP_REPORT_CSV, bo.TRIP_STATE, bo.OUT, bo.REPORT, bo.DATA)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "data").mkdir()
        (d / "data" / "itinerary.json").write_text(json.dumps(ITIN))
        (d / "data" / "sites.json").write_text(json.dumps(SITES))
        (d / "data" / "species_index.json").write_text(json.dumps(INDEX))
        bo.DATA, bo.OUT, bo.REPORT = d / "data", d / "data" / "observations.json", d / "data" / "report.md"
        bo.TRIP_CSV, bo.LIFE_JSON = d / "colombia_2026.csv", d / "life.json"
        bo.TRIP_REPORT_CSV, bo.TRIP_STATE = d / "trip_report.csv", d / "state.json"
        try:
            bo.import_export(FIX, "2026-10-02")
            header, rows = bo.read_csv(bo.TRIP_CSV.read_text())
            extra = {**rows[0], "Submission ID": "S9", "Date": "2026-10-04", "Time": "05:00 PM", "Protocol": ""}
            pre = {**rows[0], "Submission ID": "S0", "Date": "2026-09-30"}  # before the trip: ignored
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
            w.writeheader()
            w.writerows([rows[0], extra, pre])
            bo.TRIP_REPORT_CSV.write_text(buf.getvalue())
            people = [{"person_id": 1, "user_id": "USER1", "name": "Anna K", "role": "editor", "species": 437, "other_taxa": 1, "checklists": 58},
                      {"person_id": 2, "user_id": "USER2", "name": "Igor B", "role": "editor", "species": 337, "other_taxa": 0, "checklists": 49},
                      {"person_id": 3, "user_id": "USER3", "name": "Sergey V", "role": "owner", "species": 447, "other_taxa": 2, "checklists": 57}]
            bo.TRIP_STATE.write_text(json.dumps({"fetched_at": "2026-10-18T18:00:00Z", "user_id": "USER1", "reports": {
                "579125": {"person_id": 1, "people": people, "group": {"species": 519, "other_taxa": 6, "checklists": 92}}}}))
            sys.argv = ["build_observations.py"]
            bo.main()
            text = bo.OUT.read_text()
            obs = json.loads(text)
            g = obs["group"]
            assert g["fetched"] == "2026-10-18T18:00:00Z" and g["report_ids"] == [579125]
            assert g["total"] == {"species": 519, "other_taxa": 6, "checklists": 92}
            assert g["people"] == [  # by species desc; `me` only on the configured user; no ids
                {"name": "Sergey V", "role": "owner", "species": 447, "other_taxa": 2, "checklists": 57},
                {"name": "Anna K", "role": "editor", "species": 437, "other_taxa": 1, "checklists": 58, "me": True},
                {"name": "Igor B", "role": "editor", "species": 337, "other_taxa": 0, "checklists": 49}]
            assert "USER" not in text and "person_id" not in text
            md = bo.REPORT.read_text()
            assert "| Anna K (Аня) | 437 | 1 | 58 |" in md and "| **вся группа** | 519 | 6 | 92 |" in md and "USER" not in md
            assert obs["fetched"] == "2026-10-18T18:00:00Z" and obs["exported"] == "2026-10-04"
            tr = obs["sources"]["trip_report"]
            assert tr["ids"] == [579125] and tr["added"] == ["S9"] and tr["checklists"] == 2
            assert obs["sources"]["export"] == {"exported": "2026-10-04", "checklists": 4}
            src = {c["id"]: c["source"] for c in obs["checklists"]}
            assert src.pop("S9") == "trip_report" and set(src.values()) == {"export"}
            assert "S0" not in src
            # without the trip-report files: as before, fetched null
            bo.TRIP_REPORT_CSV.unlink()
            bo.main()
            obs = json.loads(bo.OUT.read_text())
            assert obs["fetched"] is None and obs["sources"]["trip_report"] is None and obs["group"] is None
            assert {c["source"] for c in obs["checklists"]} == {"export"}
        finally:
            bo.TRIP_CSV, bo.LIFE_JSON, bo.TRIP_REPORT_CSV, bo.TRIP_STATE, bo.OUT, bo.REPORT, bo.DATA = saved


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print(f"ok {name}")
    print(f"{n} tests passed")
