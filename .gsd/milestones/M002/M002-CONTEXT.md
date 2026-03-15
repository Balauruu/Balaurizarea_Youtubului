# M002: Asset Pipeline — Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

## Project Description

Complete the documentary video pipeline by building 5 new skills that take a narrated Script.md and produce an organized, numbered asset folder ready for DaVinci Resolve editing. Each skill is built using the skill-creator methodology with full SKILL.md, CONTEXT.md, scripts, prompts, and tests.

## Why This Milestone

M001 delivered the narrative pipeline (competitor analysis → research → script). The output is a polished narrated script, but no visual assets. Without M002, the user must manually search for footage, create graphics, build maps, and organize everything — the most time-consuming part of documentary production.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run the Visual Orchestrator on any Script.md + VISUAL_STYLE_GUIDE → get shotlist.json
- Run Media Acquisition on shotlist.json → get downloaded assets with manifest and gap analysis
- Run Graphics Generator on gaps → get code-gen and ComfyUI-generated assets
- Run Animation skill on map/diagram entries → get rendered .mp4 clips
- Run Asset Manager → get numbered, organized asset folder ready for DaVinci

### Entry point / environment

- Entry point: Claude Code skill invocations (same pattern as M001 agents)
- Environment: local dev (Windows), ComfyUI local server, Node.js for Remotion
- Live dependencies involved: ComfyUI (local), Remotion (local Node.js), archive.org API, LOC API, Wikimedia Commons API, Pexels API, Pixabay API, Smithsonian API, YouTube (yt-dlp)

## Completion Class

- Contract complete means: each skill has tests proving its deterministic code works, and SKILL.md + CONTEXT.md are complete
- Integration complete means: the 5 skills can be invoked in sequence on a real project and produce a valid organized asset folder
- Operational complete means: none (on-demand pipeline, not a service)

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Full pipeline on the Duplessis Orphans project: Script.md → shotlist.json → acquired assets → generated graphics → animations → numbered organized folder with manifest
- manifest.json accurately reflects all assets, shot mappings, and gap status
- At least one asset from each category exists (archival, generated graphic, animation)

## Risks and Unknowns

- **Media source API availability** — Free APIs may rate-limit, require keys, or change. Multiple sources provide redundancy.
- **ComfyUI workflow reliability** — Z-image-turbo prompt engineering for specific visual styles (silhouettes on red backgrounds, ritual illustrations) may need iteration
- **Remotion setup complexity** — Node.js project scaffold + composition templates must be created and maintained alongside Python pipeline
- **Asset-to-shot matching quality** — [HEURISTIC] matching depends on Claude's ability to evaluate visual relevance from descriptions
- **Source licensing verification** — Automated scraping must respect license terms; some "free" sources have attribution requirements

## Existing Codebase / Prior Art

- `.claude/skills/visual-style-extractor/` — Reference for skill structure (6-stage pipeline, CONTEXT.md, SKILL.md, scripts/)
- `.claude/skills/writer/` — Reference for context-loader CLI pattern
- `.claude/skills/researcher/` — Reference for crawl4ai scraping patterns, tier-based retry
- `.claude/skills/crawl4ai-scraper/` — Utility scraper (domain-isolated browser contexts)
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — The decision framework the Visual Orchestrator applies
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md` — Test input for the pipeline
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/research/media_urls.md` — Media URLs from research (input to acquisition)
- `Architecture.md` — Loose pipeline spec (treated as guidance, not strict spec)

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001-R011 — All active requirements are owned by M002 slices
- R019 (media_urls.md) — Validated in M001, provides input to Media Acquisition

## Scope

### In Scope

- 5 new skills: visual-orchestrator, media-acquisition, graphics-generator, animation, asset-manager
- Each skill: SKILL.md, CONTEXT.md, scripts/, prompts/ (where applicable), tests
- Manifest.json as coordination artifact between all Phase 2 skills
- shotlist.json as output of Visual Orchestrator, input to all downstream skills
- Multi-source media acquisition (archive.org, LOC, Wikimedia, Pexels, Pixabay, Smithsonian, DPLA, Europeana, YouTube CC)
- Code-generated flat graphics (Pillow/Cairo/SVG) for constrained visual building blocks
- ComfyUI integration for creative/artistic asset generation
- Remotion compositions for animated maps and diagrams
- Asset numbering, consolidation, and _pool/ sorting

### Out of Scope / Non-Goals

- Pre-styling assets (film grain, sepia, CRT effects) — editor's domain
- Text overlay asset generation — editor places these in DaVinci
- DaVinci Resolve timeline/EDL export — deferred to future milestone
- Automated asset quality scoring — human review sufficient initially
- Audio/voiceover generation — not in this pipeline

## Technical Constraints

- Python for all scripting except Remotion (Node.js exception)
- No LLM API wrappers — Claude Code runtime handles all reasoning
- ComfyUI runs locally with Z-image-turbo model (open to other models)
- All media must be free: public domain, CC0, or Creative Commons
- Skill-creator methodology for building each skill
- Assets delivered raw — no post-production effects

## Integration Points

- **ComfyUI** — Local server at 127.0.0.1:8188, REST API for queuing prompts and downloading images
- **Remotion** — Node.js project with React compositions, rendered via `npx remotion render` subprocess
- **archive.org** — `internetarchive` Python library for search and download
- **LOC** — JSON API at loc.gov/search for photos, maps, documents
- **Wikimedia Commons** — MediaWiki API for image/video search
- **Pexels** — REST API (requires free API key, 200 req/hr)
- **Pixabay** — REST API (requires free API key)
- **Smithsonian** — Open Access API at api.si.edu (requires free API key)
- **YouTube** — yt-dlp for CC-licensed footage download
- **crawl4ai** — Web scraping for sources without APIs

## Open Questions

- Exact Remotion composition templates needed — will be determined during S04 planning based on VISUAL_STYLE_GUIDE map building blocks
- Which ComfyUI workflows/LoRAs produce best results for each building block type — will be iterated during S03
- Pexels/Pixabay API key setup — will use secure_env_collect during S02 execution
