"""Wikidata (CC0) spine: QID, labels ru/en/es, external IDs, IUCN status, Commons category, sitelinks.

Query by eBird species code (P3444) first, then by scientific name (P225) for the rest.

Wikidata sometimes carries the eBird code on a SUBSPECIES item (trinomial P225, e.g. "Butorides striata striata"),
which has no sitelinks, ru label or Commons category. Such matches are replaced by the species item: the eBird
name by P225, then the subspecies' parent taxon (P171, rank species), then the first two words of the trinomial,
accepting a candidate only when its epithet is the eBird one (a genus move like Tangara -> Stilpnia is fine, but
"Grallaria quitensis alticola" must not resolve to Grallaria quitensis, a different eBird species). The record
keeps `subspecies_qid` (and takes the eBird/iNat/Avibase ids the species item lacks from it); with no acceptable species item the subspecies record stays (`ebird_code_subspecies`).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import MAPPINGS, SOURCES, checklist, get_json, log, norm_sci, read_json, write_json  # noqa: E402

# Official WDQS rate-limits shared IPs aggressively; QLever is a full Wikidata mirror with a SPARQL API.
ENDPOINT = "https://qlever.dev/api/wikidata"
FALLBACK = "https://query.wikidata.org/sparql"
BATCH = 150

QUERY = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
SELECT ?item ?sci ?ebird ?avibase ?iucnId ?iucn ?commonsCat ?image ?inat ?gbif ?xc
       ?labelEn ?labelEs ?labelRu ?enwiki ?eswiki ?ruwiki WHERE {
  VALUES ?%(var)s { %(values)s }
  ?item wdt:%(prop)s ?%(var)s ; wdt:P225 ?sci .
  OPTIONAL { ?item wdt:P3444 ?ebird }
  OPTIONAL { ?item wdt:P2026 ?avibase }
  OPTIONAL { ?item wdt:P627 ?iucnId }
  OPTIONAL { ?item wdt:P141 ?iucnItem . ?iucnItem rdfs:label ?iucn FILTER(lang(?iucn)="en") }
  OPTIONAL { ?item wdt:P373 ?commonsCat }
  OPTIONAL { ?item wdt:P18 ?image }
  OPTIONAL { ?item wdt:P3151 ?inat }
  OPTIONAL { ?item wdt:P846 ?gbif }
  OPTIONAL { ?item wdt:P2426 ?xc }
  OPTIONAL { ?item rdfs:label ?labelEn FILTER(lang(?labelEn)="en") }
  OPTIONAL { ?item rdfs:label ?labelEs FILTER(lang(?labelEs)="es") }
  OPTIONAL { ?item rdfs:label ?labelRu FILTER(lang(?labelRu)="ru") }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL { ?eswiki schema:about ?item ; schema:isPartOf <https://es.wikipedia.org/> }
  OPTIONAL { ?ruwiki schema:about ?item ; schema:isPartOf <https://ru.wikipedia.org/> }
}
"""


