# Phase 8: Survey Pass (Pass 1) - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

A single `cmd_survey` command that scrapes 10-15 broad sources for any documentary topic, stores all content as individual JSON files in scratch (never in conversation context), produces a machine-readable JSON source manifest, and triggers an automatic Claude evaluation that annotates the manifest with deep-dive recommendations. The evaluation prompt and annotated manifest schema are delivered in this phase. Pass 2 execution (cmd_deepen) is Phase 9.

</domain>

<decisions>
## Implementation Decisions

### Source discovery
- DDG parse + expand: fetch DDG HTML results page, parse out top 10-12 result URLs, then fetch those actual pages
- Wikipedia stays as a guaranteed first source (constructed from topic string)
- Single broad DDG query per topic (no multi-query variations)
- DDG results page is used only for URL extraction — no src_NNN.json created for the DDG page itself
- Tier 3 URLs found in DDG results (Facebook, X.com, Instagram) are filtered out before fetching
- **Reddit reclassified to Tier 2** — reddit.com and old.reddit.com moved from Tier 3 to Tier 2 (attempt once). Reddit provides alternative perspectives and firsthand accounts valuable for documentary research

### Evaluation prompt
- Evaluation criteria (in priority order):
  1. Primary source potential — sources that reference or link to primary documents (court records, government reports, archives)
  2. Unique perspective — angles not found in Wikipedia: firsthand accounts, **local journalism** (often has details mainstream outlets miss), academic analysis, Reddit discussions
  3. Contradiction signals — sources that contradict each other, creating narrative tension (feeds DOSS-02)
- Claude reads **full content** of each src_NNN.json during evaluation (not just manifest metadata) — needed for URL extraction and contradiction detection
- Evaluation runs **automatically** after cmd_survey completes (SKILL.md instruction, not code) — one command triggers full Pass 1 flow
- Output format: **annotated manifest** — Claude modifies source_manifest.json adding fields: `evaluation_notes`, `deep_dive_urls` (extracted from source content), and `verdict` (recommended/skip) per source

### Content handling
- Store full scraped content — no fixed word count truncation
- Strip structural noise (references/bibliography sections, navigation, footers, see-also) rather than arbitrary word cuts — research crawl4ai's content extraction options or post-processing patterns during planning
- Each src_NNN.json includes a `domain` field extracted from the URL for easier filtering

### Survey output
- Summary table printed to stdout after fetching: columns #, Domain, Tier, Words, Status; footer with totals (succeeded/failed/skipped)
- After automatic evaluation, Claude prints a verdict summary: which sources recommended for deep dive, which skipped, any contradictions spotted
- Claude asks "proceed to Pass 2?" before user runs deepen — explicit confirmation gate between passes

### Claude's Discretion
- DDG HTML parsing implementation (regex, BeautifulSoup, or crawl4ai's link extraction)
- Exact content cleaning approach for stripping structural noise (research options during planning)
- Evaluation prompt wording and rubric details
- Annotated manifest field names and schema details beyond the agreed fields

</decisions>

<specifics>
## Specific Ideas

- Local journalism sources should be prioritized in evaluation — they often have details that larger outlets miss or sanitize. The evaluation prompt should explicitly call this out.
- Reddit moved to Tier 2 because user values alternative perspectives from community discussions, not just traditional journalism
- Content cleaning should be smart (strip references/navboxes) not brute-force (word count caps) — if no good solution exists during research, fall back to storing full content

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli.py:cmd_survey()` — existing survey command with fetch loop, src_NNN.json writing, and manifest generation. Needs expansion for DDG URL parsing and domain field.
- `url_builder.py:build_survey_urls()` — currently returns [Wikipedia, DDG]. Will be refactored to return [Wikipedia] + parsed DDG result URLs.
- `url_builder.py:make_ddg_url()` — builds DDG HTML endpoint URL, already working.
- `fetcher.py:fetch_with_retry()` — crawl4ai wrapper with domain isolation and retry. No changes needed.
- `tiers.py` — tier constants and classify_domain(). Needs reddit.com/old.reddit.com moved from TIER_3 to TIER_2.

### Established Patterns
- Context-loader CLI: code fetches and stores data, Claude does all reasoning (evaluation is a [HEURISTIC] step)
- Scratch pad convention: `.claude/scratch/researcher/` for transient source files
- JSON per-source files with lightweight manifest index (Phase 7 schema)

### Integration Points
- `source_manifest.json` — Phase 9 cmd_deepen reads the annotated version to know which URLs to deep-dive
- `survey_evaluation.md` prompt — new prompt file in `.claude/skills/researcher/prompts/` read by SKILL.md workflow
- SKILL.md workflow update — must instruct Claude to auto-evaluate after cmd_survey completes

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-survey-pass*
*Context gathered: 2026-03-12*
