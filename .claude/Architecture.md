# Pipeline Architecture

Automated documentary video generation pipeline, orchestrated by Claude Code via skill invocations. No application entry point — the pipeline is driven entirely through skills.

## Critical Architecture Rules

**For skill routing, folder map, and conventions, see `CLAUDE.md`.
For detailed skill workflows and schemas, see each skill's `SKILL.md`.**

> Architecture rules (zero LLM wrappers, heuristic vs. deterministic separation, CONTEXT.md maintenance) live in `CLAUDE.md` — they apply globally.

---

## Infrastructure Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Scraper | crawl4ai | Web scraping with domain-isolated browser contexts |
| Database | SQLite (`data/channel_assistant.db`) | Relational data: competitors, videos, stats |
| Asset Library | LanceDB (`D:/VideoLibrary/`) | Semantic vector search for video clips |
| Knowledge System | Filesystem | Context-engineering via CONTEXT.md routing |

**Database separation:** SQLite stores relational data. LanceDB stores vectors for similarity search. Both are file-based embedded databases — no servers.

---

## Pipeline Parallelism

The pipeline has parallel pairs to minimize total time:

```
Phase 1: Narrative Engineering

  channel-assistant → researcher ─┬─► writer ──────────┬─► shot-planner
                                  └─► media-scout ─────┘

Phase 2: Asset Pipeline

  media_leads.json ─┬─► asset-downloader ─► asset-analyzer ─► edit-sheet-compiler
  shotlist.json ────┘
  shotlist.json ────────► vector-generation (planned)
```

- After Research completes, **Media Scout** and **Writer** run in parallel — both depend on Research.md but not on each other.
- After the Shot Planner produces the shotlist, **Asset Downloader** downloads all video assets (YouTube + archive.org), then **Asset Analyzer** processes staged videos. **Edit Sheet Compiler** compiles all assets into a numbered project folder with a formatted edit sheet. **Vector Generation** can run in parallel with the asset pipeline — it reads the shotlist but serves different shot types.

---

## Asset Library

Persistent, cross-project semantic video search engine. Every indexed channel enriches the library for all future projects. Any skill can query it to find clips by natural language description.

**Location:** `D:/VideoLibrary/` — video files and index live outside the project tree, shared across all video projects.

**Component Stack:**

| Component | Tool | Role |
|-----------|------|------|
| Download | yt-dlp | Batch download curated YouTube channels at 720p max |
| Scene Detection | PySceneDetect | Detect scene boundaries (ContentDetector, threshold-based) |
| Frame Extraction | ffmpeg | Extract representative frame (middle) per scene |
| Embedding Model | Qwen3-VL-Embedding-8B (INT4) | Generate semantic embeddings for scenes and queries |
| Vector Storage | LanceDB | Store and search embeddings (embedded, file-based) |
| Clip Extraction | ffmpeg | Cut matched segments from source videos |

**LanceDB Schema** (one row per detected scene):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `{channel}_{video_id}_{scene_num}` |
| `embedding` | vector[768] | Qwen3-VL-Embedding output (Matryoshka 768-d) |
| `video_path` | string | Relative path from VideoLibrary root |
| `start_sec` | float | Scene start timestamp |
| `end_sec` | float | Scene end timestamp |
| `channel` | string | Source channel slug |
| `title` | string | Video title |

**CLI Commands:**

| Command | Function |
|---------|----------|
| `python -m asset_manager index` | Download and index an entire YouTube channel (resumable) |
| `python -m asset_manager search` | Find clips matching a text description (returns ranked results with timestamps) |
| `python -m asset_manager extract` | Cut a matched segment to a project's assets folder (ffmpeg stream copy) |
| `python -m asset_manager status` | Report library status (channels, scene counts, index size) |

---

## Asset Categories

Per-project asset directories under `projects/N. [Title]/assets/`:

**Pipeline-sourced (skills + user):**

| Directory | Contents | Source |
|-----------|----------|--------|
| `archival/` | Real footage AND photos from the era/event — news clips, home video, portraits, mugshots, press photos | Media Scout (images) → asset-downloader (videos) → asset-analyzer |
| `documents/` | Newspaper clippings, document scans, wiki screenshots, web page captures | Media Scout downloads |
| `broll/` | Atmospheric/conceptual footage (non-cartoon) — industrial films, nature, urban atmosphere | Shot Planner (leads) → asset-downloader → asset-analyzer |
| `cartoon_broll/` | Old cartoon clips used as conceptual b-roll | Shot Planner (leads) → asset-downloader → asset-analyzer |
| `vectors/` | Flat silhouette compositions | Vector Generation (planned — ComfyUI) |

**Editor handles manually (DaVinci Resolve):**
- All text elements (quote cards, testimony cards, date cards, keyword stingers, warning cards)
- Motion graphics (animated diagrams, kinetic typography)
- Backgrounds, overlays, effects
- Color grading, film grain, vignettes, CRT/VHS effects
- All glitch/distortion effects
- Maps and geographic visuals

---

## Vector Generation (Planned)

> **Status:** Not yet implemented.

- **Function:** Generate flat silhouette vector compositions from shotlist briefs using a ComfyUI generate → edit workflow. Each brief produces 1-3 sequential beats depicting a change in state.
- **Tools:** ComfyUI — generation model + edit model (specific models to be validated against RTX 4070 12GB VRAM budget).
- **Logic:**
  1. **Beat 1 (generate):** Base composition — flat vector silhouette scene. Compositions describe subject, pose, and spatial arrangement only (no color, effects, or lighting — editor decisions).
  2. **Beat 2+ (edit):** Feed previous beat's output into edit model. Max 2 edits per base image to avoid artifact accumulation.
- **Scope:** Vector/silhouette generation only. Realistic AI-generated imagery is out of scope and violates the channel's hard constraints (see `VISUAL_STYLE_GUIDE.md`).
- **Output:** `projects/N. [Title]/assets/vectors/` + generation log.

**Edit Model Prompting Best Practices:**
- Be specific: use accurate descriptions and clear action verbs
- Directly name the subject: "The seated group of figures" not "they"
- Explicitly state what should remain unchanged: "Maintain the same [style/composition/pose]"
- Start simple, then build on successful results
- Max 2 sequential edits per base image to avoid visual drift

---

## Source Policy

No paid or subscription sources. No generic footage marketplaces — they feel cheap and don't match the channel aesthetic. Primary sources:
- Internet Archive (Prelinger Archives, British Pathé, PD animation collections)
- Local Asset Library (LanceDB-indexed video clips)
- Web-scraped primary materials (images, documents, screenshots)
- YouTube clips surfaced as leads for human review
