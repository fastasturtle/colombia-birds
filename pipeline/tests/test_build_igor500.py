"""Tests for steps/build_igor500.py with a fake trip-report fetcher and small invented species (no real data).

Run: `cd pipeline && uv run pytest tests/test_build_igor500.py` (or `uv run python tests/test_build_igor500.py`).
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "steps"))
sys.path.insert(0, str(HERE.parent))
import build_igor500 as b  # noqa: E402
import fetch_ebird_trip as ft  # noqa: E402

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
CFG = {"report": 1, "person": "Zed", "person_ru": "Зед", "goal": 10, "sites": ["alpha", "beta", "gamma"],
       "reserve": ["gamma"]}
# invented species: a..h
INDEX = [{"id": f"fakus-{x}", "sci": f"Fakus {x}", "en": f"Fake {x.upper()}", "ru": f"Фейк {x}" if x != "h" else None,
          "family": "fake1"} for x in "abcdefgh"]


def taxon(x: str, cat: str = "species") -> dict:
    return {"speciesCode": f"fak{x}", "category": cat, "sciName": f"Fakus {x}", "commonName": f"Fake {x.upper()}",
            "numIndividuals": 1, "numChecklists": 1}


PERSON_TAXA = [taxon("a"), taxon("b"), {**taxon("x", "spuh"), "sciName": "Fakus sp."}]
GROUP_TAXA = PERSON_TAXA + [taxon("c"), taxon("d"), taxon("g"), {**taxon("z"), "sciName": "Nonesuch zed"}]
CHECKLISTS = [{"subId": "S1", "numSpecies": 2, "isoObsDate": "2026-10-19 07:05", "loc": {"locId": "L1", "name": "Secret"}},
              {"subId": "S2", "numSpecies": 1, "isoObsDate": "2026-10-20 16:40", "loc": {"locId": "L2", "name": "Hidden"}}]
PEOPLE = [{"tripReportPersonId": 11, "userDisplayName": "Ann Other"}, {"tripReportPersonId": 22, "userDisplayName": "Zed Fake"}]


def row(x: str, n_aut: int, n: int = 100) -> dict:
    return {"id": f"fakus-{x}", "n_aut": n_aut, "n": n, "freq_aut": 0.01, "state": "maybe"}


SITE_SPECIES = {
    "alpha": {"species": [row("a", 50), row("c", 25), row("d", 7), row("e", 2), row("f", 0), row("h", 20)]},
    "beta": {"species": [row("c", 3), row("e", 30), row("g", 4)]},
    "gamma": {"species": [row("d", 40), row("g", 90), row("b", 10)]},
    "other": {"species": [row("e", 500)]},
}


class FakeFetcher(ft.Fetcher):
    def __init__(self, fail: bool = False):
        super().__init__(client=object(), min_interval=0)
        self.fail = fail
        self.calls = []

    def trip(self, path, params=None):
        self.requests += 1
        self.calls.append((path, params))
        if self.fail:
            raise ft.FetchError(f"{path}: ConnectError")
        pid = (params or {}).get("tripReportPersonId")
        if path == "people/1":
            return PEOPLE
        if path == "taxon-list/1":
            assert pid in (None, 22)
            return PERSON_TAXA if pid else GROUP_TAXA
        if path == "checklists/1":
            assert pid == 22
            return CHECKLISTS
        raise KeyError(path)


def compute():
    person, mine, group, cl = b.fetch(FakeFetcher(), CFG)
    return b.compute(CFG, person, mine, group, cl, INDEX, SITE_SPECIES)


def test_counts_and_as_of():
    out, unmatched = compute()
    assert out["person"] == "Zed Fake" and out["person_ru"] == "Зед"
    assert out["species"] == 2 and out["checklists"] == 2 and out["as_of"] == "2026-10-20 16:40"
    assert out["group_species"] == 6 and out["missed_in_group"] == 4 and out["goal"] == 10
    assert unmatched == ["Nonesuch zed"]


def test_tiers_and_group_flag():
    out, _ = compute()
    alpha = out["sites"]["alpha"]
    assert [c["id"] for c in alpha] == ["fakus-c", "fakus-h", "fakus-d", "fakus-e"]  # no a (has it), no f (n_aut 0)
    assert [c["tier"] for c in alpha] == ["sure", "sure", "likely", "chance"]
    assert [c["group"] for c in alpha] == [True, False, True, False]
    assert alpha[0] == {"id": "fakus-c", "sci": "Fakus c", "en": "Fake C", "ru": "Фейк c", "family": "fake1",
                        "n_aut": 25, "n": 100, "tier": "sure", "group": True}
    assert alpha[1]["ru"] is None
    assert [c["id"] for c in out["sites"]["gamma"]] == ["fakus-g", "fakus-d"]  # b is the person's
    assert set(out["sites"]) == {"alpha", "beta", "gamma"}
    # totals skip the reserve site gamma: sure c, h, e (beta); likely d only (sure nowhere)
    assert out["sure_total"] == 3 and out["likely_total"] == 1


def test_reachable_missed():
    out, _ = compute()
    rm = out["reachable_missed"]
    # group-only species c, d, g (e, h are not in the group's list); n_aut >= 3, the reserve gamma not counted
    assert [m["id"] for m in rm] == ["fakus-c", "fakus-d", "fakus-g"]
    assert rm[0] == {"id": "fakus-c", "sci": "Fakus c", "en": "Fake C", "ru": "Фейк c", "sites": {"alpha": 25, "beta": 3}}
    assert rm[1]["sites"] == {"alpha": 7} and rm[2]["sites"] == {"beta": 4}


def test_requests():
    f = FakeFetcher()
    b.fetch(f, CFG)
    assert f.calls == [("people/1", None), ("taxon-list/1", {"tripReportPersonId": 22}), ("taxon-list/1", None),
                       ("checklists/1", {"tripReportPersonId": 22})]


def test_person_must_match_once():
    for people in ([], PEOPLE + [{"tripReportPersonId": 33, "userDisplayName": "Zed Two"}]):
        try:
            b.find_person(people, "zed")
        except LookupError:
            continue
        raise AssertionError("must raise")


def _run(tmp: Path, f=None, now=NOW):
    return b.run(f or FakeFetcher(), now, tmp / "igor500.json", CFG, INDEX, SITE_SPECIES)


def test_privacy_and_determinism():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        s = _run(tmp)
        assert s["wrote"]
        text = (tmp / "igor500.json").read_text()
        out = json.loads(text)
        assert set(out) == b.KEYS
        assert out["fetched"] == "2026-10-21T12:00:00Z"
        cand_keys = {"id", "sci", "en", "ru", "family", "n_aut", "n", "tier", "group"}
        assert all(set(c) == cand_keys for rows in out["sites"].values() for c in rows)
        assert all(set(m) == {"id", "sci", "en", "ru", "sites"} for m in out["reachable_missed"])
        for secret in ("S1", "S2", "L1", "Secret", "Hidden", "Ann Other", "fakx", "Fakus sp.", "Fakus a", "Fakus b"):
            assert secret not in text, secret
        assert [p.name for p in tmp.iterdir()] == ["igor500.json"]  # nothing else written
        # same report later: file untouched, byte for byte (fetched kept)
        s2 = _run(tmp, now=datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc))
        assert not s2["wrote"] and (tmp / "igor500.json").read_text() == text


def test_network_failure_leaves_file():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "igor500.json").write_text("old\n")
        try:
            _run(tmp, FakeFetcher(fail=True))
        except ft.FetchError:
            pass
        else:
            raise AssertionError("must raise")
        assert (tmp / "igor500.json").read_text() == "old\n"


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print(f"ok {name}")
    print(f"{n} tests passed")
