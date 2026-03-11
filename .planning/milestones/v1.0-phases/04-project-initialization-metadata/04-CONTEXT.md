# Phase 4: Project Initialization + Metadata - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

User selects a topic from generated briefs and the system creates a project directory with YouTube-optimized title variants and description. Covers OUTP-03 (project directory creation), OUTP-04 (title variants), OUTP-05 (description), and OUTP-06 (metadata.md output). Topic generation and scoring are Phase 3. Trend scanning is Phase 5.

</domain>

<decisions>
## Implementation Decisions

### Topic Selection Flow
- User selects by number from chat cards (matching the `[N]` format from Phase 3's `format_chat_cards()`)
- One topic per run — user runs again for another topic
- No title edit step — title from the brief is used as-is for the directory name
- Integrated into `topics` flow — after `channel-assistant topics` generates and displays briefs, Claude asks the user to pick a number, then creates the project in the same session
- No separate `select` subcommand — selection is a continuation of the `topics` invocation

### Project Directory Structure
- Location: `projects/` at the project root (alongside `context/`, `data/`)
- Naming: `projects/N. [Video Title]/` where N is auto-incremented (scan existing dirs, find highest number, add 1; first project = 1)
- Scaffold subdirectories on creation: `research/`, `assets/`, `script/`
- `metadata.md` written into the project directory
- Selected topic is auto-appended to `context/channel/past_topics.md` to close the dedup loop for future runs

### Title Variant Strategy
- 5 variants per topic
- Pattern-informed: load Phase 2 title patterns from `context/competitors/analysis.md` and generate variants that follow top-performing competitor formulas
- 70 character max enforced on all variants
- One variant marked as recommended with brief reasoning (based on competitor pattern fit and topic strengths)
- Hook types vary across variants (question, statement, revelation, curiosity gap, etc.) — informed by data, not fixed

### Description Format
- Minimal: hook paragraph only, no chapters/sources/links sections
- No hashtags
- 2-3 sentences: short enough to show before YouTube's "Show more" fold
- Marketing tone: slightly more engaging/clickable than the video's neutral narration — descriptions serve discovery, not narration
- One description per topic (not multiple variants)

### Claude's Discretion
- Exact wording of title variants and description
- How to map Phase 2 title patterns to variant generation
- Which competitor pattern to mark as "recommended" and reasoning
- Order of variants in metadata.md (beyond recommended being labeled)
- How to handle edge cases (e.g., title over 70 chars after pattern application)

</decisions>

<specifics>
## Specific Ideas

- The `topics` command already displays compact cards — selection by number should feel like a natural continuation, not a new workflow
- Phase 4 reads `context/topics/topic_briefs.md` as its primary input (self-contained, written by Phase 3)
- `past_topics.md` auto-append format should match the existing format: `- **Title** | YYYY-MM-DD | one-line summary`

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `topics.py`: `load_topic_inputs()` reads analysis, channel DNA, and past topics — can be extended or a new loader created for project init
- `topics.py`: `write_topic_briefs()` writes full briefs to `context/topics/topic_briefs.md` — Phase 4 reads this file
- `topics.py`: `format_chat_cards()` produces `[N] Title -- hook` format — selection by number aligns with this
- `topics.py`: `check_duplicates()` does SequenceMatcher comparison — same logic validates auto-append to past_topics.md
- `topics.py`: `_load_past_topics()` parses `past_topics.md` with `**Title**` pattern — new entries must match this format

### Established Patterns
- [HEURISTIC] tasks (title generation, description writing) are done by Claude reasoning, not Python code
- [DETERMINISTIC] code handles: reading topic_briefs.md, creating directories, writing metadata.md, appending to past_topics.md
- CLI uses argparse subcommands in `cli.py` — Phase 4 adds to the existing `topics` flow rather than a new subcommand
- Output files use `pathlib.Path` with `mkdir(parents=True, exist_ok=True)` pattern

### Integration Points
- `cli.py`: `cmd_topics()` is the entry point — Phase 4 extends this flow (or Claude orchestrates after `topics` output)
- Input: `context/topics/topic_briefs.md` (Phase 3 output)
- Input: `context/competitors/analysis.md` (Phase 2 title patterns for variant generation)
- Output: `projects/N. [Title]/metadata.md` + scaffolded subdirs
- Side effect: append to `context/channel/past_topics.md`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-project-initialization-metadata*
*Context gathered: 2026-03-11*
