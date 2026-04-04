# Pi Multi-Team Migration Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Scope:** Full migration of the documentary video pipeline from Claude Code skills to Pi CLI multi-team agent framework.

---

## 1. Overview

### Motivation

The current pipeline (9 Claude Code skills in a linear chain) has cross-skill context gaps concentrated in the media pipeline:
- Asset-analyzer discovers insights that shot-planner and media-scout should use, but can't feed back to them.
- Team-wide changes to the media pipeline require touching each skill individually.
- Cross-skill troubleshooting requires separate sessions with no shared context.

### Solution

Migrate to Pi CLI's multi-team agent framework. The three-tier delegation model (Orchestrator -> Leads -> Workers), persistent expertise files per agent, and shared conversation logs solve these gaps by introducing coordinating leads, cross-agent memory, and shared session awareness.

### Key Decision

Full migration to Pi CLI — not a hybrid approach. Pi CLI has feature parity with Claude Code (prompt caching, 1M context, extended thinking). The `.claude/` directory will be removed after migration.

---

## 2. Team Structure

**17 agents** (1 orchestrator + 4 leads + 12 workers). Style Extractor is counted among the 12 workers — it's a rare-use worker under Editorial Lead.

```
Orchestrator (Opus)
|
+-- Strategy Lead (Opus)
|   +-- Market Analyst (Sonnet)
|
+-- Editorial Lead (Opus)
|   +-- Researcher (Sonnet)
|   +-- Writer (Sonnet)
|   +-- Style Extractor (Sonnet) -- invoked rarely, when new reference scripts added
|
+-- Media Lead (Opus)
|   +-- Visual Researcher (Sonnet)
|   +-- Visual Planner (Sonnet)
|   +-- Asset Processor (Sonnet)
|   +-- Asset Curator (Sonnet)
|   +-- Compiler (Sonnet)
|
+-- Meta Lead (Opus)
    +-- Pipeline Observer (Sonnet)
    +-- Code Reviewer (Sonnet)
    +-- UX Improver (Sonnet)
```

### Team Purposes

| Team | Lead | Purpose |
|------|------|---------|
| Research | Strategy Lead | Market intelligence, topic selection, project initialization |
| Editorial | Editorial Lead | Research quality gate, script generation, script review (voice, pacing, engagement) |
| Media | Media Lead | Visual planning, resource gathering, asset acquisition, analysis, compilation |
| Meta | Meta Lead | Pipeline health, code quality, UX improvements |

---

## 3. Agent Definitions

### 3.1 Orchestrator

| Field | Value |
|-------|-------|
| **Model** | Opus |
| **Pi Skills** | high-autonomy, zero-micro-management, conversational-response, active-listener, mental-model |
| **Tools** | read, grep, find, ls, delegate |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/` only. Delete: none. |

Routes user requests to appropriate leads. Synthesizes final output. Manages human checkpoints (topic selection, asset review approval). Never writes project files or runs scripts.

### 3.2 Research Team

#### Strategy Lead

| Field | Value |
|-------|-------|
| **Model** | Opus |
| **Pi Skills** | zero-micro-management, conversational-response, active-listener, mental-model |
| **Tools** | read, grep, find, ls, delegate |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `strategy/`, `projects/` (project init only). Delete: none. |

Decides which topics to pursue based on Market Analyst intelligence. Generates topic suggestions with short briefs. Handles project initialization (creates directory + metadata.md). Maintains strategic channel-level memory.

#### Market Analyst

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output, verification-first |
| **Pipeline Skills** | `data-analysis.md` |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `strategy/`, `{{SESSION_DIR}}`. Delete: `{{SESSION_DIR}}` only. |

Competitor scraping + statistical analysis + trend discovery + trend analysis. Produces structured analysis with visualizations (dashboards, graphs). Has skills for statistical methods, NLP text processing, and data visualization.

**Inherits from:** channel-assistant (`cli.py`, `scraper.py`, `analyzer.py`, `trend_scanner.py`)

### 3.3 Editorial Team

#### Editorial Lead

| Field | Value |
|-------|-------|
| **Model** | Opus |
| **Pi Skills** | zero-micro-management, conversational-response, active-listener, mental-model |
| **Tools** | read, grep, find, ls, delegate |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/` only. Delete: none. |

Quality gate for Researcher and Writer. After research: evaluates completeness, source diversity, narrative hook potential. After writing: acts as Script Reviewer / Style Guardian — evaluates voice consistency, pacing, and engagement. Sends workers back with specific feedback if below threshold.

