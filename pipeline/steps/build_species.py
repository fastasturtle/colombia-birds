"""Merge data/sources/*.json into data/species/<slug>.json, data/species_index.json, data/families.json.

Canonical taxonomy is eBird/Clements (matches Merlin and eBird in the field). The ACO checklist is the
canonical *list* of what occurs in Colombia and carries the status flags. Hand-written content lives in
content/species/<slug>.md and is merged at site build time, never here.

Lynx "Birds of Colombia" (Hilty 2021) pages from step `lynx`: `book.lynx_page` in the species files,
`lynx_page` in species_index.json (from data/lynx_pages.json) and in families.json (from
data/sources/lynx_families.json + lynx_index.json). Kept from the previous build when that step never ran.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, MAPPINGS, SOURCES, SPECIES_DIR, checklist, log, norm_sci, read_json, slugify, write_json, write_text  # noqa: E402

REGION_ORDER = ["Tinamiformes"]  # unused placeholder to keep import tidy


def wiki_url(lang: str, title: str | None) -> str | None:
    if not title:
        return None
    return f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"


def ru_name(name: str | None) -> str | None:
    """Clean a Russian species name: None when it has no Cyrillic letter (Wikidata labels that are the Latin
    binomial), first letter upper case (Wikidata labels are lower case: «масковый дакнис»)."""
    if not name or not re.search(r"[а-яё]", name, re.I):
        return None
    return name[0].upper() + name[1:]


def family_names(sci: str, ebird_names: dict, wd: dict | None) -> dict:
    """en/es from eBird; ru from Wikidata (label, else ru Wikipedia title), null when missing or Latin.

    eBird has no Russian family names (its `ru` is the English one), so the site falls back to English."""
    names = {"en": ebird_names.get("en"), "es": ebird_names.get("es"), "ru": None}
    if wd:
        ru = wd["labels"].get("ru") or wd.get("ruwiki")
        if ru and ru.lower() != sci.lower() and re.search(r"[а-яё]", ru, re.I) and "(" not in ru:
            names["ru"] = ru
    return names


# eBird/Clements family name -> family name in the Lynx "Birds of Colombia" family index (HBW/BirdLife names).
# Every pair checked against the book's own index line for the Latin family name (e.g. ANATIDAE 39).
LYNX_FAMILY_ALIASES = {
    "Ducks, Geese, and Waterfowl": "Ducks, Geese and Swans",
    "New World Quail": "New World Quails",
    "Nightjars and Allies": "Nightjars",
    "Stilts and Avocets": "Avocets and Stilts",
    "Plovers and Lapwings": "Plovers",
    "Skuas and Jaegers": "Skuas",
    "Gulls, Terns, and Skimmers": "Gulls and Terns",
    "Shearwaters and Petrels": "Petrels and Shearwaters",
    "Boobies and Gannets": "Gannets and Boobies",
    "Anhingas": "Darters",
    "Cormorants and Shags": "Cormorants",
    "Herons, Egrets, and Bitterns": "Herons",
    "Hawks, Eagles, and Kites": "Hawks and Eagles",
    "Owls": "Typical Owls",
    "Toucan-Barbets": "Prong-billed Barbets",
    "New World and African Parrots": "Parrots",
    "Antthrushes": "Ground-antbirds",
    "Ovenbirds and Woodcreepers": "Ovenbirds",
    "Tityras and Allies": "Tityras, Becards, Schiffornises and Mourners",
    "Royal Flycatchers and Allies": "Long-bristled Flycatchers",
    "Vireos, Shrike-Babblers, and Erpornis": "Vireos",
    "Crows, Jays, and Magpies": "Crows and Jays",
    "Swallows": "Swallows and Martins",
    "Thrushes and Allies": "Thrushes",
    "Waxbills and Allies": "Waxbills",
    "Wagtails and Pipits": "Pipits and Wagtails",
    "Finches, Euphonias, and Allies": "Finches",
    "Troupials and Allies": "New World Blackbirds",
    "Mitrospingid Tanagers": "Aberrant Tanagers",
    "Cardinals and Allies": "Cardinals",
    "Tanagers and Allies": "Tanagers",
}


def _norm_family(name: str) -> str:
    s = re.sub(r"\band\b|&", " ", name.lower())
    return re.sub(r"[^a-z]", "", s)


def lynx_family_pages(fam_list: list[dict]) -> dict[str, int | None] | None:
    """Family code -> first page in the Lynx book (step `lynx`): by English name in the book's family index
    (with LYNX_FAMILY_ALIASES), else by the Latin family line of the main index (ANATIDAE 39). None when
    the step has not run."""
    book_fams = read_json(SOURCES / "lynx_families.json")
    index = read_json(SOURCES / "lynx_index.json")
    if book_fams is None and index is None:
        return None
    by_name = {_norm_family(f["name"]): f["page"] for f in book_fams or [] if not f.get("fragment") and f.get("page")}
    by_sci = {e["family"].lower(): e["first_page"] for e in (index or {}).get("entries", [])
              if e["kind"] == "family" and e.get("first_page")}
    out: dict[str, int | None] = {}
    for f in fam_list:
        en = f["names"].get("en") or ""
        page = by_name.get(_norm_family(LYNX_FAMILY_ALIASES.get(en, en)))
        sci_page = by_sci.get(f["sci"].lower())
        if page is None and sci_page is not None:
            log(f"  lynx: family {en} ({f['sci']}) not in the family index, page {sci_page} from the main index")
            page = sci_page
        elif page is None:
            log(f"  lynx: family {en} ({f['sci']}) not found in the book")
        elif sci_page is not None and sci_page != page:
            log(f"  lynx: family {en}: family index {page} vs main index {f['sci'].upper()} {sci_page}")
        out[f["code"]] = page
    return out


def endemics_report(aco: dict, chaparro: dict, index: list[dict], src: dict) -> None:
    """Log and write data/sources/endemics_report.md: ACO endemics vs Chaparro-Herrera et al. 2024."""
    if not src:
        return
    aco = {k: a for k, a in aco.items() if a["source"] == "aco2022"}  # the report compares the two lists only
    aco_e = {k for k, a in aco.items() if a["endemic"]}
    ch_e = {k for k, v in chaparro.items() if v["category"] == "endemic"}
    only_aco = sorted(aco_e - ch_e)
    only_ch = sorted(ch_e - aco_e)
    counts = src.get("counts", {})
    lines = [
        "# Endemics: ACO 2022 vs Chaparro-Herrera et al. 2024",
        "",
        "Generated by `pipeline/steps/build_species.py`. `colombia.endemic` stays ACO; "
        "`colombia.near_endemic` and `colombia.endemic_source` come from Chaparro-Herrera et al. 2024 (Anexo 3, CC BY-NC 4.0).",
        "",
        f"- Anexo 3 taxa: {src.get('count')} (endemic {counts.get('endemic', 0)}, near-endemic {counts.get('near_endemic', 0)}, "
        f"of interest {counts.get('of_interest', 0)}, insufficient info {counts.get('insufficient_info', 0)})",
        f"- Matched to the ACO list: {len(chaparro)}",
        f"- ACO endemics: {len(aco_e)}; Chaparro-Herrera endemics: {len(ch_e)}; both: {len(aco_e & ch_e)}",
        "",
        f"## Endemic in ACO, not in Chaparro-Herrera ({len(only_aco)})",
        "",
    ]
    lines += [f"- *{aco[k]['sci_name']}*: Chaparro-Herrera {chaparro[k]['code'] if k in chaparro else 'not listed'}" for k in only_aco] or ["- none"]
    lines += ["", f"## Endemic in Chaparro-Herrera, not in ACO ({len(only_ch)})", ""]
    lines += [f"- *{aco[k]['sci_name']}*: ACO status {aco[k]['status']['raw']}" for k in only_ch] or ["- none"]
    write_text(SOURCES / "endemics_report.md", "\n".join(lines) + "\n")
    log(f"  endemics: ACO {len(aco_e)}, Chaparro-Herrera {len(ch_e)}, both {len(aco_e & ch_e)}; "
        f"near-endemic {sum(1 for i in index if i['near_endemic'])}")
    for k in only_aco:
        log(f"    ACO-only endemic: {aco[k]['sci_name']} (Chaparro-Herrera: {chaparro[k]['code'] if k in chaparro else 'not listed'})")
    for k in only_ch:
        log(f"    Chaparro-Herrera-only endemic: {aco[k]['sci_name']} (ACO: {aco[k]['status']['raw']})")


def main() -> None:
    aco = checklist()  # ACO 2022 (+ aco_fixes) + clements2025 additions
    ebird = read_json(SOURCES / "ebird.json")
    ebird_sp, ebird_fam = ebird["species"], ebird["families"]
    name_map = read_json(SOURCES / "ebird_name_map.json")
    birdbase = read_json(SOURCES / "birdbase.json")["species"]
    wikidata = read_json(SOURCES / "wikidata.json")["species"]
    aco_to_ebird = {k: k for k in aco}
    for k, v in {**name_map["auto_by_english_name"], **name_map["manual"]}.items():
        aco_to_ebird[k] = norm_sci(v)

    fam_names = (read_json(SOURCES / "family_names.json") or {}).get("families", {})
    # Chaparro-Herrera et al. 2024 (step `endemics`), keyed by ACO key. ACO's `endemic` flag stays canonical.
    endemics_src = read_json(SOURCES / "endemics.json") or {}
    # Russian names fixed by hand (typos, ru.wikipedia titles): mappings/names_ru_overrides.json
    ru_overrides = {k: v for k, v in (read_json(MAPPINGS / "names_ru_overrides.json") or {}).items() if not k.startswith("_")}
    # One-off slug renames after eBird/Clements remaps (mappings/clements2025.json `renamed`)
    renamed = (read_json(MAPPINGS / "clements2025.json") or {}).get("renamed", {})
    chaparro = {v["aco_key"]: v for v in endemics_src.get("species", {}).values() if v.get("aco_key")}
    if not endemics_src:
        log("  WARNING: data/sources/endemics.json missing, run step `endemics`; near_endemic will be false")

    # Carry over fields filled by later steps (upload, wikipedia, sounds) so a rebuild does not wipe them.
    SPECIES_DIR.mkdir(parents=True, exist_ok=True)
    preserved: dict[str, dict] = {}
    for p in SPECIES_DIR.glob("*.json"):
        old = read_json(p) or {}
        preserved[p.stem] = {k: old[k] for k in ("photos", "texts", "sounds", "book") if old.get(k)}
    for old_slug, r in renamed.items():  # the new slug inherits media of the old one (same Colombian bird)
        if r.get("carry") and old_slug in preserved and r["to"] not in preserved:
            preserved[r["to"]] = {k: v for k, v in preserved[old_slug].items() if k != "book"}
            log(f"  renamed {old_slug} -> {r['to']}: kept {', '.join(preserved[r['to']]) or 'nothing'}")
    # Lynx "Birds of Colombia" page per species (step `lynx`); without it keep what the files already have.
    lynx_pages = read_json(DATA / "lynx_pages.json")
    if lynx_pages is None:
        log("  lynx: data/lynx_pages.json missing (step `lynx`), keeping book pages from the previous build")
    old_files = {p.stem for p in SPECIES_DIR.glob("*.json")}

    index = []
    families: dict[str, dict] = {}
    slugs: dict[str, str] = {}
    for key, a in sorted(aco.items(), key=lambda kv: ebird_sp.get(aco_to_ebird[kv[0]], {}).get("taxon_order", 1e9)):
        e = ebird_sp[aco_to_ebird[key]]
        b = birdbase.get(key, {})
        w = wikidata.get(key, {})
        sci = e["sci_name"]
        if norm_sci(w.get("sci_wikidata") or "") == key != norm_sci(sci) and key in ebird_sp:
            # ACO taxon remapped to the other half of an eBird split (aco_to_ebird.json) and wikidata.json still
            # holds the item of the ACO name (the extralimital species): ignore it until step `wikidata` re-runs.
            log(f"  wikidata: {key} -> {sci}: stale item {w.get('qid')} ({w.get('sci_wikidata')}) ignored, re-run `wikidata`")
            w = {}
        slug = slugify(sci)
        if slug in slugs:  # two ACO taxa lumped into one Clements species
            slug = slugify(a["sci_name"])
        slugs[slug] = key

        name_ru = ru_name(e["names"].get("ru"))
        name_ru_source = "ebird" if name_ru else None
        if not name_ru and ru_name(w.get("labels", {}).get("ru")):
            name_ru, name_ru_source = ru_name(w["labels"]["ru"]), "wikidata"
        if slug in ru_overrides:
            name_ru, name_ru_source = ru_name(ru_overrides[slug]["ru"]), ru_overrides[slug].get("source")

        fam_code = e["family_code"]
        fam = ebird_fam.get(fam_code, {})
        families.setdefault(
            fam_code,
            {
                "code": fam_code,
                "sci": fam.get("sci") or a["family"],
                "order": fam.get("order") or a["order"],
                "names": family_names(fam.get("sci") or a["family"], fam.get("names", {}), fam_names.get(fam_code)),
                "species_count": 0,
                "slug": slugify(fam.get("sci") or a["family"]),
            },
        )["species_count"] += 1

        ch = chaparro.get(key)
        near_endemic = bool(ch and ch["category"] == "near_endemic")
        endemic_source = (
            {"category": ch["category"], "code": ch["code"], "source": ch["source"]} if ch else None
        )

        taxonomy_note = None
        if a["source"] == "clements2025":
            taxonomy_note = f"Not in the ACO 2022 checklist (split from {a['split_from']}); added from eBird/Clements 2025. {a.get('clements_note') or ''}".strip()
        elif norm_sci(sci) != key:
            taxonomy_note = f"ACO/SACC lists this as {a['sci_name']}; eBird/Clements uses {sci}."

        rec = {
            "id": slug,
            "source": a["source"],
            "sci_name": sci,
            "sci_name_aco": a["sci_name"] if a["source"] == "aco2022" else None,
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
                "near_endemic": near_endemic,
                "endemic_source": endemic_source,
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
            # Filled by later pipeline steps (kept from the previous build, see `preserved`)
            "photos": preserved.get(slug, {}).get("photos", []),
            "texts": preserved.get(slug, {}).get("texts", {}),
            "sounds": preserved.get(slug, {}).get("sounds", []),
            "book": (
                {"lynx_page": (lynx_pages.get(slug) or {}).get("page")} if lynx_pages is not None
                else preserved.get(slug, {}).get("book", {"lynx_page": None})
            ),
            # Filled by agents (content/species/<slug>.md) — kept null here on purpose
            "difficulty": None,
        }
        write_json(SPECIES_DIR / f"{slug}.json", rec)
        index.append(
            {
                "id": slug,
                "sci": sci,
                "source": a["source"],
                "en": rec["names"]["en"],
                "ru": name_ru,
                "family": fam_code,
                "order": rec["order"],
                "taxon_order": e["taxon_order"],
                "status": rec["colombia"]["status"],
                "endemic": a["endemic"],
                "near_endemic": near_endemic,
                "iucn": a["iucn"],
                "elev": [b.get("elevation", {}).get("min"), b.get("elevation", {}).get("max")] if b.get("elevation") else None,
                "habitat": b.get("primary_habitat"),
                "photo": rec["photos"][0]["sizes"]["thumb"] if rec["photos"] else None,
                "lynx_page": rec["book"].get("lynx_page"),
            }
        )

    endemics_report(aco, chaparro, index, endemics_src)

    for stale in old_files - {i["id"] for i in index}:
        (SPECIES_DIR / f"{stale}.json").unlink()
    write_json(DATA / "species_index.json", index)
    fam_list = sorted(families.values(), key=lambda f: min(i["taxon_order"] for i in index if i["family"] == f["code"]))
    fam_pages = lynx_family_pages(fam_list)
    if fam_pages is None:  # step `lynx` never ran: keep pages from the previous families.json
        old_fams = {f["code"]: f for f in read_json(DATA / "families.json") or []}
        fam_pages = {f["code"]: old_fams.get(f["code"], {}).get("lynx_page") for f in fam_list}
    for f in fam_list:
        f["lynx_page"] = fam_pages.get(f["code"])
    write_json(DATA / "families.json", fam_list)
    log(f"built {len(index)} species, {len(fam_list)} families")
    log(f"  ru names: {sum(1 for i in index if i['ru'])} (ebird {sum(1 for i in index if i['ru'] and read_json(SPECIES_DIR / (i['id'] + '.json'))['name_ru_source']=='ebird')})")
    log(f"  photos kept: {sum(1 for i in index if i['photo'])}; families with ru name: {sum(1 for f in fam_list if f['names'].get('ru'))}")
    log(f"  elevation: {sum(1 for i in index if i['elev'])}")
    log(f"  lynx pages: {sum(1 for i in index if i['lynx_page'])} species, {sum(1 for f in fam_list if f['lynx_page'])} families")


if __name__ == "__main__":
    main()
