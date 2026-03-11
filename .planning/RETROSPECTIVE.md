# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

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

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 175 | 100% deterministic | 0 (all stdlib) |

### Top Lessons (Verified Across Milestones)

1. (First milestone — lessons to be verified in v1.1+)
