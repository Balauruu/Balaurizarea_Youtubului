# Codebase Structure

**Analysis Date:** 2026-03-11

## Directory Layout

```
D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3/
├── .claude/                                    # Agent infrastructure (gitignored assets)
│   ├── scratch/                                # Transient files during skill runs
│   │   ├── synthesis_input.txt                 # Data for synthesis subagent
│   │   ├── merged_analysis.json                # Frame analysis results (Stage 5)
│   │   ├── analysis_batch_*.json               # Per-subagent analysis outputs
│   │   └── manifest_slice_*.json               # Manifest batches for parallel analysis
│   └── skills/
│       ├── visual-style-extractor/             # Visual pattern extraction pipeline
│       │   ├── SKILL.md                        # Skill documentation & usage
│       │   ├── docs/plans/                     # Design specs (v4 framework)
│       │   └── scripts/
│       │       ├── requirements.txt            # Dependencies
│       │       ├── save_analysis.py            # Helper for saving results
│       │       └── visual_style_extractor/
│       │           ├── __init__.py
│       │           ├── pipeline.py             # Main orchestrator (stages 0-6)
│       │           ├── acquire.py              # Stage 0: yt-dlp download / local validation
│       │           ├── scene_detect.py         # Stage 1: PySceneDetect keyframes
│       │           ├── dedup.py                # Stage 2: Perceptual hash deduplication
│       │           ├── align.py                # Stage 3: Transcript alignment
│       │           ├── contact_sheets.py       # Stage 4: Grid generation
│       │           ├── synthesize.py           # Stage 6: Synthesis input preparation
│       │           ├── prompts/
│       │           │   ├── analysis_prompt.txt # Instructions for Stage 5 subagents
│       │           │   └── synthesis_prompt.txt# Instructions for Stage 6 synthesis
│       │           └── tests/
│       │               ├── __init__.py
│       │               └── test_pipeline.py    # Pipeline integration tests
│       └── crawl4ai-scraper/                   # Web scraping skill
│           ├── SKILL.md                        # Skill documentation
│           └── scripts/
│               ├── requirements.txt            # Dependencies
│               └── scraper.py                  # Main scraper entry point
├── .planning/
│   └── codebase/                               # GSD mapping output (this document)
│       ├── ARCHITECTURE.md                     # This file's sibling
│       └── STRUCTURE.md                        # This file
├── context/                                    # Persistent reference materials
│   ├── channel/
│   │   ├── channel.md                          # Channel DNA (voice, tone, niche)
│   │   ├── past_topics.md                      # Previously covered topics (prevent duplication)
│   │   └── style_guide.md                      # Writing style rules
│   ├── competitors/
│   │   └── competitors.md                      # Competitor analysis and research
│   ├── script references/
│   │   └── Mexico's Most Disturbing Cult.md   # Full reference script for style extraction
│   └── visual-references/                      # Extracted visual style guides (output of skill)
│       ├── Mexico's Most Disturbing Cult/
│       │   ├── VISUAL_STYLE_GUIDE.md           # Visual pattern decision framework
│       │   ├── frames_manifest.json            # Frame metadata (timestamps, scene numbers)
│       │   ├── scenes.json                     # Scene boundary data
│       │   ├── dedup_report.json               # Frame deduplication audit log
│       │   ├── frames/                         # Extracted keyframes (one per scene)
│       │   │   ├── frame_0000.jpg
│       │   │   ├── frame_0001.jpg
│       │   │   └── ...
│       │   └── contact_sheets/                 # 3×3 grid contact sheets for analysis
│       │       ├── contact_sheet_000.jpg       # Frames 0-8
│       │       ├── contact_sheet_001.jpg       # Frames 9-17
│       │       └── ...
│       ├── test0/                              # Test run outputs
│       ├── test 1/                             # Test run outputs
│       ├── test 2/                             # Test run outputs
│       └── test 3/                             # Test run outputs
├── docs/
│   └── plans/                                  # Implementation plans and design docs
│       ├── 2026-03-09-visual-style-extractor-design.md
│       ├── 2026-03-09-visual-style-extractor-v2-implementation.md
│       ├── 2026-03-10-context-optimization.md
│       └── ...
├── projects/                                   # (Empty) Reserved for future project runs
├── .git/                                       # Git repository
├── .gitignore                                  # Excludes: .claude/scratch, *.pyc, __pycache__
├── Architecture.md                             # Full pipeline specification (user instructions)
├── CLAUDE.md                                   # Claude Code project instructions
├── README.md                                   # Quick reference (phases, skills, stack)
```

