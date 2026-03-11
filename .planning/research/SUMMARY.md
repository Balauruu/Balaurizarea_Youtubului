# Project Research Summary

**Project:** Channel Assistant (Agent 1.1)
**Domain:** YouTube Competitor Intelligence & Topic Ideation
**Researched:** 2026-03-11
**Confidence:** HIGH

---

## Executive Summary

Agent 1.1 is a CLI-only, Claude Code-orchestrated competitor intelligence and topic ideation tool for a dark mysteries documentary channel. Its purpose is to track 10-30 competitor YouTube channels, analyze their content strategy, surface content gaps, and generate 5 scored topic briefs per run. The output feeds the rest of the pipeline: a selected topic becomes a `projects/N. Title/` directory that Agent 1.2 (Deep Research) reads to begin its work. Architecturally, the tool is a data pipeline with a heuristic cap — deterministic Python scripts handle all scraping and storage; Claude Code's native reasoning handles all analysis and topic generation.

The recommended approach is a 4-phase build: scraping infrastructure first (yt-dlp + SQLite storage), then query and analysis layer, then topic generation and project initialization, then advanced features like trend scanning. Each phase delivers independently useful capability. Two decisions are non-negotiable and must be made correctly in Phase 1: the data layer must be SQLite (not JSON files), and the scraping layer must be resilient from day one. Both decisions become very expensive to correct later — SQLite migration mid-project is tedious and error-prone, and a scraper without rate limiting will get the home IP banned within the first week of use.

The most important risk is infrastructure brittleness masquerading as a product problem. yt-dlp breaks every few weeks due to YouTube's active countermeasures, and stale data passed off as current degrades every downstream decision without obvious error signals. These failure modes are preventable through explicit engineering choices in Phase 1: retry/fallback logic, rate limiting with randomized delays, staleness tiers on every record, and a normalization layer between yt-dlp and storage. The LLM-facing risk is score drift in topic briefs — without concrete rubric anchors in the scoring prompt, obscurity and shock factor scores are not comparable across runs.

---

## Key Findings

### Recommended Stack

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| Python | 3.14.2 | Runtime | Already installed. Project constraint: Python only. |
| yt-dlp | 2026.2.4 | YouTube metadata extraction | Already installed. No API quotas. Use `extract_info(download=False)` exclusively — never download media. |
| SQLite (stdlib `sqlite3`) | bundled | Primary data store | Zero dependencies. ACID-safe. SQL aggregation native. Single file, works on Windows without configuration. |
| sqlite-utils | 3.39 | SQLite convenience layer | Upsert support, auto-schema. Reduces storage boilerplate to `db["table"].upsert_all(data, pk="id")`. Verify 3.14 compatibility on install; fallback is stdlib `sqlite3`. |
| crawl4ai | 0.8.x | Trend data scraping | Specified in Architecture.md. Async Playwright-based. Use only for non-YouTube sources — yt-dlp handles all structured YouTube data. Do not use crawl4ai on YouTube pages (11% noise ratio). |
| python-dateutil | 2.9.x | Date parsing | Parse yt-dlp upload dates (YYYYMMDD format), compute staleness intervals. |
| tabulate | 0.9.0 | Table formatting | Lightweight markdown table output for Claude Code chat. No color/styling overhead. |

**Total new pip installs:** 3 packages (sqlite-utils, tabulate, python-dateutil). crawl4ai installed separately in Phase 4 — it pulls in Playwright and browser binaries.

### Expected Features

**Must-have (P0 — table stakes):**
- Competitor channel registry (JSON config, manually curated, 10-15 seed channels to start)
- Video metadata scraping via yt-dlp with per-run upsert into SQLite
- Staleness tracking (`scraped_at` timestamps, 7-day refresh policy, freshness tiers)
- Basic channel stats: video count, avg views, upload frequency
- Performance signal detection: flag outlier videos at 2x+ channel median views
- Competitor topic clustering: group by theme to surface oversaturated vs. underserved areas
- Past topic deduplication — semantic match (not just exact title) against `context/channel/past_topics.md`
- Topic brief generation: 5 scored briefs per run, following the Topic Brief Schema from Architecture.md
- Scoring against 4-criteria channel filter (obscurity, complexity, shock factor, verifiability — 3/4 required)
- Project directory creation: `projects/N. Title/metadata.md` after user topic selection
- Title variants: 3-5 per selected topic

