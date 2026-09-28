"""Russian (and English) species names from the IOC World Bird List Multilingual spreadsheet.

Downloads the IOC Multilingual XLSX (CC BY 3.0; linked from
https://www.worldbirdnames.org/new/ioc-lists/master-list-2/), reads the scientific-name column
(`IOC_<version>`) and the English and Russian columns, and writes data/sources/ioc_names.json:
`{"version", "license", "url", "retrieved", "species": {"<norm_sci binomial>": {"ru", "en"}}}`.
Rows with an empty Russian cell are kept with `ru: null`. The IOC Russian names are lower case;
build_species.py capitalises them (`ru_name`) and uses them as the last fallback before
mappings/names_ru_overrides.json, matching by exact binomial only (IOC and eBird/Clements differ in splits).

The XLSX itself is cached in pipeline/cache/ioc/ (gitignored). To move to a newer IOC release, change URL.
"""
from __future__ import annotations

import io
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import SOURCES, get, log, norm_sci, write_json  # noqa: E402

URL = "https://worldbirdnames.org/Multiling%20IOC%2015.2_b.xlsx"
LICENSE = "CC BY 3.0"


def main() -> None:
    data = get(URL, kind="ioc", binary=True, min_interval=1.0)
    if data[:2] != b"PK":
        raise RuntimeError(f"{URL} did not return an XLSX (got {data[:60]!r})")
    ws = openpyxl.load_workbook(io.BytesIO(data), read_only=True).worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(c or "").strip() for c in next(rows)]
    sci_col = next(i for i, h in enumerate(header) if h.startswith("IOC_"))
    version = header[sci_col].removeprefix("IOC_")
    en_col, ru_col = header.index("English"), header.index("Russian")
    log(f"  IOC World Bird List {version} Multilingual: {URL}")

    species: dict[str, dict] = {}
    for r in rows:
        sci = str(r[sci_col] or "").strip()
        if len(sci.split()) != 2:  # anything but a binomial (blank rows, higher taxa)
            continue
        species[norm_sci(sci)] = {
            "ru": str(r[ru_col] or "").strip() or None,
            "en": str(r[en_col] or "").strip() or None,
        }

    with_ru = [v["ru"] for v in species.values() if v["ru"]]
    dup = sum(1 for c in Counter(with_ru).values() if c > 1)
    log(f"  {len(species)} species, {len(with_ru)} with a Russian name ({dup} Russian names shared by 2+ species)")
    write_json(SOURCES / "ioc_names.json", {
        "version": version,
        "license": LICENSE,
        "url": URL,
        "retrieved": date.today().isoformat(),
        "species": species,
    })


if __name__ == "__main__":
    main()
