# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — The Researcher

**Shipped:** 2026-03-14
**Phases:** 4 | **Plans:** 8 | **Sessions:** ~6

### What Was Built
- Two-pass web research pipeline: survey (10-15 sources) → deep dive (5-10 primary sources) → structured dossier
- 5 Python modules (fetcher, tiers, url_builder, writer, cli with 3 subcommands) + 2 prompt files
- crawl4ai integration with domain-isolated browser contexts and tier-based retry
- Research.md with 9 narrative-first sections (HOOK/QUOTE callouts, contradictions, correcting-the-record)
- media_urls.md grouped by Architecture.md asset categories

### What Worked
- **Two-pass architecture** — separating broad survey from targeted deep dive kept context clean and focused
- **JSON source manifest between passes** — machine-readable handoff let Claude evaluate and route without ambiguity
- **Context-loader CLI pattern (continued from v1.0)** — `cmd_survey`, `cmd_deepen`, `cmd_write` each print data for Claude to consume
- **Heuristic prompts for evaluation + synthesis** — survey_evaluation.md and synthesis.md encode judgment without code
- **TDD continued** — test suite caught regressions across phases (e.g., DDG redirect parsing edge cases)
- **Fast execution** — 8 plans across 4 phases completed in 3 days with ~47 min total execution time

### What Was Inefficient
- **SUMMARY frontmatter one_liner field missing** — all 8 summaries lack the `one_liner` field, making milestone extraction harder
- **ROADMAP checkbox drift continued** — Phase plan checkboxes `[ ]` never updated to `[x]` during execution despite v1.0 lesson
- **Nyquist validation never run** — all 4 phases show draft status. Validation strategy files exist but were never executed
- **STATE.md stale** — body still referenced Phase 7 as current position when Phase 10 was complete

### Patterns Established
- Two-pass research with JSON manifest handoff between passes
- Budget guard (max 15 total source files) prevents context bloat
- Synthesis prompt encodes full dossier schema — writer.py handles only data aggregation
- SKILL.md as complete workflow documentation (3-pass sequence with exact commands)
- media_urls.md as separate artifact matching Architecture.md asset categories

### Key Lessons
1. **Update ROADMAP checkboxes during execution** — same lesson from v1.0, still not automated. Consider making this a hook
2. **Populate SUMMARY frontmatter completely** — `one_liner`, `requirements_completed` fields are empty across all summaries. Milestone extraction suffers
3. **Run Nyquist validation or disable it** — having draft VALIDATION.md files that are never used creates audit noise
4. **Keep STATE.md body in sync with frontmatter** — frontmatter was updated by tools but body was stale

### Cost Observations
- Model mix: opus for planning/execution, sonnet for subagents (research, verification)
- Sessions: ~6 across 3 days
- Notable: Phases 8-10 executed much faster than Phase 7 — foundation investment pays off in later phases

---

## Milestone: v1.0 — Channel Assistant

**Shipped:** 2026-03-11
**Phases:** 6 | **Plans:** 12 | **Sessions:** ~12

### What Was Built
- Full competitor intelligence pipeline: scrape → analyze → trends → topics → project init
- 7 Python modules (models, registry, database, scraper, analyzer, topics, trend_scanner, project_init) + CLI
- 175 unit tests with 100% deterministic code coverage
- 3 heuristic prompt files (topic_generation.md, project_init.md, trends_analysis.md)
- SQLite database with competitor data model

### What Worked
- **TDD discipline** — Red-green cycle caught regressions immediately (e.g., scraper test caught flat-playlist fallback change)
- **Heuristic/deterministic separation** — Clean boundary: Python handles data, Claude handles reasoning. Zero debugging of LLM API wrappers
- **Context-loader CLI pattern** — `cmd_*()` functions print structured data for Claude to consume. Simple, testable, extensible
- **stdlib-only approach** — Zero dependency conflicts. statistics, difflib, sqlite3, pathlib all just work
- **2-day sprint** — Entire v1.0 from zero to 175 tests in 2 days. GSD workflow kept momentum high

### What Was Inefficient
- **ROADMAP.md checkbox drift** — Plan checkboxes for Phases 3, 4, 6 never updated during execution. Milestone audit caught it as tech debt
- **SUMMARY frontmatter gaps** — `requirements_completed` field empty across all 12 summaries. Had to verify via VERIFICATION.md instead
- **Phase 3 progress table wrong** — Showed "1/2 plans, In Progress" despite completion. Documentation lagged behind execution
- **Duplicate `_extract_section()` in topics.py and cli.py** — Accepted as trade-off to avoid coupling, but could have been a shared util

### Patterns Established
- Context-loader CLI: `cmd_*()` prints data, Claude reasons over it
- Heuristic prompt files in `prompts/` directory with anchored rubrics
- `analysis.md` as shared data bus between analyze, trends, and topics phases
- Graceful degradation: empty strings for missing optional data (no crashes if trends haven't run yet)
- Windows-safe ASCII output (no Unicode box-drawing chars)

### Key Lessons
1. **Update ROADMAP checkboxes during execution, not after** — checkbox drift creates false audit signals
2. **SUMMARY frontmatter fields must be populated by the executor** — empty fields reduce audit efficiency
3. **stdlib-only is viable for channel-scale data** — no need for pandas, numpy, or external DB drivers
4. **Prompt files as calibration artifacts** — anchored rubrics (Jack the Ripper = Obscurity 1) produce consistent scoring across runs

### Cost Observations
- Model mix: primarily opus for planning/execution, sonnet for subagents
- Sessions: ~12 across 2 days
- Notable: Phase 6 (tech debt cleanup) took only 2 minutes — small, focused gap closure is efficient

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~12 | 6 | Established TDD + context-loader pattern |
| v1.1 | ~6 | 4 | Added two-pass research + JSON manifest handoff |

### Cumulative Quality

| Milestone | Tests | Coverage | External Deps Added |
|-----------|-------|----------|-------------------|
| v1.0 | 175 | 100% deterministic | 0 (all stdlib) |
| v1.1 | 175+ | 100% deterministic | crawl4ai, playwright |

### Top Lessons (Verified Across Milestones)

1. **ROADMAP checkbox drift is persistent** — occurred in both v1.0 and v1.1. Needs automation (hook or executor step)
2. **SUMMARY frontmatter gaps recur** — `one_liner` and `requirements_completed` empty in both milestones. Executor discipline or enforcement needed
3. **Context-loader CLI pattern scales** — worked for 7 modules in v1.0, extended cleanly to 5 more in v1.1
4. **Foundation investment pays off** — Phase 7 (foundation) took longest; Phases 8-10 built on it rapidly
