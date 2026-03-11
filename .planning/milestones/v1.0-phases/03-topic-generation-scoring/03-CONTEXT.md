# Phase 3: Topic Generation + Scoring - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

System generates 10-15 scored topic briefs that surface obscure, high-impact topics the channel has not covered, ranked and presented to the user. Covers ANLZ-04 (anchored scoring rubrics), OUTP-01 (topic briefs following Topic Brief Schema), and OUTP-02 (past-topic deduplication). Topic selection, project directory creation, and metadata generation are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Scoring Rubric Design
- 1-5 scale for all four dimensions: obscurity, complexity, shock factor, verifiability
- Total score out of 20
- Example-anchored rubric: each level references real topics as calibration points
  - E.g., Obscurity 5 = "Zero mainstream coverage, requires deep research" with a concrete example
  - E.g., Obscurity 1 = "Jack the Ripper, widely covered by 50+ channels"
- No minimum score threshold — all generated topics are shown, ranked by total score
- No content pillar weighting — scores are purely based on the 4 criteria
- Content pillar shown as a tag/label on each topic but doesn't affect scoring

### Topic Generation Source & Method
- Three sources combined: competitor data (Phase 2 analysis), channel DNA pillars, and live web research
- Web research via tavily-mcp at generation time — Claude searches for obscure cases/events matching content pillars
- Generate 10-15 candidates, present ALL ranked (not filtered to top 5)
- Broad generation, gap-aware: competitor gaps from Phase 2 inform ranking tags but don't constrain generation
- Underserved clusters from Phase 2 topic clustering are tagged on relevant topics but all sources compete equally

### Deduplication Strategy
- Check generated topics against `context/channel/past_topics.md`
- `past_topics.md` format: simple list with metadata — title, date published, 1-line summary per entry
- Strictness: exact topic only — same subject with different angle is allowed
- Near-duplicates shown with warning tag: "Similar to: [past topic]" rather than silently dropped
- No competitor overlap checking — competitor coverage is already visible in Phase 2 analysis report

### Output Format & Invocation
- Subcommand: `channel-assistant topics`
- Output to both chat and file
- Chat output: compact cards with scores per topic — title, hook (1 sentence), scores (O:4 C:3 S:5 V:3 = 15/20), estimated runtime, content pillar tag, duplicate warning if applicable
- File output: `context/topics/topic_briefs.md` — full Topic Brief Schema per topic (title, hook, timeline with 3-8 entries, all 4 scores with justification text, estimated runtime, content pillar)
- File overwritten each run (latest snapshot, no history)
- Chat summary line after cards: "N topics generated. Full briefs: context/topics/topic_briefs.md"

### Claude's Discretion
- Exact rubric example topics per level (informed by channel niche)
- Tavily search queries and how many searches per run
- How to structure the generation prompt (single pass vs iterative)
- Internal candidate ranking tiebreakers
- Timeline entry detail level in full briefs

</decisions>

<specifics>
## Specific Ideas

- Compact card format in chat should be scannable — user should be able to pick interesting topics at a glance without reading full briefs
- The scoring rubric should feel calibrated to the dark mysteries niche specifically, not generic content scoring
- Phase 4 will read `context/topics/topic_briefs.md` as input for project initialization, so the file must be self-contained

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `analyzer.py`: `serialize_videos_for_analysis()` produces channel-grouped video data — useful as input context for topic generation
- `analyzer.py`: `compute_channel_stats()`, `detect_outliers()` — stats already computed during `analyze` command
- `cli.py`: `cmd_analyze()` writes to `context/competitors/analysis.md` — topic generation reads this file
- `models.py`: `Video` and `Channel` dataclasses — topic briefs will need a new dataclass or dict schema

### Established Patterns
- [HEURISTIC] tasks (topic clustering, title patterns) are done by Claude reasoning over structured data, not by Python code
- Topic generation is fundamentally [HEURISTIC] — Claude generates and scores topics using competitor data + web research as context
- [DETERMINISTIC] code handles: reading past_topics.md, writing output file, CLI subcommand, data loading from SQLite
- CLI uses argparse subcommands in `cli.py` — `topics` follows the same pattern
- Output files go to `context/` directory tree

### Integration Points
- `cli.py`: Add `topics` subcommand alongside existing `add`, `scrape`, `status`, `migrate`, `analyze`
- Input: `context/competitors/analysis.md` (Phase 2 output) + `context/channel/past_topics.md` + `context/channel/channel.md` (channel DNA)
- Output: `context/topics/topic_briefs.md` (new file, read by Phase 4)
- Web research: tavily-mcp tool calls during [HEURISTIC] reasoning phase

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-topic-generation-scoring*
*Context gathered: 2026-03-11*
