# External Integrations

**Analysis Date:** 2026-03-11

## APIs & External Services

**YouTube:**
- Video/audio downloading with auto-subtitle extraction
  - SDK/Client: yt-dlp (command-line tool invoked via subprocess)
  - Auth: None (public videos only), optional API key for private/unlisted content
  - Implementation: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/acquire.py` - `download_from_youtube()` function
  - Command: `yt-dlp -f bestvideo[height<=1080]+bestaudio/best[height<=1080] --write-auto-sub --sub-lang en --convert-subs vtt <URL>`
  - Output: Video file (.mp4) + VTT transcript stored in `context/visual-references/[video-title]/`

**Web Scraping (1800+ sites):**
- Crawl4AI asynchronous web crawler
  - SDK/Client: crawl4ai (Python async library)
  - Auth: None required (public web content only)
  - Implementation: `.claude/skills/crawl4ai-scraper/scripts/scraper.py` - `AsyncWebCrawler` class
  - Invocation: `python .claude/skills/crawl4ai-scraper/scripts/scraper.py "<URL>"`
  - Output: Clean Markdown extracted from HTML (stdout only, no persistence in skill)
  - Purpose: Research data for Agent 1.2 (Researcher), competitor analysis for Agent 1.1 (Channel Assistant)

## Data Storage

**Databases:**
- Not applicable - No traditional database in use

**File Storage:**
- Local filesystem only (no cloud)
  - Video source: Downloaded via yt-dlp to `context/visual-references/[video-title]/`
  - Frames: Extracted to `context/visual-references/[video-title]/frames/` by ffmpeg
  - Contact sheets: Generated to `context/visual-references/[video-title]/contact_sheets/` by Pillow (3x3 grids, 1568x1568px)
  - Manifests: `frames_manifest.json`, `dedup_report.json`, `scenes.json` in `context/visual-references/[video-title]/`
  - Transient analysis: `.claude/scratch/` (gitignored) for subagent communication
  - Final output: `context/visual-references/[video-title]/VISUAL_STYLE_GUIDE.md`

**Caching:**
- Frame deduplication: PHash index computed per-run in-memory (not persisted)
- Manifest slices: Temporary `.claude/scratch/manifest_slice_N.json` for subagent batching

## Authentication & Identity

**Auth Provider:**
- None required
- Pipeline operates with public video/content access only
- Claude Code runtime provides all agentic reasoning (no external auth)

## Monitoring & Observability

**Error Tracking:**
- Not detected

**Logs:**
- Console output: Progress messages from `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py` stages 0-6
- Example: `[Stage 0/6] Acquiring video...`, `[Stage 1/6] Detecting scenes...`
- Dedup report: `context/visual-references/[video-title]/dedup_report.json` for auditing frame merges
- Warnings: Scene detection anomalies (< 10 scenes, > 200 scenes) logged to stdout

## CI/CD & Deployment

**Hosting:**
- Not applicable - Pipeline runs locally on user's machine via Claude Code

**CI Pipeline:**
- Not detected - No GitHub Actions or equivalent
- Manual testing: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py` via pytest

## External Tool Dependencies

**yt-dlp (Video Download):**
- Type: CLI tool invoked via `subprocess.run()`
- Location: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/acquire.py`
- Error handling: Raises `RuntimeError` if exit code non-zero
- Dependencies: Must be available in system PATH

**ffmpeg (Frame Extraction):**
- Type: CLI tool invoked via `subprocess.run()`
- Location: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/scene_detect.py`
- Usage: Extracts keyframe per scene, one PNG per detected scene boundary
- Dependencies: Must be available in system PATH (required by scenedetect[opencv])

## Environment Configuration

**Required env vars:**
- `PYTHONPATH=.claude/skills/visual-style-extractor/scripts` (for visual extractor pipeline imports)

**Optional Configuration (PipelineConfig dataclass):**
- `source` (required): YouTube URL or local directory path
- `output_dir` (optional): Override output location (defaults to `context/visual-references/` for YouTube)
- `adaptive_threshold` (optional): Scene detection sensitivity (default: 3.0; recommend: 2.0-4.0)
- `min_scene_len` (optional): Minimum scene duration in frames (default: 15)
- `dedup_threshold` (optional): Perceptual hash similarity (default: 8; range: 0-20)

**Secrets location:**
- No secrets required
- `.env` files gitignored but not used in pipeline

## Webhooks & Callbacks

**Incoming:**
- Not applicable

**Outgoing:**
- Not applicable
- All outputs are file-based

## LLM Integration

**Claude (Anthropic):**
- Integration: Claude Code native runtime (not SDK-based)
- No SDK imports (per Architecture.md ZERO LLM WRAPPERS rule)
- Subagent communication: File-based
  - Analysis subagents read: Contact sheets (images), manifest slices (JSON), analysis prompt (text)
  - Analysis subagents write: `.claude/scratch/analysis_batch_N.json`
  - Synthesis subagent reads: `.claude/scratch/synthesis_input.txt`, synthesis prompt
  - Synthesis subagent writes: `context/visual-references/[video-title]/VISUAL_STYLE_GUIDE.md`
- Prompts:
  - `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/analysis_prompt.txt` - Frame analysis pattern detection
  - `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/synthesis_prompt.txt` - Pattern synthesis into decision framework

**No Other LLM Providers:**
- No OpenAI, Gemini, Replicate, or ComfyUI API calls in codebase
- ComfyUI and Remotion prompts generated as text files (future Phase 2 integration)

## Data Flow & Communication

**Inter-Agent Communication:**
- Manifest slices: `.claude/scratch/manifest_slice_N.json` (prepared by main pipeline, read by analysis subagents)
- Analysis results: `.claude/scratch/analysis_batch_N.json` (written by subagents, merged by pipeline)
- Merged analysis: `.claude/scratch/merged_analysis.json` (prepared for synthesis)
- Synthesis input: `.claude/scratch/synthesis_input.txt` (prepared by stage 6, read by synthesis subagent)
- Final output: `context/visual-references/[video-title]/VISUAL_STYLE_GUIDE.md` (written by synthesis subagent)

**Context Sharing Between Agents (Phase 1):**
- Reference scripts: `context/script references/` → Agent 1.3 (Writer) for style extraction
- Channel DNA: `context/channel/channel.md` → Agent 1.1 (Channel Assistant) for topic selection
- Competitor data: `context/competitors/` → Agent 1.1 for novelty filtering
- Visual style guides: `context/visual-references/[video-title]/VISUAL_STYLE_GUIDE.md` → Agent 1.4 (Visual Orchestrator), Agent 2.2 (Generative Visual Engine)

## Constraints

**No API Keys or Cloud Services:**
- All integrations operate on public content (YouTube public videos, web scraping)
- No OAuth, authentication tokens, or credentials required
- No cloud storage, external databases, or email services

**Subprocess Security:**
- Command arguments passed as lists (no shell=True), preventing shell injection
- stderr captured on failure with explicit error messages
- Exit code checking on all external tool invocations

**Video Format Constraints:**
- Maximum resolution: 1080p (yt-dlp format constraint)
- Audio: Best available quality, merged with video
- Subtitles: English auto-generated VTT (YouTube auto-caption API), user-provided .vtt/.srt/.txt as fallback

---

*Integration audit: 2026-03-11*
