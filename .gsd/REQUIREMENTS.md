# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R001 — Script-to-shotlist mapping via VISUAL_STYLE_GUIDE
- Class: core-capability
- Status: validated
- Description: Parse Script.md and apply VISUAL_STYLE_GUIDE decision tree to produce shotlist.json with building block type assignments for every narrative segment
- Why it matters: This is the bridge between written script and visual production — without it, editors must manually decide every visual
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: unmapped
- Notes: The VISUAL_STYLE_GUIDE already has a complete Type Selection Decision Tree; the orchestrator applies it

### R002 — Text overlay entries in shotlist
- Class: core-capability
- Status: validated
- Description: Shotlist includes entries for text overlays (quote cards, date cards, keyword stingers, warning cards) with text content and timing, but no assets are generated for them
- Why it matters: Editor needs to know where text elements go even though they're placed manually in DaVinci
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Text overlay types are placed by the editor in DaVinci Resolve — pipeline only provides placement guidance

### R003 — Multi-source media acquisition
- Class: core-capability
- Status: active
- Description: Bulk scrape and download free/public domain media from 7+ sources including archive.org (Python lib), Wikimedia Commons API, Pexels API, Pixabay API, Smithsonian Open Access API, YouTube CC (yt-dlp), and direct URL downloads
- Why it matters: More sources = better coverage of visual needs, fewer gaps for the generator to fill
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: contract-tested (102 mocked tests, live API validation in S06)
- Notes: Source policy: all media must be free (public domain, CC0, or Creative Commons). Rate limiting per source required. DPLA/Europeana/LOC dropped due to API instability (D014).

### R004 — Asset-to-shot matching with gap identification
- Class: core-capability
- Status: active
- Description: Match acquired assets to shotlist entries by visual need, update manifest.json with mappings, output unmatched shots as gaps for downstream generation
- Why it matters: Gap analysis is the handoff point between acquisition and generation — without it, generators don't know what to make
- Source: user
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: contract-tested (gap identification logic tested with mocks, live validation in S06)
- Notes: Matching is [HEURISTIC] — Claude evaluates visual relevance. Gap identification only flags acquisition-relevant types (archival_photo, archival_video, document_scan).

### R005 — Code-generated flat graphics
- Class: core-capability
- Status: active
- Description: Generate constrained flat graphics (silhouettes, symbolic icons, concept diagrams, character profile cards) using Pillow/Cairo/SVG for maximum consistency and repeatability
- Why it matters: These are highly controlled, rule-based visuals where code-gen is more reliable than AI generation
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: contract-tested (7 Pillow renderers with 18 tests, live validation in S06)
- Notes: Building blocks with constrained production specs (flat black silhouette on red background, clean line art, etc.)

### R006 — ComfyUI creative asset generation
- Class: core-capability
- Status: active
- Description: Generate creative/artistic assets (ritual illustrations, atmospheric textures, glitch icons) via ComfyUI with Z-image-turbo model, using workflow templates and prompt engineering
- Why it matters: Some visual building blocks require artistic interpretation that code-gen can't provide
- Source: user
- Primary owning slice: M002/S03
- Supporting slices: none
- Validation: contract-tested (REST client, 4 workflow templates, prompt builder — 35 mocked tests, live validation in S06)
- Notes: ComfyUI runs locally. Code-gen handles constrained graphics; ComfyUI handles creative ones.

### R007 — Remotion animated maps and diagrams
- Class: core-capability
- Status: active
- Description: Render animated location maps (with glowing points, connection arcs, labels) and animated diagrams as .mp4 clips using Remotion compositions orchestrated from Python via subprocess
- Why it matters: Maps and animated diagrams are the only building blocks that genuinely need motion
- Source: user
- Primary owning slice: M002/S04
- Supporting slices: none
- Validation: contract-tested (22 mocked tests for CLI/manifest, scaffold smoke render proves .mp4 output, live validation in S06)
- Notes: Remotion (Node.js) is the sole exception to the Python-only scripting constraint. Node.js is installed.

