"""Tests for steps/build_observations.py on an invented export (tests/fixtures/observations/MyEBirdData.csv).

Run: `cd pipeline && uv run python tests/test_build_observations.py` (plain asserts, no pytest needed).
"""
from __future__ import annotations

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
    assert st["by_day"]["2026-10-03"] == {"species": 2, "new": 1, "lifers": 2, "checklists": 2, "observations": 3}
    assert st["by_site"]["alpha"] == {"species": 3, "new": 3, "lifers": 1, "checklists": 2, "observations": 3,
                                      "passing_checklists": 1}
    assert st["off_site"] == {"species": 1, "new": 0, "lifers": 1, "checklists": 1, "observations": 1}


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


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print(f"ok {name}")
    print(f"{n} tests passed")
