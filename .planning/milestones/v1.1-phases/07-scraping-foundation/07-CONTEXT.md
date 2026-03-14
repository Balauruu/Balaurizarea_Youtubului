# Phase 7: Scraping Foundation - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

A reliable crawl4ai integration layer with domain-isolated browser contexts, retry logic, source tiering, and topic input resolution — so every downstream phase (8-10) never touches scraping internals. This phase delivers fetcher.py, source tier constants, URL builder, and topic-to-project directory resolution.

</domain>

<decisions>
## Implementation Decisions

### Code location
- New skill directory: `.claude/skills/researcher/` with SKILL.md, scripts/researcher/, and prompts/
- Follows same CLI pattern as channel-assistant: `PYTHONPATH=.claude/skills/researcher/scripts python -m researcher <subcommand>`
- Subcommands planned: `survey` (Pass 1), `deepen` (Pass 2), `write` (dossier output)
- crawl4ai-scraper skill remains as standalone one-off URL scraper — different use case
- Fresh implementation — do NOT import from channel-assistant's trend_scanner.py. Different requirements (domain isolation, retry, content validation vs. simple YouTube HTML fetch)

### Source tier design
- Python constants in a tiers.py module (not JSON config)
- Three tiers: tier_1 (reliable, 3 retries), tier_2 (attempt, 1 retry), tier_3 (do-not-attempt, skip and log)
- Unknown domains default to Tier 2 behavior
- DuckDuckGo HTML scraping via crawl4ai as primary search engine for finding sources (needs validation testing in this phase)

### Claude's Discretion
- Domain-only vs domain+path tier matching — pick what's practical
- Minimum content length threshold (SCRP-02 says >200 chars, but Claude can raise if testing shows 200 is too noisy)
- Exact tier domain lists — populate based on research use cases

### Fetcher output format
- Structured JSON per source: one .json file per scraped URL with metadata (url, domain, tier, word_count, fetch_status) + content field
- Separate source_manifest.json as lightweight index (no content) — small enough for Claude to load into context for evaluation
- File naming: `src_001.json`, `src_002.json`, etc.
- Clean `.claude/scratch/researcher/` at the start of each new survey run — scratch is transient

### Topic input flow
- Topic provided as CLI string argument: `python -m researcher survey "Jonestown Massacre"`
- Fuzzy case-insensitive substring match against `projects/N. [Title]/` directory names
- If multiple matches: error and list them. If zero matches: still run research (standalone mode)
- Standalone mode: if no project directory found, output to `.claude/scratch/researcher/` only — user can move results later
- Auto-create `projects/N. [Title]/research/` subdirectory if project dir exists but research/ doesn't

</decisions>

<specifics>
## Specific Ideas

- Retry pattern reference: channel-assistant's scraper.py uses 3 attempts with progressive delay — good starting point for fetcher.py
- DuckDuckGo HTML scraping is flagged as needing validation (STATE.md blocker) — this phase must test and confirm it works before Phase 8 depends on it
- crawl4ai API field names differ between versions (STATE.md blocker) — run `crawl4ai-doctor` and verify field names before writing fetcher.py

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_get_project_root()` in cli.py: finds project root via CLAUDE.md marker — same pattern needed for researcher CLI
- `scraper.py` retry pattern: `_run_ytdlp()` with max_attempts=3, progressive delay — adapt for crawl4ai fetcher
- `crawl4ai-scraper/scripts/scraper.py`: minimal 28-line crawl4ai usage showing AsyncWebCrawler + arun() pattern

### Established Patterns
- Context-loader CLI: code prints structured data to stdout, Claude does all reasoning (Architecture.md Rule 2)
- PYTHONPATH + `python -m` invocation pattern (channel-assistant precedent)
- Scratch pad convention: `.claude/scratch/` for transient large outputs, gitignored
- stdlib-only dependencies where possible (sqlite3, pathlib, json, argparse)

### Integration Points
- `projects/N. [Title]/` directories created by channel-assistant's project_init.py
- `.claude/scratch/researcher/` as output location (read by Phase 8-10 commands and Claude)
- source_manifest.json schema must be stable — Phase 8 cmd_survey and Phase 9 cmd_deepen read it

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-scraping-foundation*
*Context gathered: 2026-03-12*
