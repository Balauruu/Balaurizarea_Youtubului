# Architecture

**Analysis Date:** 2026-03-11

## Pattern Overview

**Overall:** Agentic pipeline with skill-based subtask distribution

**Key Characteristics:**
- Claude Code acts as the orchestrator — no fixed application entry point
- Two-phase workflow: Narrative Engineering (Phase 1) → Asset Pipeline (Phase 2)
- Skills are invoked via Claude Code, which coordinates with subagents for LLM work
- Deterministic code (scraping, media processing) is separated from heuristic reasoning (narrative, evaluation)
- Context stored entirely on filesystem (markdown, JSON) — no database
- No LLM API wrappers (all reasoning handled natively by Claude Code runtime)

## Layers

**Orchestration Layer:**
- Purpose: Coordinate phase execution and invoke skills
- Location: Claude Code conversations (ephemeral, not in codebase)
- Delegates to: Skills and subagents
- No code artifact — coordination happens in prompt context

**Phase 1: Narrative Engineering Layer:**
- Purpose: Research, ideate, and script documentary narratives
- Location: Handled by four agents (1.1–1.4) via Claude Code skills
- Agents:
  - **1.1 Channel Assistant** — Topic ideation, competitor filtering
  - **1.2 Researcher** — Web scraping via crawl4ai skill
  - **1.3 Writer** — Script generation from research
  - **1.4 Visual Orchestrator** — Shot listing and asset requirements
- Outputs: Topic briefs, research dossiers, scripts, shotlists (JSON)

**Phase 2: Asset Pipeline Layer:**
- Purpose: Acquire and generate visual assets for the script
- Location: Agents 2.1–2.4 (asset acquisition, generative visuals, animation, management)
- Agents:
  - **2.1 Media Acquisition** — Scraping for archival media, downloads
  - **2.2 Generative Visual Engine** — AI image prompts for missing visuals
  - **2.3 Animation Agent** — Remotion-based motion graphics generation
  - **2.4 Asset Manager** — Final asset sequencing and organization
- Outputs: Sequential asset folder with numbered files

**Skill Layer:**
- Purpose: Provide deterministic, reusable tools for specific tasks
- Locations:
  - `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/visual-style-extractor/` — Frame analysis and visual pattern extraction
  - `D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3/.claude/skills/crawl4ai-scraper/` — Web scraping
- Skills are invoked by agents and contain no LLM logic

**Context Layer:**
- Purpose: Store reference materials, channel rules, and analysis results
- Location: `context/` directory
- Contents:
  - `context/channel/` — Channel DNA, past topics, style guide
  - `context/competitors/` — Competitor analysis data
  - `context/script references/` — Full reference scripts for style extraction
  - `context/visual-references/` — Reference videos and extracted visual style guides

**Utility/Scratch Layer:**
- Purpose: Transient storage for large outputs during skill execution
- Location: `.claude/scratch/` (gitignored)
- Used for: Manifest slices, batch analysis results, merged analysis, synthesis input
- Lifecycle: Written during skill runs, read by subagents, deleted after phase completes

## Data Flow

**Topic Selection Flow:**
1. Channel Assistant (Agent 1.1) reads `context/channel/channel.md`, `past_topics.md`, competitor data
2. Generates topic brief with scoring (complexity, obscurity, shock)
3. User selects topic from chat window

**Research → Script → Shotlist Flow:**
1. **Agent 1.2** (Researcher) uses `crawl4ai-scraper` skill to scrape sources → `research.md`
2. **Agent 1.3** (Writer) reads `research.md` + `context/script references/` to extract style → generates script
3. **Agent 1.4** (Visual Orchestrator) reads script → outputs `shotlist.json` and `needed_assets.json`

