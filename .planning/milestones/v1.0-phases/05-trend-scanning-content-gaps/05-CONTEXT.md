# Phase 5: Trend Scanning + Content Gaps - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance topic generation with real-time trend data and content gap analysis. Covers ANLZ-05 (content gaps via YouTube autocomplete vs competitor coverage), ANLZ-06 (trending topics via YouTube search results sorted by recency), and ANLZ-07 (cross-channel convergence detection within 30-day windows). This phase adds new data acquisition and analysis capabilities — topic generation logic itself (Phase 3) and project initialization (Phase 4) are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Data Sources & Scraping
- **crawl4ai only** for all YouTube search/autocomplete scraping — no yt-dlp for search (yt-dlp stays for channel metadata in Phase 1)
- Keywords auto-derived from channel DNA content pillars (dark history, cults, unsolved mysteries, institutional corruption, dark web) + Phase 2 topic clusters — no manual keyword list
- Live scrape each run — no caching of autocomplete or search results
- Top 20 search results per keyword — first page of YouTube results
- With ~5-10 auto-derived keywords, expect 100-200 results per scan

### Content Gap Detection
- Gap = high autocomplete search demand + low/no competitor coverage + factor in performance of similar topics when covered
- Composite score: demand × opportunity, weighted by how well similar topics performed when competitors DID cover them
- Output as ranked list sorted by composite score — each gap shows: keyword, autocomplete volume indicator, competitor coverage count, estimated opportunity
- Gap threshold (how many competitors = "covered") at Claude's discretion based on data patterns
- Gap report auto-injected into `cmd_topics()` context alongside competitor analysis — topic generation prompt sees gaps and can prioritize them

### Convergence Detection
- Adjacency defined by Phase 2's topic clusters — if 3+ competitors publish videos in the same cluster within 30 days, that's convergence
- Fixed 30-day window — not configurable
- Also cross-reference with YouTube search trends — check if a converging topic is ALSO trending in search for a stronger signal
- Actionable framing at Claude's discretion (opportunity vs saturation vs neutral — depends on the data)

### Output & Integration
- Extend `context/competitors/analysis.md` with new sections: ## Trending Topics, ## Content Gaps, ## Convergence Alerts
- New `trends` CLI subcommand — independent of `analyze`, can be run separately and more frequently
- Trends command does NOT re-run competitor analysis — user runs `analyze` separately for fresh stats
- Chat output: print top 3 content gaps and any convergence alerts inline, plus file path for full report

### Claude's Discretion
- Exact crawl4ai scraping implementation (page parsing, request handling)
- Gap threshold (0, 1, or 2 competitors = "underserved")
- Convergence framing (opportunity alert vs saturation warning vs neutral flag)
- How to extract and rank autocomplete volume indicators
- Internal module structure for trend scanning code
- How to merge trend sections into existing analysis.md without overwriting Phase 2 content

</decisions>

<specifics>
## Specific Ideas

- The `trends` command should feel lightweight — run it frequently to stay current, unlike `analyze` which is heavier
- Gap detection should directly improve topic generation quality by surfacing proven-demand + low-competition sweet spots
- Convergence detection combining competitor uploads AND search trends gives a stronger signal than either alone
- Chat output with inline top-3 gaps matches the "brief summary + file path" pattern from Phase 2's analyze, but adds more immediate value

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `analyzer.py`: `compute_channel_stats()`, `detect_outliers()`, `serialize_videos_for_analysis()` — convergence detection can reuse video data serialization
- `database.py`: `get_videos_by_channel()`, `get_all_channels()` — needed to compare search results against existing competitor video titles/topics
- `topics.py`: `load_topic_inputs()` — needs extension to also load trend/gap data for topic generation context injection
- `cli.py`: `cmd_analyze()` writes to `context/competitors/analysis.md` — trends command appends to this same file
- Phase 2's topic clusters (written by Claude heuristic analysis) provide the adjacency framework for convergence detection

### Established Patterns
- [HEURISTIC] vs [DETERMINISTIC] split: crawl4ai scraping and data extraction is [DETERMINISTIC] code, topic matching/gap scoring/convergence framing is [HEURISTIC] Claude reasoning
- CLI uses argparse subcommands — `trends` follows same pattern as `add`, `scrape`, `status`, `analyze`, `topics`
- Output files use overwrite semantics (latest snapshot, no history)
- Scraper module uses subprocess calls with retry logic — crawl4ai integration follows similar resilience pattern

### Integration Points
- `cli.py`: Add `trends` subcommand
- `context/competitors/analysis.md`: Append trend sections (## Trending Topics, ## Content Gaps, ## Convergence Alerts)
- `topics.py`: `load_topic_inputs()` extended to include gap/trend data for auto-injection into topic generation context
- `context/channel/channel.md`: Content pillars section used to derive search keywords

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-trend-scanning-content-gaps*
*Context gathered: 2026-03-11*