**Quality gate criteria:**
- Research: key claims sourced, >= 3 distinct source domains, timeline populated, no major narrative gaps
- Script: voice matches WRITTING_STYLE_PROFILE.md, pacing varied, hook formula applied, chapter count and word count in range, engaging narrative flow

#### Researcher

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Pipeline Skills** | `documentary-research.md` |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/research/`, `{{SESSION_DIR}}`. Delete: `{{SESSION_DIR}}` only. |

Three-pass research pipeline: survey web sources, deep-dive into primary documents, synthesize into structured dossier.

**Inherits from:** researcher skill (full package)
**Outputs:** `Research.md`, `entity_index.json`, `source_manifest.json`

#### Writer

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/script/`. Delete: none. |

Generates narrated chapter scripts from research + style profile. Pure prose, no stage directions. 4-7 chapters, 3,000-7,000 words.

**Inherits from:** writer skill (`generation.md` prompt)
**Outputs:** `Script.md`

#### Style Extractor

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `channel/voice/`, `channel/scripts/`. Delete: none. |

Extracts channel voice and style rules from reference scripts into WRITTING_STYLE_PROFILE.md. Invoked rarely — only when new reference scripts are added to `channel/scripts/`.

**Inherits from:** style-extraction skill (full package)
**Outputs:** `channel/voice/WRITTING_STYLE_PROFILE.md`

### 3.4 Media Team

#### Media Lead

| Field | Value |
|-------|-------|
| **Model** | Opus |
| **Pi Skills** | zero-micro-management, conversational-response, active-listener, mental-model |
| **Tools** | read, grep, find, ls, delegate |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/` only. Delete: none. |

The pipeline's most valuable coordinator. Manages the 5-step internal media pipeline. Curates team-level expertise from worker feedback — cross-agent patterns that no individual worker can see. Issues team-wide directives. Knows the archive collection landscape at a strategic level.

**Internal delegation sequence:** Visual Researcher -> Visual Planner -> Asset Curator (check) -> Asset Processor -> Asset Curator (promote) + Compiler

**Expertise file tracks cross-agent patterns:**
- "Asset Processor finding: concrete visual descriptions score 40% higher -> Visual Planner should generate more concrete search_queries"
- "Archive.org coverage weak for pre-1950 topics -> Visual Researcher should front-load YouTube discovery for historical topics"
- Rate limit budgets across agents, source quality patterns, editorial preferences

#### Visual Researcher

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Pipeline Skills** | `visual-narrative.md` |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/visuals/`, `projects/*/assets/archival/`, `projects/*/assets/documents/`, `{{SESSION_DIR}}`. Delete: `{{SESSION_DIR}}` only. |

Two-part role:
1. Define visual intent per chapter — mood, palette, era cues, composition guidance. Considers the channel's visual format vocabulary: first-hand footage, old movie b-roll, archive.org media, cartoon b-roll, and silhouette illustrations.
2. Gather all first-hand primary resources — photos, documents, web screenshots, Wikipedia captures. Everything relevant gets gathered regardless of whether a specific shot exists for it.

**Inherits from:** media-scout Pass 1 (`crawl_images.py`, `wiki_screenshots.py`, `search_queries.md`)
**Outputs:** `visual_brief.json` (NEW), `media_leads.json`, downloaded files in `assets/archival/` and `assets/documents/`

