---
name: polish
description: Copy-edit AI-written content in content/ for style, terminology and length without changing facts. Use for "причеши", "отредактируй стиль", "выровняй терминологию", or after a fact-check pass.
---

# Polish content

Argument: a path, folder or glob under `content/` (default: files changed since the last `main` commit).
Read AGENTS.md and `content/README.md` (schema) first. Run `/fact-check` before this when facts are in doubt;
this skill never changes facts, numbers, names or claims.

Fan out one background subagent per 10–20 files for large sets (Sonnet is enough here).

## Style guide (Russian, the primary language)

- Voice: friendly field guide, precise, second person singular («смотри на…») is fine; no exclamation marks,
  no marketing adjectives («потрясающий»), no AI filler («стоит отметить», «важно понимать»).
- Length: family/group portraits 120–220 words body; species cards 60–120 words body; bullets ≤ 20 words.
- Terminology, fixed spellings: антпитта (жаргон, всегда рядом с каноническим названием при первом
  упоминании), тапакуло, танагра, котинга, манакин, колибри, парамо, облачный лес, предгорья, кормушка,
  микст-флок (смешанная стая), лек (ток), подлесок, кроны, эндемик, почти-эндемик, залётный, мигрант.
  Elevations «1 800–3 150 м» (thin space or normal space as thousands separator, en dash range).
  Species names in text: English name as in `data/species_index.json` (link-friendly), Latin in italics only
  when needed for disambiguation, Russian name from `names.ru` when it exists.
- Structure: bullets in `recognize` start with the feature, not with «у птицы…»; `confusable.how` contrasts
  in one sentence («мельче, хвост вверх, бегает как мышь»); `route_note` names sites and days explicitly.
- Keep the `en` mirror in sync: same meaning, natural English birding usage (e.g. "antpitta", "mixed flock",
  "lek"), same length class.

## Procedure

1. Read the file, fix style per the guide, keep every fact intact (diff should show wording only).
2. Validate frontmatter against `content/README.md`; fix key names and types.
3. `cd site && npm run build` after editing a batch; look at one page via `npm run shots`.
4. Commit `content/` with message `content: polish <scope>`; report the list of files and notable changes in
   under 200 words.