**Visual Style Extraction Flow:**
1. **Visual Style Extractor Skill** (`pipeline.py` orchestrates stages 0–6):
   - **Stage 0 (acquire.py)**: Validate local input or download from YouTube via yt-dlp
   - **Stage 1 (scene_detect.py)**: Detect scene boundaries, extract keyframe per scene
   - **Stage 2 (dedup.py)**: Deduplicate near-identical frames using perceptual hashing (imagededup)
   - **Stage 3 (align.py)**: Parse transcript, align frames to narrative timestamps
   - **Stage 4 (contact_sheets.py)**: Generate 3×3 grids of contact sheets (1568×1568px, 4px padding)
   - **Stage 5** (LLM subagents): Manifest is sliced, each batch analyzed in parallel → per-batch JSON
   - **Stage 5 merge**: Merge batch results, filter low-confidence frames → `.claude/scratch/merged_analysis.json`
   - **Stage 6**: Prepare synthesis input → spawn synthesis subagent → generate `VISUAL_STYLE_GUIDE.md`

2. Output: `VISUAL_STYLE_GUIDE.md` contains 10–15 visual building blocks with recipes, decision rules, and production specs

**Asset Acquisition Flow:**
1. **Agent 2.1** (Media Acquisition) reads `shotlist.json` → scrapes historical media via crawl4ai or yt-dlp
2. **Agent 2.2** (Generative Visual Engine) identifies gaps → generates ComfyUI prompts
3. **Agent 2.3** (Animation Agent) reads `shotlist.json` → parameterizes Remotion templates → renders `.mp4` files
4. **Agent 2.4** (Asset Manager) collects all assets → renames sequentially (e.g., `001_Audio_Intro.wav`, `002_Visual_Archival.jpg`) → final ordered folder

**State Management:**
- **Active Phase State**: Encoded in Claude Code conversation context (not persisted)
- **Persistent Context**: Markdown files in `context/` — read by agents as needed
- **Intermediate Results**: JSON files (research.md, shotlist.json, scripts) stored in project folders or `.claude/scratch/`
- **Analysis Outputs**: VISUAL_STYLE_GUIDE.md and dedup_report.json in `context/visual-references/{video_name}/`

## Key Abstractions

**Skill:**
- Purpose: Encapsulates a deterministic, reusable tool (scraping, frame analysis, asset generation)
- Files: Each skill has a `SKILL.md` with instructions, a `scripts/` folder with Python code
- Pattern: Invoked by Claude Code via bash, produces structured output (JSON, markdown, files)
- Examples: `visual-style-extractor` (6-stage pipeline), `crawl4ai-scraper` (async web scraper)

**Visual Building Block:**
- Purpose: Reusable visual pattern extracted from reference video
- Representation: JSON entry with fields: `pattern_name`, `visual_recipe`, `narrative_function`, `variant_name`, `confidence`, `weight`
- Used by: Visual Orchestrator (Agent 1.4) to populate shotlists; Generative Visual Engine (Agent 2.2) to prompt AI image generation
- Generated by: Visual Style Extractor Stage 6 (synthesis subagent)

**Shotlist Entry:**
- Purpose: Maps a script chapter to required visual assets
- Representation: JSON object with: `chapter`, `timestamp_range`, `visual_type`, `description`, `source_hint`, `duration_seconds`, `transition`, `motion`
- Generated by: Agent 1.4 (Visual Orchestrator)
- Consumed by: Agent 2.1 (Media Acquisition), Agent 2.3 (Animation Agent), Agent 2.2 (Generative Visual Engine)

**Topic Brief:**
- Purpose: Summarizes a documentary topic with scores and metadata
- Representation: Markdown with fields: `title`, `hook`, `timeline`, `complexity_score`, `obscurity_score`, `shock_factor`, `estimated_runtime`
- Generated by: Agent 1.1 (Channel Assistant)
- Selected by: User in chat window

## Entry Points

