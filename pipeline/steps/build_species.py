"""Merge data/sources/*.json into data/species/<slug>.json, data/species_index.json, data/families.json.

Canonical taxonomy is eBird/Clements (matches Merlin and eBird in the field). The ACO checklist is the
canonical *list* of what occurs in Colombia and carries the status flags. Hand-written content lives in
content/species/<slug>.md and is merged at site build time, never here.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, SOURCES, SPECIES_DIR, log, norm_sci, read_json, slugify, write_json  # noqa: E402

REGION_ORDER = ["Tinamiformes"]  # unused placeholder to keep import tidy


def wiki_url(lang: str, title: str | None) -> str | None:
    if not title:
        return None
    return f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"


def main() -> None:
    aco = read_json(SOURCES / "aco.json")["species"]
    ebird = read_json(SOURCES / "ebird.json")
    ebird_sp, ebird_fam = ebird["species"], ebird["families"]
    name_map = read_json(SOURCES / "ebird_name_map.json")
    birdbase = read_json(SOURCES / "birdbase.json")["species"]
    wikidata = read_json(SOURCES / "wikidata.json")["species"]
    aco_to_ebird = {k: k for k in aco}
    for k, v in {**name_map["auto_by_english_name"], **name_map["manual"]}.items():
        aco_to_ebird[k] = norm_sci(v)

    if SPECIES_DIR.exists():
        shutil.rmtree(SPECIES_DIR)
    SPECIES_DIR.mkdir(parents=True)

    index = []
    families: dict[str, dict] = {}
    slugs: dict[str, str] = {}
    for key, a in sorted(aco.items(), key=lambda kv: ebird_sp.get(aco_to_ebird[kv[0]], {}).get("taxon_order", 1e9)):
        e = ebird_sp[aco_to_ebird[key]]
        b = birdbase.get(key, {})
        w = wikidata.get(key, {})
        sci = e["sci_name"]
        slug = slugify(sci)
        if slug in slugs:  # two ACO taxa lumped into one Clements species
            slug = slugify(a["sci_name"])
        slugs[slug] = key

        name_ru = e["names"].get("ru") or None
        name_ru_source = "ebird" if name_ru else None
        if not name_ru and w.get("labels", {}).get("ru"):
            name_ru, name_ru_source = w["labels"]["ru"], "wikidata"

        fam_code = e["family_code"]
        fam = ebird_fam.get(fam_code, {})
        families.setdefault(
            fam_code,
            {
                "code": fam_code,
                "sci": fam.get("sci") or a["family"],
                "order": fam.get("order") or a["order"],
                "names": fam.get("names", {}),
                "species_count": 0,
                "slug": slugify(fam.get("sci") or a["family"]),
            },
        )["species_count"] += 1

        taxonomy_note = None
        if norm_sci(sci) != key:
            taxonomy_note = f"ACO/SACC lists this as {a['sci_name']}; eBird/Clements uses {sci}."

        rec = {
            "id": slug,
            "sci_name": sci,
            "sci_name_aco": a["sci_name"],
            "authorship": a["authorship"],
            "taxonomy_note": taxonomy_note,
            "names": {
                "en": e["names"].get("en") or a["name_en_aco"],
                "ru": name_ru,
                "es": e["names"].get("es") or None,
                "en_aco": a["name_en_aco"],
            },
            "name_ru_source": name_ru_source,
            "ebird_code": e["code"],
            "taxon_order": e["taxon_order"],
            "order": e.get("order") or a["order"],
            "family": {"code": fam_code, "sci": fam.get("sci") or a["family"], "en": fam.get("names", {}).get("en")},
            "genus": sci.split()[0],
            "colombia": {
                "status": a["status"]["codes"],
                "status_uncertain": a["status"]["uncertain"],
                "status_raw": a["status"]["raw"],
                "endemic": a["endemic"],
                "introduced": a["introduced"],
                "migration_note": a["migration_note"],
                "libro_rojo": a["libro_rojo"],
                "habitat_aco": a["habitat_aco"],
            },
            "iucn": {"aco_2022": a["iucn"], "birdbase_2024": b.get("iucn_2024"), "wikidata": w.get("iucn_status")},
            "traits": {
                "elevation_m": b.get("elevation"),
                "mass_g": b.get("mass_g"),
                "primary_habitat": b.get("primary_habitat"),
                "habitats": b.get("habitats", []),
                "habitat_breadth": b.get("habitat_breadth"),
                "primary_diet": b.get("primary_diet"),
                "diet_desc": b.get("diet_desc"),
                "mobility": b.get("mobility"),
                "range_restricted": b.get("range_restricted"),
            },
            "ids": {
                "wikidata": w.get("qid"),
                "gbif": a.get("gbif_key") or w.get("gbif_key"),
                "avibase": w.get("avibase_id"),
                "inaturalist": w.get("inaturalist_id"),
                "iucn": w.get("iucn_id"),
                "xeno_canto": w.get("xeno_canto"),
                "birdbase": b.get("birdbase_id"),
            },
            "links": {
                "ebird": f"https://ebird.org/species/{e['code']}",
                "wikipedia": {lang: wiki_url(lang, w.get("wikipedia", {}).get(lang)) for lang in ("en", "es", "ru")},
                "commons_category": (
                    f"https://commons.wikimedia.org/wiki/Category:{w['commons_category'].replace(' ', '_')}"
                    if w.get("commons_category") else None
                ),
                "xeno_canto": f"https://xeno-canto.org/explore?query={sci.replace(' ', '+')}",
                "inaturalist": f"https://www.inaturalist.org/taxa/{w['inaturalist_id']}" if w.get("inaturalist_id") else None,
            },
            "wikidata_images": w.get("images", []),
            # Filled by later pipeline steps
            "photos": [],
            "texts": {},
            "sounds": [],
            # Filled by agents (content/species/<slug>.md) — kept null here on purpose
            "difficulty": None,
        }
        write_json(SPECIES_DIR / f"{slug}.json", rec)
        index.append(
            {
                "id": slug,
                "sci": sci,
                "en": rec["names"]["en"],
                "ru": name_ru,
                "family": fam_code,
                "order": rec["order"],
                "taxon_order": e["taxon_order"],
                "status": rec["colombia"]["status"],
                "endemic": a["endemic"],
                "iucn": a["iucn"],
                "elev": [b.get("elevation", {}).get("min"), b.get("elevation", {}).get("max")] if b.get("elevation") else None,
                "habitat": b.get("primary_habitat"),
                "photo": None,
            }
        )

    write_json(DATA / "species_index.json", index)
    fam_list = sorted(families.values(), key=lambda f: min(i["taxon_order"] for i in index if i["family"] == f["code"]))
    write_json(DATA / "families.json", fam_list)
    log(f"built {len(index)} species, {len(fam_list)} families")
    log(f"  ru names: {sum(1 for i in index if i['ru'])} (ebird {sum(1 for i in index if i['ru'] and read_json(SPECIES_DIR / (i['id'] + '.json'))['name_ru_source']=='ebird')})")
    log(f"  elevation: {sum(1 for i in index if i['elev'])}")


if __name__ == "__main__":
    main()
