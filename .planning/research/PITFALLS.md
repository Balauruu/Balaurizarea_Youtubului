# Pitfalls Research

**Domain:** YouTube Channel Assistant / Competitor Intelligence
**Researched:** 2026-03-11
**Confidence:** HIGH (core scraping/storage pitfalls well-documented; LLM orchestration pitfalls verified across multiple sources)

---

## Critical Pitfalls

### Pitfall 1: yt-dlp Breaks Every Few Weeks

**What goes wrong:** YouTube continuously changes its backend — client deprecations (android_sdkless removed), SABR streaming enforcement, 403 errors, format availability changes. As of March 2026, yt-dlp 2026.03.03 broke DASH format extraction. YouTube now requires external JS runtimes (Deno) for some operations. Your scraper works on Monday, returns nothing on Wednesday.

**Why it happens:** YouTube actively fights third-party tools. They deprecate internal APIs, rotate client tokens, and deploy anti-bot ML detection. yt-dlp maintainers patch reactively, so there is always a window where things are broken.

**How to avoid:**
- Pin yt-dlp version but have an automated update-and-test script. Do not auto-update blindly.
- Use `--flat-playlist --dump-single-json` for metadata extraction (lighter footprint, less likely to trigger anti-bot).
- Never download actual video files for competitor analysis — metadata-only extraction reduces detection risk.
- Build a retry/fallback layer: if yt-dlp fails, log it and use cached data instead of crashing the pipeline.
- Store the yt-dlp version in your config so you know which version produced each data snapshot.

**Warning signs:** Increasing 403/429 errors in logs. yt-dlp GitHub issues page shows new YouTube-related bugs. Metadata fields returning `None` that previously had values.

**Phase to address:** Phase 1 (Competitor Scraping Infrastructure). Build the resilience layer from day one, not as an afterthought.

---

### Pitfall 2: Scraping Without Rate Limiting Leads to IP Bans

**What goes wrong:** Scraping 10+ competitor channels sequentially in a tight loop triggers YouTube's rate limiting. You get 429 errors, then temporary IP blocks, then potentially permanent blocks on your home IP.

**Why it happens:** YouTube uses ML-based bot detection that analyzes request patterns. Bot traffic is predictable — same intervals, same patterns. Human browsing is chaotic. Batch scraping looks nothing like a human.

**How to avoid:**
- Add randomized delays between channel scrapes (5-15 seconds minimum, jittered).
- Never scrape all competitors in one run. Stagger: scrape 3-4 channels per session, rotate across runs.
- Implement per-session request counting with hard caps (e.g., max 50 metadata extractions per run).
- Use `--flat-playlist` mode exclusively — it makes fewer requests than full extraction.
- Consider scraping at off-peak hours (less scrutiny from anti-bot systems).

**Warning signs:** First 429 error is your canary. If you see one, stop immediately and increase delays. Do not retry aggressively — that compounds the problem.

**Phase to address:** Phase 1 (Scraper Implementation). Rate limiting must be built into the scraper module, not bolted on later.

---

### Pitfall 3: Stale Data Treated as Fresh

**What goes wrong:** You cache competitor data (good), but then make strategic decisions based on 3-week-old data without realizing it. A competitor's recent upload shift goes unnoticed. View counts are snapshots, not current. Your "gap analysis" identifies a gap that was filled last week.

**Why it happens:** Caching is necessary (see Pitfall 2), but without explicit freshness metadata, the LLM and the user both treat cached data as current truth. JSON files have no built-in "last fetched" concept.

**How to avoid:**
- Every cached record MUST have a `scraped_at` ISO timestamp. Non-negotiable.
- The analysis prompt/skill must receive the data age and factor it into confidence: "Based on data from 14 days ago, this gap MAY still exist."
- Define freshness tiers: <3 days = fresh, 3-14 days = stale (usable with caveat), >14 days = expired (must re-scrape before analysis).
- Surface data age to the user in topic briefs: "Competitor data freshness: 8 days average."

**Warning signs:** You stop thinking about when data was collected. Topic briefs cite competitor patterns without mentioning data age. User makes decisions on old data without knowing it.

**Phase to address:** Phase 1 (Data Model Design). The `scraped_at` field and freshness logic must be in the schema from the start.

