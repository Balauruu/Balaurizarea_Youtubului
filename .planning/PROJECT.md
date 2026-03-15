# Channel Automation Pipeline

## What This Is

An agentic documentary video generation pipeline for a YouTube channel focused on dark mysteries content. Claude Code itself is the orchestrator — it spawns sub-agents with skills to complete each phase. Three agents are shipped: Agent 1.1 (Channel Assistant) handles strategy and ideation, Agent 1.2 (The Researcher) performs two-pass web research, and Agent 1.3 (The Writer) generates narrated chapter scripts from research dossiers in the channel's extracted voice. Agent 1.4 (Visual Orchestrator) is next — parsing scripts into shot lists for the asset pipeline.

## Core Value

Surface obscure, high-impact documentary topics backed by competitor data and deep web research — not guesswork.

## Requirements

### Validated

- Competitor discovery and tracking (JSON registry, yt-dlp scraping, SQLite storage) — v1.0
- Cached competitor data with on-demand refresh (rate limiting, jittered delays, failure fallback) — v1.0
- Competitor analysis (per-channel stats, outlier detection, topic clustering, title patterns) — v1.0
- Topic generation (5 scored briefs per run, anchored rubrics, past-topic deduplication) — v1.0
- Trend awareness (YouTube autocomplete, search results, cross-channel convergence) — v1.0
- Topic selection flow (project directory creation, sequential numbering, metadata.md) — v1.0
- Metadata generation (3-5 title variants, 1 description per topic) — v1.0
- Domain-isolated crawl4ai scraping with tier-based retry and content validation — v1.1
- Two-pass research: broad survey (10-15 sources) → deep primary source dive — v1.1
- Structured Research.md dossier with timeline, key figures, contradictions, narrative hooks — v1.1
- Media URL cataloging (separate media_urls.md grouped by asset category) — v1.1
- Niche-agnostic research agent with manual topic input and project directory output — v1.1
- ✓ Style extraction from reference scripts → STYLE_PROFILE.md — v1.2
- ✓ Script generation from research dossier → numbered chapters with pure narration — v1.2

### Active

- [ ] Visual Orchestrator skill — parse Script.md and generate shotlist.json with per-shot narrative context and visual needs

### Out of Scope

- Upload scheduling or publishing automation — not part of this agent's scope
- Real-time monitoring or notifications — this runs on demand, not as a background service
- Social media analysis (Reddit, Twitter/X) — YouTube-only data sources for competitor intel
- Third-party analytics integration (SocialBlade, VidIQ) — adds complexity without clear ROI
- LLM API wrappers for reasoning — Architecture.md Rule 1
- PDF extraction (PyMuPDF/OCR) — add reactively when first PDFs encountered
- Paid source access (PACER, newspaper archives) — free sources only per Architecture.md
- NLP/spaCy style metrics — heuristic task, LLM reasoning is more effective
- Inline visual/production notes in script — Agent 1.4 (Visual Orchestrator) owns visual cues
- Automated fact-checking against external sources — Research.md is source of truth
- Word count gates or automated quality scoring — defer to human review

## Context

**Current state (v1.2 shipped):**
- Agent 1.1 (Channel Assistant): 7,018 LOC Python, 175 tests, full pipeline `scrape → analyze → trends → topics → project init`
- Agent 1.2 (The Researcher): 1,737 LOC Python + prompts, two-pass research `survey → deepen → write`, validated on real topic
- Agent 1.3 (The Writer): stdlib-only CLI + generation prompt, style extraction skill, `load → generate → Script.md`
- STYLE_PROFILE.md: 371-line channel voice behavioral ruleset (5 Universal Voice Rules, arc templates, transitions, open endings)
- SQLite database with 37 migrated competitor videos from 3 channels
- End-to-end validated: Duplessis Orphans topic from competitor analysis → research dossier → narrated script
- Full test suite passing across all agents

**Channel profile:** Dark history, true crime, unsolved mysteries. 20-50 min documentaries. Neutral, cinematic tone. Target audience: 22-38, intellectually curious.

## Constraints

- **Language:** Python only — no Node.js or JavaScript for scripting
- **No LLM API wrappers:** All reasoning handled natively by Claude Code runtime
- **Scraping tools:** yt-dlp for video/channel metadata, crawl4ai for web pages and search results
- **Storage:** SQLite via stdlib sqlite3 (zero external dependencies for channel-assistant)
- **Output location:** `projects/N. [Video Title]/` at repo root

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite over JSON for competitor DB | Queryable, handles growth, stdlib support | ✓ Good |
| yt-dlp subprocess over Python API | More stable, debuggable, consistent JSON output | ✓ Good |
| stdlib-only dependencies for channel-assistant | Zero install friction, no version conflicts | ✓ Good |
| Context-loader CLI pattern | CLI prints structured data, Claude does all reasoning | ✓ Good |
| Anchored scoring rubrics in prompt files | Consistent scoring across runs without code gates | ✓ Good |
| 5 topics per run | Focused shortlist, no decision fatigue | ✓ Good |
| Heuristic/deterministic separation | Matches Architecture.md Rule 2 perfectly | ✓ Good |
| TDD red-green for all deterministic code | 175+ tests caught regressions early | ✓ Good |
| crawl4ai with domain-isolated browser contexts | Prevents cross-domain contamination in scraping | ✓ Good |
| Two-pass research (survey → deep dive) | Broad coverage first, then targeted depth | ✓ Good |
| JSON source manifest between passes | Machine-readable, schema-locked, Claude evaluates | ✓ Good |
| Structured credibility signals (no scalar scores) | Richer than numbers, matches Architecture.md dossier schema | ✓ Good |
| Narrative-first dossier with HOOK/QUOTE callouts | Scriptwriter-optimized output, not raw research dump | ✓ Good |
| Writer handoff: factual only, no editorial guidance | Agent 1.3 owns narrative decisions, not Agent 1.2 | ✓ Good |
| Budget guard: max 15 total source files | Prevents context bloat across both passes | ✓ Good |
| Style extraction as [HEURISTIC] skill | Zero Python code, LLM reasoning more effective than NLP metrics | ✓ Good |
| Two-pass style extraction (reconstruct → extract) | Auto-caption reconstruction preserves narrator rhythm before analysis | ✓ Good |
| STYLE_PROFILE.md separates universal rules from arc templates | Prevents cult-arc overfitting on non-cult topics | ✓ Good |
| Writer CLI is stdlib-only context-loader | No LLM calls in code, Claude does all reasoning at generation time | ✓ Good |
| 9-section generation prompt | Self-contained prompt with all constraints, no implicit knowledge needed | ✓ Good |

## Current Milestone: v1.3 The Director

**Goal:** Build the Visual Orchestrator skill that parses finished scripts into structured shot lists, bridging narrative engineering (Phase 1) to the asset pipeline (Phase 2).

**Target features:**
- Parse Script.md chapter structure and narrative content
- Generate shotlist.json with per-shot visual needs and suggested asset types
- Pure [HEURISTIC] skill — zero Python code, Claude does all reasoning

---
*Last updated: 2026-03-15 after v1.3 milestone started*
