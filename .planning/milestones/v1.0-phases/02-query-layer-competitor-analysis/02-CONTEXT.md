# Phase 2: Query Layer + Competitor Analysis - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Build analysis capabilities so the user can ask questions about competitor strategy and get data-backed answers. Covers DATA-05, ANLZ-01, ANLZ-02, ANLZ-03: per-channel stats, outlier detection, topic clustering, and title pattern extraction. All analysis operates on the existing SQLite database from Phase 1. Topic generation, scoring, and project creation are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Heuristic vs Deterministic Split
- **[DETERMINISTIC]** DATA-05 (channel stats) and ANLZ-01 (outlier detection): Pure Python/SQL computation. Code queries the DB, computes aggregates, and outputs structured data.
- **[HEURISTIC]** ANLZ-02 (topic clustering) and ANLZ-03 (title patterns): Claude reasons over structured data at query time. No NLP libraries or pre-computed clusters in the DB.
- Data flow: Code extracts full video lists from SQLite as structured dicts/JSON → Claude receives the full dataset → Claude performs reasoning (clustering, pattern recognition) → Claude writes analysis to file.
- Full video list per channel loaded into Claude's context (all titles, views, dates, durations, tags). With 3-5 channels at 50-100 videos each, expect 5-15k tokens of data.

### Analysis Output
- Single comprehensive report written to `context/competitors/analysis.md`
- Report has sections: ## Channel Stats, ## Outlier Videos, ## Topic Clusters, ## Title Patterns
- Overwritten on each full analysis run (latest snapshot, no history)
- Phase 3 (topic generation) reads this file as input context

### Stats Format (DATA-05)
- ASCII table in markdown (consistent with Phase 1 status output, Windows-safe)
- Per-channel: total videos, average views, median views, upload frequency, most recent upload

### Outlier Presentation (ANLZ-01)
- Single list sorted by performance multiplier (highest first), across all channels
- Each entry shows: video title, channel name, views, multiplier vs channel median
- Threshold: views >= 2x channel median (per requirements)

### Topic Clustering (ANLZ-02)
- Two-level hierarchy: Broad theme > specific topics
  - Example: "Cults" > ["Jonestown", "Heaven's Gate", "Aum Shinrikyo"]
  - Example: "Disappearances" > ["D.B. Cooper", "Maura Murray"]
- Saturation assessment uses three factors:
  1. **Coverage count** — how many channels covered this topic
  2. **Recency** — when was it last covered (a topic covered 3 years ago may be revisitable)
  3. **Performance** — saturated topics that perform well indicate proven demand worth a unique angle; saturated + poor performance = avoid
- Claude determines clusters, saturation levels, and editorial recommendations

### Title Pattern Extraction (ANLZ-03)
- Extract both structural formulas AND emotional hooks
  - Structural: "Question + Location", "Superlative + Topic", "Number + Category"
  - Emotional: "Mystery/suspense", "Revelation", "Warning/danger"
- Rank patterns by performance — show which formulas correlate with outlier videos
  - E.g., "Question titles average 2.3x median views"
- Flag sample size when pattern has <5 examples (honest about confidence)

### Invocation
- Single `/channel-assistant analyze` subcommand runs all four analyses in sequence
- Always analyzes ALL channels (cross-channel comparison is the core value)
- No per-channel or per-analysis-type filtering (keep it simple)
- Freshness check: warn if data older than 7 days ("Run /channel-assistant scrape for fresh data") but never block analysis
- Chat output: brief summary + file path only. Full report in `context/competitors/analysis.md`
  - Example: "Analysis complete. 3 channels, 127 videos analyzed. 8 outliers found, 12 topic clusters identified. Full report: context/competitors/analysis.md"

### Claude's Discretion
- Exact cluster names and hierarchy structure
- How to present saturation levels (scores, labels, or narrative)
- Title pattern categorization taxonomy
- Internal code module structure for the query functions
- Whether to add new database query methods or compose from existing ones

</decisions>

<specifics>
## Specific Ideas

- The analysis file should be a self-contained briefing document — reading it cold should give a complete picture of competitor landscape
- Performance multiplier in outliers should make it immediately obvious which videos "broke out" (e.g., "14.2x median" catches the eye)
- Topic clusters should directly inform Phase 3's topic generation — underserved clusters with proven demand are the sweet spot

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `database.py`: `get_videos_by_channel()` returns full Video objects with all fields — can be used to load complete video lists
- `database.py`: `get_channel_stats()` returns video_count, last_scraped, latest_upload — partial DATA-05 coverage, needs avg/median views and upload frequency added
- `database.py`: `get_all_channels()` returns all Channel objects — useful for iterating analysis across all channels
- `models.py`: `Video` and `Channel` dataclasses with all fields needed for analysis

### Established Patterns
- Database uses stdlib sqlite3 with Row factory — new queries follow the same pattern
- Data models are plain dataclasses (no ORM) — keep analysis models similarly simple
- CLI uses argparse with subcommands in `cli.py` — `analyze` subcommand follows same pattern
- Tags stored as JSON strings in SQLite, deserialized to lists on read

### Integration Points
- `cli.py`: Add `analyze` subcommand alongside existing `add`, `scrape`, `status`
- `database.py`: May need new query methods (e.g., `get_all_videos()`, views aggregation queries)
- Output file: `context/competitors/analysis.md` — new file, referenced by Phase 3
- The analyze command's [HEURISTIC] portion (clustering, patterns) runs as Claude reasoning, not as Python code

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-query-layer-competitor-analysis*
*Context gathered: 2026-03-11*
