# Preferences

- Long research (web browsing, reading documents, multi-page lookups) must be delegated to a background subagent (Agent tool, run_in_background: true) so the conversation stays responsive. Do it in the main thread only for a single quick lookup.
- Long, well-defined operations (bulk fetching, scaffolding, refactors) go to Opus subagents with run_in_background: true. The same applies to small batches of UI fixes (2–5 tweaks at once): hand them to one Opus subagent with a precise list, verify its screenshots, then commit.

Project rules for agents: see AGENTS.md. Open work: docs/TODO.md.
