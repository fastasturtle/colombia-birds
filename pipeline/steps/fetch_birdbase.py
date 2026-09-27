"""BIRDBASE v2025.1 (Şekercioğlu et al. 2025, CC BY 4.0) -> data/sources/birdbase.json

Traits kept: elevation (min/max, normal and extreme), primary habitat, habitat flags, primary diet, body mass,
mobility (migration/altitudinal), IUCN 2024, and keys to IOC/Clements/BirdLife/AviList taxonomies.
Source: https://doi.org/10.6084/m9.figshare.27051040
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import SOURCES, checklist, get, log, norm_sci, read_json, write_json  # noqa: E402

FILE_URL = "https://ndownloader.figshare.com/files/55634729"
CITATION = (
    "Şekercioğlu, Ç. H., et al. 2025. BIRDBASE: A Global Database of Avian Biogeography, Conservation, "
    "Ecology and Life History Traits. Scientific Data. v2025.1, CC BY 4.0. "
    "https://doi.org/10.6084/m9.figshare.27051040"
)

HABITAT_CODES = {
    "F": "forest", "BM": "bamboo", "WD": "woodland", "SH": "shrubland", "SV": "savanna", "G": "grassland",
    "PL": "plantation", "R": "riparian", "D": "desert", "A": "agricultural", "RV": "rivers_lakes",
    "C": "coastal", "W": "wetland", "SE": "sea", "O": "other",
}


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def main() -> None:
    aco = checklist()  # ACO 2022 + clements2025 additions
    ebird = read_json(SOURCES / "ebird.json")["species"]
    name_map = read_json(SOURCES / "ebird_name_map.json")
    wanted: dict[str, str] = {}  # any normalized name -> aco key
    for k in aco:
        wanted[k] = k
    for k, v in {**name_map["auto_by_english_name"], **name_map["manual"]}.items():
        wanted[norm_sci(v)] = k

    raw = get(FILE_URL, kind="birdbase", binary=True)
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Data", header=[0, 1])
    df.columns = [b for a, b in df.columns]
    log(f"BIRDBASE: {len(df)} rows")

    tax_cols = [
        "Latin (BirdLife > IOC > Clements>AviList)",
        "HBW/BirdLife International (v9.1)",
        "IOC World Bird List (v15.1)",
        "eBird/Clements (V2024b)",
        "AviList v1 2025",
    ]
    # A row matched by the eBird name of a remapped ACO taxon (aco_to_ebird.json, e.g. Numenius hudsonicus for
    # ACO N. phaeopus) beats a row matched by the ACO name, which after a split is the other half.
    ebird_names = {norm_sci(v): k for k, v in {**name_map["auto_by_english_name"], **name_map["manual"]}.items()}
    out: dict[str, dict] = {}
    by_ebird: set[str] = set()
    for _, r in df.iterrows():
        keys = {norm_sci(str(r[c])) for c in tax_cols if isinstance(r[c], str)}
        hit = next((wanted[k] for k in keys if k in wanted), None)
        via_ebird = any(ebird_names.get(k) == hit for k in keys)
        if hit is None or (hit in out and (hit in by_ebird or not via_ebird)):
            continue
        if via_ebird:
            by_ebird.add(hit)
        habitats = [name for code, name in HABITAT_CODES.items() if clean(r.get(code)) not in (None, 0)]
        out[hit] = {
            "birdbase_id": clean(r["IOC 15.1"]),
            "name_en": r["English Name (BirdLife > IOC > Clements>AviList)"],
            "sci_ioc": clean(r["IOC World Bird List (v15.1)"]),
            "sci_clements": clean(r["eBird/Clements (V2024b)"]),
            "sci_birdlife": clean(r["HBW/BirdLife International (v9.1)"]),
            "sci_avilist": clean(r["AviList v1 2025"]),
            "iucn_2024": clean(r["2024 IUCN Red List category"]),
            "range_restricted": clean(r["RR"]),
            "elevation": {
                "min_extreme": clean(r["Xmin"]),
                "min": clean(r["NormMin"]),
                "max": clean(r["NormMax"]),
                "max_extreme": clean(r["Xmax"]),
            },
            "mass_g": clean(r["Average Mass"]),
            "primary_habitat": clean(r["Primary Habitat"]),
            "habitat_breadth": clean(r["HB"]),
            "habitats": habitats,
            "primary_diet": clean(r["Primary Diet"]),
            "diet_desc": clean(r["Desc"]),
            "mobility": {
                "migratory": clean(r["Mig"]),
                "altitudinal": clean(r["Alt"]),
                "irregular": clean(r["Irreg"]),
                "dispersive": clean(r["Disp"]),
                "sedentary": clean(r["Sed"]),
            },
        }
    write_json(SOURCES / "birdbase.json", {"citation": CITATION, "count": len(out), "species": out})
    missing = sorted(k for k in aco if k not in out)
    write_json(SOURCES / "birdbase_unmatched.json", missing)
    log(f"BIRDBASE: matched {len(out)} of {len(aco)}; unmatched {len(missing)}")


if __name__ == "__main__":
    main()
