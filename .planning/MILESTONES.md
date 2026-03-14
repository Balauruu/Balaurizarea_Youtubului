# Milestones

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

