"""eBird/Clements taxonomy with common names in ru/en/es_CO -> data/sources/ebird.json

Uses the public eBird API v2 taxonomy endpoint (no key needed). Terms: non-commercial, credit Cornell Lab,
link back to eBird. We store only names/codes for species on the Colombian list, not eBird observation data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import SOURCES, checklist, get_json, log, norm_sci, read_json, write_json  # noqa: E402

URL = "https://api.ebird.org/v2/ref/taxonomy/ebird"
LOCALES = {"ru": "ru", "en": "en", "es": "es_CO"}
CITATION = (
    "Clements, J. F., et al. 2025. The eBird/Clements checklist of Birds of the World: v2025. "
    "Cornell Lab of Ornithology. https://www.birds.cornell.edu/clementschecklist/ ; names via eBird API v2."
)


def main() -> None:
    aco = checklist()  # ACO 2022 + clements2025 additions
    wanted = set(aco)
    manual = read_json(Path(__file__).resolve().parents[1] / "mappings" / "aco_to_ebird.json", {})
    # manual: {aco_norm_sci: ebird_sci_name}
    wanted |= {norm_sci(v) for v in manual.values()}

    by_sci: dict[str, dict] = {}
    for lang, loc in LOCALES.items():
        rows = get_json(URL, {"fmt": "json", "cat": "species", "locale": loc}, kind="ebird", min_interval=1.0)
        log(f"eBird {loc}: {len(rows)} species")
        for r in rows:
            key = norm_sci(r["sciName"])
            rec = by_sci.setdefault(
                key,
                {
                    "sci_name": r["sciName"],
                    "code": r["speciesCode"],
                    "taxon_order": r["taxonOrder"],
                    "order": r.get("order"),
                    "family_code": r.get("familyCode"),
                    "family_sci": r.get("familySciName"),
                    "family_en": r.get("familyComName"),
                    "names": {},
                },
            )
            name = r.get("comName", "")
            # eBird falls back to English when no localized name exists
            if lang == "ru" and not any("Ѐ" <= ch <= "ӿ" for ch in name):
                name = ""
            rec["names"][lang] = name

    # Family names in ru/es come from the localized family fields when available
    species = {k: v for k, v in by_sci.items() if k in wanted}
    families: dict[str, dict] = {}
    for lang, loc in LOCALES.items():
        rows = get_json(URL, {"fmt": "json", "cat": "species", "locale": loc}, kind="ebird", min_interval=1.0)
        for r in rows:
            fc = r.get("familyCode")
            if not fc:
                continue
            fam = families.setdefault(fc, {"sci": r.get("familySciName"), "order": r.get("order"), "names": {}})
            fam["names"].setdefault(lang, r.get("familyComName"))

    # Fallback: match by English name (ACO uses SACC genera; Clements may differ)
    by_en = {}
    for k, v in by_sci.items():
        en = (v["names"].get("en") or "").lower().replace("-", " ").replace("'", "")
        by_en.setdefault(en, k)
    auto_map = {}
    for k, rec in aco.items():
        if k in species or k in manual:
            continue
        en = rec["name_en_aco"].lower().replace("-", " ").replace("'", "")
        if en in by_en:
            auto_map[k] = by_sci[by_en[en]]["sci_name"]
            species[by_en[en]] = by_sci[by_en[en]]
    for k, v in manual.items():
        if norm_sci(v) in by_sci:
            species[norm_sci(v)] = by_sci[norm_sci(v)]
    missing = sorted(k for k in aco if k not in species and k not in manual and k not in auto_map)
    write_json(SOURCES / "ebird_name_map.json", {"auto_by_english_name": auto_map, "manual": manual})
    write_json(
        SOURCES / "ebird.json",
        {"citation": CITATION, "count": len(species), "species": species, "families": families},
    )
    log(f"eBird: matched {len(species)} of {len(aco)} ACO species; {len(missing)} unmatched by name")
    write_json(SOURCES / "ebird_unmatched.json", missing)


if __name__ == "__main__":
    main()
