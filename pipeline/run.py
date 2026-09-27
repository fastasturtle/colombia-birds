"""Run pipeline steps in order. Usage: uv run python run.py [step ...]

Steps: aco ebird birdbase wikidata build   (default: all of these, in order)
Later steps (wikipedia, photos, upload) are run explicitly.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ORDER = ["aco", "ebird", "birdbase", "wikidata", "build"]
FILES = {
    "aco": "fetch_aco.py",
    "ebird": "fetch_ebird.py",
    "birdbase": "fetch_birdbase.py",
    "wikidata": "fetch_wikidata.py",
    "build": "build_species.py",
    "wikipedia": "fetch_wikipedia.py",
    "photos": "fetch_photos.py",
    "upload": "upload_media.py",
    "sites": "build_sites.py",
}

steps = sys.argv[1:] or ORDER
for s in steps:
    print(f"=== {s}", flush=True)
    runpy.run_path(str(Path(__file__).parent / "steps" / FILES[s]), run_name="__main__")
