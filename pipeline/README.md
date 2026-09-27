# Data pipeline

Builds everything under `data/` from open sources. Python deps are managed with uv:

```sh
cd pipeline
uv run python run.py                      # aco ebird birdbase wikidata build (default)
uv run python run.py wikipedia photos upload
uv run python run.py "photos upload" --only grallaria-milleri rupicola-peruvianus
uv run python steps/fetch_photos.py --limit 20     # any step can also run on its own
uv run python run.py wikipedia photos upload --max-minutes 270   # stop cleanly after 270 min (resume by re-running)
```

Every step is resumable: HTTP responses are cached in `pipeline/cache/` (gitignored), outputs are written
atomically, and per-species errors are logged and skipped, so re-running fills the gaps.

## Steps

| Step | Script | Output |
|---|---|---|
| `aco` | `steps/fetch_aco.py` | `data/sources/aco.json`: ACO checklist of Colombia (species list, status) |
| `ebird` | `steps/fetch_ebird.py` | `data/sources/ebird.json`: eBird/Clements taxonomy, names |
| `birdbase` | `steps/fetch_birdbase.py` | `data/sources/birdbase.json`: traits, elevation, habitats |
| `wikidata` | `steps/fetch_wikidata.py` | `data/sources/wikidata.json`: ids, ru/es names, P18 images, Commons category |
| `build` | `steps/build_species.py` | `data/species/*.json`, `species_index.json`, `families.json` (keeps `photos`, `texts`, `sounds` already in the species files and the index `photo`; family `names.ru` from `family_names`, null when Wikidata has only the Latin name) |
| `family_names` | `steps/fetch_family_names.py` | `data/sources/family_names.json`: Wikidata (QLever) item per family (`P225` + rank `P105 = Q35409`): labels ru/en/es, ru Wikipedia title. Run before `build` |
| `endemics` | `steps/fetch_endemics.py` | `data/sources/endemics.json`: Chaparro-Herrera et al. 2024 (Ornitología Colombiana 25, CC BY-NC 4.0) Anexo 3 XLSX from the journal site: 323 taxa with category endemic (E) / near_endemic (CE, CEa = marine/insular) / of_interest (EI) / insufficient_info (II), 2013 category, country and elevation-band codes; matched to ACO by scientific name (ACO, then eBird name), then `pipeline/mappings/endemics_names.json`; misses in `data/sources/endemics_unmatched.json`. Run before `build`, which sets `colombia.near_endemic` / `colombia.endemic_source` (ACO `endemic` unchanged) and writes `data/sources/endemics_report.md` (ACO vs Chaparro-Herrera endemics) |
| `wikipedia` | `steps/fetch_wikipedia.py` | `data/texts/<slug>.json`: en/es/ru extracts (CC BY-SA 4.0) |
| `photos` | `steps/fetch_photos.py` | `data/photos/<slug>.json`: up to 4 CC0/CC BY/CC BY-SA/PD candidates from Commons + iNaturalist (nothing downloaded) |
| `upload` | `steps/upload_media.py` | downloads the top candidates (1 per species, 4 for slugs in `data/focus_species.json`), makes 400/1000/1600px JPEGs, uploads to R2 as `photos/<slug>/<n>-{thumb,medium,large}.jpg`, writes `data/credits/<slug>.json` and `photos` in the species file right after each species, `photo` in `species_index.json` every 50 species and at the end. Focus species first, then alphabetical; progress line every 25 species. Photos already in R2 from the same source are not downloaded again, only their metadata is written back to `data/` (so a re-run restores a lost run quickly). `--dry-run` resizes only (files in `pipeline/cache/media/resized/`) |
| `sites` | `steps/build_sites.py` | `data/sites_resolved.json`, `data/focus_species.json`, `data/region_species.json` from hand-authored `data/sites.json` |
| `basemap` | `steps/build_basemap.py` | `site/src/generated/basemap.json`: static SVG base map for the route map (homepage) (land, Colombia outline, departments, rivers, place labels) clipped to `data/sites.json` ± 0.8°, from Natural Earth 1:10m (public domain). Needs shapely: `uv run --with shapely python run.py basemap`. Output is checked in; rerun after adding sites far from the current bbox |
| `gbif_sites` | `steps/fetch_gbif_sites.py` | `data/site_species.json`: likely species per site from GBIF occurrence counts (Aves, Colombia) within 7 km (`--radius`; doubled up to x4 for sites with < 1000 records, `--min-records`), species with >= 3 records (`--min-count`), two facet queries per site, all-year (`n`) and autumn Sep-Nov (`n_aut`, `month=9,11`), with `freq_aut` = n_aut / autumn total and `state` sure (>= 1%) / maybe (0.1-1%) / unlikely (< 0.1% or n_aut < 3); thresholds `SURE_FREQ`, `MAYBE_FREQ`, `MIN_N_AUT` and `likelihood()` in `common.py` (the only place); sorted by n_aut. GBIF keys not in `data/species/*.json` `ids.gbif` are matched by scientific name, then family + epithet (genus moves), then `pipeline/mappings/gbif_to_species.json` (lumps/splits); the rest go to `data/sources/gbif_sites_unmatched.json` |
| `study` | `steps/build_study_lists.py` | `data/study_lists.json`: per itinerary day, `species` = union of the day's sites' GBIF lists and highlights, each `{id, state, interesting, why, freq_aut, new_for_route}`: `state` = best across the day's sites (not in a site's GBIF list = unlikely; highlights are never dropped), `why` ⊆ highlight / endemic / range_restricted, `interesting` = bool(why), `new_for_route` = not sure/maybe on an earlier day. Sorted interesting first, then sure > maybe > unlikely, then `freq_aut`; no caps. Report (per-day counts): `data/sources/study_lists_report.md`. Run after `gbif_sites` and `sites` |
| `hotspots` | `steps/verify_hotspots.py` | `data/sources/hotspots_check.json`, `docs/research/hotspots-check.md`, `pipeline/mappings/hotspot_suggestions.json`: checks every `ebird_hotspots` id in `data/sites.json` via eBird `ref/hotspot/info` (`ok` = within 15 km of the site and the names share a meaningful token, else `suspect`; unknown id = `invalid`) and lists the 8 nearest hotspots (`ref/hotspot/geo`, 10 km, widened to 25/50 km if empty) with species counts. Reference data only, no observations. Never edits `sites.json`: apply suggestions by hand. Needs `EBIRD_API_KEY`; run in Actions |