## Directory Purposes

**`.claude/`**
- Purpose: Agent infrastructure and skills (not committed; large binaries)
- Contains: Skills with Python implementations, scratch pads for transient data
- Key files: Each skill has `SKILL.md` (user-facing) and `scripts/` (implementation)

**`.claude/scratch/`**
- Purpose: Transient storage during skill runs (gitignored)
- Contains: Large JSON outputs (manifests, analysis batches), synthesis input
- Lifecycle: Written during phase, read by subagents, deleted after completion
- Examples: `merged_analysis.json` (full frame analysis), `synthesis_input.txt` (for synthesis subagent)

**`.claude/skills/visual-style-extractor/`**
- Purpose: Frame-to-pattern extraction pipeline
- Core module: `scripts/visual_style_extractor/` with 7 stages (0–6)
- Entry points: `pipeline.py` orchestrates stages
- Tests: `tests/test_pipeline.py` for integration validation
- Prompts: `prompts/analysis_prompt.txt` and `synthesis_prompt.txt` guide subagent reasoning

**`.claude/skills/crawl4ai-scraper/`**
- Purpose: Web scraping for research and competitor data
- Core: `scraper.py` (async crawl4ai wrapper)
- Usage: Invoked by bash with URL argument → returns markdown to stdout

**`context/`**
- Purpose: Persistent reference materials (committed to git)
- Never modified by skills — only read
- Organized by: channel rules, competitors, script references, visual references

**`context/channel/`**
- `channel.md`: Channel DNA — niche, voice, tone, audience, content pillars, differentiation
- `past_topics.md`: Topics already covered (prevents duplicate videos)
- `style_guide.md`: Writing conventions (sentence length, vocabulary, tone rules)

**`context/competitors/`**
- `competitors.md`: Competitor research (channels, topics, length, differentiation)

**`context/script references/`**
- Full reference scripts used for style extraction
- Currently: `Mexico's Most Disturbing Cult.md` (example reference script)
- Used by: Writer skill to extract narrative style

**`context/visual-references/`**
- Output directory for visual style extraction skill
- Per-video subdirectories (named after video title):
  - `VISUAL_STYLE_GUIDE.md` — Decision framework with 10-15 building blocks
  - `frames_manifest.json` — Metadata for all extracted frames
  - `scenes.json` — Scene boundary timestamps
  - `dedup_report.json` — Which frames were merged and why
  - `frames/` — Individual keyframe JPEGs (one per scene)
  - `contact_sheets/` — 3×3 grid contact sheets for visual review

**`docs/plans/`**
- Purpose: Implementation plans and design specs (not directly used by pipeline)
- Contents: v4 framework spec, context optimization notes, past design iterations

**`projects/`**
- Purpose: Reserved for future per-project asset folders
- Currently empty — may be used when Phase 2 (Asset Pipeline) agents create project-specific outputs

## Key File Locations

**Entry Points (Skills):**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py` — Main orchestrator for stages 0–6
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/crawl4ai-scraper/scripts/scraper.py` — Web scraper (bash invocation)

**Configuration & Instructions:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/Architecture.md` — Full pipeline spec (user reference)
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/CLAUDE.md` — Claude Code instructions
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/README.md` — Quick reference (phases, skills, stack)

**Channel Context:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/context/channel/channel.md` — Channel DNA
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/context/channel/past_topics.md` — Covered topics

**Reference Scripts & Visuals:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/context/script references/Mexico's Most Disturbing Cult.md` — Example script for style extraction
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — Extracted visual patterns