**Defer to v2 (P2/P3):**
- Content gap detection (requires crawl4ai trend scraping, needs Phase 1-3 baseline first)
- YouTube search/autocomplete trend awareness
- Cross-channel trend detection (3+ competitors covering adjacent topics)
- Upload cadence tracking
- Selective per-channel refresh

**Explicitly do not build:**
- Real-time monitoring or notifications (requires background service — wrong architecture)
- SEO keyword optimization (irrelevant for documentary content; topics compete on depth, not keywords)
- Thumbnail analysis (post-production decision, out of scope)
- Social media cross-platform analysis (each platform multiplies scraping complexity 3-4x for marginal signal)
- View count prediction models (unreliable even for commercial tools; outlier detection is more honest)
- Upload scheduling or content calendar (this channel is quality-gated, no fixed schedule)
- Historical trend graphs or dashboards (CLI-only; tables in chat are sufficient)
- YouTube Data API v3 (quotas, OAuth overhead; yt-dlp is strictly better here)
- Fully automated competitor discovery (manual curation produces higher-quality watchlists for a niche this narrow)
- Comment sentiment analysis (separate yt-dlp call per video, massive data volume, marginal signal vs. view/like ratio)

### Architecture Approach

The skill follows the established pattern from `.claude/skills/visual-style-extractor/`: SKILL.md orchestration instructions, Python scripts for deterministic work, prompt files for heuristic work. The HEURISTIC/DETERMINISTIC split from Architecture.md is enforced throughout.

**Seven components:**

| Component | Type | Responsibility |
|-----------|------|----------------|
| `scrape.py` | DETERMINISTIC | Fetch channel and video metadata via yt-dlp |
| `store.py` | DETERMINISTIC | Normalize yt-dlp output, upsert into SQLite with idempotency |
| `query.py` | DETERMINISTIC | SQL queries + markdown table formatting for Claude context |
| `trends.py` | DETERMINISTIC | Scrape YouTube search results via crawl4ai (Phase 4) |
| `init_project.py` | DETERMINISTIC | Create project directory + metadata.md after topic selection |
| `competitor_analysis.txt` | HEURISTIC (prompt) | Claude reads pre-aggregated stats, generates strategic insights |
| `topic_generation.txt` | HEURISTIC (prompt) | Claude synthesizes all context, generates 5 scored topic briefs |

**Key architectural patterns:**
- Cache-first with staleness check: never re-scrape if data is within freshness tier
- Normalization layer between yt-dlp and storage: never pass raw JSON directly to DB
- Pre-aggregation before LLM context: SQL summaries go into prompts, not raw records (raw data floods context window — 15 channels x 50 videos = context overload before any analysis begins)
- Idempotent upserts: re-scraping updates records, never creates duplicates
- Strict HEURISTIC/DETERMINISTIC separation: Python for data, Claude for judgment

**Data storage layout:**
```
context/competitors/
    competitors.db              # SQLite — single file, zero config

context/channel/
    channel.md                  # Read-only channel DNA
    past_topics.md              # Read + append after topic selection

projects/
    1. Video Title/
        metadata.md             # Handoff point for Agent 1.2
```

**Downstream handoff:** `projects/N. Title/metadata.md` is the contract between Agent 1.1 and Agent 1.2. Agents communicate through the filesystem. No message passing, no shared state beyond files.

### Critical Pitfalls

