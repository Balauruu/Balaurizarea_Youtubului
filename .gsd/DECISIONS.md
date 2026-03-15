# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Database for competitor data | SQLite via stdlib sqlite3 | Queryable, handles growth, zero deps | No |
| D002 | M001 | pattern | CLI integration pattern | Context-loader (CLI prints data, Claude reasons) | Matches Architecture.md Rule 2, clean separation | No |
| D003 | M001 | arch | Research methodology | Two-pass (survey → deep dive) | Broad coverage first, then targeted depth | No |
| D004 | M001 | pattern | Style extraction approach | [HEURISTIC] skill, zero Python code | LLM reasoning more effective than NLP metrics | No |
| D005 | M001 | pattern | Source credibility tracking | Structured signals (no scalar scores) | Richer than numbers, matches dossier schema | No |
| D006 | M002 | arch | Animation framework | Remotion (Node.js) | Powerful React-based rendering, user preference despite Python-only constraint | Yes — if Python alternative proves sufficient |
| D007 | M002 | arch | Graphics generation strategy | Hybrid: code-gen (Pillow/Cairo) + ComfyUI | Code-gen for constrained flat graphics (reliable, repeatable), ComfyUI for creative assets (artistic interpretation) | Yes — boundary between code-gen and ComfyUI may shift |
| D008 | M002 | arch | Asset delivery format | Raw assets, no pre-styling | Editor controls final look in DaVinci Resolve | No |
| D009 | M002 | scope | Text overlays | Shotlist entries only, no generated assets | Editor places text elements in DaVinci with proper fonts/styles | No |
| D010 | M002 | arch | Media source strategy | 10+ free sources (archive.org, LOC, Wikimedia, Pexels, Pixabay, Smithsonian, DPLA, Europeana, YouTube CC, crawl4ai) | More sources = better coverage, fewer gaps for generators | Yes — sources may be added/removed based on reliability |
| D011 | M002 | arch | Pipeline coordination artifact | manifest.json at assets/ root | Central state tracking for all Phase 2 agents, gap lifecycle | No |
