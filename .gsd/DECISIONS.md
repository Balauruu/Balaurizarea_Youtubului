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
| D012 | M002/S01 | schema | shotlist.json schema | Single shotlist_type + building_block per shot (not Architecture.md's suggested_types array) | Cleaner downstream filtering — each shot routes to exactly one skill | No |
| D013 | M002/S01 | pattern | VISUAL_STYLE_GUIDE variability | CLI accepts --guide flag, defaults to first guide in context/visual-references/ | Orchestrator must work with any valid guide, not hardcode the Mexico cult guide's 25 blocks | No |
| D014 | M002/S02 | scope | Media source list | 7 sources: archive.org, Wikimedia, Pexels, Pixabay, Smithsonian, YouTube CC, direct URL. Drop DPLA (API 404) and Europeana (Cloudflare). | Supersedes D010 — 7 reliable sources exceeds 5-source success criterion. LOC deferred due to Cloudflare blocking. | Yes — sources added/removed based on reliability |
| D015 | M002/S02 | arch | License metadata location | In manifest.json asset entries, not separate source_licenses.json | Single source of truth — downstream skills only read manifest.json. Trivial to extract later if needed. | Yes |
| D016 | M002/S03 | pattern | Renderer signature contract | `render(shot: dict, output_dir: Path) → Path` for all renderers | Uniform interface enables registry-based routing. ComfyUI renderers (T02) will follow the same signature. | No |
| D017 | M002/S03 | pattern | Building block routing | Dict registry lookup (RENDERER_REGISTRY) with None → skip for ComfyUI blocks | Clean separation — Pillow blocks are registered at import time, unregistered blocks skip with message. T02 wires ComfyUI blocks into same registry. | No |
| D018 | M002/S03 | arch | ComfyUI communication | HTTP polling via GET /history/{prompt_id} instead of websockets | Avoids extra dependency (websocket-client), sufficient for batch generation — no real-time progress needed | No |
| D019 | M002/S03 | pattern | ComfyUI workflow template structure | Standard txt2img pipeline shared across all 4 templates — differentiation in prompt text and style modifiers only | Simpler maintenance, consistent node structure, style differences captured in prompts not graph topology | Yes — may need custom pipelines for complex compositions |
| D020 | M002/S03 | pattern | ComfyUI import strategy | Deferred import inside cmd_generate function body | Avoids import errors when ComfyUI package isn't needed (code-gen-only mode), keeps CLI responsive | No |
| D021 | M002/S04 | pattern | Remotion map props contract | `{variant, title, locations[{name,x,y}], connections[{from,to}], durationSeconds}` with normalized 0-1 coordinates | Python CLI writes props without knowing pixel dimensions; component handles coordinate conversion with padding. calculateMetadata derives frame count from durationSeconds. | No |
| D022 | M002/S04 | pattern | Single MapComposition with variant prop | One component + PALETTES lookup instead of 4 separate components | All variants share animation logic (spring markers, fade labels, draw arcs); only colors differ. Reduces duplication. | Yes — may split if variants diverge significantly |
| D023 | M002/S05 | pattern | Unmapped assets removed from manifest | _pool/ assets not tracked in manifest — outside pipeline scope | _pool/ is for manual editorial browsing; pipeline only tracks numbered assets | No |
| D024 | M002/S05 | pattern | Idempotent prefix strategy | Strip existing `\d{3}_` prefix then reapply, rather than skip-if-numbered | Handles re-runs where shotlist order changed — always produces correct numbering | No |
| D025 | M002/S06 | pattern | direct_url source search-as-URL | direct_url.search() returns query URL as SearchResult when query starts with http | Enables media_urls.md entries to flow through standard search→download pipeline without special-casing in acquire.py | No |