---

### Pitfall 4: JSON File Storage Hits a Wall at ~50 Videos per Competitor

**What goes wrong:** You start with JSON files per competitor (simple, readable). At 10 competitors x 100 videos each = 1,000 records. Querying "which topics got >500K views across all competitors in the last 6 months" requires loading and parsing every file. It works at 100 records, gets slow at 1,000, becomes painful at 5,000+.

**Why it happens:** JSON requires full-file parse for any query. No indexing, no partial reads, no concurrent writes. Every analysis run loads everything into memory.

**How to avoid:**
- Use SQLite from the start. It handles this scale trivially, supports SQL queries, and is a single file — still simple to manage.
- Use JSON only for the schema definition and human-readable exports, not as the primary data store.
- SQLite's JSON1 extension lets you store semi-structured data in columns while still getting indexed queries.
- Keep the DB at `context/competitors/competitors.db` — one file, no server, works on Windows without setup.

**Warning signs:** Analysis scripts taking >2 seconds. Growing number of "load all files, filter in Python" patterns. Desire to add "indexes" to JSON (you are reinventing a database).

**Phase to address:** Phase 1 (Data Model Design). Choose SQLite before writing any storage code. Migrating from JSON to SQLite mid-project is tedious and error-prone.

---

### Pitfall 5: LLM Instruction Drift in Topic Scoring

**What goes wrong:** Claude Code is asked to score topics on obscurity (1-10), complexity (1-10), and shock factor (1-10). Over multiple runs, scores drift: what was a 7 last month is a 5 this month. Scores are not calibrated against anything concrete. The LLM hallucinates confidence in numbers that are essentially arbitrary.

**Why it happens:** LLMs produce probabilistic output. Without anchoring criteria, a "complexity score of 7" is meaningless across sessions. The model has no memory of previous scoring unless explicitly given calibration context. Research shows LLMs degrade in instruction adherence beyond ~8 directives.

**How to avoid:**
- Define concrete anchors for each score level in the prompt. Example: "Obscurity 8-10: Zero English Wikipedia article OR fewer than 3 YouTube videos on the topic. Obscurity 5-7: Wikipedia stub or single-paragraph section."
- Store previously scored topics with their scores as calibration examples in the prompt context.
- Limit the scoring prompt to ONLY scoring — do not combine with topic generation, research, and formatting in one massive prompt.
- Accept that scores are ordinal rankings within a single run, not absolute values. Compare within a batch, not across batches.

