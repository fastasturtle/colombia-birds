---
name: fact-check
description: Verify AI-written content in content/ (family/group portraits, species cards, comparisons) against the project's data and open sources; fix errors, flag what cannot be verified, record sources. Use for "проверь факты", "факт-чек", or before mass-publishing a content batch.
---

# Fact-check content

Argument: a path (`content/families/grallariidae.md`), a folder (`content/species/`), or a glob. Default: all
files changed since the last commit on `main`. Read AGENTS.md first. Never commit secrets; do not touch `data/`.
Unchecked species cards are listed in `docs/fact-check/INDEX.md`.

For large sets, fan out: one background Opus/Sonnet subagent per 5–10 files, each following this procedure,
then merge their reports. Keep the main thread for the summary.

## Sources, in order

1. Local first — settles most claims offline: `data/species/<slug>.json`, `data/species_index.json`,
   `data/texts/<slug>.json` (Wikipedia en/es/ru extracts), `data/site_species.json`, `data/itinerary.json`.
2. Live Wikipedia pages (en/es/ru) and eBird species pages (read-only, never copy text).
3. Birds of the World is paywalled: cite only what a search snippet shows, and say so ("BOW, по сниппету поиска").
4. xeno-canto needs an API key (`XENO_CANTO_API_KEY`); skip it if the key is not available.

Use WebFetch/WebSearch sparingly; cite URLs.

## Precedence

- `data/` (ACO 2022, BIRDBASE) is authoritative for status and endemism.
- For elevation and ranges, Colombia-specific figures from Wikipedia or literature may override global BIRDBASE
  numbers in the prose (name the source). `data/` is never edited; a data problem goes to `docs/TODO.md`.

## Procedure per file

0. **Taxonomy and subspecies.** Confirm the card's species and names against eBird/Clements 2025 (en) and attested
   Russian usage (ru.wikipedia, eBird ru). Identify the subspecies occurring on the route (southern Colombia,
   Bogotá area) and check the field marks for it. If the species itself is mismapped (e.g. a split), do not rewrite
   the card: flag it in the report and in `docs/TODO.md` for a pipeline mapping fix.
1. **Extract claims.** List every checkable statement: species counts ("32 колумбийских вида"), elevations,
   endemism, sizes/masses, colours and field marks, behaviour, voice, where on the route it occurs, named
   feeders/sites, historical facts, names (ru/en/latin spelling).
2. **Check against project data first**:
   - species list, status, endemism, IUCN: `data/species_index.json`, `data/species/<slug>.json` (`colombia.*`)
   - elevation, habitat, mass, diet: `data/species/<slug>.json` `traits.*` (BIRDBASE)
   - names: `names.*`, `data/families.json`, `data/sources/family_names.json`
   - where on the route: `data/site_species.json`, `data/sites_resolved.json` (`target_species`), `data/itinerary.json`
   - Wikipedia extracts: `data/texts/<slug>.json` (en/es/ru sections)
3. **Check external sources** (see Sources) only for claims the data cannot settle (field marks, voice,
   behaviour, history). Check every species listed in `similar` too, not only the card's own species:
   the "how it differs" phrases are where memory errors hide. Their Wikipedia extracts are local as well:
   `data/texts/<similar-slug>.json` exists for 1 901 of 1 966 species, so read those before any web lookup.
4. **Classify** each claim: ✅ confirmed · ✏️ corrected (say what and why) · ❓ unverifiable (keep only if
   harmless and phrased as tentative, else remove) · ❌ wrong → fix.
5. **Edit the file** in place: fix facts, keep the voice and length, do not rewrite style (that is `/polish`).
   Update frontmatter `sources:` with what you used (short labels + URLs). If the `en` mirror exists, apply
   the same correction there.
6. **Cross-file consistency**: species counts and names must match `data/`; Russian family names must
   match `data/families.json`; if a claim depends on the itinerary, check the dates/sites still exist.
7. **Mark as checked.** Set `checked: <today, YYYY-MM-DD>` in the card's frontmatter right after `lynx_page`,
   then run `python3 scripts/card_index.py` to refresh `docs/fact-check/INDEX.md`.

## Output

A markdown report (to chat, and append a dated section to `docs/fact-check-log.md`, creating the file if missing):
per file, the counts (claims / confirmed / corrected / removed / unverifiable) and a bullet per correction with the
source. Build (`cd site && npm run verify`) and commit `content/` + the log + INDEX.md
(`content: fact-check <scope>`) only when the caller asks. When running as a subagent, do not build: validate the
edited cards against the card validator rules (`site/src/lib/content.ts`, `content/README.md`: frontmatter
schema, `traits` vocabulary, `similar` ids exist and match `en.similar` order, `checked` is a valid date).

## Budget

Target 1–2 minutes per species card. Priority order: `similar` phrases → voice → elevation/range → names →
the rest. Everything else is checked against local `data/` only; go to the web only for the priority items and
only when the local Wikipedia extract does not settle them. Report corrections and removals with sources; do not
count or list confirmed claims one by one (a single total per card is enough).

## Rules

- Prefer removing a doubtful claim over keeping it; a field guide must not bluff.
- Never copy sentences from copyrighted guides (Lynx, Birds of the World, HBW); paraphrase facts only.
- Do not "fix" things that are matters of birder usage (e.g. slang «антпитты» next to the canonical name).
- Concurrency: if `git status` shows edits by others in your files, edit only your sentences and say so in the report.
