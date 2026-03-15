# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.3 — The Director

**Shipped:** 2026-03-15
**Phases:** 3 | **Plans:** 3 | **Sessions:** 1

### What Was Built
- Visual Orchestrator stage contract (CONTEXT.md) with pipeline-reset invariant and [HEURISTIC] classification
- 182-line generation prompt with 10 consolidated building blocks, 9-field shot schema, 6-type routing table
- 6 WRONG/RIGHT anti-pattern pairs for visual_need specificity
- Synthetic worked example (Carol Marden case) with 3 shots across 3 different types
- SKILL.md with 3-step invocation workflow and CLAUDE.md routing (4 integration points)

### What Worked
- **Contract-first build order** — CONTEXT.md → generation.md → SKILL.md prevented documentation drift. Each phase built against a locked contract from the previous phase
- **User review at checkpoint** — 25 building blocks were consolidated to 10 during human-verify checkpoint, removing production-specific and redundant blocks. Better vocabulary emerged from review
- **Vocabulary consolidation principle** — using `building_block_variant` for specificity within a block instead of separate blocks keeps routing unambiguous
- **Fastest milestone yet** — entire v1.3 shipped in ~1.5 hours (single session), proving that documentation-only milestones with clear contracts execute rapidly
- **Anti-pattern pairs** — WRONG/RIGHT examples in generation.md are more effective than rules-only. They give concrete calibration

### What Was Inefficient
- **ROADMAP checkbox drift (4th consecutive milestone)** — plan checkboxes still `[ ]` despite completion. v1.2 retro noted "needs automation" — still not addressed
- **STATE.md still had double frontmatter** — tool appended a second YAML block instead of overwriting
- **Phase 14 VERIFICATION.md not re-run after fix** — dangling "Concept Diagram" reference was fixed in code but verification status remains `gaps_found`
- **Phase 15 SUMMARY missing requirements-completed field** — same frontmatter gap flagged in v1.0/v1.1/v1.2
- **Nyquist validation incomplete for Phase 15** — Phase 13 and 14 show compliant, but 15 never completed

### Patterns Established
- Contract-first skill development: CONTEXT.md → prompt → SKILL.md (sequential dependency chain)
- Building block vocabulary with variant field for sub-type specificity
- Anti-pattern pairs (WRONG/RIGHT) as calibration artifacts in generation prompts
- Pipeline-reset invariant as explicit design principle documented in stage contracts
- Establishing shot rule: every chapter must begin with an orienting shot

### Key Lessons
1. **Documentation milestones are fast** — 3 phases, ~1.5 hours. Zero Python code means zero debugging, zero test writing
2. **User checkpoints produce better architecture** — the 25→10 block consolidation would not have happened without the human-verify gate
3. **Re-run verification after fixes** — dangling reference was fixed but verification file stayed stale. Add re-verification step to executor
4. **SUMMARY frontmatter is a recurring gap** — 4th milestone with incomplete fields. Must be enforced in executor workflow
5. **Automate ROADMAP checkboxes** — flagged in v1.0, v1.1, v1.2, and now v1.3. This is clearly a tooling gap, not a discipline issue

### Cost Observations
- Model mix: opus for planning/execution, sonnet for subagents (research, verification, integration)
- Sessions: 1 (single session)
- Notable: Entire milestone from roadmap creation to shipping in a single context window

---

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

## Milestone: v1.2 — The Writer

**Shipped:** 2026-03-15
**Phases:** 2 | **Plans:** 4 | **Sessions:** ~4

### What Was Built
- Style extraction skill (zero Python, pure heuristic) that reconstructs auto-caption scripts and extracts voice rules
- STYLE_PROFILE.md (371 lines): 5 Universal Voice Rules, Narrative Arc Templates, 16 transition phrases, Open Ending Template
- Writer CLI context-loader (stdlib-only): aggregates Research.md + STYLE_PROFILE.md + channel.md
- 9-section generation prompt with hook formula, HOOK/QUOTE rules, voice rules, and Open Ending Template
- End-to-end script: Duplessis Orphans (7 chapters, 3,006 words), human-approved

