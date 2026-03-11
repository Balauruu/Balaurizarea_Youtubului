# Roadmap: Channel Assistant (Agent 1.1)

## Overview

Build a competitor intelligence and topic ideation skill for a dark mysteries YouTube channel. The build progresses from data infrastructure (scraping + storage) through analysis capabilities, topic generation with calibrated scoring, project initialization with metadata output, and finally trend scanning for content gap detection. Each phase delivers independently useful capability, and the full ideation flow activates at Phase 4 completion.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Scraping Infrastructure + Data Model** - Competitor registry, yt-dlp metadata scraping, SQLite storage with resilience (completed 2026-03-11)
- [x] **Phase 2: Query Layer + Competitor Analysis** - Channel stats, outlier detection, topic clustering, title pattern extraction (completed 2026-03-11)
- [ ] **Phase 3: Topic Generation + Scoring** - Scored topic briefs with calibrated rubrics and past-topic deduplication
- [x] **Phase 4: Project Initialization + Metadata** - Topic selection flow, project directory creation, title variants, description (completed 2026-03-11)
- [ ] **Phase 5: Trend Scanning + Content Gaps** - YouTube search trends, content gap detection, cross-channel convergence

## Phase Details

### Phase 1: Scraping Infrastructure + Data Model
**Goal**: User can register competitor channels and scrape their video metadata into a reliable, queryable database
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. User can add a competitor channel to a JSON config file and the system recognizes it
  2. User can trigger a scrape and video metadata (title, views, upload date, description, duration, tags) appears in the SQLite database
  3. Re-running the scraper updates existing records without creating duplicates (idempotent upserts)
  4. Scraper uses randomized delays between channels and falls back to cached data when yt-dlp fails
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md -- Data models, registry, database layer, and tests
- [x] 01-02-PLAN.md -- yt-dlp scraper, CLI entry point, and data migration

### Phase 2: Query Layer + Competitor Analysis
**Goal**: User can ask questions about competitor strategy and get data-backed answers
**Depends on**: Phase 1
**Requirements**: DATA-05, ANLZ-01, ANLZ-02, ANLZ-03
**Success Criteria** (what must be TRUE):
  1. User can view per-channel summary stats (total videos, average views, median views, upload frequency, most recent upload) formatted as a readable table
  2. System flags outlier videos that got 2x or more the channel median views, with the performance multiplier shown
  3. System groups competitor videos into topic clusters and reports which topics are oversaturated vs. underserved
  4. System extracts title patterns from top-performing videos (e.g., "Question + Location" or "Number + Superlative") and reports them
**Plans:** 3 plans (2 complete, 1 gap closure)

Plans:
- [x] 02-01-PLAN.md -- Analyzer module: channel stats, outlier detection, formatting, serialization (TDD)
- [x] 02-02-PLAN.md -- CLI analyze subcommand, report generation, heuristic data prep
- [x] 02-03-PLAN.md -- Gap closure: pytest config, heuristic topic clustering and title pattern analysis

### Phase 3: Topic Generation + Scoring
**Goal**: System generates scored topic briefs that surface obscure, high-impact topics the channel has not covered
**Depends on**: Phase 2
**Requirements**: ANLZ-04, OUTP-01, OUTP-02
**Success Criteria** (what must be TRUE):
  1. System generates 5 topic briefs per run, each following the Topic Brief Schema (title, hook, timeline, scores, estimated runtime)
  2. Each topic is scored on obscurity, complexity, shock factor, and verifiability using concrete rubric anchors (not subjective LLM judgment)
  3. Generated topics are checked against past_topics.md and duplicates or near-duplicates are rejected before presentation
**Plans:** 1/2 plans executed

Plans:
- [ ] 03-01-PLAN.md -- TDD: topics.py deterministic helpers (load inputs, dedup check, write briefs, chat cards)
- [ ] 03-02-PLAN.md -- CLI topics subcommand + anchored scoring rubric prompt

### Phase 4: Project Initialization + Metadata
**Goal**: User can select a topic and the system creates a ready-to-use project directory with YouTube-optimized metadata
**Depends on**: Phase 3
**Requirements**: OUTP-03, OUTP-04, OUTP-05, OUTP-06
**Success Criteria** (what must be TRUE):
  1. User selects a topic from the chat and system creates `projects/N. [Video Title]/` with correct sequential numbering
  2. System generates 3-5 YouTube title variants per topic, each using a different hook type (question, statement, revelation)
  3. System generates 1 YouTube description per topic
  4. Title variants and description are written to `metadata.md` in the project directory
**Plans:** 2/2 plans complete

Plans:
- [ ] 04-01-PLAN.md -- TDD: project_init.py module (directory creation, metadata writing, past_topics append)
- [ ] 04-02-PLAN.md -- CLI topics extension + heuristic prompt for title variants and description

### Phase 5: Trend Scanning + Content Gaps
**Goal**: Topic generation is enhanced with real-time trend data and content gap analysis
**Depends on**: Phase 2
**Requirements**: ANLZ-05, ANLZ-06, ANLZ-07
**Success Criteria** (what must be TRUE):
  1. System scrapes YouTube search results for niche keywords sorted by recency and surfaces what is currently trending
  2. System compares YouTube autocomplete search demand against competitor topic coverage and identifies underserved topics
  3. System detects when 3+ competitors cover adjacent topics within a 30-day window and flags the convergence
**Plans:** 2 plans

Plans:
- [ ] 05-01-PLAN.md -- TDD: trend_scanner.py module (autocomplete scraping, search results parsing, convergence queries, analysis.md updates)
- [ ] 05-02-PLAN.md -- CLI trends subcommand, heuristic prompt, topics.py gap injection

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5
Note: Phase 5 depends on Phase 2, not Phase 4. Phases 3-4 and Phase 5 could theoretically run in parallel after Phase 2 completes.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scraping Infrastructure + Data Model | 2/2 | Complete   | 2026-03-11 |
| 2. Query Layer + Competitor Analysis | 3/3 | Complete | 2026-03-11 |
| 3. Topic Generation + Scoring | 1/2 | In Progress|  |
| 4. Project Initialization + Metadata | 2/2 | Complete   | 2026-03-11 |
| 5. Trend Scanning + Content Gaps | 0/2 | Not started | - |