PARENT_QUERY = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
SELECT ?sub ?parent ?psci WHERE {
  VALUES ?sub { %(values)s }
  ?sub wdt:P171 ?parent . ?parent wdt:P225 ?psci ; wdt:P105 wd:Q7432 .
}
"""


def run(prop: str, var: str, values: list[str]) -> list[dict]:
    rows = []
    for i in range(0, len(values), BATCH):
        chunk = values[i : i + BATCH]
        q = QUERY % {"prop": prop, "var": var, "values": " ".join(f'"{v}"' for v in chunk)}
        data = get_json(ENDPOINT, {"query": q}, kind="wikidata", min_interval=1.0, headers={"Accept": "application/sparql-results+json"})
        merged: dict[str, dict] = {}
        for b in data["results"]["bindings"]:
            row = {k: v["value"] for k, v in b.items()}
            key = row["item"] + "|" + row[var]
            if key in merged:
                images = merged[key].setdefault("images", [])
                if row.get("image") and row["image"] not in images:
                    images.append(row["image"])
                continue
            row["images"] = [row["image"]] if row.get("image") else []
            merged[key] = row
        rows.extend(merged.values())
        log(f"  wikidata {prop}: {min(i + BATCH, len(values))}/{len(values)}")
    return rows


def wiki_title(url: str | None) -> str | None:
    if not url:
        return None
    from urllib.parse import unquote
    return unquote(url.rsplit("/wiki/", 1)[-1]).replace("_", " ")


def qid(r: dict) -> str:
    return r["item"].rsplit("/", 1)[-1]


def n_sitelinks(r: dict) -> int:
    return sum(1 for k in ("enwiki", "eswiki", "ruwiki") if r.get(k))


def parents(qids: list[str]) -> dict[str, list[str]]:
    """Subspecies QID -> scientific names of its parent taxa of rank species (P171, P105 = Q7432)."""
    out: dict[str, list[str]] = {}
    for i in range(0, len(qids), BATCH):
        q = PARENT_QUERY % {"values": " ".join(f"wd:{v}" for v in qids[i : i + BATCH])}
        data = get_json(ENDPOINT, {"query": q}, kind="wikidata", min_interval=1.0, headers={"Accept": "application/sparql-results+json"})
        for b in data["results"]["bindings"]:
            out.setdefault(b["sub"]["value"].rsplit("/", 1)[-1], []).append(b["psci"]["value"])
    return out


def species_for_subspecies(sub: dict, target: str, parent_names: list[str], by_sci: dict[str, list[dict]]) -> tuple[dict, str] | None:
    """The species item for a subspecies row matched by eBird code: `target` (the eBird name) by P225, then the
    parent taxon, then the trinomial's first two words; only candidates with the eBird epithet are accepted."""
    epithet = target.split()[1]
    first_two = " ".join(norm_sci(sub["sci"]).split()[:2])
    cands = [(target, "ebird_code_subspecies->species")]
    cands += [(norm_sci(n), "ebird_code_subspecies->parent") for n in parent_names]
    cands.append((first_two, "ebird_code_subspecies->binomial"))
    for name, how in cands:
        if len(name.split()) != 2 or name.split()[1] != epithet:
            continue
        rows = by_sci.get(name) or []
        if rows:  # homonyms (fossils, plants): the item with most sitelinks
            return max(rows, key=n_sitelinks), how
    return None


