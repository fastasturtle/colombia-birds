"""ACO national checklist of Colombian birds (CC BY 4.0) -> data/sources/aco.json

Source: Asociación Colombiana de Ornitología, "Lista de referencia de especies de aves de Colombia 2022",
published via SiB Colombia IPT as a Darwin Core Archive.
"""
from __future__ import annotations

import csv
import re
import io
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import SOURCES, get, log, norm_sci, write_json  # noqa: E402

URL = "https://ipt.biodiversidad.co/sib/archive.do?r=aco_listaavescolombia2017"
CITATION = (
    "Asociación Colombiana de Ornitología (ACO) / Comité Colombiano de Registros Ornitológicos. "
    "Lista de referencia de especies de aves de Colombia 2022. SiB Colombia. CC BY 4.0. "
    "https://ipt.biodiversidad.co/sib/resource?r=aco_listaavescolombia2017"
)

STATUS_MAP = {
    "Residente": "resident",
    "Residente Endémica": "endemic",
    "Migratorio Boreal": "boreal_migrant",
    "Migratorio Austral": "austral_migrant",
    "Errática": "vagrant",
    "Hipotética": "hypothetical",
    "Exótica establecida": "introduced",
}


def parse_status(raw: str) -> dict:
    """'Migratorio Boreal? - Residente' -> {'codes': ['boreal_migrant','resident'], 'uncertain': True, 'raw': ...}"""
    uncertain = "?" in raw
    parts = [p.strip().rstrip("?").strip() for p in raw.split(" - ")]
    codes = []
    for p in parts:
        if p in ("Extinta",):
            codes.append("extinct")
        elif p == "Austral":
            codes.append("austral_migrant")
        elif p in STATUS_MAP:
            codes.append(STATUS_MAP[p])
        else:
            codes.append(p)
    return {"codes": codes, "uncertain": uncertain, "raw": raw}


def read_tsv(z: zipfile.ZipFile, name: str) -> list[dict]:
    with z.open(name) as f:
        text = io.TextIOWrapper(f, encoding="utf-8")
        return list(csv.DictReader(text, delimiter="\t", quoting=csv.QUOTE_NONE))


def main() -> None:
    raw = get(URL, kind="aco", binary=True)
    z = zipfile.ZipFile(io.BytesIO(raw))
    taxa = read_tsv(z, "taxon.txt")
    dist = {r["id"]: r for r in read_tsv(z, "distribution.txt")}
    prof = {r["id"]: r for r in read_tsv(z, "speciesprofile.txt")}
    desc: dict[str, dict[str, str]] = defaultdict(dict)
    for r in read_tsv(z, "description.txt"):
        desc[r["id"]][r["type"]] = r["description"]

    out = {}
    for t in taxa:
        tid = t["id"]
        d = desc[tid]
        habitat = prof.get(tid, {}).get("habitat", "")
        rec = {
            "gbif_key": int(m.group(1)) if (m := re.search(r"(\d+)$", tid)) else None,
            "source_id": tid,
            "sci_name": t["scientificName"].strip(),
            "authorship": t["scientificNameAuthorship"],
            "order": t["order"],
            "family": t["family"],
            "genus": t["genus"],
            "name_en_aco": t["vernacularName"],
            "status": parse_status(d.get("Estado de cada taxón", "")),
            "migration_note": d.get("Descripción de la migración", ""),
            "status_avendano_2017": d.get("establishmentMeans Avendaño et. al 2017", ""),
            "libro_rojo": d.get("Estado de amenaza según el Libro Rojo", ""),
            "endemic": dist.get(tid, {}).get("establishmentMeans") == "Endémica",
            "introduced": dist.get(tid, {}).get("establishmentMeans") == "Exótica",
            "iucn": dist.get(tid, {}).get("threatStatus", ""),
            "habitat_aco": [h.strip() for h in habitat.split("|")][0] if habitat else "",
            "is_marine": prof.get(tid, {}).get("isMarine") == "VERDADERO",
        }
        out[norm_sci(rec["sci_name"])] = rec

    write_json(SOURCES / "aco.json", {"citation": CITATION, "source_url": URL, "count": len(out), "species": out})
    log(f"ACO: {len(out)} species -> data/sources/aco.json")
    endemic = sum(1 for r in out.values() if r["endemic"])
    log(f"  endemic={endemic}")


if __name__ == "__main__":
    main()