**Skill: visual-style-extractor**
- Location: `.claude/skills/visual-style-extractor/`
- Triggers: User invokes via prompt (e.g., "extract visual style from this YouTube URL")
- Responsibilities:
  1. Accepts YouTube URL or local video+transcript directory
  2. Runs stages 0–4 automatically (Python)
  3. Prepares manifest, generates contact sheets
  4. Dispatches subagents for parallel frame analysis (Stage 5)
  5. Merges results, runs synthesis subagent (Stage 6)
  6. Outputs `VISUAL_STYLE_GUIDE.md` in `context/visual-references/{video_name}/`
- Entrypoint code: `pipeline.py` `run_stages_0_to_4()` and `run_stage_6()`

**Skill: crawl4ai-scraper**
- Location: `.claude/skills/crawl4ai-scraper/scripts/scraper.py`
- Triggers: Bash invocation with URL argument
- Responsibilities:
  1. Takes URL as argument
  2. Runs crawl4ai async crawler
  3. Returns markdown to stdout
- Entrypoint code: `scraper.py` `main()`

**Phase 1 Agent 1.1 (Channel Assistant)**
- Triggers: User prompt requesting topic ideation
- Reads: `context/channel/channel.md`, `context/channel/past_topics.md`, `context/competitors/`
- Outputs: Topic brief (markdown or JSON)

**Phase 1 Agent 1.2 (Researcher)**
- Triggers: Topic selected by user
- Invokes: `crawl4ai-scraper` skill to scrape sources
- Outputs: `research.md` with schema: subject_overview, timeline, key_figures, primary/secondary sources, media_inventory, contradictions, unanswered_questions, source_reliability

**Phase 1 Agent 1.3 (Writer)**
- Triggers: Research dossier completed
- Reads: `research.md` (from Agent 1.2) + `context/script references/` (for style extraction)
- Outputs: Clean script text with numbered chapters

**Phase 1 Agent 1.4 (Visual Orchestrator)**
- Triggers: Script completed
- Reads: Script text, `context/visual-references/{video_name}/VISUAL_STYLE_GUIDE.md` (if available)
- Outputs: `shotlist.json`, `needed_assets.json`

## Error Handling

**Strategy:** Try → Log → Suggest Alternative

**Patterns:**
- **yt-dlp failure** → Show error, suggest manual download of video
- **Missing transcript on YouTube** → Request user provide transcript file (.vtt/.srt/.txt)
- **Scene detection insufficient** → Suggest re-run with `adaptive_threshold=2.0` (lower) for more scenes
- **Scene detection excessive** → Suggest re-run with `adaptive_threshold=4.0` (higher) for fewer scenes
- **> 90% frame dedup rate** → Warn user: video may be too uniform for style extraction
- **Read tool fails on contact sheet** → Re-generate at 1200px and retry
- **Low confidence frames in analysis** → Filter during merge stage, report count to user

## Cross-Cutting Concerns

**Logging:**
- Python stages (0–4) print progress to stdout automatically
- Stages report: scenes detected, unique frames after dedup, contact sheets generated
- Dedup stage writes `dedup_report.json` for frame merge auditing
- CLI invocations via bash capture stderr for error diagnosis

**Validation:**
- `acquire.py` validates that local directory contains both video and transcript before proceeding
- `dedup.py` checks for near-black frames (transition frames) separately before perceptual hashing
- Frame analysis subagents filter by `confidence >= 3` during merge stage

**Authentication:**
- YouTube URLs: yt-dlp handles authentication transparently (public videos)
- Crawl4ai scraping: No authentication required; respects robots.txt and rate limiting

**Configuration:**
- `PipelineConfig` dataclass in `pipeline.py` accepts parameters:
  - `source` (URL or path)
  - `adaptive_threshold` (for scene detection, default 3.0)
  - `min_scene_len` (minimum frames per scene, default 15)
  - `dedup_threshold` (perceptual hash distance, default 8)
- Manifest slicing customizable: `start_idx`, `end_idx` for batching control

---

*Architecture analysis: 2026-03-11*