**Skill Documentation:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/SKILL.md` — How to use visual extractor
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/crawl4ai-scraper/SKILL.md` — How to use scraper

**Prompts for Subagent Analysis:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/analysis_prompt.txt` — Stage 5 analysis instructions
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/synthesis_prompt.txt` — Stage 6 synthesis instructions

**Tests:**
- `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py` — Pipeline integration tests

## Naming Conventions

**Files:**
- **Python modules**: `snake_case.py` (e.g., `scene_detect.py`, `acquire.py`)
- **Data files**: `lowercase_with_underscores.json` (e.g., `frames_manifest.json`, `dedup_report.json`)
- **Markdown context**: `lowercase_with_underscores.md` (e.g., `channel.md`, `past_topics.md`)
- **Output directories**: Sanitized video title (spaces replaced, invalid Windows chars removed) (e.g., `Mexico's Most Disturbing Cult`)
- **Frame files**: `frame_NNNN.jpg` (zero-padded 4-digit index, one per scene)
- **Contact sheets**: `contact_sheet_NNN.jpg` (zero-padded 3-digit index, 9 frames per sheet)

**Directories:**
- **Agent infrastructure**: `.claude/` (dot-prefixed, gitignored)
- **Skill folders**: `skill-name-with-hyphens/` (e.g., `visual-style-extractor`, `crawl4ai-scraper`)
- **Feature directories**: `lowercase_with_hyphens/` (e.g., `script references`, `visual-references`)
- **Transient directories**: `scratch/` (inside `.claude/`, gitignored)

## Where to Add New Code

**New Skill (Deterministic Task):**
- Create: `.claude/skills/{skill-name}/`
- Structure:
  ```
  .claude/skills/{skill-name}/
  ├── SKILL.md                    # User-facing documentation
  └── scripts/
      ├── requirements.txt        # Dependencies
      └── {main_script}.py        # Entry point
  ```
- Examples: `visual-style-extractor`, `crawl4ai-scraper`

**New Pipeline Stage (Visual Extractor):**
- Add Python module: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/{stage_name}.py`
- Define stage function (e.g., `def extract_X(...):`)
- Import and wire into `pipeline.py` orchestrator
- Example: `acquire.py`, `scene_detect.py`, `dedup.py`

**New Agent (Heuristic Task):**
- No code artifact — handled entirely via Claude Code prompts
- Reference materials: Add to `context/` (e.g., style guide → `context/channel/style_guide.md`)
- Agent invokes skills as needed, outputs markdown/JSON files to project folders

**New Context Reference:**
- Add to `context/{category}/{filename}.md` (e.g., `context/competitors/new_channel.md`)
- Never modified by pipeline — read-only for agents
- Committed to git for persistent reference

**New Test:**
- Add to: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_{module}.py`
- Use pytest conventions
- Import from `visual_style_extractor` modules (PYTHONPATH must include `scripts/` folder)

## Special Directories

**`.claude/scratch/`:**
- Purpose: Transient outputs during skill execution
- Generated: During pipeline runs (stages 0–6)
- Committed: No (in .gitignore)
- Lifecycle: Created during run, read by subagents, cleaned up after phase
- Contents: Large JSON files, manifest slices, batch analysis results

**`context/visual-references/`:**
- Purpose: Store extracted visual style guides (persistent output)
- Generated: By visual-style-extractor skill (Stage 6 writes `VISUAL_STYLE_GUIDE.md`)
- Committed: Yes (git-tracked after initial extraction)
- Contents: Guides + frames + contact sheets (for reference and re-use)

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: By `/gsd:map-codebase` command
- Committed: Yes
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md, STACK.md, INTEGRATIONS.md

**`docs/plans/`:**
- Purpose: Implementation specs and design documentation
- Generated: By user during planning phases
- Committed: Yes
- Contents: Design docs, improvement specs, past iterations

---

*Structure analysis: 2026-03-11*