**1. yt-dlp breaks every few weeks (CRITICAL — Phase 1)**
YouTube actively fights scraping tools. As of March 2026, yt-dlp 2026.03.03 broke DASH format extraction; some operations now require Deno for JS execution. Prevention: pin version, build retry/fallback to cached data on failure, use `--flat-playlist` metadata-only mode, never download actual video files (reduces detection footprint).

**2. Sequential scraping triggers IP bans (CRITICAL — Phase 1)**
Tight-loop scraping of 10+ channels triggers ML-based bot detection. Batch traffic patterns are immediately distinguishable from human browsing. Prevention: randomized delays of 5-15 seconds between channels, hard cap of 50 extractions per run, stagger across sessions rather than scraping all competitors at once.

**3. Stale data treated as fresh (CRITICAL — Phase 1)**
Without explicit freshness metadata, 3-week-old cached data is indistinguishable from current data. Prevention: `scraped_at` ISO timestamp on every record (non-negotiable), three freshness tiers (<3 days = fresh, 3-14 days = stale with caveat, >14 days = must re-scrape), surface data age in topic briefs so the user knows what they are acting on.

**4. JSON file storage does not scale to this use case (CRITICAL — Phase 1)**
10 competitors x 100-500 videos = 1,000-5,000 records. Any cross-channel aggregation requires loading all files and filtering in Python. SQLite handles all of this in SQL natively. See storage adjudication below.

**5. LLM score drift in topic briefs (HIGH — Phase 3)**
Without concrete rubric anchors, obscurity/shock/complexity scores are not comparable across sessions. LLMs degrade in instruction adherence beyond ~8 directives. Prevention: define score anchors in the prompt with concrete thresholds ("Obscurity 8-10: zero English Wikipedia article OR fewer than 3 YouTube videos"), include 3-5 calibration examples in prompt context, keep the scoring prompt focused only on scoring — do not combine with topic generation in one massive prompt.

---

## Storage Conflict Adjudication: SQLite vs JSON

**The conflict:** FEATURES.md lists SQLite as an anti-feature and recommends JSON files per channel. STACK.md, ARCHITECTURE.md, and PITFALLS.md all independently recommend SQLite. This is the most consequential design decision in the project.

**Verdict: SQLite. This is not a close call.**

FEATURES.md's argument for JSON rests on a scale estimate of "20-30 channels x 100-500 videos = manageable at this scale." The estimate is correct. The conclusion is wrong. "Manageable" means the data can be loaded and filtered — it does not mean the queries are efficient, readable, or maintainable. At 5,000 records, every cross-channel aggregation (average views, topic clustering, outlier detection, upload cadence, content gaps) requires loading all files and running Python loops. SQLite handles every one of these in a single SQL statement with an index.

FEATURES.md also contradicts itself: it requires queryability, aggregation, and visualization as features in the competitor analysis section, then recommends a backend that provides none of those natively.

The three remaining files present detailed, independent counter-arguments. ARCHITECTURE.md explicitly notes it revised its recommendation from JSON to SQLite based on STACK.md analysis. PITFALLS.md dedicates a full critical pitfall entry to JSON's failure mode at this scale with documented warning signs. STACK.md provides a nine-criteria comparison table with SQL winning on seven.

The practical argument that seals it: Claude Code writes SQL faster and more reliably than ad-hoc Python filtering. When the user asks "which competitor topics got 3x average views in the last 6 months?" the answer with SQLite is a 3-line SQL query. With JSON it is a Python script that loads files, parses, filters, sorts, and formats. The SQL is written in 10 seconds. The Python script takes 2 minutes and introduces edge cases.

**Where JSON still belongs:**
- `channel.md` and `past_topics.md` — human-readable config, never queried programmatically
- `.claude/scratch/` — transient intermediate data
- Export formats when piping data to external tools

---

## Implications for Roadmap

### Suggested Phase Structure

**Phase 1: Scraping Infrastructure + Data Model**
Build `scrape.py`, `store.py`, and the SQLite schema as a unit. This is the foundation — nothing else operates without data. Rate limiting, error handling, freshness tracking, and the normalization layer all belong here.

