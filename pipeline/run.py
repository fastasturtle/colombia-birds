"""Run pipeline steps in order. Usage: uv run python run.py [step ...] [--only slug ...]

Steps: aco ebird birdbase wikidata build   (default: all of these, in order)
Later steps (wikipedia, photos, upload, sites, basemap, gbif_sites, family_names, hotspots) are run explicitly.

Steps may also be given as one whitespace-separated string ("wikipedia photos upload"), as the CI
workflow does. `--only slug ...` restricts per-species steps (wikipedia, photos, upload) to those
slugs by setting the ONLY_SLUGS env var, which those steps read; setting ONLY_SLUGS directly also works.
"""
from __future__ import annotations

import os
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
    "basemap": "build_basemap.py",
    "gbif_sites": "fetch_gbif_sites.py",
    "family_names": "fetch_family_names.py",
    "hotspots": "verify_hotspots.py",
}

args = " ".join(sys.argv[1:]).split()
steps, only = [], []
target = steps
for a in args:
    if a == "--only":
        target = only
        continue
    target.append(a)
if only:
    os.environ["ONLY_SLUGS"] = " ".join(only)
steps = steps or ORDER
unknown = [s for s in steps if s not in FILES]
if unknown:
    sys.exit(f"unknown step(s): {', '.join(unknown)}; known: {', '.join(FILES)}")

for s in steps:
    print(f"=== {s}", flush=True)
    script = Path(__file__).parent / "steps" / FILES[s]
    sys.argv = [str(script)]  # steps must not see run.py's arguments as their own
    runpy.run_path(str(script), run_name="__main__")