### What Worked
- **[HEURISTIC] classification** — style extraction has zero Python files. Claude's reasoning produced a richer profile than any NLP analysis could
- **Two-pass extraction (reconstruct → extract)** — reconstructing auto-captions before analysis preserved narrator rhythm that would be lost in raw caption text
- **Applicability labels on arc templates** — prevents cult-arc overfitting on non-cult topics. Explicit labeling ("Not applicable to: institutional corruption, serial killer") is simple and effective
- **Context-loader CLI pattern (3rd milestone)** — `cmd_load` for writer follows the exact same pattern as channel-assistant and researcher. Zero learning curve
- **Generation prompt written before CLI** — prompt structure drove what the CLI needed to load, not the reverse. Prevented unused context loading
- **Human approval checkpoints** — both STYLE_PROFILE.md and Script.md were reviewed before proceeding. Caught no major issues, confirming quality

### What Was Inefficient
- **ROADMAP checkbox drift (3rd consecutive milestone)** — plan checkboxes still show `[ ]` despite completion. Not automated despite being flagged in v1.0 and v1.1
- **STATE.md triple frontmatter** — file accumulated 3 YAML frontmatter blocks from successive tool updates. Body was also stale
- **Nyquist validation still not run** — draft VALIDATION.md files exist for both phases, never executed. Same issue as v1.1
- **Hook sentence-count inconsistency** — generation.md says "four sentences max", STYLE_PROFILE.md says "two sentences max". Human approved 3-sentence output; canonical constraint unclear

### Patterns Established
- [HEURISTIC] skill pattern: zero Python, SKILL.md + CONTEXT.md + prompts/ only
- STYLE_PROFILE.md as channel-level artifact (same tier as channel.md) — loaded by writer, not owned by writer
- Behavioral ruleset format: Do-this/Not-this with verbatim examples and counter-examples
- Script generation as purely prompt-driven: CLI loads context, prompt encodes all constraints, Claude generates

### Key Lessons
1. **Automate ROADMAP checkbox updates** — 3 milestones in a row with drift. This is not a discipline problem, it's a tooling gap
2. **STATE.md needs single-write semantics** — multiple tools appending frontmatter creates corrupt files. Need overwrite, not append
3. **Single reference script is limiting but manageable** — STYLE_PROFILE.md works well for one arc type; adding a second reference (non-cult topic) would significantly improve arc template coverage
4. **Prompt-first design for heuristic skills** — writing the generation prompt before the CLI ensures the CLI loads exactly what's needed and nothing more
5. **Context budget matters** — 8,000 words max at generation time keeps the model focused. Overstuffing context degrades output quality

### Cost Observations
- Model mix: opus for planning/execution, sonnet for subagents
- Sessions: ~4 across 6 days (less intensive than v1.0/v1.1 due to smaller scope)
- Notable: Phase 11 was a pure heuristic phase — zero code written, zero tests needed. Fastest phase type

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~12 | 6 | Established TDD + context-loader pattern |
| v1.1 | ~6 | 4 | Added two-pass research + JSON manifest handoff |
| v1.2 | ~4 | 2 | Added [HEURISTIC] skill pattern + prompt-first design |
| v1.3 | 1 | 3 | Contract-first build order + building block vocabulary |

### Cumulative Quality

| Milestone | Tests | Coverage | External Deps Added |
|-----------|-------|----------|-------------------|
| v1.0 | 175 | 100% deterministic | 0 (all stdlib) |
| v1.1 | 175+ | 100% deterministic | crawl4ai, playwright |
| v1.2 | 184 (175+9) | 100% deterministic | 0 (stdlib-only writer CLI) |
| v1.3 | 184 (unchanged) | 100% deterministic | 0 (zero Python, pure heuristic) |

### Top Lessons (Verified Across Milestones)

1. **ROADMAP checkbox drift is persistent** — occurred in all 4 milestones. Needs automation (hook or executor step)
2. **SUMMARY frontmatter gaps recur** — `one_liner` and `requirements_completed` empty across all milestones. Must be enforced
3. **Context-loader CLI pattern scales** — worked for 7 modules in v1.0, extended to v1.1 and v1.2 with zero friction
4. **Foundation investment pays off** — Phase 7 (foundation) took longest; Phases 8-10 built on it rapidly
5. **STATE.md corruption recurs** — multiple frontmatter blocks in v1.2 and v1.3. Tool writes need overwrite semantics
6. **Nyquist validation is consistently skipped** — draft files exist in all milestones, rarely completed. Remove or automate
7. **Documentation milestones execute fastest** — v1.3 (pure heuristic) shipped in 1 session. Contract-first approach eliminates debugging time
8. **User checkpoints improve architecture** — v1.2 style review, v1.3 vocabulary consolidation both produced better designs through human review
