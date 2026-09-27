"""Run pipeline steps in order. Usage: uv run python run.py [step ...] [--only slug ...]

Steps: aco ebird birdbase wikidata build   (default: all of these, in order)
Later steps (wikipedia, photos, upload, sites, basemap, gbif_sites, family_names, endemics, hotspots, study, lynx) are run explicitly.
`lynx` runs after `build` (needs species_index.json); re-run `build` afterwards to merge the book pages:
`uv run python run.py lynx build`.

Steps may also be given as one whitespace-separated string ("wikipedia photos upload"), as the CI
workflow does. `--only slug ...` restricts per-species steps (wikipedia, photos, upload) to those
slugs by setting the ONLY_SLUGS env var, which those steps read; setting ONLY_SLUGS directly also works.

`--max-minutes N` (or the MAX_MINUTES env var) is a time budget for the whole run: per-species steps
(wikipedia, photos, upload) finish the current species, write their outputs and stop cleanly once it is
spent (later steps then stop at once); the run still exits 0. Re-running resumes where it stopped.
The CI workflow sets MAX_MINUTES below its hard step timeout.
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
    "study": "build_study_lists.py",
    "endemics": "fetch_endemics.py",
    "lynx": "build_lynx.py",
}

args = " ".join(sys.argv[1:]).split()
if "--max-minutes" in args:
    i = args.index("--max-minutes")
    os.environ["MAX_MINUTES"] = args[i + 1]
    del args[i:i + 2]
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

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("STEPS", " ".join(steps))  # recorded in the status file (CI sets it itself)
from common import fmt_elapsed, sigterm_as_interrupt, status  # noqa: E402  (also starts the MAX_MINUTES clock)

sigterm_as_interrupt()
if os.environ.get("MAX_MINUTES"):
    print(f"time budget: {os.environ['MAX_MINUTES']} minutes (MAX_MINUTES)", flush=True)

# Each step start/finish (and failure) also lands in pipeline/cache/status.json (common.status).
for i, s in enumerate(steps, 1):
    print(f"=== {s}", flush=True)
    status(s, None, None, f"{s}: started (step {i}/{len(steps)})", echo=False)
    script = Path(__file__).parent / "steps" / FILES[s]
    sys.argv = [str(script)]  # steps must not see run.py's arguments as their own
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as e:  # sys.exit() in a step ends the whole run, as before
        done = f"finished (step {i}/{len(steps)}, elapsed {fmt_elapsed()})" if not e.code else f"exited with {e.code!r}"
        status(s, None, None, f"{s}: {done}", echo=False)
        raise
    except BaseException as e:
        status(s, None, None, f"{s}: failed ({type(e).__name__}: {str(e)[:150]}) after {fmt_elapsed()}")
        raise
    status(s, None, None, f"{s}: finished (step {i}/{len(steps)}, elapsed {fmt_elapsed()})", echo=False)
