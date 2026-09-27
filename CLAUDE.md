# Preferences

- Long research (web browsing, reading documents, multi-page lookups) must be delegated to a background subagent (Agent tool, run_in_background: true) so the conversation stays responsive. Do it in the main thread only for a single quick lookup.
- Instructions to subagents are written in English (content they produce stays Russian + English per the site conventions).
- Subagents that edit files run with `isolation: "worktree"` so the main working tree stays clean for the lead to commit and merge independently; tell them to run `npm ci` in site/ (and `uv sync` in pipeline/ if needed) first, and merge their branch when they report. Read-only agents (research, review) do not need a worktree.
- Long, well-defined operations (bulk fetching, scaffolding, refactors) go to Opus subagents with run_in_background: true. The same applies to UI fixes, even single small ones: hand them to an Opus subagent with a precise list, verify its screenshots, then commit. The lead session only plans, reviews, commits, deploys and talks to the owner; it does not edit site/pipeline code itself.

Project rules for agents: see AGENTS.md. Open work: docs/TODO.md.