- Delivers: "Add a competitor channel, scrape its metadata, view its stats."
- FEATURES.md: Competitor registry, metadata scraping, data cache + staleness, basic channel stats
- Must avoid: Pitfall 1 (yt-dlp resilience), Pitfall 2 (rate limiting), Pitfall 3 (freshness), Pitfall 4 (SQLite from day one), yt-dlp JSON normalization layer, Windows path safety

**Phase 2: Query Layer + Competitor Analysis**
Build `query.py` and the `competitor_analysis.txt` prompt. Wire SKILL.md so Claude can interpret pre-aggregated competitor data and surface strategic insights.

- Delivers: "What are competitors doing well? Where are the content gaps?"
- FEATURES.md: Performance signal detection, topic clustering, title pattern analysis
- Must avoid: Trap 2 (context overload — pre-aggregate with SQL before prompting), Gotcha 2 (never use crawl4ai on YouTube pages — yt-dlp only)

**Phase 3: Topic Generation + Project Initialization**
Build the `topic_generation.txt` prompt with calibrated scoring rubric, `init_project.py`, and the SKILL.md orchestration that ties the full flow together. This is the minimum viable skill.

- Delivers: Full ideation flow — 5 scored topic briefs, user selects one, project directory created, ready for Agent 1.2.
- FEATURES.md: Topic brief generation, scoring, past topic dedup, project directory creation, title variants
- Must avoid: Pitfall 5 (score drift — define rubric anchors before first run), semantic dedup not just exact-match title check

**Phase 4: Trend Scanning (Enhancement)**
Build `trends.py` using crawl4ai to scrape YouTube search results and autocomplete. Not blocking.

- Delivers: Real-time trend data feeding into topic generation, content gap detection
- FEATURES.md: Content gap detection, trend awareness, cross-channel trend detection
- Must avoid: crawl4ai noise on YouTube pages — use targeted CSS selectors, not full-page markdown

### Phase Ordering Rationale

The ordering is dependency-driven:
- Phase 2 requires data in the DB (Phase 1)
- Phase 3 requires the analysis layer (Phase 2) to have meaningful context for topic generation — without competitor insights, topic briefs are just "Claude guessing" with no data backing
- Phase 4 is genuinely independent but provides diminishing value without the competitor baseline from Phase 2

Phases 1-3 together are the minimum viable skill. The full ideation flow only activates at Phase 3 completion. Each phase independently delivers value that the previous phase does not.

### Research Flags

| Phase | Needs Phase Research? | Notes |
|-------|----------------------|-------|
| Phase 1: Scraping Infrastructure | NO | yt-dlp and SQLite are well-documented. All pitfalls identified with prevention strategies. Patterns are established. |
| Phase 2: Query + Analysis | NO | SQL query patterns are standard. Analysis prompt structure follows the existing visual-style-extractor skill convention. |
| Phase 3: Topic Generation | LOW | The scoring rubric design (Pitfall 5 mitigation) may benefit from a focused spike after first real use. The rubric can be iterated — not a blocker. |
| Phase 4: Trend Scanning | LOW | crawl4ai scraping is documented. Spike-test YouTube search scraping before committing to the full trends.py design (CSS selector targeting required to avoid noise). |

No phase requires a full research sprint before implementation begins.

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Stack | HIGH | All recommended tools installed and version-verified. No speculative choices. Fallbacks identified for the one compatibility risk (sqlite-utils on Python 3.14). |
| Features | HIGH | Grounded in commercial tool analysis (VidIQ, TubeBuddy, Subscribr) and channel DNA constraints. Anti-features are well-argued with clear alternatives. |
| Architecture | HIGH | Follows established patterns from the existing `visual-style-extractor` skill in this repo. No novel architecture required. Storage conflict resolved with clear rationale. |
| Pitfalls | HIGH | yt-dlp pitfalls documented in active GitHub issues (cited by issue number). Rate limiting behavior documented across multiple sources. LLM score drift backed by Salesforce research. |