### R008 — Sequential asset numbering and manifest consolidation
- Class: core-capability
- Status: active
- Description: Assign sequential prefixes (001_, 002_, ...) based on order of appearance in shotlist.json. Assets mapped to multiple shots get the number of their first appearance.
- Why it matters: Numbered assets can be quickly assembled into a DaVinci timeline in order
- Source: user
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: unmapped
- Notes: Follows Architecture.md numbering convention

### R009 — Unmatched assets sorted to _pool/
- Class: core-capability
- Status: active
- Description: Assets acquired but not mapped to any shot are moved to _pool/ directory, kept for manual editorial use
- Why it matters: No acquired media is wasted — editor can browse unmatched assets for creative decisions
- Source: user
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: unmapped
- Notes: _pool/ assets are unnumbered

### R010 — Gap lifecycle tracking
- Class: integration
- Status: active
- Description: Track gap status through lifecycle: pending_generation → filled (by graphics/animation agents) → unfilled (terminal state set by asset manager)
- Why it matters: Clear gap lifecycle means the editor knows exactly what the pipeline couldn't provide
- Source: inferred
- Primary owning slice: M002/S05
- Supporting slices: M002/S02, M002/S03, M002/S04
- Validation: unmapped
- Notes: Status tracked in manifest.json gaps section

### R011 — Raw assets delivered without pre-styling
- Class: constraint
- Status: active
- Description: All assets delivered raw — no film grain, sepia toning, CRT scanlines, or other post-production effects applied by the pipeline
- Why it matters: Editor controls the final look in DaVinci Resolve; pre-styled assets fight the grading process
- Source: user
- Primary owning slice: M002/S05
- Supporting slices: none
- Validation: unmapped
- Notes: VISUAL_STYLE_GUIDE production specs describe the final look, not how assets should be delivered

## Validated

### R012 — Competitor discovery and tracking
- Class: core-capability
- Status: validated
- Description: JSON registry, yt-dlp scraping, SQLite storage for competitor channels and videos
- Why it matters: Foundation for data-driven topic selection
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S06
- Validation: validated
- Notes: 176 passing tests, SQLite DB with 37 videos from 3 channels

### R013 — Competitor analysis
- Class: core-capability
- Status: validated
- Description: Per-channel stats, outlier detection, topic clustering, title patterns
- Why it matters: Identifies what content performs and where gaps exist
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: none
- Validation: validated
- Notes: test_analyzer.py passes

### R014 — Topic generation with scoring
- Class: core-capability
- Status: validated
- Description: 5 scored briefs per run with anchored rubrics and past-topic deduplication
- Why it matters: Focused shortlist prevents decision fatigue
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: test_topics.py passes

### R015 — Trend awareness
- Class: core-capability
- Status: validated
- Description: YouTube autocomplete + search convergence scanning
- Why it matters: Topics aligned with current audience interest
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: validated
- Notes: test_trend_scanner.py passes

### R016 — Project initialization
- Class: core-capability
- Status: validated
- Description: Sequential project directory creation with metadata.md (title variants, description)
- Why it matters: Standardized project structure for downstream agents
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: validated
- Notes: test_project_init.py passes

### R017 — Two-pass web research
- Class: core-capability
- Status: validated
- Description: Broad survey (10-15 sources) → deep primary source dive via crawl4ai
- Why it matters: Breadth then depth produces comprehensive factual foundation
- Source: user
- Primary owning slice: M001/S08
- Supporting slices: M001/S07, M001/S09
- Validation: validated
- Notes: 68 researcher tests pass, validated on Duplessis Orphans topic

### R018 — Research dossier output
- Class: core-capability
- Status: validated
- Description: 9-section Research.md with timeline, key figures, contradictions, narrative hooks
- Why it matters: Scriptwriter-optimized research output
- Source: user
- Primary owning slice: M001/S10
- Supporting slices: none
- Validation: validated
- Notes: Research.md exists in projects/1/

### R019 — Media URL cataloging
- Class: core-capability
- Status: validated
- Description: Separate media_urls.md grouped by asset category
- Why it matters: Visual media catalog for acquisition agent
- Source: user
- Primary owning slice: M001/S10
- Supporting slices: none
- Validation: validated
- Notes: media_urls.md exists in projects/1/research/

