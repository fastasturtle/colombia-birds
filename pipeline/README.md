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

To reuse the HTTP cache of CI runs locally (needs the R2 vars in `.env`):

```sh
uv run python cache_sync.py pull           # download cached responses missing locally
uv run python cache_sync.py push           # upload yours (incremental); add --dry-run to see the plan
```

## Steps

| Step | Script | Output |
|---|---|---|
| `aco` | `steps/fetch_aco.py` | `data/sources/aco.json`: ACO checklist of Colombia (species list, status) |
| `ebird` | `steps/fetch_ebird.py` | `data/sources/ebird.json`: eBird/Clements taxonomy, names |
| `birdbase` | `steps/fetch_birdbase.py` | `data/sources/birdbase.json`: traits, elevation, habitats |
| `wikidata` | `steps/fetch_wikidata.py` | `data/sources/wikidata.json`: ids, ru/es names, P18 images, Commons category (QLever). Matched by eBird code (P3444), then P225. When the code sits on a subspecies item (trinomial P225, no sitelinks), the species item is used instead: the eBird name by P225, else the parent taxon (P171) or the trinomial's first two words, only with the eBird epithet (`matched_by: ebird_code_subspecies->species/parent/binomial`, `subspecies_qid`/`subspecies_sci` kept, missing eBird/iNat/Avibase ids taken from the subspecies) |
| `build` | `steps/build_species.py` | `data/species/*.json`, `species_index.json`, `families.json` from `common.checklist()` (see *Species list and taxonomy mappings*; ru names: eBird `locale=ru`, else the Wikidata ru label, else the ru.wikipedia article title when Cyrillic (disambiguation «(птица)» stripped, `name_ru_source: "ruwiki"`), then `mappings/names_ru_overrides.json`) (keeps `photos`, `texts`, `sounds` already in the species files and the index `photo`, carried to a renamed slug per `mappings/clements2025.json`; family `names.ru` from `family_names`, null when Wikidata has only the Latin name) |
| `family_names` | `steps/fetch_family_names.py` | `data/sources/family_names.json`: Wikidata (QLever) item per family (`P225` + rank `P105 = Q35409`): labels ru/en/es, ru Wikipedia title. Run before `build` |
| `endemics` | `steps/fetch_endemics.py` | `data/sources/endemics.json`: Chaparro-Herrera et al. 2024 (Ornitología Colombiana 25, CC BY-NC 4.0) Anexo 3 XLSX from the journal site: 323 taxa with category endemic (E) / near_endemic (CE, CEa = marine/insular) / of_interest (EI) / insufficient_info (II), 2013 category, country and elevation-band codes; matched to ACO by scientific name (ACO, then eBird name), then `pipeline/mappings/endemics_names.json`; misses in `data/sources/endemics_unmatched.json`. Run before `build`, which sets `colombia.near_endemic` / `colombia.endemic_source` (ACO `endemic` unchanged) and writes `data/sources/endemics_report.md` (ACO vs Chaparro-Herrera endemics) |
| `wikipedia` | `steps/fetch_wikipedia.py` | `data/texts/<slug>.json`: en/es/ru extracts (CC BY-SA 4.0) |
| `photos` | `steps/fetch_photos.py` | `data/photos/<slug>.json`: up to 4 CC0/CC BY/CC BY-SA/PD candidates from Commons + iNaturalist (nothing downloaded) |
| `upload` | `steps/upload_media.py` | downloads the top candidates (1 per species, 4 for slugs in `data/focus_species.json`), makes 400/1000/1600px JPEGs, uploads to R2 as `photos/<slug>/<n>-{thumb,medium,large}.jpg`, writes `data/credits/<slug>.json` and `photos` in the species file right after each species, `photo` in `species_index.json` every 50 species and at the end. Focus species first, then alphabetical; progress line every 25 species. Photos already in R2 from the same source are not downloaded again, only their metadata is written back to `data/` (so a re-run restores a lost run quickly). `--dry-run` resizes only (files in `pipeline/cache/media/resized/`). `--from-credits` is offline: refills empty `photos` (and the index `photo`) from `data/credits/<slug>.json` (`uv run python steps/upload_media.py --from-credits [--only slug ...]`, then `build`) |
| `sites` | `steps/build_sites.py` | `data/sites_resolved.json`, `data/focus_species.json`, `data/region_species.json` from hand-authored `data/sites.json` (fields pass through; `"optional": true` marks a site outside the group tour, a possible own trip from Bogotá with no itinerary days, shown separately on the site) |
| `basemap` | `steps/build_basemap.py` | `site/src/generated/basemap.json`: static SVG base map for the route map (homepage) (land, Colombia outline, departments, rivers, place labels) clipped to `data/sites.json` ± 0.8°, from Natural Earth 1:10m (public domain). Needs shapely: `uv run --with shapely python run.py basemap`. Output is checked in; rerun after adding sites far from the current bbox |
| `gbif_sites` | `steps/fetch_gbif_sites.py` | `data/site_species.json`: likely species per site from GBIF occurrence counts (Aves, Colombia) within 7 km (`--radius`; doubled up to x4 for sites with < 1000 records, `--min-records`), species with >= 3 records (`--min-count`), two facet queries per site, all-year (`n`) and autumn Sep-Nov (`n_aut`, `month=9,11`), with `freq_aut` = n_aut / autumn total and `state` sure (>= 1%) / maybe (0.1-1%) / unlikely (< 0.1% or n_aut < 3); thresholds `SURE_FREQ`, `MAYBE_FREQ`, `MIN_N_AUT` and `likelihood()` in `common.py` (the only place); sorted by n_aut. GBIF keys not in `data/species/*.json` `ids.gbif` are matched by scientific name, then family + epithet (genus moves), then `pipeline/mappings/gbif_to_species.json` (lumps/splits); the rest go to `data/sources/gbif_sites_unmatched.json` |
| `study` | `steps/build_study_lists.py` | `data/study_lists.json`: per itinerary day, `species` = union of the day's sites' GBIF lists and highlights, each `{id, state, interesting, why, freq_aut, new_for_route}`: `state` = best across the day's sites (not in a site's GBIF list = unlikely; highlights are never dropped), `why` ⊆ highlight / endemic / range_restricted, `interesting` = bool(why), `new_for_route` = not sure/maybe on an earlier day. Sorted interesting first, then sure > maybe > unlikely, then `freq_aut`; no caps. Report (per-day counts): `data/sources/study_lists_report.md`. Run after `gbif_sites` and `sites` |
| `lynx` | `steps/build_lynx.py` | Page numbers in the Lynx field guide *Birds of Colombia* (Steven L. Hilty 2021, Lynx and BirdLife International Field Guides, Lynx Edicions; the tour group's book) from the owner's photos of its index, transcribed by Claude agents into `pipeline/sources/lynx/` (`index/p559.txt`…`p590.txt`, `spanish_index/p591.txt`, `references.txt`, `family_index.txt`, `p604_fragment.txt`). Writes `data/sources/lynx_index.json` (every index entry: `kind` sci / genus / family / en_group / en / other, page ranges, `first_page`; the current bold heading carries across columns and pages), `lynx_references.json`, `lynx_families.json`, and `data/lynx_pages.json` (`{slug: {page, sci, en, conflict}}`): scientific name exact, then `pipeline/mappings/lynx_names.json` (`{"<site sci>": "<book sci or English name>"}`), then the same epithet within the family (genus moves, `via: "epithet"`); English name normalised (case, hyphens, spaces, apostrophes, diacritics, grey/gray etc.), eBird name then ACO's. Misses in `data/sources/lynx_unmatched.json`; counts, conflicts, unmatched by family and near-miss suggestions in `data/sources/lynx_report.md`. Run after `build`, then `build` again, which writes `book.lynx_page` / index `lynx_page` / family `lynx_page`: `uv run python run.py lynx build`. Parser tests: `uv run python tests/test_build_lynx.py` |
| `hotspots` | `steps/verify_hotspots.py` | `data/sources/hotspots_check.json`, `docs/research/hotspots-check.md`, `pipeline/mappings/hotspot_suggestions.json`: checks every `ebird_hotspots` id in `data/sites.json` via eBird `ref/hotspot/info` (`ok` = within 15 km of the site and the names share a meaningful token, else `suspect`; unknown id = `invalid`) and lists the 8 nearest hotspots (`ref/hotspot/geo`, 10 km, widened to 25/50 km if empty) with species counts. Reference data only, no observations. Never edits `sites.json`: apply suggestions by hand. Needs `EBIRD_API_KEY`; run in Actions |

Photo keys stored in `data/` are relative; the site prepends `PUBLIC_MEDIA_BASE_URL`.

## Species list and taxonomy mappings

Base list = ACO 2022, names and splits = eBird/Clements 2025 (`docs/DECISIONS.md` row 19). Every step that
reads the list (`ebird`, `birdbase`, `wikidata`, `build`) goes through `common.checklist()`: the ACO records of
`data/sources/aco.json` (`source: "aco2022"`) plus the Clements 2025 species ACO lacks. Species files and
index entries carry that `source`.

| Mapping | Used by | What |
|---|---|---|
| `mappings/aco_to_ebird.json` | `ebird`, `wikidata`, `birdbase`, `build` | ACO name -> eBird species when the names differ. Also whole-species remaps after eBird splits where the Colombian population is the other half (ACO *Numenius phaeopus* -> *N. hudsonicus*, *Heliangelus amethysticollis* -> *H. clarisse*, *Myiothlypis chrysogaster* -> *M. chlorophrys*, *Atlapetes tricolor* -> *A. crassus*, *Rallus limicola* -> *R. aequatorialis*, and 20 more from the 27.09 audit, e.g. *Troglodytes aedon* -> *T. musculus*, *Tyto alba* -> *T. furcata*, *Oxyura jamaicensis* -> *O. ferruginea*; the full list is `renamed` in `clements2025.json`): the slug follows the eBird name. How to decide: eBird records in Colombia per department (GBIF eBird dataset, `verbatimScientificName` facet under the ACO species' GBIF key) and the Lynx book index (Hilty 2021 already splits most of these). `wikidata` then never uses the ACO name (or an item found by a reused eBird code whose `P225` is another species) for these taxa, and `build` ignores a `wikidata.json` item still matched to the ACO name or one of its subspecies (the extralimital half) until `wikidata` re-runs |
| `mappings/clements2025.json` | `common.checklist()`, `build` | `species`: Clements 2025 species absent from ACO but recorded at route sites (`split_from`, status, `endemic`, GBIF key, note), added with `source: "clements2025"` (family/order from the parent; `taxonomy_note` explains the split). `renamed`: one-off old slug -> new slug for the remaps above (`aco`: the ACO name when it is not the old slug, e.g. *Phyllomyias burmeisteri* -> old slug `acrochordopus-burmeisteri`; `why`: why photos are not carried); with `carry: true` `build` moves `photos`/`sounds`/`texts` of the old species file to the new slug (when the new one has none yet) |
| `mappings/aco_fixes.json` | `common.checklist()` | field corrections to the ACO archive (e.g. the swapped `name_en_aco` of *Grallaria saturata* / *G. saltuensis*; `status` of *Oxyura jamaicensis* and *Setophaga petechia*, whose ACO boreal-migrant status belongs to the other half of the split) |
| `mappings/names_ru_overrides.json` | `build` | `{slug: {ru, source}}` applied after eBird ru, the Wikidata label and the ru.wikipedia title, and wins over all of them (`ru: null` removes a name): only attested names (eBird typos fixed, ru.wikipedia article titles). All ru names are also normalised in code: first letter upper case, names without Cyrillic (Latin labels) dropped |
| `mappings/gbif_to_species.json` | `gbif_sites` | GBIF backbone name -> slug for lumps/misapplied names |
| `mappings/gbif_region_splits.json` | `gbif_sites` | `{from_slug: {to_slug: [regions]}}` for splits GBIF keeps under one species key (*Dacnis lineata* / *D. egregia*, *Grallaria quitensis* / *G. alticola*, and since the 27.09 audit the west-of-Andes vs Amazonian pairs such as *Automolus subulatus* / *A. virgatus*, *Myiopagis cinerea* / *M. parambae*, coast vs inland *Setophaga petechia* / *S. aestiva*; also a split into an existing ACO species: *Trogon rufus* records on the Pacific slope -> *T. cupreicauda*): the route site's `region` decides. The added species' names are usually not separate GBIF species (GBIF keeps them as subspecies), so their `gbif_key` in `clements2025.json` is null and only this mapping sends records to them |

## Selecting species

`--only slug ...` (on `run.py`) or the `ONLY_SLUGS` env var (space/comma separated) restricts
`wikipedia`, `photos` and `upload` to those species. Those scripts also accept slugs as positional args
when run directly (`upload_media.py --only slug ...`).

## Environment

Copy `.env.example` to `.env` (never commit it).

| Var | Used by |
|---|---|
| `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | `upload` (not needed with `--dry-run`), `cache_sync.py` |
| `R2_CLOUDFLARE_TOKEN` | Cloudflare API (bucket settings, CORS); not used by the steps above |
| `XENO_CANTO_API_KEY` | sounds (xeno-canto API v3) |
| `EBIRD_API_KEY` | `hotspots` (eBird API 2.0 token) |
| `PUBLIC_MEDIA_BASE_URL` | site build only |
| `ONLY_SLUGS` | per-species steps, see above |
| `MAX_MINUTES` | time budget for the whole `run.py` process (`--max-minutes N` sets it): `wikipedia`, `photos`, `upload` finish the current species, write their outputs and stop with "stopped early after N minutes, resume by re-running"; exit code stays 0 |

## CI

`.github/workflows/pipeline.yml` (Actions → pipeline → Run workflow) takes `steps` (default
`wikipedia photos upload`) and optional `only` slugs, runs `run.py` with secrets `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, `R2_CLOUDFLARE_TOKEN`, `XENO_CANTO_API_KEY`, `EBIRD_API_KEY` and variable/secret
`R2_ACCOUNT_ID`, and commits changed files under `data/` (plus `docs/research/hotspots-check.md` and
`pipeline/mappings/`) back to the branch it ran on. The run gets `MAX_MINUTES=270` (hard step timeout 300,
job 330), so long runs stop cleanly and the final commit always has time; re-dispatch to continue.

- **HTTP cache in R2.** `cache_sync.py pull` before the run, `push` every 20 minutes and at the end
  (`if: always()`). Objects live under `cache/http/<relpath>` in the media bucket (everything in
  `pipeline/cache/` except `media/`, dotfiles and `*.tmp`), with a manifest `cache/http/_manifest.json`
  (`{relpath: {sha1, size}}`) so pull/push never list thousands of keys (they list once if the manifest
  is missing). Incremental: pull downloads only files missing locally, push uploads only new/changed
  ones (local sha1s memoised in `pipeline/cache/.sync_hashes.json`). Nothing is ever deleted.
  **The bucket is public (r2.dev), so `cache/http/` is world-readable.** It holds only bodies of public
  API responses (file names are sha1 hashes of request URLs; the eBird key goes in a header and is not
  stored); never cache anything secret or private.
- **Progress commits.** `ci_run.sh` runs `run.py` in the background and every 20 minutes calls
  `ci_commit.sh` ("data: pipeline progress (<steps>)", then `deploy.yml` is dispatched when on `main`)
  and `cache_sync.py push`; a failed flush only warns, the pipeline keeps running. The loop ends when
  `run.py` exits (cancel is forwarded to it as SIGTERM). The final "Commit data changes" step runs the
  same `ci_commit.sh` once more ("data: pipeline run (<steps>)"), so a cancelled or crashed run loses at
  most ~20 minutes of work.
- **`ci_commit.sh`** never touches the working tree, HEAD or index of the checkout (run.py is still
  writing there): it fetches the branch, loads its tip into a temporary index, stages the paths that
  differ from the start commit (modified, new, deleted), commits that tree on top of the remote tip and
  pushes, 3 attempts. No rebase, so no conflicts with commits pushed meanwhile (the light queue, the
  owner, an earlier flush); a file changed by both keeps this run's version, except `data/species/*.json`
  and `data/species_index.json`, which `ci_merge_json.py` (stdlib only) merges 3-way with `BASE_SHA` as
  the base: the remote file plus the top-level keys (species) or per-`id` entry fields (index) this run
  changed, this run winning on a key changed by both. Two runs started from the same commit rewrite those
  files (light `build`, heavy `upload`); on 27.09.2026 whole-file commits wiped `photos` of 4 species and
  the Wikipedia links / ids of 34. Files deleted by the run, new ones and ones unchanged upstream keep the
  default. Tests: `uv run python tests/test_ci_merge_json.py` (incl. an end-to-end run of `ci_commit.sh`
  against a temporary bare repo). Other touched files
  (`pipeline/uv.lock`, `site/`) are never committed. All pipeline writes are atomic (tmp + rename,
  `common.atomic_write` / `write_json` / `write_text`), so a snapshot never holds a half-written file;
  `*.tmp` is gitignored.

- **Live status.** GitHub shows a job's log only after it ends, so progress is published separately.
  Every progress line of `run.py` (step started/finished/failed, the periodic `wikipedia`/`photos`/`upload`
  lines, their final summaries, "stopped early") also goes through `common.status()`, which rewrites
  `pipeline/cache/status.json` atomically: `{run_id (GITHUB_RUN_ID or "local"), steps, step, done, total,
  message, elapsed, started, updated (ISO UTC), history (last 20 lines)}`. `ci_run.sh` uploads it every
  60 s (`STATUS_SECONDS`) with `cache_sync.py status` to R2 `status/pipeline.json` (no-cache), once more
  when `run.py` exits (message + "(finished)" / "(exit N)") and in the final commit step
  ("(finished: run <outcome>, commit exit N)"). The Python process itself never talks to R2 for this.

  ```sh
  curl -s https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev/status/pipeline.json
  ```

  Locally the same file is written with no upload: `cat pipeline/cache/status.json` (or
  `watch -n 30 cat pipeline/cache/status.json`) during e.g. `run.py photos --max-minutes 30`;
  `cache_sync.py status --dry-run` prints what would be uploaded. `cache_sync.py push/pull` skip it.

## Rate limits

- **Wikimedia (Wikipedia, Commons, Wikidata)** blocks shared/cloud IPs quickly (HTTP 403/429). Dev
  containers are often blocked outright; run the bulk `wikipedia` and `photos` steps in GitHub Actions.
  Requests are serial with >= 1 s spacing and `maxlag=5`. `fetch_photos.py` stops calling Commons after
  3 consecutive failures in a run and marks those species `sources_ok.commons: false`, so the next run
  retries only them (species with both sources OK are skipped unless `--refresh` or explicit slugs).
- **iNaturalist**: <= 60 req/min (we use 1.1 s spacing), < 10 000 req/day, media < 5 GB/hour.

Dispatch inputs: `steps`, `only`, and `queue` (`heavy` default; use `light` for quick steps such as hotspots, sites, family_names, gbif_sites, basemap so they do not wait behind multi-hour runs).