**Pipeline skill — `visual-narrative.md`:**
- Mood-to-visual mapping: emotional register -> visual choices
- Era-specific aesthetics: authentic visual references per decade
- Channel visual format vocabulary: first-hand footage, old movie b-roll, archive.org media, cartoon b-roll, silhouette illustrations
- Distinction between primary resources (gather broadly) and b-roll (curate selectively — not this agent's job)

#### Visual Planner

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output, verification-first |
| **Pipeline Skills** | `archive-search.md` |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/visuals/`, `{{SESSION_DIR}}`. Delete: `{{SESSION_DIR}}` only. |

Generates shotlist from script + visual brief. Assigns gathered primary resources to `find` shots. Curates b-roll (atmospheric, cartoon) and silhouettes for `curate`/`generate` shots — searches archive.org and YouTube, evaluates leads.

**Inherits from:** shot-planner (shotlist generation, equilibrium rules, `ia_search.py`) + media-scout Pass 2 (YouTube search, validation, scoring, `youtube_evaluation.md`)
**Outputs:** `shotlist.json`, `shotlist_edit_sheet.md`

**Pipeline skill — `archive-search.md`:**
- Internet Archive: collection-level browsing, metadata search, format selection
- Prelinger Archives: decade-based navigation, industrial film categories
- British Pathe / AP Archive: keyword + date range patterns
- YouTube: search query formulation, AI content detection, scoring (1-4 scale)
- Rate limiting: yt-dlp call budgets, batch pauses

#### Asset Processor

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, verification-first |
| **Pipeline Skills** | `media-evaluation.md` |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/assets/`, `projects/*/visuals/`, `{{SESSION_DIR}}`, `data/`. Delete: `{{SESSION_DIR}}` only. |

Downloads videos (YouTube + archive.org) then embeds, searches, and evaluates footage. Two operational modes backed by existing scripts. Presents candidates for user review. Exports approved clips.

**Inherits from:** asset-downloader (`download.py`) + asset-analyzer (`embed.py`, `search.py`, `ingest.py`, `export_clips.py`, `pool.py`, all references)
**Outputs:** `assets/staging/`, `download_manifest.json`, `asset_review.json`, extracted clips, catalog entries in `data/asset_catalog.db`

**Critical operational notes:**
- PE-Core conda env: `C:/Users/iorda/miniconda3/envs/perception-models/python.exe`
- GPU peak: ~4.6GB VRAM on RTX 4070
- Pool index: no file locking — one embed at a time
- YouTube: stop on first 429

#### Asset Curator

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `D:/VideoLibrary/`, `D:/Youtube/D. Mysteries Channel/3. Assets/`, `data/`. Delete: none. |

Manages global asset library. Two modes:
1. **Check** — before Asset Processor runs, search LanceDB for existing clips matching shotlist queries, report matches to avoid redundant downloads.
2. **Promote** — after Asset Processor finishes, identify global-worthy assets and promote to shared library with proper categorization.

**Inherits from:** edit-sheet-compiler's global asset logic
**Outputs:** `library_matches.json`, global library entries in `D:/VideoLibrary/`, copies in `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/`, catalog entries in `data/asset_catalog.db`

#### Compiler

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `projects/*/assets/`, `projects/*/`. Delete: none. |

Pipeline terminal step. Compiles all upstream outputs into a formatted edit sheet and organizes assets into a flat folder with standardized naming. Primary scope is UX — making the editor's experience in DaVinci Resolve as smooth as possible.

**Inherits from:** edit-sheet-compiler (`organize_assets.py`) minus global asset promotion
**Outputs:** `assets/` (flat, renamed: `S{NNN}_{name}.ext`), `edit_sheet.md`

### 3.5 Meta Team

#### Meta Lead

| Field | Value |
|-------|-------|
| **Model** | Opus |
| **Pi Skills** | zero-micro-management, conversational-response, active-listener, mental-model |
| **Tools** | read, grep, find, ls, delegate |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/` only. Delete: none. |

Coordinates pipeline improvement activities. Reviews worker findings and decides which optimizations to propose to the orchestrator/user. Prioritizes improvements by impact. Runs post-pipeline or on-demand.

#### Pipeline Observer

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Tools** | read, write, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, `{{SESSION_DIR}}`. Delete: none. |

Monitors cross-team patterns, cost/timing, rate limit budgets. Reads all team expertise files and detects patterns spanning teams. Proposes pipeline-level optimizations.

#### Code Reviewer

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output, verification-first |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, agent script directories. Delete: none. |

Reviews Python scripts across agents for quality, performance, and cross-script interaction correctness. Can propose and implement optimizations.

#### UX Improver

| Field | Value |
|-------|-------|
| **Model** | Sonnet |
| **Pi Skills** | precise-worker, active-listener, mental-model, structured-output |
| **Tools** | read, write, edit, bash, grep, find, ls |
| **Domain** | Read: everywhere. Write: `.pi/multi-team/`, agent prompt/template directories. Delete: none. |

Reviews pipeline outputs for usability — edit sheet readability, checkpoint experience, asset review presentation, dashboard clarity. Proposes formatting and interaction improvements.

---

## 4. Pipeline-Specific Behavioral Skills

Five new `.md` skill files in `.pi/multi-team/skills/`, beyond the 8 template skills:

| Skill | Used By | Purpose |
|-------|---------|---------|
| `data-analysis.md` | Market Analyst | Statistical methods (outlier detection, z-score), NLP text processing (title clustering, topic similarity), dashboard/graph generation (chart selection, matplotlib/seaborn) |
| `documentary-research.md` | Researcher | Multi-pass research methodology, source triangulation, primary source prioritization, source tier evaluation |
| `visual-narrative.md` | Visual Researcher | Mood-to-visual mapping, era-specific aesthetics, channel visual format vocabulary (first-hand footage, old movie b-roll, archive.org media, cartoon b-roll, silhouette illustrations) |
| `archive-search.md` | Visual Planner | Internet Archive/Prelinger/British Pathe search strategies, YouTube discovery and AI content detection, rate limiting awareness |
| `media-evaluation.md` | Asset Processor | Video quality assessment, relevance scoring, scoring calibration, query refinement strategies |

---

## 5. Expertise File Design

### Architecture

Each agent gets two types of expertise:

| Type | Updatable | Purpose |
|------|-----------|---------|
| Mental model (own) | Yes | Learned patterns, decisions, observations — grows across projects |
| Read-only references (injected) | No | Domain knowledge the agent consults but never modifies |

Mental models use the `.pi` template YAML format with sections: `system`, `key_files`, `decisions`, `patterns`, `observations`, `team_dynamics`, `open_questions`.

### Per-Agent Mental Model Contents

**Strategy Lead:** Topic performance patterns, channel growth decisions, content gap observations.

**Market Analyst:** Statistical thresholds, competitor signals that predict virality, title clustering patterns, seasonal trends, rate limiting incidents.

**Editorial Lead:** Review standards evolution, common script weaknesses (pacing, voice drift), revision patterns.

**Researcher:** Source reliability by domain, research depth per topic type, deep-dive success rates.

**Writer:** Chapter structure patterns, hook formula variations, voice application edge cases, Editorial Lead feedback patterns.

**Style Extractor:** Auto-caption detection patterns, extraction edge cases.

**Media Lead (most valuable):** Cross-agent patterns ("Asset Processor scoring correlates with Visual Planner query specificity"), archive coverage gaps by era/region, team-wide directive history, worker strengths and watch-fors.

**Visual Researcher:** Era-specific visual vocabulary, mood-to-asset-category mappings, gathering strategy effectiveness, source discovery patterns.

**Visual Planner:** Search query formulations that find good b-roll by category, archive collection coverage by era, visual register distributions editors liked, equilibrium rule adjustments.

**Asset Processor:** Scoring threshold adjustments from user calibration, rate limiting recovery, blank frame patterns by source, query refinement strategies, PE-Core scoring behavior.

**Asset Curator:** Library coverage map, most-reused assets, coverage gaps, channel quality ratings, promotion criteria.

**Compiler:** Asset naming conventions, edit sheet format preferences, match coverage patterns.

**Meta Lead:** Optimization proposals approved/rejected, cross-run improvement trends.

**Pipeline Observer:** Bottleneck patterns, token cost per agent per run, failure recovery patterns, cross-team correlations.

**Code Reviewer:** Code improvements proposed/accepted, common script bugs, performance patterns.

**UX Improver:** UX changes proposed/accepted, output readability issues, checkpoint friction points.

### Read-Only Reference Assignments

| Agent | Read-Only References |
|-------|---------------------|
| Researcher | `survey-evaluation.md`, `synthesis.md` |
| Writer | `generation.md` |
| Visual Researcher | `search-queries.md` |
| Visual Planner | `youtube-evaluation.md` |
| Asset Processor | `operational-guide.md`, `known-issues.md`, `scoring-guide.md`, `pe-core-usage.md` |
| Market Analyst | `topic-generation.md`, `trends-analysis.md` |

### Cross-Agent Feedback Flow

Worker reflection -> Lead curation -> Team expertise:

1. Worker completes task, writes observation to OWN expertise file.
2. Lead reviews worker expertise files after each delegation, identifies cross-agent patterns, promotes to OWN expertise file (team-level).
3. Next delegation cycle: lead includes relevant team-level context when delegating to workers.

Workers never write to each other's files. The lead curates cross-agent insights to prevent contradictions.

---

## 6. Delegation Flow

### Full Pipeline Run

```
USER: "New video on [topic]"

1. ORCHESTRATOR -> STRATEGY LEAD: "Analyze market, recommend topics"
   Strategy Lead -> Market Analyst: scrape, analyze, discover trends
   Strategy Lead: synthesize into topic suggestions with briefs
   -> Orchestrator -> USER: present topics

   USER: selects topic
   Strategy Lead: initialize project directory

2. ORCHESTRATOR -> EDITORIAL LEAD: "Research and write script"
   Editorial Lead -> Researcher: three-pass research
   Editorial Lead: QUALITY GATE (research sufficient?)
     NO -> Researcher: deepen weak sections
     YES -> continue
   Editorial Lead -> Writer: generate script
   Editorial Lead: QUALITY GATE (voice, pacing, engagement?)
     NO -> Writer: revise with specific feedback
     YES -> Orchestrator: script approved

3. ORCHESTRATOR -> MEDIA LEAD: "Handle all visuals"
   Media Lead -> Visual Researcher: define visual intent + gather resources
   Media Lead -> Visual Planner: generate shotlist + curate b-roll
   Media Lead -> Asset Curator: check global library for matches
   Media Lead -> Asset Processor: download + embed + evaluate + present
   -> Orchestrator -> USER: asset review checkpoint
   USER: approves/rejects segments
   Media Lead -> Asset Processor: export approved clips
   Media Lead -> Asset Curator: promote global-worthy assets
   Media Lead -> Compiler: compile edit sheet + organize assets

4. ORCHESTRATOR -> META LEAD: "Review this run" (post-pipeline)
   Meta Lead -> Pipeline Observer: analyze timing, costs, patterns
   Meta Lead -> Code Reviewer: audit scripts
   Meta Lead -> UX Improver: review output formats
```

### Human Checkpoints

| Checkpoint | When | User Decides |
|------------|------|-------------|
| Topic selection | After Strategy Lead presents briefs | Which topic to pursue |
| Asset review | After Asset Processor presents candidates | Approve/reject segments, adjust timestamps |

All other quality gates are handled by leads. User can always intervene via the orchestrator.

### Parallelism Opportunity

After research completes, Visual Researcher's gathering pass (needs Research.md + entity_index.json, not Script.md) could run in parallel with Writer. Visual intent definition waits for Script.md. The orchestrator decides based on the situation.

---

## 7. Migration Mapping

### Current Skill -> New Agent(s)

| Current Skill | Destination Agent(s) | What Migrates | What Changes |
|---|---|---|---|
| channel-assistant | Strategy Lead + Market Analyst | Lead: topic suggestion, project init. Analyst: `cli.py`, `scraper.py`, `analyzer.py`, `trend_scanner.py` | Analyst gains data-analysis skill. Lead synthesizes and recommends. |
| researcher | Researcher | Full three-pass pipeline, all prompts | Minimal change. Expertise file replaces insights.md. |
| writer | Writer | Script generation, `generation.md` prompt | Editorial Lead now gates quality. |
| style-extraction | Style Extractor (rare-use worker) | Full package, unchanged | Runs under Editorial Lead, invoked rarely. |
| shot-planner | Visual Planner (+ Visual Researcher gathering) | Planner: shotlist generation, equilibrium rules, `ia_search.py`, b-roll curation. | Reads visual_brief.json for richer shots. |
| media-scout | Visual Researcher (gathering) + Visual Planner (curation) | Researcher: Pass 1 (web crawl, screenshots). Planner: Pass 2 (YouTube search, scoring). | Two-pass monolith splits by function. |
| asset-downloader | Asset Processor (download mode) | `download.py`, YouTube + archive.org logic | Becomes operational mode within Asset Processor. |
| asset-analyzer | Asset Processor (analysis mode) | `embed.py`, `search.py`, `ingest.py`, `export_clips.py`, `pool.py`, all references | Becomes operational mode within Asset Processor. |
| edit-sheet-compiler | Compiler + Asset Curator | Compiler: `organize_assets.py`, edit sheet. Curator: global asset promotion. | Global promotion logic extracted to Asset Curator. |

### New Agents (no current skill equivalent)

| Agent | Purpose |
|-------|---------|
| Visual Researcher | Visual intent definition + primary resource gathering |
| Asset Curator | Global asset library management |
| Pipeline Observer | Cross-team pattern detection, cost/timing |
| Code Reviewer | Script quality, performance, cross-script interactions |
| UX Improver | Output format quality, checkpoint UX |

---

## 8. Configuration

### Directory Structure

```
Channel-automation V4/
+-- .pi/
|   +-- multi-team/
|       +-- multi-team-config.yaml
|       +-- agents/              (17 agent .md files)
|       +-- expertise/           (17 mental model .yaml files)
|       |   +-- read-only/       (migrated prompts + references)
|       +-- skills/              (8 template + 5 pipeline behavioral skills)
|       +-- scripts/
|       |   +-- strategy/        (cli.py, scraper.py, analyzer.py, trend_scanner.py)
|       |   +-- media/           (crawl_images.py, wiki_screenshots.py, ia_search.py,
|       |   |                     download.py, embed.py, search.py, ingest.py,
|       |   |                     export_clips.py, pool.py, organize_assets.py)
|       |   +-- data/            (catalog.py)
|       +-- sessions/            (auto-created per session)
|       +-- logs/
|
+-- channel/                     UNCHANGED
+-- strategy/                    UNCHANGED
+-- projects/                    UNCHANGED
+-- data/                        UNCHANGED
+-- CLAUDE.md                    REWRITTEN for Pi
+-- CONTEXT.md                   REWRITTEN (simplified)
```

### Shared Context (loaded by all agents)

| File | Why |
|------|-----|
| `CLAUDE.md` | Project overview, conventions, architecture rules |
| `channel/channel.md` | Channel DNA — identity, audience, pillars |
| `channel/visuals/VISUAL_STYLE_GUIDE.md` | Visual vocabulary for all agents |

### File Migration

| Source | Destination | Action |
|--------|-------------|--------|
| `.claude/skills/*/scripts/*.py` | `.pi/multi-team/scripts/{team}/` | Move, reorganize by team |
| `.claude/skills/*/prompts/*.md` | `.pi/multi-team/expertise/read-only/` | Move |
| `.claude/skills/*/references/*` | `.pi/multi-team/expertise/read-only/` | Move |
| `.claude/skills/*/insights.md` | `.pi/multi-team/expertise/*-mm.yaml` | Seed observations |
| `LEARNINGS.md` | `.pi/multi-team/expertise/media-lead-mm.yaml` | Seed, then archive |
| `.claude/skills/*/SKILL.md` | `.pi/multi-team/agents/*.md` | Rewrite as agent definitions |
| `.claude/Architecture.md` | `CLAUDE.md` + agent system prompts | Absorb, then remove |
| `.claude/` directory | Removed after migration | Archived first |

---

## 9. Migration Sequence

### Phase 0: Pre-Migration Setup
- Install and configure Pi CLI
- Verify features (delegate tool, sessions, expertise files, conversation log)
- Git commit clean baseline, create `migration` branch

### Phase 1: Foundation
- Copy `.pi` template into project
- Create `multi-team-config.yaml`
- Copy 8 template behavioral skills
- Write 5 pipeline-specific behavioral skills
- Rewrite `CLAUDE.md` and `CONTEXT.md` for Pi

### Phase 2: Script & Reference Migration
- Move Python scripts to `.pi/multi-team/scripts/` (reorganized by team)
- Move prompts to `.pi/multi-team/expertise/read-only/`
- Move references to `.pi/multi-team/expertise/read-only/`
- Audit scripts for hardcoded paths (update project-internal paths only)
- Verify all scripts execute from new locations

### Phase 3: Agent Definitions (team by team)
Build and validate one team at a time:
1. **Research Team** (3 agents: orchestrator, strategy-lead, market-analyst)
2. **Editorial Team** (4 agents: editorial-lead, researcher, writer, style-extractor)
3. **Media Team** (6 agents: media-lead, visual-researcher, visual-planner, asset-processor, asset-curator, compiler)
4. **Meta Team** (4 agents: meta-lead, pipeline-observer, code-reviewer, ux-improver)

### Phase 4: Expertise File Seeding
- Create 17 mental model YAML files from template
- Seed from existing insights.md files
- Seed Media Lead from LEARNINGS.md
- Assign read-only reference files in agent frontmatter

### Phase 5: Integration Testing
1. **Smoke test** — per-team delegation with minimal tasks
2. **Dry run** — media pipeline on an existing completed project
3. **Full run** — complete pipeline on a new topic
4. **Expertise validation** — verify mental models updated after run

### Phase 6: Cleanup
- Archive `.claude/skills/` to `_archive/`
- Remove `.claude/` directory references
- Update `CLAUDE.md` folder map
- Merge migration branch to main
- Delete archive after 2 successful runs

### Phase Dependencies

```
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6
```

Strictly sequential. Within Phase 3, teams are built one at a time. Within Phase 5, tests increase in scope.