**Warning signs:** User notices the same type of topic getting wildly different scores across runs. All topics cluster around 6-8 (the LLM's comfort zone). Scores feel arbitrary rather than informative.

**Phase to address:** Phase 1 (Topic Brief Schema & Scoring Skill). Define the rubric before the first scoring run.

---

## Technical Debt Patterns

### Debt 1: Hardcoded Competitor List

**What goes wrong:** Competitor channels are hardcoded in a Python list or config file. Adding/removing competitors requires editing code. No metadata about WHY a channel is tracked (direct competitor? adjacent niche? inspiration?).

**How to avoid:** Store competitors in the SQLite DB with fields: `channel_id`, `channel_name`, `channel_url`, `niche_relevance` (direct/adjacent/inspiration), `added_date`, `active` (boolean). The skill reads from DB, not from code.

### Debt 2: No Scrape History / Audit Trail

**What goes wrong:** You overwrite competitor data on each scrape. You cannot answer: "When did this competitor start covering cult topics?" or "How has their upload frequency changed?" Trend analysis becomes impossible.

**How to avoid:** Append-only data model. Each scrape creates new rows with timestamps, not updates. Keep historical snapshots. SQLite makes this trivial — just never UPDATE, always INSERT.

### Debt 3: Monolithic Skill File

**What goes wrong:** The Channel Assistant skill grows to 500+ lines combining scraping, caching, analysis, scoring, and output formatting. Debugging any part requires understanding everything. Claude Code context window fills with irrelevant code.

**How to avoid:** Separate into discrete Python modules from day one:
- `scraper.py` — yt-dlp wrapper with rate limiting
- `storage.py` — SQLite read/write operations
- `analyzer.py` — data aggregation and pattern detection
- The SKILL.md prompt handles orchestration (which module to call when)

---

## Integration Gotchas

### Gotcha 1: yt-dlp's JSON Output is Unstable

**What goes wrong:** yt-dlp's `--dump-json` output schema is not versioned or guaranteed. Fields appear, disappear, or change type between versions. Your Python code expects `view_count` as an int, but a yt-dlp update returns it as a string, or `None`, or omits it entirely.

**How to avoid:**
- Write a normalization layer (`normalize_video_metadata(raw_json) -> VideoRecord`) that handles missing fields, type coercion, and defaults.
- Never pass raw yt-dlp JSON directly to storage or analysis. Always normalize first.
- Test the normalizer against saved sample outputs from different yt-dlp versions.

### Gotcha 2: crawl4ai Noise in YouTube Page Scraping

**What goes wrong:** crawl4ai's markdown output from YouTube pages has an 11% noise ratio (navigation elements, ads, recommended videos mixed with actual content). When fed to Claude for analysis, irrelevant tokens waste context and can mislead analysis.

**How to avoid:**
- Use yt-dlp for all structured YouTube data (metadata, video lists, descriptions). It is purpose-built.
- Reserve crawl4ai for non-YouTube sources only (news articles, Wikipedia, blogs for research enrichment).
- If you must use crawl4ai on YouTube, use CSS selectors to extract specific elements, not full-page markdown.

### Gotcha 3: Windows Path Issues with yt-dlp Output

**What goes wrong:** yt-dlp output templates use Unix path conventions. On Windows, paths with special characters in video titles (colons, question marks, quotes — common in dark mystery content) cause file write failures or silent truncation.

**How to avoid:**
- Always use `--output` with sanitized filenames: `%(id)s.%(ext)s` not `%(title)s.%(ext)s`.
- Use `pathlib.Path` for all path operations in Python.
- When storing titles, store them in the database, not in filenames.

---

## Performance Traps

### Trap 1: Scraping All Videos for Every Competitor

**What goes wrong:** Competitor channels have 200-500+ videos. Scraping full history on every run takes 10+ minutes and risks rate limiting. Most of that data has not changed since last scrape.

**How to avoid:**
- On first scrape: get full history (`--flat-playlist --dump-single-json`).
- On subsequent scrapes: only fetch videos newer than the most recent `upload_date` in your DB. yt-dlp supports `--dateafter` for this.
- Store the "last full scrape" timestamp per competitor. Do incremental updates by default, full refreshes on demand.

### Trap 2: Loading Entire Competitor DB into LLM Context

**What goes wrong:** You dump all competitor data into the Claude Code prompt for analysis. At 10 competitors x 100 videos, that is 50,000+ tokens of raw data. The LLM loses focus, misses patterns, and the response quality degrades.

**How to avoid:**
- Pre-aggregate in Python before passing to Claude. The LLM should receive summary statistics and curated examples, not raw data.
- Example: "Competitor X: 45 videos in last 6 months. Top 5 by views: [list]. Topic distribution: cults 30%, disappearances 25%, crime 45%."
- Write aggregation queries in SQL, output summaries to `.claude/scratch/`, feed summaries to the analysis prompt.

### Trap 3: Re-analyzing Unchanged Data

**What goes wrong:** Every time the user asks for topic ideas, the system re-scrapes and re-analyzes everything from scratch. This is slow and produces near-identical results if nothing has changed.

**How to avoid:**
- Cache analysis results alongside data, with a `valid_until` timestamp.
- Only re-run analysis when underlying data has been refreshed.
- Separate "scrape" and "analyze" as distinct user-triggerable actions, not a single monolithic flow.

---

## "Looks Done But Isn't" Checklist

| Feature | Looks done when... | Actually done when... |
|---------|--------------------|-----------------------|
| Competitor scraping | You can pull metadata for one channel | Handles rate limits, retries, version changes, and partial failures gracefully |
| Data caching | Data saves to disk | Has `scraped_at` timestamps, freshness tiers, incremental updates, and history preservation |
| Topic scoring | Claude returns numbers 1-10 | Scores are anchored to concrete rubrics, calibrated across runs, and the user understands their meaning |
| Duplicate rejection | Exact title match against past_topics.md | Semantic similarity check (LLM-based) catches "The Jonestown Massacre" vs "Jim Jones and the Peoples Temple" |
| Competitor analysis | Raw data is displayed | Aggregated insights are generated: gaps, trends, title patterns, performance signals |
| Error handling | Happy path works | yt-dlp failures, network timeouts, malformed data, and empty results all have graceful fallbacks |

---

## Recovery Strategies

### When yt-dlp Breaks Completely
1. Check yt-dlp GitHub issues for known YouTube breakage.
2. Try updating: `pip install --upgrade yt-dlp` (fixes land within days usually).
3. If update does not fix it: fall back to cached data for analysis. Log that data is stale.
4. Do NOT switch to YouTube Data API as a "quick fix" — it has quotas and requires OAuth setup. It is a different architecture decision.

### When Competitor Data is Corrupted
1. SQLite with WAL mode provides crash-safe writes. Enable it.
2. Keep the previous DB file as a backup before each full scrape (`competitors.db.bak`).
3. Normalization layer (Gotcha 1) should reject records with missing critical fields rather than inserting garbage.

### When Topic Scores Feel Random
1. Print the scoring prompt with all its context — is it overloaded?
2. Run the same topics through scoring 3 times. If variance is >2 points on any axis, the rubric is too vague.
3. Add 3-5 calibration examples to the prompt: "Topic X was scored Obscurity 9 because [reason]."

---

## Pitfall-to-Phase Mapping

| Phase/Milestone | Relevant Pitfalls | Priority |
|-----------------|-------------------|----------|
| Competitor Scraping Infrastructure | Pitfall 1 (yt-dlp breaks), Pitfall 2 (IP bans), Gotcha 1 (unstable JSON), Gotcha 3 (Windows paths), Trap 1 (scrape scope) | CRITICAL — must be resilient from day one |
| Data Model & Storage | Pitfall 3 (stale data), Pitfall 4 (JSON scaling), Debt 1 (hardcoded list), Debt 2 (no history) | CRITICAL — wrong storage choice cascades everywhere |
| Competitor Analysis Skill | Trap 2 (context overload), Trap 3 (re-analysis), Gotcha 2 (crawl4ai noise) | HIGH — determines output quality |
| Topic Generation & Scoring | Pitfall 5 (score drift), "Looks Done" items (duplicate rejection, rubric calibration) | HIGH — this is the user-facing output |
| Skill Architecture | Debt 3 (monolithic skill) | MEDIUM — modularity prevents later pain |

---

## Sources

- [yt-dlp GitHub Issues: DASH formats missing in 2026.03.03](https://github.com/yt-dlp/yt-dlp/issues/16128)
- [yt-dlp GitHub Issues: YouTube 403 errors](https://github.com/yt-dlp/yt-dlp/issues/15735)
- [yt-dlp GitHub Issues: Fragment retries trigger IP bans](https://github.com/yt-dlp/yt-dlp/issues/15899)
- [Bypassing YouTube SABR blocks with yt-dlp (2026)](https://dev.to/ali_ibrahim/bypassing-the-2026-youtube-great-wall-a-guide-to-yt-dlp-v2rayng-and-sabr-blocks-1dk8)
- [yt-dlp AI-scale scraping challenges](https://medium.com/@DataBeacon/how-to-tackle-yt-dlp-challenges-in-ai-scale-scraping-8b78242fedf0)
- [Crawl4AI reliability: 72% success rate on anti-bot sites, 11.3% noise ratio](https://scrapegraphai.com/blog/crawl4ai-alternatives)
- [When JSON Sucks — The Road to SQLite](https://pl-rants.net/posts/when-not-json/)
- [LLM instruction adherence degrades beyond 8 directives (Salesforce)](https://thoughtcred.com/dailybrief/salesforce-just-admitted-what-enterprise-buyers-already-suspected-about-llms)
- [2026 Playbook for Reliable Agentic Workflows](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)
- [YouTube scraping: rate limiting and anti-bot detection](https://capmonster.cloud/en/blog/how-to-scrape-youtube)
- [yt-dlp channel metadata extraction](https://github.com/yt-dlp/yt-dlp/issues/13155)
