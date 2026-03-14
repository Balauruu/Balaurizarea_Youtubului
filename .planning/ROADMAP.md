# Roadmap: Channel Automation Pipeline

## Milestones

- ✅ **v1.0 Channel Assistant** — Phases 1-6 (shipped 2026-03-11)
- 🚧 **v1.1 The Researcher** — Phases 7-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 Channel Assistant (Phases 1-6) — SHIPPED 2026-03-11</summary>

- [x] Phase 1: Scraping Infrastructure + Data Model (2/2 plans) — completed 2026-03-11
- [x] Phase 2: Query Layer + Competitor Analysis (3/3 plans) — completed 2026-03-11
- [x] Phase 3: Topic Generation + Scoring (2/2 plans) — completed 2026-03-11
- [x] Phase 4: Project Initialization + Metadata (2/2 plans) — completed 2026-03-11
- [x] Phase 5: Trend Scanning + Content Gaps (2/2 plans) — completed 2026-03-11
- [x] Phase 6: Tech Debt Cleanup + OUTP-02 Wiring (1/1 plan) — completed 2026-03-11

</details>

### 🚧 v1.1 The Researcher (In Progress)

**Milestone Goal:** Build a niche-agnostic web research agent that takes any documentary topic and produces a structured Research.md dossier optimized for the scriptwriting agent.

## Phases (v1.1)

- [x] **Phase 7: Scraping Foundation** - crawl4ai integration layer with domain isolation, retry, source tiering, and topic input (completed 2026-03-12)
- [ ] **Phase 8: Survey Pass (Pass 1)** - CLI survey subcommand that fetches broad sources and produces a JSON source manifest
- [ ] **Phase 9: Deep-Dive Pass (Pass 2)** - CLI deepen subcommand that reads the source manifest and fetches targeted primary sources
- [ ] **Phase 10: Dossier Output** - Synthesis prompt, writer.py, and cmd_write that produce Research.md and media_urls.md

## Phase Details

### Phase 7: Scraping Foundation
**Goal**: The agent has a reliable, battle-tested scraping layer that handles browser context contamination, anti-bot failures, and source tiering — so every phase built on top of it never has to touch scraping internals.
**Depends on**: Nothing (first v1.1 phase)
**Requirements**: SCRP-01, SCRP-02, SCRP-03, RSRCH-01
**Success Criteria** (what must be TRUE):
  1. User can run `cmd_survey` with a topic string and the agent locates the correct `projects/N. [Title]/` directory without error
  2. fetcher.py uses a fresh browser context per source domain — a failed fetch on one domain does not corrupt subsequent fetches from other domains
  3. Any fetch returning fewer than 200 characters triggers a retry and is logged as a failed fetch, not silently dropped
  4. Sources are classified into tiers before any request is made — Tier 3 sources are skipped entirely and logged as do-not-attempt
**Plans**: 2 plans

Plans:
- [ ] 07-01: fetcher.py — crawl4ai wrapper with domain-isolated contexts, retry, and minimum-content verification
- [ ] 07-02: url_builder.py + source tier config, RSRCH-01 topic input + project directory resolution

### Phase 8: Survey Pass (Pass 1)
**Goal**: Users can run a single command that scrapes 10-15 broad sources for any documentary topic, stores all content in scratch (never in conversation context), and produces a machine-readable JSON source manifest ready for Claude to evaluate.
**Depends on**: Phase 7
**Requirements**: RSRCH-02, RSRCH-04
**Success Criteria** (what must be TRUE):
  1. Running `cmd_survey [topic]` fetches 10-15 broad sources (Wikipedia, DuckDuckGo, news archives) and prints a summary table to stdout
  2. Every scraped page is written as an individual file under `.claude/scratch/researcher/` — no scraped content appears in conversation context
  3. The command produces a `source_manifest.json` file containing source metadata (URL, file path, word count, access quality) — not prose
  4. The JSON manifest schema is locked and documented so Phase 9 can read it without ambiguity
**Plans**: 2 plans