Photo keys stored in `data/` are relative; the site prepends `PUBLIC_MEDIA_BASE_URL`.

## Selecting species

`--only slug ...` (on `run.py`) or the `ONLY_SLUGS` env var (space/comma separated) restricts
`wikipedia`, `photos` and `upload` to those species. Those scripts also accept slugs as positional args
when run directly (`upload_media.py --only slug ...`).

## Environment

Copy `.env.example` to `.env` (never commit it).

| Var | Used by |
|---|---|
| `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | `upload` (not needed with `--dry-run`) |
| `R2_CLOUDFLARE_TOKEN` | Cloudflare API (bucket settings, CORS); not used by the steps above |
| `XENO_CANTO_API_KEY` | sounds (xeno-canto API v3) |
| `EBIRD_API_KEY` | `hotspots` (eBird API 2.0 token) |
| `PUBLIC_MEDIA_BASE_URL` | site build only |
| `ONLY_SLUGS` | per-species steps, see above |
| `MAX_MINUTES` | time budget for the whole `run.py` process (`--max-minutes N` sets it): `wikipedia`, `photos`, `upload` finish the current species, write their outputs and stop with "stopped early after N minutes, resume by re-running"; exit code stays 0 |

## CI

`.github/workflows/pipeline.yml` (Actions → pipeline → Run workflow) takes `steps` (default
`wikipedia photos upload`) and optional `only` slugs, runs `run.py` with secrets `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, `R2_CLOUDFLARE_TOKEN`, `XENO_CANTO_API_KEY`, `EBIRD_API_KEY` and variable/secret `R2_ACCOUNT_ID`,
then commits changed files under `data/` (plus `docs/research/hotspots-check.md` and `pipeline/mappings/`) back to the branch it ran on. The API cache is kept between
runs with `actions/cache`. The run gets `MAX_MINUTES=270` (hard step timeout 300, job 330), so long runs
stop cleanly and the commit step always has time; re-dispatch to continue. The commit step prints
`git status`, commits only those paths, discards other tracked changes (e.g. `pipeline/uv.lock`), then
`git pull --rebase --autostash` + push, up to 3 attempts.

## Rate limits

- **Wikimedia (Wikipedia, Commons, Wikidata)** blocks shared/cloud IPs quickly (HTTP 403/429). Dev
  containers are often blocked outright; run the bulk `wikipedia` and `photos` steps in GitHub Actions.
  Requests are serial with >= 1 s spacing and `maxlag=5`. `fetch_photos.py` stops calling Commons after
  3 consecutive failures in a run and marks those species `sources_ok.commons: false`, so the next run
  retries only them (species with both sources OK are skipped unless `--refresh` or explicit slugs).
- **iNaturalist**: <= 60 req/min (we use 1.1 s spacing), < 10 000 req/day, media < 5 GB/hour.

Dispatch inputs: `steps`, `only`, and `queue` (`heavy` default; use `light` for quick steps such as hotspots, sites, family_names, gbif_sites, basemap so they do not wait behind multi-hour runs).
