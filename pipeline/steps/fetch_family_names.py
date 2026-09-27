"""Canonical family names from Wikidata (CC0) via QLever: labels ru/en/es and the ru Wikipedia title.

For every family in data/families.json, finds the taxon item with P225 = family scientific name and
P105 (taxon rank) = Q35409 (family). Writes data/sources/family_names.json, keyed by family code.
build_species.py uses the ru label for families.json (`names.ru`) when it is not just the Latin name.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, SOURCES, get_json, log, read_json, write_json  # noqa: E402

ENDPOINT = "https://qlever.dev/api/wikidata"
BATCH = 100

QUERY = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
SELECT ?item ?sci ?labelRu ?labelEn ?labelEs ?ruwiki WHERE {
  VALUES ?sci { %s }
  ?item wdt:P225 ?sci ; wdt:P105 wd:Q35409 .
  OPTIONAL { ?item rdfs:label ?labelRu FILTER(lang(?labelRu)="ru") }
  OPTIONAL { ?item rdfs:label ?labelEn FILTER(lang(?labelEn)="en") }
  OPTIONAL { ?item rdfs:label ?labelEs FILTER(lang(?labelEs)="es") }
  OPTIONAL { ?ruwiki schema:about ?item ; schema:isPartOf <https://ru.wikipedia.org/> }
}
"""


def clean(label: str | None, sci: str) -> str | None:
    """None when missing or just the Latin name; Russian labels are capitalised."""
    if not label or label.strip().lower() == sci.lower():
        return None
    label = label.strip()
    return label[0].upper() + label[1:]


def main() -> None:
    fams = read_json(DATA / "families.json")
    by_sci = {f["sci"]: f["code"] for f in fams}
    names = sorted(by_sci)
    rows: dict[str, dict] = {}
    for i in range(0, len(names), BATCH):
        chunk = names[i : i + BATCH]
        q = QUERY % " ".join(f'"{n}"' for n in chunk)
        data = get_json(ENDPOINT, {"query": q}, kind="wikidata", min_interval=1.0,
                        headers={"Accept": "application/sparql-results+json"})
        for b in data["results"]["bindings"]:
            r = {k: v["value"] for k, v in b.items()}
            prev = rows.get(r["sci"])
            # several items per name (homonyms, duplicates): keep the one with a ru sitelink / ru label
            score = (bool(r.get("ruwiki")), bool(r.get("labelRu")))
            if prev and prev["_score"] >= score:
                continue
            r["_score"] = score
            rows[r["sci"]] = r
    out = {}
    for sci, code in sorted(by_sci.items(), key=lambda kv: kv[1]):
        r = rows.get(sci)
        if not r:
            out[code] = {"sci": sci, "qid": None, "labels": {"ru": None, "en": None, "es": None}, "ruwiki": None}
            continue
        out[code] = {
            "sci": sci,
            "qid": r["item"].rsplit("/", 1)[-1],
            "labels": {lang: clean(r.get(k), sci) for lang, k in (("ru", "labelRu"), ("en", "labelEn"), ("es", "labelEs"))},
            "ruwiki": unquote(r["ruwiki"].rsplit("/wiki/", 1)[-1]).replace("_", " ") if r.get("ruwiki") else None,
        }
    write_json(SOURCES / "family_names.json", {"license": "CC0", "source": "Wikidata via QLever", "families": out})
    log(f"family names: {len(out)} families, matched {sum(1 for v in out.values() if v['qid'])}, "
        f"ru label {sum(1 for v in out.values() if v['labels']['ru'])}, ru wiki {sum(1 for v in out.values() if v['ruwiki'])}")


if __name__ == "__main__":
    main()
