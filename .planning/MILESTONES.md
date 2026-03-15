# Milestones

## v1.3 The Director (Shipped: 2026-03-15)

**Phases completed:** 3 phases, 3 plans, 6 tasks
**Timeline:** 1 day (2026-03-15) | **Commits:** 23 | **Files changed:** 21 (+2,317 / -318)

**Key accomplishments:**
1. Visual Orchestrator stage contract (CONTEXT.md) — pipeline-reset invariant, [HEURISTIC] classification, deferred scope documented
2. Self-contained 182-line generation prompt with 10 consolidated building blocks, 9-field shot schema, 6-type routing table
3. 6 WRONG/RIGHT anti-pattern pairs for visual_need specificity (era + geography + subject, no production terms)
4. Synthetic worked example (Carol Marden case) demonstrates text_overlay, archival_photo, and animation routing
5. SKILL.md with 3-step invocation workflow and CLAUDE.md routing (4 integration points updated)
6. All 4 shipped agents now discoverable and invocable through CLAUDE.md task routing

**Tech debt:** 7 non-blocking items (human verification pending, Phase 15 nyquist incomplete, CLAUDE.md path inconsistency). See `milestones/v1.3-MILESTONE-AUDIT.md`.

---

## v1.2 The Writer (Shipped: 2026-03-15)

**Phases completed:** 2 phases, 4 plans, 8 tasks
**Timeline:** 6 days (2026-03-09 → 2026-03-15) | **Files changed:** 30 (+3,651 / -57)

**Key accomplishments:**
1. Zero-code style extraction skill — reconstructs auto-caption scripts and extracts behavioral voice rules into STYLE_PROFILE.md (371 lines)
2. STYLE_PROFILE.md with 5 Universal Voice Rules, Narrative Arc Templates with applicability labels, 16 verbatim transition phrases, Open Ending Template
3. Writer CLI context-loader (stdlib-only) — aggregates Research.md + STYLE_PROFILE.md + channel.md for script generation
4. 9-section generation prompt with hook formula, HOOK/QUOTE rules, all 5 voice rules, and Open Ending Template
5. End-to-end validated — Duplessis Orphans documentary script (7 chapters, 3,006 words) generated and human-approved
6. Full pipeline wired — CLAUDE.md routing tables updated for style-extraction and writer skills

**Tech debt:** 4 non-blocking items (stale writting_style_guide.md reference, CLAUDE.md routing overstatement, hook sentence-count inconsistency, script line count below plan spec). See `milestones/v1.2-MILESTONE-AUDIT.md`.

---

## v1.1 The Researcher (Shipped: 2026-03-14)

**Phases completed:** 4 phases, 8 plans, 4 tasks

**LOC:** 1,737 (Python + prompts) | **Tests:** 175 (full suite passing)
**Timeline:** 3 days (2026-03-12 → 2026-03-14) | **Commits:** 43

**Key accomplishments:**
1. crawl4ai scraping layer with domain-isolated browser contexts, tier-based retry, and minimum content validation
2. Two-pass research pipeline — broad survey (10-15 sources via Wikipedia + DuckDuckGo) followed by targeted primary source deep-dive
3. Structured dossier output — Research.md with 9 narrative-first sections including timeline, key figures, contradictions, narrative hooks, and correcting-the-record
4. Media URL cataloging — separate media_urls.md grouped by Architecture.md asset categories for direct Agent 2.1 consumption
5. End-to-end pipeline validated on "The Duplessis Orphans" with human-verified output quality

**Tech debt:** 3 non-blocking items (SKILL.md doc drift, bare except in writer.py, Windows backslashes in paths). See `milestones/v1.1-MILESTONE-AUDIT.md`.

---

## v1.0 Channel Assistant (Shipped: 2026-03-11)

**Phases:** 6 | **Plans:** 12 | **Tasks:** ~21
**LOC:** 7,018 Python | **Tests:** 175/175 passing
**Timeline:** 2 days (2026-03-09 → 2026-03-11) | **Commits:** 109

**Key accomplishments:**
1. Competitor intelligence infrastructure — yt-dlp scraping, SQLite storage, registry with 3 seed channels and 37 migrated videos
2. Data-driven competitor analysis — channel stats, outlier detection (2x median), topic clustering with saturation, title pattern extraction
3. Scored topic generation — 5 briefs per run with anchored rubrics, past-topic deduplication safety net
4. Project initialization pipeline — topic selection creates `projects/N. [Video Title]/` with metadata (3-5 title variants + description)
5. Trend scanning & content gaps — YouTube autocomplete scraping, search result parsing, cross-channel convergence detection
6. Full TDD coverage — 175 passing tests across 7 modules (registry, database, scraper, analyzer, topics, project_init, trend_scanner)

**Known tech debt:** 10 non-blocking items (documentation checkbox inconsistencies, first-run dependencies, architectural by-design patterns). See `milestones/v1.0-MILESTONE-AUDIT.md`.

---

