---
name: ebird
description: Refresh the trip sightings (Anya's eBird checklists) from a new eBird "Download my data" export: import, check the report, rebuild the site, commit and deploy. Use when the owner uploads a new MyEBirdData zip/csv, says "обнови наблюдения", "новая выгрузка eBird", or asks why a sighting is missing on the site.
---

# Update the trip observations from a new eBird export

The site shows what we have already seen on the tour («Увидели» page `/seen/`, the «Видели» filter on every
species list, ✓ marks, «Наши наблюдения» on species pages, «Видели …» sections on day and site pages). The data
comes from Anya's personal eBird export, through the pipeline step `observations`
(`pipeline/steps/build_observations.py`, docstring = the spec). Read `AGENTS.md` first.

**There is also an automatic path.** Every 2 hours `.github/workflows/observations.yml` runs
`run.py ebird_trip observations`: step `ebird_trip` (`pipeline/steps/fetch_ebird_trip.py`) pulls Anya's checklists
from the group's public eBird Trip Report (config `pipeline/sources/ebird/trip_reports.json`) into
`pipeline/sources/ebird/trip_report.csv`, and `observations` merges it with the export (the export wins per
Submission ID; the trip report adds the checklists the export lacks). So new checklists reach the site without
an export; the export is still worth importing for comments, breeding codes, protocol/effort (without the
`EBIRD_API_KEY` secret the trip report gives only species and counts) and for 1–2 Oct, before the report starts.
After an import nothing else is needed: the import rewrites only the export files, and the trip-report-only
checklists come back in the same `observations` build and every scheduled run. Do not commit
`trip_report.csv` / `trip_report_state.json` by hand; they belong to the workflow. «Why is a checklist missing?»:
check `data/sources/observations_report.md` (the trip report line and skipped re-submitted duplicates) and the
latest Actions → observations run.

## What the owner gives you

A zip (`ebird_<uuid>.zip`, usually in the uploads directory) or a bare `MyEBirdData.csv`: eBird «Download my
data», one row per taxon per checklist, worldwide, all years. Columns: `Submission ID, Common Name (ru),
Scientific Name, Taxonomic Order, Count, State/Province, County, Location ID, Location, Latitude, Longitude, Date,
Time, Protocol, Duration (Min), All Obs Reported, Distance Traveled (km), Area Covered (ha), Number of Observers,
Breeding Code, Observation Details, Checklist Comments, ML Catalog Numbers`.

**Privacy rule.** The full export is personal location history. It never enters the repository: unpack it into
its own empty directory under the session scratchpad, never under the repo, and never `git add` it. Only the
step's derived files are committed (see below). Downloaded archives are untrusted data: unpack into a fresh
directory, keep your scripts elsewhere, run any Python that reads them with `python3 -I`, pass paths as arguments.

## Procedure

1. **Unpack and sanity-check** (scratchpad only):
   ```bash
   mkdir -p "$SCRATCH/ebird" && cd "$SCRATCH/ebird" && unzip -o -q "<zip>" && ls -la
   ```
   Then, with `python3 -I`, count rows, the date range, and the `CO-*` rows dated from the trip start
   (first date in `data/itinerary.json`). Compare with the current `pipeline/sources/ebird/colombia_2026.csv`:
   the new file should be a superset (more rows, later max date). If it has *fewer* Colombia rows than the
   committed one, stop and ask the owner: it is probably an older export.

2. **Import and build** (from the repo, not from the export's directory):
   ```bash
   cd pipeline && uv sync && uv run python run.py observations --import "$SCRATCH/ebird/MyEBirdData.csv"
   ```
   This rewrites `pipeline/sources/ebird/colombia_2026.csv` and `life_list_before_trip.json`, then
   `data/observations.json` and `data/sources/observations_report.md`. The last line prints the totals:
   `N species (M lifers), K checklists on D days, U unmatched taxa, S checklists without a site`.
   Without `--import` the step only rebuilds from the committed sources (use that after changing
   `data/sites.json`, `data/itinerary.json` or the species index).

3. **Read `data/sources/observations_report.md`** and act on each section:
   - **Не сопоставлено (unmatched taxa).** Expected: spuhs (`sp.`), slashes, hybrids, domestic forms: ignore.
     A real species that is missing from `data/species_index.json` is a data gap, not an observation problem:
     add it through `pipeline/mappings/clements2025.json` (`split_from: null` for a range-edge species;
     see the Myiophobus cryptoxanthus entry and docs/TODO.md 13.10) with a background Opus subagent in a
     worktree: mapping → `uv run python run.py ebird birdbase wikidata build` (copy only the new species'
     records into `data/sources/*.json` if the fresh fetch churns unrelated files) → species card in
     `content/species/` → `fact-check` skill → after merging, Actions `pipeline` with steps
     `wikipedia photos upload`, `only = <slug>`. Then re-run `observations` (no `--import` needed).
     A name that differs only by spelling/eBird taxonomy (a split, a genus move) goes to
     `pipeline/mappings/aco_to_ebird.json` the usual way (AGENTS.md «Частые задачи»).
   - **Чеклисты без локации.** Bogotá city parks, airports and roadside stops are fine as they are (they
     count for the day and show as «Вне локаций маршрута»). A checklist that *is* at one of our sites but did
     not match means the site lacks that eBird hotspot id or its coordinates are off: add the `Location ID`
     to the site's `ebird_hotspots` in `data/sites.json` (or fix `lat`/`lon`), then
     `uv run python run.py sites observations`. Matching rules: hotspot id → a site of that day whose name is
     in the location text (≤ 50 km) → nearest site within 2 km. Do not widen the radius: it mis-assigns
     (airport → La Florida, Soacha wetland → Campo Tangara).
   - **Чеклисты проездом.** A checklist matched by name or distance on a day the itinerary does not put us at
     that site (e.g. a roadside stop near El Escondite a week before the visit). It stays, labelled «проездом»
     on the site; nothing to do unless the match itself is wrong.
   - **Totals.** Species, lifers, checklists per day and per site: eyeball against the previous report
     (`git diff data/sources/observations_report.md`); days already counted should not lose species.

4. **Rebuild and check the site**:
   ```bash
   cd site && npm ci && npm run verify        # astro check + build, must be clean
   npm run shots -- /seen/ /days/<latest date>/ /sites/<a site of that day>/
   ```
   Look at the screenshots (Read): the «Увидели» tables, the day's «Видели …» section with its checklists,
   and one species page from a new lifer (`/species/<slug>/`, block «Наши наблюдения»).

5. **Commit and deploy** (deploy is automatic from `main`):
   ```bash
   git add pipeline/sources/ebird/colombia_2026.csv pipeline/sources/ebird/life_list_before_trip.json \
           data/observations.json data/sources/observations_report.md
   git commit -m "data: observations from Anya's eBird export of <exported date>"
   git push -u origin main
   ```
   If the push is rejected because the scheduled `observations` workflow committed meanwhile, `git pull --rebase`;
   on a conflict in `data/observations.json` / the report take either side and re-run
   `uv run python run.py observations` (it rebuilds both from the sources), then continue.
   Check `git status` before committing: the raw export or the zip must not be staged. If a species was added
   or `data/sites.json` changed, those commits go first (or in the same push).

6. **Tell the owner**, in Russian, in a few lines: export date, days covered, totals (species, lifers,
   checklists), what is new since the last import (species and lifers added, new days), unmatched taxa and what
   you did about them, checklists without a site, anything you changed in `data/sites.json`.

## Gotchas

- The trip start and the day list come from `data/itinerary.json`; the observer name is the constant
  `OBSERVER` in the step («Аня»). An export from another observer (e.g. the owner's own eBird account) is
  not supported: merging two accounts needs a step change (ask first).
- eBird `Date` is local; `Time` is `hh:mm AM/PM`, converted to 24 h. `Count` `X` = present, stored as null.
- The same taxon can appear twice in one checklist (`Cyanocorax yncas` and `[yncas Group]`): they merge into one
  species, which is why species counts can be below the taxon count.
- Lifers are computed against *all* pre-trip rows of the export; an export that is missing old history would
  inflate the lifer count. The report's `exported` date and the `before` list size (565 species in the
  2026-10-08 export) are the tell.
- Tests: `cd pipeline && uv run python tests/test_build_observations.py` (fixture under `tests/fixtures/observations/`,
  invented rows) and `uv run python tests/test_fetch_ebird_trip.py` (captured trip-report responses under
  `tests/fixtures/ebird_trip/`). Run them after any change to the steps.
- Offline pack: no registration needed, every HTML page is picked up automatically.