Plans:
- [ ] 08-01-PLAN.md — test stubs + tiers.py Reddit reclassification + url_builder.py DDG expansion refactor
- [ ] 08-02-PLAN.md — cli.py DDG URL extraction + domain field + summary table + survey_evaluation.md prompt + SKILL.md workflow

### Phase 9: Deep-Dive Pass (Pass 2)
**Goal**: Users can run a second command that reads Claude's evaluated source manifest and fetches 5-10 targeted primary sources, completing the two-pass research architecture with full provenance from broad survey to primary source depth.
**Depends on**: Phase 8
**Requirements**: RSRCH-03
**Success Criteria** (what must be TRUE):
  1. Running `cmd_deepen` reads the JSON source manifest and fetches only the URLs Claude identified as deep-dive targets — not a fresh broad survey
  2. Pass 2 fetched content is written to `.claude/scratch/researcher/` as individual `pass2_src_N.md` files distinct from Pass 1 files
  3. The two passes together produce no more than 15 total fetched source files in scratch
**Plans**: 2 plans

Plans:
- [ ] 09-01: cmd_deepen subcommand — reads manifest, fetches targeted primary sources, writes to scratch

### Phase 10: Dossier Output
**Goal**: Users can run a final command that synthesizes all scraped content into a structured, Writer-ready Research.md dossier and a separate media_urls.md — the complete deliverable for Agent 1.3 and SKILL.md fully documents the end-to-end workflow.
**Depends on**: Phase 9
**Requirements**: DOSS-01, DOSS-02, DOSS-03, DOSS-04, DOSS-05, DOSS-06, DOSS-07, DOSS-08, DOSS-09, MEDIA-01, MEDIA-02
**Success Criteria** (what must be TRUE):
  1. Research.md contains a ~500-word subject overview, chronological timeline with source attribution, and key figures with names, roles, and at least one attributed quote each
  2. Research.md includes a contradictions section (conflicting accounts across sources) and an unanswered questions section (narrative tension hooks)
  3. Research.md contains 3-5 explicitly labeled narrative hooks and labeled direct quote callouts for scene anchoring, plus a correcting-the-record section where mainstream coverage contradicts primary sources
  4. All source entries in Research.md use structured credibility signals (source_type, corroborated_by, access_quality) — no scalar scores — and the total curated content is capped at ~2,000 words
  5. Research.md is written to `projects/N. [Title]/research/Research.md` and media_urls.md (URL, description, source type per entry) is written as a separate file in the same directory
**Plans**: 2 plans

Plans:
- [ ] 10-01: synthesis.md prompt — instructs Claude to produce schema-compliant structured JSON dossier from all scraped content
- [ ] 10-02: writer.py + cmd_write — formats JSON dossier to Research.md and media_urls.md with schema validation
- [ ] 10-03: SKILL.md finalization + integration test with a real topic end-to-end

## Progress

**Execution Order:** Phases execute in numeric order: 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Scraping Infrastructure + Data Model | v1.0 | 2/2 | Complete | 2026-03-11 |
| 2. Query Layer + Competitor Analysis | v1.0 | 3/3 | Complete | 2026-03-11 |
| 3. Topic Generation + Scoring | v1.0 | 2/2 | Complete | 2026-03-11 |
| 4. Project Initialization + Metadata | v1.0 | 2/2 | Complete | 2026-03-11 |
| 5. Trend Scanning + Content Gaps | v1.0 | 2/2 | Complete | 2026-03-11 |
| 6. Tech Debt Cleanup + OUTP-02 Wiring | v1.0 | 1/1 | Complete | 2026-03-11 |
| 7. Scraping Foundation | v1.1 | 2/2 | Complete | 2026-03-12 |
| 8. Survey Pass (Pass 1) | 1/2 | In Progress|  | - |
| 9. Deep-Dive Pass (Pass 2) | v1.1 | 0/1 | Not started | - |
| 10. Dossier Output | v1.1 | 0/3 | Not started | - |
