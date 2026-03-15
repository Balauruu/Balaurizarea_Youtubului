# M002: Asset Pipeline

**Vision:** Complete the documentary pipeline from narrated script to organized, numbered visual asset folder ready for DaVinci Resolve editing. Five new skills — visual orchestrator, media acquisition, graphics generator, animation, and asset manager — transform Script.md into a production-ready asset folder via shotlist.json and manifest.json coordination.

## Success Criteria

- Visual Orchestrator produces valid shotlist.json from any Script.md + VISUAL_STYLE_GUIDE combination
- Media Acquisition downloads assets from at least 5 different free sources and produces manifest.json with shot mappings
- Graphics Generator produces code-gen flat graphics and ComfyUI creative assets that fill manifest gaps
- Animation skill renders at least one animated map as .mp4 via Remotion
- Asset Manager produces numbered files in type folders with consolidated manifest and _pool/ for unmatched
- Full pipeline runs end-to-end on Duplessis Orphans project producing a complete organized asset folder

## Key Risks / Unknowns

- **Media source API reliability** — Free APIs rate-limit and change; multiple sources provide redundancy
- **ComfyUI prompt engineering** — Z-image-turbo producing specific visual styles (silhouettes, ritual illustrations) may need iteration
- **Remotion scaffold** — Node.js project setup + composition templates alongside Python pipeline
- **Asset-to-shot matching** — [HEURISTIC] quality depends on Claude evaluating visual relevance from text descriptions

## Proof Strategy

- Media source API reliability → retire in S02 by proving downloads from 5+ sources with rate limiting and fallback
- ComfyUI prompt engineering → retire in S03 by proving at least 3 building block types render correctly
- Remotion scaffold → retire in S04 by proving a map composition renders to .mp4 from Python subprocess
- Asset-to-shot matching → retire in S02 by proving gap analysis correctly identifies unmatched shots

## Verification Classes

- Contract verification: pytest tests for all deterministic code (CLI, file ops, manifest handling, API clients)
- Integration verification: full pipeline on real project (Duplessis Orphans), ComfyUI renders, Remotion renders
- Operational verification: none (on-demand pipeline)
- UAT / human verification: visual quality of generated assets, completeness of organized folder

## Milestone Definition of Done

This milestone is complete only when all are true:

- All 5 skills have SKILL.md, CONTEXT.md, scripts, and passing tests
- shotlist.json schema is stable and consumed by all downstream skills
- manifest.json tracks all assets with shot mappings and gap lifecycle
- Full pipeline produces organized asset folder from Duplessis Orphans Script.md
- At least one asset from each source category (acquired, code-gen, ComfyUI, Remotion) exists
- All success criteria re-checked against live pipeline output

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011
- Partially covers: none
- Leaves for later: R025 (DaVinci timeline export), R026 (quality scoring)
- Orphan risks: none

## Slices

- [x] **S01: Visual Orchestrator Skill** `risk:medium` `depends:[]`
  > After this: feed Script.md + VISUAL_STYLE_GUIDE.md → get valid shotlist.json with building block type assignments and text overlay entries

- [x] **S02: Media Acquisition Skill** `risk:high` `depends:[S01]`
  > After this: feed shotlist.json → bulk download assets from 10+ free sources, get manifest.json with shot mappings + gap list

- [x] **S03: Graphics Generator Skill** `risk:high` `depends:[S01]`
  > After this: feed manifest gaps → code-gen silhouettes/icons/diagrams via Pillow + ComfyUI creative assets in assets/ folder

- [x] **S04: Remotion Animation Skill** `risk:medium` `depends:[S01]`
  > After this: feed map/diagram shot entries from shotlist → rendered .mp4 animation clips via Remotion

- [x] **S05: Asset Manager Skill** `risk:low` `depends:[S02,S03,S04]`
  > After this: feed populated assets/ → numbered files in type folders, consolidated manifest, _pool/ for unmatched

- [ ] **S06: End-to-End Integration** `risk:medium` `depends:[S01,S02,S03,S04,S05]`
  > After this: full pipeline on Duplessis Orphans project proves Script.md → organized numbered asset folder with manifest

## Boundary Map

### S01 → S02, S03, S04, S05

Produces:
- `shotlist.json` — Array of shot entries with: id (S001...), chapter, narrative_context, visual_need, building_block (from VISUAL_STYLE_GUIDE), shotlist_type (archival_video|archival_photo|animation|map|text_overlay|document_scan), suggested_sources
- Schema contract: every downstream skill reads shotlist.json and filters by shotlist_type

Consumes:
- `projects/N/Script.md` — Narrated script from writer skill
- `context/visual-references/*/VISUAL_STYLE_GUIDE.md` — Decision framework with building blocks and type selection decision tree

### S02 → S05

Produces:
- `assets/manifest.json` — Assets array (filename, folder, description, mapped_shots, acquired_by) + gaps array (shot_id, visual_need, status: pending_generation)
- Downloaded files in type folders: `archival_footage/`, `archival_photos/`, `documents/`, `broll/`
- `assets/source_licenses.json` — License metadata per acquired asset

Consumes from S01:
- `shotlist.json` — Filters entries with shotlist_type in (archival_video, archival_photo, document_scan)

### S03 → S05

Produces:
- Generated images in `assets/vectors/` (code-gen) and `assets/vectors/` (ComfyUI)
- Updates `assets/manifest.json` gaps: pending_generation → filled
- Each generated file has entry in manifest assets array with acquired_by: "agent_graphics"

Consumes from S01:
- `shotlist.json` — Filters entries with shotlist_type = animation (silhouettes, icons, diagrams, illustrations)
Consumes from S02:
- `assets/manifest.json` — Reads gaps section to know what needs generation

### S04 → S05

Produces:
- Rendered .mp4 clips in `assets/animations/`
- Updates `assets/manifest.json` gaps: pending_generation → filled for map/animated entries
- Each rendered clip has entry in manifest assets array with acquired_by: "agent_animation"

Consumes from S01:
- `shotlist.json` — Filters entries with shotlist_type = map or animation entries needing motion

### S05 → User (DaVinci Resolve)

Produces:
- Numbered files (001_description.ext, 002_description.ext) in type folders
- Consolidated `assets/manifest.json` with final state: all assets numbered, all gaps terminal (filled or unfilled)
- `assets/_pool/` — Unnumbered unmatched assets

Consumes from S02, S03, S04:
- All files in `assets/` type folders
- `assets/manifest.json` — Current state with mappings and gap statuses

### S06

Produces:
- Verified end-to-end pipeline output on Duplessis Orphans project
- Integration test proving all skills chain correctly

Consumes from S01-S05:
- All skill outputs in sequence
