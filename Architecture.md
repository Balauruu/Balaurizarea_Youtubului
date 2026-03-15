*description:*  Automated documentary video generation pipeline, optimized for generating narrative-driven video content. This pipeline is executed by a CLI-based coding agent (Claude Code.). The agent itself is the orchestrator.

The pipeline state will be managed via Claude Code invoking specific skills. Each skill/agent outputs markdown or JSON artifacts, which are then read by the next skill/agent in the pipeline.

*Do not write wrapper code for LLM APIs. LLM reasoning is provided natively by the runtime environment (being run in claude code).*

# CRITICAL ARCHITECTURE RULES

1. **ZERO LLM API WRAPPERS:** Never write code that initializes LLM SDKs (`@anthropic-ai/sdk`, `openai`, etc.). All reasoning and orchestration is handled natively by Claude Code. LLM API Wrappers can be used only if are part of an essential tool for my workflow.
2. **SEPARATION OF CONCERNS:** PROMPT VS. CODE
Before executing any task, explicitly classify it as:
- [HEURISTIC]: Requires logic, narrative design, or evaluation. Solved via Claude Code skills and prompt files. No code written.
- [DETERMINISTIC]: Requires structured data manipulation, scraping, or media rendering. Solved via code.

## Requirements:

- Must be an agentic framework with specific agents created along with their skills and tool calls.
- Must be context-engineered

## Pipeline:

- **Scraper: Crawl4ai** (with domain-isolated browser contexts)
- **Database:** SQLite (`data/channel_assistant.db`) for competitors & videos
- **Knowledge System/Context-engineering:** Filesystem

### Phase 1: Narrative Engineering ✅ SHIPPED

This phase manages the intellectual rigor of the documentary. All agents are implemented and validated (252 tests passing).

- **Agent 1.1: Channel Assistant (Strategy & Ideation)** ✅
    - **Skill:** `channel-assistant`
    - **Main Function:** Select viable topics for future videos.
    - **Logic:** Filters for obscurity, complexity and shock factor. Rejects previously covered topics via cosine similarity (threshold 0.85) against `past_topics.md`.
    - **Capabilities:**
        - `cmd_add` / `cmd_scrape` — Register and scrape competitor YouTube channels via yt-dlp into SQLite
        - `cmd_analyze` — Statistical outlier detection (2× median threshold), topic clusters, title patterns
        - `cmd_topics` — Generate 5 scored topic briefs via [HEURISTIC] Claude reasoning
        - `cmd_init_project` — Create `projects/N. [Title]/` with metadata.md (title variants, description)
        - Trend scanning — YouTube autocomplete + DuckDuckGo search convergence
    - **Output:** 5 topic briefs with scores. User selects from chat → project directory created with metadata.md.

    ```
    ## Topic Brief Schema
    - **title**: Working title (max 80 chars, YouTube-optimized)
    - **hook**: The core mystery in 1 sentence
    - **timeline**: Key events in chronological order (3-8 entries)
    - **complexity_score**: 1-10 (how layered is the story)
    - **obscurity_score**: 1-10 (how little-known)
    - **shock_factor**: 1-10 (emotional impact potential)
    - **estimated_runtime**: minutes
    ```

    - **Context:**

    ```
    - context/channel/channel.md -- Channel DNA
    - context/channel/past_topics.md -- Past topics to avoid duplication
    - context/competitors/analysis.md -- Competitor stats and outliers
    ```

    - **Storage:** SQLite database (`data/channel_assistant.db`) — channels + videos tables, upsert-safe

- **Agent 1.2: The Researcher** ✅
    - **Skill:** `researcher`
    - **Function:** Two-pass web research to build a factual foundation.
    - **Logic:**
        - **Pass 1 (Survey):** Broad scrape of 10-15 sources via crawl4ai with domain-isolated browser contexts. DuckDuckGo + Wikipedia URL building. Tier-based retry: Tier 1 (authoritative: 3 retries), Tier 2 (general: 1 retry), Tier 3 (social: skipped).
        - **Evaluation:** [HEURISTIC] Claude evaluates source credibility, selects deep-dive targets.
        - **Pass 2 (Deepen):** Targeted deep-dive into primary sources identified in Pass 1.
        - **Write:** [HEURISTIC] Claude synthesizes all sources into a 9-section narrative dossier.
    - **Budget Guard:** Max 15 total source files across both passes.
    - **Output:**
        - `projects/N. [Title]/research/Research.md` — 9-section narrative dossier
        - `projects/N. [Title]/research/media_urls.md` — Visual media catalog grouped by asset type
        - `projects/N. [Title]/research/source_manifest.json` — Source verdicts + deep-dive URLs

    ```
    ## Research Dossier Schema (9 sections)
    - **subject_overview**: 500-word summary
    - **timeline**: Detailed chronological events with sources
    - **key_figures**: People involved, roles, quotes
    - **primary_sources**: Official documents, court records, interviews
    - **secondary_sources**: News articles, books, documentaries
    - **media_inventory**: URLs of available images, videos, audio recordings
    - **contradictions**: Conflicting accounts across sources
    - **unanswered_questions**: Gaps that create narrative tension
    - **source_reliability**: Credibility rating per source
    ```

    - **Context:**

    ```
    - context/channel/channel.md -- Channel DNA
    - researcher/CONTEXT.md -- Stage contract
    - projects/N/metadata.md -- Topic brief
    ```

