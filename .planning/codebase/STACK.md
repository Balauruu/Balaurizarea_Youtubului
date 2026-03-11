# Technology Stack

**Analysis Date:** 2026-03-11

## Languages

**Primary:**
- Python 3.14 - All scripts, utilities, and pipeline orchestration

**Secondary:**
- Markdown - All documentation, context files, and output formats

## Runtime

**Environment:**
- Python 3.14 (native execution via Claude Code)
- ffmpeg - Video processing and frame extraction (system binary)

**Package Manager:**
- pip - Python package dependency management
- Lockfile: Not present (requirements.txt used for explicit versioning in `.claude/skills/visual-style-extractor/scripts/requirements.txt`)

## Frameworks

**Core Orchestration:**
- Claude Code (native runtime) - Pipeline orchestrator with agentic control (no external SDK wrappers)

**Media Processing:**
- yt-dlp - Video/audio downloading from 1800+ sites via `subprocess` in `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/acquire.py`
- ffmpeg - Video frame extraction and transcoding via `subprocess` in `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/scene_detect.py`
- PySceneDetect (`scenedetect[opencv]>=0.6`) - Scene boundary detection using AdaptiveDetector algorithm

**Image Processing:**
- Pillow (`Pillow>=10.0`) - Image I/O and manipulation; generates contact sheets (1568x1568px, 3x3 grid, 4px white padding)
- imagededup (`imagededup>=0.3`) - Perceptual hashing via PHash method for frame deduplication

**Subtitle/Transcript Parsing:**
- webvtt-py (`webvtt-py>=0.5`) - VTT subtitle file parsing in `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/align.py`
- pysrt (`pysrt>=1.1`) - SRT subtitle file parsing as fallback

**Web Scraping:**
- crawl4ai - Asynchronous web crawler (imported and invoked in `.claude/skills/crawl4ai-scraper/scripts/scraper.py`)

**Utilities:**
- numpy (`numpy>=1.24`) - Numerical array operations for image processing and statistics

**Testing:**
- pytest - Unit testing framework (implied via `.pytest_cache/` directory and test files in `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/`)

## Key Dependencies

**Critical (Visual Style Extractor):**
- `scenedetect[opencv]>=0.6` - Scene detection core to visual analysis pipeline
- `imagededup>=0.3` - Reduces frame redundancy before LLM subagent analysis
- `Pillow>=10.0` - Generates contact sheets for subagent analysis batches
- `webvtt-py>=0.5` - Maps narration timestamps to video frames
- `pysrt>=1.1` - Alternative transcript format support
- `numpy>=1.24` - Numerical operations for deduplication

**Critical (Scraping):**
- `crawl4ai` - Web scraping for research and competitor analysis (no version constraint in codebase)

**Infrastructure (Subprocess-based, not imported):**
- yt-dlp - Downloads videos with auto-subtitles from YouTube and 1800+ sites
- ffmpeg - Extracts frames, handles codec transcoding

## Configuration

**Environment Variables:**
- No `.env` file required (pipeline is stateless and context-driven)
- PYTHONPATH set at runtime:
  ```bash
  PYTHONPATH=.claude/skills/visual-style-extractor/scripts
  ```

**Context Files (Filesystem-based Configuration):**
- `CLAUDE.md` - Claude Code global instructions and conventions
- `Architecture.md` - Full pipeline specification and agent definitions
- `context/channel/channel.md` - Channel DNA (voice, tone, style, audience profile)
- `context/channel/past_topics.md` - Previous topics to avoid duplication
- `context/competitors/` - Competitor research data
- `context/script references/` - Reference scripts for style extraction
- `context/visual-references/` - Extracted visual style guides from reference videos

**Build/Execution:**
- No build system (scripts execute directly via Python or bash)
- Invocation via Claude Code skill commands in SKILL.md files:
  - `.claude/skills/visual-style-extractor/SKILL.md` - Visual style extraction pipeline
  - `.claude/skills/crawl4ai-scraper/SKILL.md` - Web scraping skill

## Platform Requirements

**Development:**
- Windows 11 (primary platform; Git Bash for shell commands)
- Python 3.14
- ffmpeg (system binary, must be available in PATH)
- pip for dependency installation

**Production/Output:**
- Output artifacts: `.mp4`, `.mov` (video files); `.md` (documentation); `.json` (asset manifests)
- Deployment target: DaVinci Resolve (external video editing application)
- Storage: Local filesystem only (no cloud, no database)

## Architecture Constraints

**ZERO LLM API WRAPPERS:**
- No Anthropic SDK (`@anthropic-ai/sdk`)
- No OpenAI SDK
- All reasoning handled natively by Claude Code runtime
- LLM API wrappers forbidden unless part of essential workflow tools

**SEPARATION OF CONCERNS:**
- **[DETERMINISTIC] Code** - Media processing, scraping, frame extraction, deduplication
  - Location: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/` (modules: `acquire.py`, `scene_detect.py`, `dedup.py`, `align.py`, `contact_sheets.py`, `synthesize.py`, `pipeline.py`)
  - Location: `.claude/skills/crawl4ai-scraper/scripts/scraper.py`
- **[HEURISTIC] Operations** - Topic selection, script writing, narrative design, visual direction
  - Executed via Claude Code skills (Agent tool, file-based communication)
  - No code written for heuristic tasks

---

*Stack analysis: 2026-03-11*