### R020 — Style extraction
- Class: core-capability
- Status: validated
- Description: Reference scripts → STYLE_PROFILE.md behavioral ruleset
- Why it matters: Consistent channel voice across all scripts
- Source: user
- Primary owning slice: M001/S11
- Supporting slices: none
- Validation: validated
- Notes: 371-line STYLE_PROFILE.md with 5 Universal Voice Rules

### R021 — Script generation
- Class: core-capability
- Status: validated
- Description: Research dossier → numbered chapters with pure narration (3,000-7,000 words)
- Why it matters: Final narrative output ready for recording
- Source: user
- Primary owning slice: M001/S12
- Supporting slices: none
- Validation: validated
- Notes: Script.md exists in projects/1/, 9 writer tests pass

## Deferred

### R025 — DaVinci Resolve timeline/EDL export
- Class: integration
- Status: deferred
- Description: Generate a DaVinci Resolve importable timeline (EDL, XML, or AAF) that pre-places assets in shot order
- Why it matters: Would save manual timeline assembly time
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — organized asset folder with numbered files is sufficient for now

### R026 — Automated asset quality scoring
- Class: quality-attribute
- Status: deferred
- Description: Automatically score acquired/generated assets for quality, resolution, and relevance
- Why it matters: Would help prioritize best assets when multiple options exist for a shot
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — human review in DaVinci is sufficient initially

## Out of Scope

### R027 — Pre-styling assets
- Class: anti-feature
- Status: out-of-scope
- Description: Applying film grain, sepia, CRT scanlines, vignettes, or other effects to assets before delivery
- Why it matters: Prevents scope confusion — editor owns the final look in DaVinci Resolve
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: VISUAL_STYLE_GUIDE describes final look, not delivery format

### R028 — Text overlay asset generation
- Class: anti-feature
- Status: out-of-scope
- Description: Generating actual image/video assets for quote cards, date cards, keyword stingers, warning cards
- Why it matters: These are editorial decisions made in DaVinci with the actual font/style system
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Shotlist includes text overlay entries for placement guidance, but no assets generated

### R029 — Upload scheduling or publishing
- Class: anti-feature
- Status: out-of-scope
- Description: Automated YouTube upload or social media publishing
- Why it matters: Out of scope for this pipeline
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Carried forward from M001

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | validated | M002/S01 | none | validated |
| R002 | core-capability | validated | M002/S01 | none | validated |
| R003 | core-capability | active | M002/S02 | none | contract-tested |
| R004 | core-capability | active | M002/S02 | none | contract-tested |
| R005 | core-capability | active | M002/S03 | none | contract-tested |
| R006 | core-capability | active | M002/S03 | none | contract-tested |
| R007 | core-capability | active | M002/S04 | none | contract-tested |
| R008 | core-capability | active | M002/S05 | none | unmapped |
| R009 | core-capability | active | M002/S05 | none | unmapped |
| R010 | integration | active | M002/S05 | M002/S02,S03,S04 | unmapped |
| R011 | constraint | active | M002/S05 | none | unmapped |
| R012 | core-capability | validated | M001/S01 | M001/S06 | validated |
| R013 | core-capability | validated | M001/S02 | none | validated |
| R014 | core-capability | validated | M001/S03 | none | validated |
| R015 | core-capability | validated | M001/S05 | none | validated |
| R016 | core-capability | validated | M001/S04 | none | validated |
| R017 | core-capability | validated | M001/S08 | M001/S07,S09 | validated |
| R018 | core-capability | validated | M001/S10 | none | validated |
| R019 | core-capability | validated | M001/S10 | none | validated |
| R020 | core-capability | validated | M001/S11 | none | validated |
| R021 | core-capability | validated | M001/S12 | none | validated |
| R025 | integration | deferred | none | none | unmapped |
| R026 | quality-attribute | deferred | none | none | unmapped |
| R027 | anti-feature | out-of-scope | none | none | n/a |
| R028 | anti-feature | out-of-scope | none | none | n/a |
| R029 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 9
- Mapped to slices: 9
- Validated: 12
- Unmapped active requirements: 0