**Overall: HIGH.** The domain is well-understood, the tools are proven, and the patterns are established in the existing codebase.

---

## Gaps to Address

1. **Competitor seed list not defined.** The registry needs an initial list of 10-15 competitor channel handles before scraping can begin. This is a content decision (which channels to track), not a technical one. Requires user input before Phase 1 can produce useful output.

2. **Scoring rubric anchors not written.** Concrete definitions for each score level (obscurity, complexity, shock factor, 1-10 scales with specific thresholds) do not exist yet. Must be written before the first topic generation run. Deferring this directly causes Pitfall 5.

3. **`past_topics.md` schema not specified.** The file exists but the exact format expected by the dedup logic is not defined. The semantic dedup prompt needs to know what fields to read. Establish the format before Phase 3.

4. **Incremental scrape boundary logic.** Pitfall Trap 1 identifies the need for `--dateafter` incremental scraping on subsequent runs. The exact implementation (how to store and compare the "last full scrape" date per channel) should be designed in Phase 1, not discovered during Phase 2.

5. **sqlite-utils Python 3.14 compatibility.** Version 3.39 claims Python 3.10-3.14 support. Verify on first install. If it fails, the fallback is stdlib `sqlite3` with more verbose upsert code. Not blocking, but should be the first check in Phase 1 setup.

6. **yt-dlp Deno requirement.** Recent yt-dlp versions may require an external JS runtime (Deno) for some YouTube operations. Installed version (2026.2.4) should be tested against metadata-only extraction before Phase 1 implementation begins. If Deno is required, it is an environment setup step, not a code change.

---

## Sources

Aggregated from research files:

- [yt-dlp PyPI](https://pypi.org/project/yt-dlp) — Version and capabilities
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp) — Metadata extraction, known issues
- [yt-dlp GitHub Issues: DASH formats broken 2026.03.03](https://github.com/yt-dlp/yt-dlp/issues/16128)
- [yt-dlp GitHub Issues: YouTube 403 errors](https://github.com/yt-dlp/yt-dlp/issues/15735)
- [yt-dlp GitHub Issues: Fragment retries trigger IP bans](https://github.com/yt-dlp/yt-dlp/issues/15899)
- [sqlite-utils GitHub](https://github.com/simonw/sqlite-utils) — Library API and upsert patterns
- [Crawl4AI Documentation](https://docs.crawl4ai.com/) — v0.8.x capabilities
- [Crawl4AI reliability benchmark](https://scrapegraphai.com/blog/crawl4ai-alternatives) — 11.3% noise ratio on YouTube pages
- [SQLite JSON Functions](https://sqlite.org/json1.html) — JSON column support in SQLite
- [When JSON Sucks — The Road to SQLite](https://pl-rants.net/posts/when-not-json/) — JSON vs SQLite analysis
- [VidIQ Features](https://vidiq.com/features/competitors/) — Commercial competitor tool feature baseline
- [TubeBuddy Competitor Analysis](https://www.tubebuddy.com/tools/youtube-competitor-analysis-tool)
- [Subscribr](https://subscribr.ai/) — AI topic ideation and research workflow reference
- [GapGens](https://www.gapgens.com/) — Content gap analysis reference
- [OutlierKit — Best YouTube Competitor Analysis Tools 2025](https://outlierkit.com/blog/best-youtube-competitor-analysis-tools-free-and-paid)
- [LLM instruction adherence (Salesforce research)](https://thoughtcred.com/dailybrief/salesforce-just-admitted-what-enterprise-buyers-already-suspected-about-llms) — Degrades beyond 8 directives
- [2026 Playbook for Reliable Agentic Workflows](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)
- [YouTube scraping: rate limiting and anti-bot detection](https://capmonster.cloud/en/blog/how-to-scrape-youtube)
- Existing skill pattern: `.claude/skills/visual-style-extractor/SKILL.md` — Direct codebase reference for skill structure
