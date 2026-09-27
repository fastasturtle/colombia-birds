"""Endemic and near-endemic birds of Colombia (Chaparro-Herrera, Lozano & Echeverry-Galvis 2024).

Downloads Anexo 3 of the paper (XLSX on the journal site, CC BY-NC 4.0): one row per species with the
2013 and 2023 categories E (endemic), CE / CEa (near-endemic; CEa = marine/insular), EI (species of
interest) and II (insufficient information). Anexos 1-2 (elevation bands, regions, country codes) are
fetched too so the codes in `countries` / `bands` can be decoded later.

Annex names are matched to the ACO list by normalised scientific name (ACO name, then the
eBird/Clements name it maps to), then via pipeline/mappings/endemics_names.json (annex name ->
ACO or eBird name, hand-checked). Writes data/sources/endemics.json (keyed by normalised annex name,
`aco_key` = the matched ACO key) and data/sources/endemics_unmatched.json. build_species.py reads it.
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PIPELINE, SOURCES, get, log, norm_sci, read_json, write_json  # noqa: E402

BASE = "https://revistas.ornitologiacolombiana.com/index.php/roc/article/download/580"
ANNEX_SPECIES = f"{BASE}/496"  # Anexo 3: species list with categories 2013 / 2023
ANNEX_OTHER = {"anexo_1_bands_regions": f"{BASE}/493", "anexo_2_countries": f"{BASE}/494"}
CITATION = (
    "Chaparro-Herrera, S., Lozano, A. & Echeverry-Galvis, M. A. (2024). Aves endémicas y casi-endémicas "
    "de Colombia: actualización. Ornitología Colombiana 25: 34-45. https://doi.org/10.59517/oc.e580"
)
SOURCE = "Chaparro-Herrera et al. 2024, Anexo 3"
CATEGORIES = {"E": "endemic", "CE": "near_endemic", "CEa": "near_endemic", "EI": "of_interest", "II": "insufficient_info"}


def load_rows(url: str) -> list[tuple]:
    data = get(url, kind="endemics", binary=True, min_interval=1.0)
    if not data[:2] == b"PK":  # an HTML wrapper instead of the file
        raise RuntimeError(f"{url} did not return an XLSX (got {data[:60]!r})")
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    return list(wb.worksheets[0].iter_rows(values_only=True))


def code_of(raw: str | None) -> tuple[str | None, bool]:
    """'E, extinta' -> ('E', True); 'CE ' -> ('CE', False); 'NC (...)' -> ('NC', False)."""
    if not raw:
        return None, False
    s = str(raw).strip()
    return s.split(",")[0].split("(")[0].strip(), "extint" in s.lower()


def split_codes(s: str | None) -> list[str]:
    return [c.strip() for c in re.split(r"[,;]", str(s or "")) if c.strip()]


def main() -> None:
    for url in ANNEX_OTHER.values():  # sanity: the whole annex set is reachable (cached for later use)
        load_rows(url)
    rows = load_rows(ANNEX_SPECIES)
    header = next(i for i, r in enumerate(rows) if r and str(r[0] or "").startswith("Nombre científico"))

    aco = read_json(SOURCES / "aco.json")["species"]
    nm = read_json(SOURCES / "ebird_name_map.json")
    to_ebird = {k: k for k in aco} | {k: norm_sci(v) for k, v in {**nm["auto_by_english_name"], **nm["manual"]}.items()}
    lookup: dict[str, str] = {}
    for k, e in to_ebird.items():
        lookup.setdefault(k, k)
        lookup.setdefault(e, k)
    manual = {norm_sci(k): norm_sci(v) for k, v in (read_json(PIPELINE / "mappings" / "endemics_names.json") or {}).items()
              if not k.startswith("_")}

    species: dict[str, dict] = {}
    unmatched: dict[str, dict] = {}
    for r in rows[header + 1:]:
        if not r or not r[0]:
            continue
        name = str(r[0]).strip()
        added = name.endswith("*")
        name = name.rstrip("*").strip()
        key = norm_sci(name)
        code, extinct = code_of(r[2])
        code_2013, _ = code_of(r[1])
        if code not in CATEGORIES:
            raise RuntimeError(f"unknown 2023 category {r[2]!r} for {name}")
        aco_key = lookup.get(key)
        how = "sci_name" if aco_key else None
        if not aco_key and key in manual:
            aco_key, how = lookup.get(manual[key]), "manual"
        rec = {
            "sci_name": name,
            "category": CATEGORIES[code],
            "code": code,
            "code_2013": code_2013,
            "category_2013_raw": str(r[1]).strip() if r[1] else None,
            "extinct": extinct,
            "added_2023": added,
            "countries": split_codes(r[3]),
            "bands": split_codes(r[4]),
            "aco_key": aco_key,
            "match": how,
            "source": SOURCE,
        }
        species[key] = rec
        if not aco_key:
            unmatched[key] = {"sci_name": name, "category": rec["category"], "code": code}

    counts = Counter(v["category"] for v in species.values())
    write_json(SOURCES / "endemics.json", {
        "citation": CITATION,
        "license": "CC BY-NC 4.0",
        "source_url": ANNEX_SPECIES,
        "count": len(species),
        "counts": dict(counts),
        "species": species,
    })
    write_json(SOURCES / "endemics_unmatched.json", unmatched)
    log(f"endemics: {len(species)} taxa in Anexo 3: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    log(f"  matched {len(species) - len(unmatched)} (manual {sum(1 for v in species.values() if v['match'] == 'manual')}), "
        f"unmatched {len(unmatched)}: {', '.join(v['sci_name'] for v in unmatched.values()) or '-'}")


if __name__ == "__main__":
    main()
