---
name: fact-check
description: Verify AI-written content in content/ (family/group portraits, species cards, comparisons) against the project's data and open sources; fix errors, flag what cannot be verified, record sources. Use for "проверь факты", "факт-чек", or before mass-publishing a content batch.
---

# Fact-check content

Argument: a path (`content/families/grallariidae.md`), a folder (`content/species/`), or a glob. Default: all
files changed since the last commit on `main`. Read AGENTS.md first. Never commit secrets; do not touch `data/`.

For large sets, fan out: one background Opus/Sonnet subagent per 5–10 files, each following this procedure,
then merge their reports. Keep the main thread for the summary.

## Procedure per file

1. **Extract claims.** List every checkable statement: species counts ("32 колумбийских вида"), elevations,
   endemism, sizes/masses, colours and field marks, behaviour, voice, where on the route it occurs, named
   feeders/sites, historical facts, names (ru/en/latin spelling).
2. **Check against project data first** (authoritative for this site):
   - species list, status, endemism, IUCN: `data/species_index.json`, `data/species/<slug>.json` (`colombia.*`)
   - elevation, habitat, mass, diet: `data/species/<slug>.json` `traits.*` (BIRDBASE)
   - names: `names.*`, `data/families.json`, `data/sources/family_names.json`
   - where on the route: `data/site_species.json`, `data/sites_resolved.json` (`target_species`), `data/itinerary.json`
   - Wikipedia extracts: `data/texts/<slug>.json` (en/es/ru sections)
3. **Check external sources** only for claims the data cannot settle (field marks, voice, behaviour,
   history): Wikipedia en/es, xeno-canto recording notes, trip reports, Cornell eBird species pages
   (read-only, no copying of text). Use WebFetch/WebSearch sparingly; cite URLs.
4. **Classify** each claim: ✅ confirmed · ✏️ corrected (say what and why) · ❓ unverifiable (keep only if
   harmless and phrased as tentative, else remove) · ❌ wrong → fix.
5. **Edit the file** in place: fix facts, keep the voice and length, do not rewrite style (that is `/polish`).
   Update frontmatter `sources:` with what you used (short labels + URLs). If the `en` mirror exists, apply
   the same correction there.
6. **Cross-file consistency**: species counts and names must match `data/`; Russian family names must
   match `data/families.json`; if a claim depends on the itinerary, check the dates/sites still exist.

## Output

A markdown report (to chat, and append a dated section to `docs/fact-check-log.md`): per file, the counts
(claims / confirmed / corrected / removed / unverifiable) and a bullet per correction with the source.
Then build the site (`cd site && npm run build`) and commit `content/` + the log with message
`content: fact-check <scope>`.

## Rules

- Prefer removing a doubtful claim over keeping it; a field guide must not bluff.
- Never copy sentences from copyrighted guides (Lynx, Birds of the World, HBW); paraphrase facts only.
- Do not "fix" things that are matters of birder usage (e.g. slang «антпитты» next to the canonical name).
