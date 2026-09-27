"""Tests for steps/build_lynx.py on small fixtures (tests/fixtures/lynx/).

Run: `cd pipeline && uv run python tests/test_build_lynx.py` (plain asserts, no pytest needed;
the test_* functions also work under pytest if it is ever added).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "steps"))
sys.path.insert(0, str(HERE.parent))
import build_lynx as bl  # noqa: E402

FIX = HERE / "fixtures" / "lynx"


def _entries():
    files = sorted((FIX / "index").glob("*.txt"))
    return bl.parse_index_files(files)


def _by_text(entries):
    return {e["text"].strip(): e for e in entries}


def test_parse_pages():
    assert bl.parse_pages("366, 379–391") == [[366, 366], [379, 391]]
    assert bl.parse_pages("19-20") == [[19, 20]]
    assert bl.parse_pages("379–91") == [[379, 391]]
    assert bl.parse_pages("8??, 12") == [[12, 12]]


def test_index_kinds():
    entries, notes = _entries()
    t = _by_text(entries)
    e = t["analis, Formicarius (analis) 304"]
    assert (e["kind"], e["genus"], e["epithet"], e["subspecies"], e["first_page"], e["page_in_index"]) == \
        ("sci", "Formicarius", "analis", "analis", 304, 560)
    assert t["angustifrons, Psarocolius 472"]["subspecies"] is None
    assert t["Anas 44"]["kind"] == "genus" and t["Anas 44"]["genus"] == "Anas"
    assert t["ANATIDAE 39"]["kind"] == "family" and t["ANATIDAE 39"]["family"] == "Anatidae"
    a = t["**Anhinga** 149"]
    assert (a["kind"], a["name"], a["group"], a["first_page"]) == ("en", "Anhinga", "Anhinga", 149)
    assert t["**Ani**"]["kind"] == "en_group" and t["**Ani**"]["group"] == "Ani"
    g = t["Greater 115"]
    assert (g["kind"], g["group"], g["qualifier"], g["name"]) == ("en", "Ani", "Greater", "Greater Ani")
    assert t["Crested 501"]["name"] == "Crested Ant-tanager"
    r = t["**Antpipit**, Ringed 365"]
    assert (r["kind"], r["group"], r["qualifier"], r["name"], r["first_page"]) == ("en", "Antpipit", "Ringed", "Ringed Antpipit", 365)
    assert t["Grey 276"]["group"] == "Antbird"  # heading after the inline form
    assert t["tyrannulus, Examplus 366, 379–391"]["pages"] == [[366, 366], [379, 391]]
    u = t["ruficeps, Chalcostigma 8??"]
    assert u["uncertain"] and u["pages"] == [] and u["first_page"] is None
    # notes are kept apart, never parsed as entries
    assert "Ignored 999" not in t and notes[560] == ["Ignored 999", "ignored, Line 1"]


def test_group_carries_across_pages():
    entries, _ = _entries()
    t = _by_text(entries)
    z = t["Zimmer's 277"]  # first line of p561 continues **Antbird** from p560
    assert z["name"] == "Zimmer's Antbird" and not z.get("group_uncertain")
    # a heading with its own page is also the group of the indented lines after it
    assert t["Black-capped 425"]["name"] == "Black-capped Donacobius"
    # p562 missing: the carried heading is flagged
    o = t["Orphan-ish 12"]
    assert o["group"] == "Donacobius" and o["group_uncertain"]


def test_references_and_families():
    refs = bl.parse_references(FIX / "references.txt")
    assert [r["page"] for r in refs] == [555, 556] and refs[1]["text"].startswith("Hilty")
    fams = bl.parse_families(FIX / "family_index.txt")
    assert fams == [{"name": "Ducks, Geese and Swans", "page": 39},
                    {"name": "Woodcreepers", "page": 308, "pages": [308, 319]}]
    frag = bl.parse_families(FIX / "p604_fragment.txt", fragment=True)
    assert frag == [{"name": "...rannulets", "page": 366, "pages": [366, 391], "fragment": True},
                    {"name": "...owlegs", "page": 163, "fragment": True}]


def test_norm_en():
    assert bl.norm_en("Grey Antbird") == bl.norm_en("Gray Antbird")
    assert bl.norm_en("Crested Ant-tanager") == bl.norm_en("Crested Ant-Tanager")
    assert bl.norm_en("Klages's Antbird") == bl.norm_en("Klages’s Antbird") == bl.norm_en("Klagess antbird")
    assert bl.norm_en("Araçari") == bl.norm_en("Aracari")


def test_match():
    entries, _ = _entries()
    species = [
        {"id": "formicarius-analis", "sci": "Formicarius analis", "en": "Black-faced Antthrush", "family": "formic1"},
        {"id": "anhinga-anhinga", "sci": "Anhinga anhinga", "en": "Anhinga", "family": "anhing1"},
        {"id": "driophlox-cristata", "sci": "Driophlox cristata", "en": "Crested Ant-Tanager", "family": "cardin1"},
        {"id": "myrmoborus-grey", "sci": "Cercomacra cinerascens", "en": "Gray Antbird", "family": "thamno1"},
        {"id": "antiurus-maculicaudus", "sci": "Antiurus maculicaudus", "en": "Spot-tailed Nightjar", "family": "caprim1"},
        {"id": "hydropsalis-cayennensis", "sci": "Hydropsalis cayennensis", "en": "White-tailed Nightjar", "family": "caprim1"},
        {"id": "coccyzus-erythropthalmus", "sci": "Coccyzus erythrophthalmus", "en": "Black-billed Cuckoo", "family": "cuculi1"},
        {"id": "psarocolius-angustifrons", "sci": "Psarocolius angustifrons", "en": "Russet-backed Oropendola", "family": "icteri1"},
        {"id": "nowhere-bird", "sci": "Nowhere bird", "en": "Nowhere Bird", "family": "x"},
        {"id": "mapped-bird", "sci": "Mapped bird", "en": "Mapped Bird", "family": "x"},
    ]
    pages, extra = bl.match_species(species, entries, {"Mapped bird": "Ringed Antpipit"})
    assert pages["formicarius-analis"]["page"] == 304 and pages["formicarius-analis"]["sci"]["via"] == "exact"
    a = pages["anhinga-anhinga"]
    assert a["sci"]["page"] == 149 and a["en"]["page"] == 149 and not a["conflict"]
    d = pages["driophlox-cristata"]
    assert d["sci"]["page"] is None and d["en"]["page"] == 501 and d["page"] == 501
    assert pages["myrmoborus-grey"]["en"]["page"] == 276  # Grey vs Gray
    # genus move: Hydropsalis maculicaudus -> Antiurus (Hydropsalis is in the same family on the site)
    m = pages["antiurus-maculicaudus"]
    assert m["sci"]["via"] == "epithet" and m["page"] == 65
    # spelling differences are not fuzzy-matched, only suggested
    assert pages["coccyzus-erythropthalmus"]["page"] is None
    assert extra["near"]["coccyzus-erythropthalmus"] == ["Coccyzus erythropthalmus (120)"]
    # the species-level line wins over the subspecies-group line
    assert pages["psarocolius-angustifrons"]["sci"]["entry"] == "angustifrons, Psarocolius 472"
    assert pages["nowhere-bird"]["page"] is None and not pages["nowhere-bird"]["conflict"]
    assert pages["mapped-bird"]["sci"] == {"page": 365, "entry": "**Antpipit**, Ringed 365", "via": "mapping"}


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print(f"ok {name}")
    print(f"{n} tests passed")