- **Skill 1.3: style_extraction** ✅
    - **Skill:** `style-extraction`
    - **Type:** [HEURISTIC] — zero Python code, Claude does all reasoning
    - **Function:** Reads reference scripts from `context/script-references/`, extracts voice rules, arc templates, transition phrases, and open ending patterns.
    - **Output:** `context/channel/STYLE_PROFILE.md` — behavioral ruleset with 5 Universal Voice Rules, narrative arc templates, transition phrase library, and open ending template.
    - **One-time operation** — re-run only when reference scripts change.

- **Agent 1.3: The Writer** ✅
    - **Skill:** `writer`
    - **Function:** Converts the research dossier into a narrated video script.
    - **Logic:** Stdlib-only CLI loads Research.md, STYLE_PROFILE.md, and channel.md. [HEURISTIC] Claude generates 4-7 chapters of pure narration (3,000-7,000 words) following the style profile rules.
    - **Output:** `projects/N. [Title]/Script.md` — pure narration text, no stage directions or visual cues.
    - **Context:**

    ```
    - context/channel/channel.md -- Channel DNA
    - context/channel/STYLE_PROFILE.md -- Voice behavioral ruleset
    - context/script-references/ -- Full reference scripts
    - projects/N/research/Research.md -- Research dossier
    ```

- **Utility Skill: Visual Style Extractor (v4)**
    - **Skill:** `visual-style-extractor`
    - **Function:** Extracts visual patterns from a reference YouTube video into reusable building blocks for the Visual Orchestrator (Agent 1.4).
    - **Architecture:** 6-stage pipeline (acquire → scene detect → dedup → align → contact sheets → synthesize). Two-pass v4: Pass 1 extracts patterns from contact sheets via parallel subagents, Pass 2 synthesizes patterns into 10-15 building blocks via LLM synthesis subagent.
    - **Output:** `context/visual-references/[Video]/VISUAL_STYLE_GUIDE.md` — building blocks with usage rules, pacing/sequencing rules, type selection decision tree.
    - **Dependencies:** scenedetect, imagededup, Pillow, numpy, webvtt-py, pysrt, ffmpeg, yt-dlp

- **Agent 1.4: Visual Orchestrator (The Director)** ⏳ NOT YET IMPLEMENTED
    - ***Function:***  Parses the script to map visual continuity and determine the necessary media for every scene. Outputs a loose shot list of narrative needs — not strict asset types.
    - **Output:** `shotlist.json`

    ```json
    {
      "shots": [
        {
          "id": "S001",
          "chapter": "intro",
          "narrative_context": "Narrator describes the remote mountain commune in 1970s Mexico",
          "visual_need": "Remote rural settlement, mountainous terrain, 1970s feel",
          "suggested_types": ["archival_video", "archival_photo", "broll"]
        }
      ]
    }
    ```

    **Shot Entry Fields:**
    - **id**: Unique shot identifier (S001, S002, ...)
    - **chapter**: Script chapter this shot belongs to
    - **narrative_context**: What the narrator is saying during this shot
    - **visual_need**: Free-text description of what visual is needed (intentionally loose)
    - **suggested_types**: Hints, not constraints — acquisition agent can use any type that fits

    **Design Principles:**
    - No duration, priority, effects, transitions, or post-production instructions — those are the editor's domain
    - `needed_assets.json` is no longer a separate output — the manifest serves this role


---

### Phase 2: Asset Pipeline ⏳ NOT YET IMPLEMENTED

This phase translates the shot list into tangible media assets. Agents run sequentially, each triggered manually by the user.

**Architecture:** Sequential pipeline. Each agent reads/writes a shared `manifest.json` at `projects/[Video Title]/assets/manifest.json`.

**Source Policy:** All footage and media must be free (public domain, CC0, or Creative Commons). No paid or subscription sources.

**Tools:** Crawl4ai for web scraping, yt-dlp for video downloads.

```
Agent 1.4 writes shotlist.json
    |
Agent 2.1 (Media Acquisition) — bulk scrape + gap analysis
    |
Agent 2.2 (Vector Generation) — ComfyUI prompts for gaps
    |
Agent 2.3 (Remotion Animations) — motion graphics [details deferred]
    |
Agent 2.4 (Asset Manager) — number, consolidate, final manifest
```