def main() -> None:
    aco = checklist()  # ACO 2022 + clements2025 additions
    ebird = read_json(SOURCES / "ebird.json")["species"]
    name_map = read_json(SOURCES / "ebird_name_map.json")
    aco_to_ebird = {k: k for k in aco}
    for k, v in {**name_map["auto_by_english_name"], **name_map["manual"]}.items():
        aco_to_ebird[k] = norm_sci(v)

    code_to_aco: dict[str, list[str]] = {}
    for k, ek in aco_to_ebird.items():
        if ek in ebird:
            code_to_aco.setdefault(ebird[ek]["code"], []).append(k)

    out: dict[str, dict] = {}

    def store(aco_key: str, r: dict, matched_by: str, subspecies: dict | None = None) -> None:
        if aco_key in out:
            return
        out[aco_key] = {
            "qid": qid(r),
            "sci_wikidata": r.get("sci"),
            "matched_by": matched_by,
            "ebird_code": r.get("ebird"),
            "avibase_id": r.get("avibase"),
            "iucn_id": r.get("iucnId"),
            "iucn_status": r.get("iucn"),
            "inaturalist_id": r.get("inat"),
            "gbif_key": r.get("gbif"),
            "xeno_canto": r.get("xc"),
            "commons_category": r.get("commonsCat"),
            "images": r.get("images", []),
            "labels": {
                lang: (None if (r.get(k) or "").lower() == (r.get("sci") or "").lower() else r.get(k))
                for lang, k in (("en", "labelEn"), ("es", "labelEs"), ("ru", "labelRu"))
            },
            "wikipedia": {"en": wiki_title(r.get("enwiki")), "es": wiki_title(r.get("eswiki")), "ru": wiki_title(r.get("ruwiki"))},
        }
        if subspecies:  # eBird code sits on a subspecies item; keep it for reference
            out[aco_key]["subspecies_qid"] = qid(subspecies)
            out[aco_key]["subspecies_sci"] = subspecies.get("sci")
            # ids the species item lacks: the subspecies' (same population concept, e.g. iNat taxa of recent splits)
            for f, k in (("ebird_code", "ebird"), ("inaturalist_id", "inat"), ("avibase_id", "avibase")):
                out[aco_key][f] = out[aco_key][f] or subspecies.get(k)

    code_rows = run("P3444", "ebird", sorted(code_to_aco))
    # eBird code on a subspecies item (trinomial P225): resolve the species item (see module docstring).
    subs = {qid(r): r for r in code_rows if len(norm_sci(r["sci"]).split()) == 3}
    sub_parents = parents(sorted(subs)) if subs else {}
    targets = {aco_key: norm_sci(ebird[aco_to_ebird[aco_key]]["sci_name"]) for r in subs.values() for aco_key in code_to_aco.get(r["ebird"], [])}
    cand_names = set(targets.values()) | {norm_sci(n) for ns in sub_parents.values() for n in ns}
    cand_names |= {" ".join(norm_sci(r["sci"]).split()[:2]) for r in subs.values()}
    sp_by_sci: dict[str, list[dict]] = {}
    if cand_names:
        # P225 literals are case-sensitive: query the capitalised binomial
        for r in run("P225", "sci", sorted(n[0].upper() + n[1:] for n in cand_names)):
            sp_by_sci.setdefault(norm_sci(r["sci"]), []).append(r)
    n_sub = n_sub_ok = 0
    for r in code_rows:
        for aco_key in code_to_aco.get(r["ebird"], []):
            if qid(r) in subs:
                n_sub += 1
                found = species_for_subspecies(r, targets[aco_key], sub_parents.get(qid(r), []), sp_by_sci)
                if found:
                    n_sub_ok += 1
                    store(aco_key, found[0], found[1], subspecies=r)
                    continue
                log(f"  {aco_key}: eBird code on subspecies {qid(r)} ({r['sci']}), no species item with that epithet")
                store(aco_key, r, "ebird_code_subspecies")
            else:
                store(aco_key, r, "ebird_code")
    if n_sub:
        log(f"  eBird code on a subspecies item: {n_sub}, resolved to the species item: {n_sub_ok}")

    # Whole-species remaps (clements2025.json `renamed`): the ACO name is the extralimital half of a split, never use it
    # (eBird codes are reused after splits, so the item found by code can be the other half or one of its subspecies).
    renamed = (read_json(MAPPINGS / "clements2025.json") or {}).get("renamed", {})
    renamed_aco = {norm_sci(r.get("aco") or old.replace("-", " ")) for old, r in renamed.items()}
    for k in renamed_aco:
        if k in out and " ".join(norm_sci(out[k]["sci_wikidata"] or "").split()[:2]) != aco_to_ebird.get(k):
            del out[k]

    rest = [k for k in aco if k not in out]
    names = sorted({aco[k]["sci_name"] for k in rest} | {ebird[aco_to_ebird[k]]["sci_name"] for k in rest if aco_to_ebird[k] in ebird})
    by_sci: dict[str, dict] = {}
    for r in run("P225", "sci", names):
        k = norm_sci(r["sci"])
        if k not in by_sci or n_sitelinks(r) > n_sitelinks(by_sci[k]):
            by_sci[k] = r
    for k in rest:
        # After a split (ACO name and eBird name are both eBird species, aco_to_ebird.json) the ACO name is the
        # other half of the split: try the eBird name first.
        split = aco_to_ebird[k] != k and k in ebird
        if k in renamed_aco:
            r = by_sci.get(aco_to_ebird[k])
        else:
            r = (by_sci.get(aco_to_ebird[k]) or by_sci.get(k)) if split else (by_sci.get(k) or by_sci.get(aco_to_ebird[k]))
        if r:
            store(k, r, "sci_name")

    missing = sorted(k for k in aco if k not in out)
    write_json(SOURCES / "wikidata.json", {"license": "CC0", "count": len(out), "species": out})
    write_json(SOURCES / "wikidata_unmatched.json", missing)
    log(f"Wikidata: matched {len(out)} of {len(aco)}; unmatched {len(missing)}")
    for lang in ("en", "es", "ru"):
        n = sum(1 for v in out.values() if v["wikipedia"][lang])
        log(f"  wikipedia {lang}: {n}")
    log(f"  P18 image: {sum(1 for v in out.values() if v['images'])}")
    log(f"  ru label: {sum(1 for v in out.values() if v['labels']['ru'])}")


if __name__ == "__main__":
    main()
