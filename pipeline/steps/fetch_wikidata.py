"""Wikidata (CC0) spine: QID, labels ru/en/es, external IDs, IUCN status, Commons category, sitelinks.

Query by eBird species code (P3444) first, then by scientific name (P225) for the rest.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import SOURCES, get_json, log, norm_sci, read_json, write_json  # noqa: E402

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


def main() -> None:
    aco = read_json(SOURCES / "aco.json")["species"]
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

    def store(aco_key: str, r: dict, matched_by: str) -> None:
        if aco_key in out:
            return
        out[aco_key] = {
            "qid": r["item"].rsplit("/", 1)[-1],
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

    for r in run("P3444", "ebird", sorted(code_to_aco)):
        for aco_key in code_to_aco.get(r["ebird"], []):
            store(aco_key, r, "ebird_code")

    rest = [k for k in aco if k not in out]
    names = sorted({aco[k]["sci_name"] for k in rest} | {ebird[aco_to_ebird[k]]["sci_name"] for k in rest if aco_to_ebird[k] in ebird})
    by_sci = {}
    for r in run("P225", "sci", names):
        by_sci[norm_sci(r["sci"])] = r
    for k in rest:
        r = by_sci.get(k) or by_sci.get(aco_to_ebird[k])
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