- **Agent 2.1: Media Acquisition**
    - **Function:** Two-pass design. Sources all relevant media for the topic.
    - **Input:** Reads only `shotlist.json` (not the script — Agent 1.4 already distilled the script into shot needs).
    - **Pass 1 — Bulk Acquisition:**
        - Reads shotlist.json to understand the topic (era, location, key figures, events)
        - Builds search queries from the topic context
        - Scrapes free/public domain sources for everything relevant
        - Downloads into type folders, unnumbered, with descriptive filenames
        - Writes each asset as an entry in `manifest.json`
    - **Pass 2 — Gap Analysis [HEURISTIC]:**
        - Matches acquired assets to shot list entries
        - Updates manifest.json with shot mappings
        - Outputs unmatched shots into the `gaps` section for downstream agents
    - **Output:** Downloaded assets in type folders + manifest.json with mappings and gaps
    - **Source Domains:**
        - Tier 1: archive.org, loc.gov, archives.gov, commons.wikimedia.org
        - Tier 2: publicdomainreview.org, images.nasa.gov, nps.gov, pdimagearchive.org, nationalarchives.gov.uk
        - Tier 3 (screenshots): en.wikipedia.org, britannica.com, news sites
        - Old cartoons: archive.org/details/19201928publicdomainanimation, publicdomainreview.org, LOC National Film Registry PD list, Wikimedia Commons animated shorts category
        - YouTube (via yt-dlp) for CC-licensed and public domain footage
    - **Rules:** Verify soundtracks on old cartoons are also PD (video may be PD but added music may not)
- **Agent 2.2: Vector Generation (ComfyUI)**
    - **Function:** Generates vector assets for shots that couldn't be filled by acquisition.
    - **Logic:** Reads `gaps` section of manifest.json. [HEURISTIC] Generates ComfyUI prompts optimized for Z-image turbo. Updates manifest and marks gaps as filled.
    - **Scope:** Vector/figure generation only. Realistic AI-generated b-roll is out of scope — gaps requiring realistic imagery remain unfilled for the editor to address manually.
    - **Output:** Vector images in `assets/vectors/`, manifest.json updated.
- **Agent 2.3: Animation Agent (Remotion)**
    - **Function:** Renders motion graphics (maps, silhouettes, diagrams, other animations).
    - **Logic:** Details deferred to later design session.
    - **Interface:** Reads shotlist.json, can use vectors from Agent 2.2, outputs to `assets/animations/`, updates manifest.json.
    - **Output:** `.mp4` or `.mov` files.
- **Agent 2.4: Asset Manager**
    - **Function:** Final consolidation and sequential numbering.
    - **Logic:** Reads manifest.json. Assigns sequential prefixes based on order of appearance in shotlist.json (e.g., `001_compound_aerial.mp4`). Assets mapped to multiple shots get the number of their first appearance. Moves unmatched assets to `_pool/`. Sets remaining gaps to `unfilled`.
    - **Output:** Numbered assets in type folders + final manifest.json.

---

### Asset Categories

**Pipeline-acquired (Agent 2.1):**
- `archival_footage/` — Video clips from the era/event
- `archival_photos/` — Period photographs, mugshots, press photos
- `documents/` — Newspaper clippings, document scans, wiki screenshots, web page captures
- `broll/` — Atmospheric/illustrative footage including old cartoons

**Pipeline-generated (Agent 2.2):**
- `vectors/` — ComfyUI Z-image turbo generated figures and assets

**Pipeline-generated (Agent 2.3):**
- `animations/` — Remotion-rendered motion graphics (maps, silhouettes, diagrams)

**Unmatched:**
- `_pool/` — Assets acquired but not mapped to any shot (kept for manual use)

**Editor handles manually (DaVinci Resolve):**
- All text elements (quote cards, testimony cards, date cards, keyword stingers, warning cards)
- Backgrounds, overlays, effects
- Color grading, film grain, vignettes, CRT/VHS effects
- All glitch/distortion effects

### Output Folder Structure

```
projects/1. [Video Title]/
  metadata.md
  research/
    Research.md             # 9-section narrative dossier
    media_urls.md           # Visual media catalog
    source_manifest.json    # Source verdicts
  Script.md
  shotlist.json             # (Phase 2)
  assets/                   # (Phase 2)
    archival_footage/       # 001_compound_aerial.mp4
    archival_photos/        # 002_leader_portrait.jpg
    documents/              # 003_wikipedia_article.png
    broll/                  # 004_rural_workers.mp4 (old cartoons go here)
    vectors/                # 009_silhouette_leader.png
    animations/             # 010_map_mexico.mp4
    _pool/                  # unmatched extras (unnumbered)
    manifest.json
```

### Manifest Schema

The manifest is the central coordination artifact between all Phase 2 agents. It lives at `assets/manifest.json` from the moment Agent 2.1 creates it.

```json
{
  "project": "The Cult of XYZ",
  "assets": [
    {
      "filename": "compound_aerial.mp4",
      "numbered_filename": null,
      "folder": "archival_footage",
      "description": "Aerial view of remote mountain settlement, 1970s film stock",
      "mapped_shots": ["S001", "S014"],
      "acquired_by": "agent_2.1"
    }
  ],
  "gaps": [
    {
      "shot_id": "S002",
      "visual_need": "Portrait or silhouette of male authority figure",
      "status": "pending_generation"
    }
  ]
}
```

**Gap status lifecycle:** `pending_generation` → `filled` (by Agent 2.2 or 2.3) → or `unfilled` (set by Agent 2.4 as terminal state)

### Resources:

Crawl4AI:
https://github.com/unclecode/crawl4ai

Context-Engineering:
https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering
