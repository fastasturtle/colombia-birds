# Data pipeline

Builds everything under `data/` from open sources. Python deps are managed with uv:

```sh
cd pipeline
uv run python run.py                      # aco ebird birdbase wikidata build (default)
uv run python run.py wikipedia photos upload
uv run python run.py "photos upload" --only grallaria-milleri rupicola-peruvianus
uv run python steps/fetch_photos.py --limit 20     # any step can also run on its own
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
| `build` | `steps/build_species.py` | `data/species/*.json`, `species_index.json`, `families.json` (**recreates species files: run `upload` again afterwards to restore `photos`**) |
| `wikipedia` | `steps/fetch_wikipedia.py` | `data/texts/<slug>.json`: en/es/ru extracts (CC BY-SA 4.0) |
| `photos` | `steps/fetch_photos.py` | `data/photos/<slug>.json`: up to 4 CC0/CC BY/CC BY-SA/PD candidates from Commons + iNaturalist (nothing downloaded) |
| `upload` | `steps/upload_media.py` | downloads the top candidates (1 per species, 4 for slugs in `data/focus_species.json`), makes 400/1000/1600px JPEGs, uploads to R2 as `photos/<slug>/<n>-{thumb,medium,large}.jpg`, writes `data/credits/<slug>.json`, fills `photos` in species files and `photo` in `species_index.json`. `--dry-run` resizes only (files in `pipeline/cache/media/resized/`) |
| `sites` | `steps/build_sites.py` | `data/sites_resolved.json`, `data/focus_species.json`, `data/region_species.json` from hand-authored `data/sites.json` |
| `basemap` | `steps/build_basemap.py` | `site/src/generated/basemap.json`: static SVG base map for the route map (homepage) (land, Colombia outline, departments, rivers, place labels) clipped to `data/sites.json` ± 0.8°, from Natural Earth 1:10m (public domain). Needs shapely: `uv run --with shapely python run.py basemap`. Output is checked in; rerun after adding sites far from the current bbox |
| `gbif_sites` | `steps/fetch_gbif_sites.py` | `data/site_species.json`: likely species per site from GBIF occurrence counts (Aves, Colombia) within 12 km (`--radius`; doubled up to x4 for sites with < 1000 records, `--min-records`), species with >= 3 records (`--min-count`), sorted by records; one facet query per site. GBIF keys not in `data/species/*.json` `ids.gbif` are matched by scientific name, then family + epithet (genus moves), then `pipeline/mappings/gbif_to_species.json` (lumps/splits); the rest go to `data/sources/gbif_sites_unmatched.json` |

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
| `PUBLIC_MEDIA_BASE_URL` | site build only |
| `ONLY_SLUGS` | per-species steps, see above |

## CI

`.github/workflows/pipeline.yml` (Actions → pipeline → Run workflow) takes `steps` (default
`wikipedia photos upload`) and optional `only` slugs, runs `run.py` with secrets `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, `R2_CLOUDFLARE_TOKEN`, `XENO_CANTO_API_KEY` and variable/secret `R2_ACCOUNT_ID`,
then commits changed files under `data/` back to the branch it ran on. The API cache is kept between
runs with `actions/cache`.

## Rate limits

- **Wikimedia (Wikipedia, Commons, Wikidata)** blocks shared/cloud IPs quickly (HTTP 403/429). Dev
  containers are often blocked outright; run the bulk `wikipedia` and `photos` steps in GitHub Actions.
  Requests are serial with >= 1 s spacing and `maxlag=5`. `fetch_photos.py` stops calling Commons after
  3 consecutive failures in a run and marks those species `sources_ok.commons: false`, so the next run
  retries only them (species with both sources OK are skipped unless `--refresh` or explicit slugs).
- **iNaturalist**: <= 60 req/min (we use 1.1 s spacing), < 10 000 req/day, media < 5 GB/hour.
