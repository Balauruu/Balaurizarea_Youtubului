---
phase: 13-stage-contract
plan: 01
subsystem: docs
tags: [visual-orchestrator, stage-contract, shot-list, heuristic, documentation]

# Dependency graph
requires:
  - phase: 13-stage-contract
    provides: Research and context decisions for visual-orchestrator design
provides:
  - Stage contract (CONTEXT.md) for visual-orchestrator skill
  - Locked inputs/outputs/process definition for shot list generation
  - Pipeline-reset invariant documentation
affects:
  - phase 14 (generation prompt — authors prompts/generation.md against this contract)
  - phase 15 (SKILL.md — authored against this contract)
  - CLAUDE.md routing table (Phase 15 will add visual-orchestrator row)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Stage contract pattern: CONTEXT.md defines skill boundary before prompt or SKILL.md is written"
    - "[HEURISTIC] classification for zero-Python, pure LLM skills"

key-files:
  created:
    - .claude/skills/visual-orchestrator/CONTEXT.md
  modified: []

key-decisions:
  - "VISUAL_STYLE_GUIDE.md deferred to SHOT-09 — v1.3 inputs are Script.md and generation.md only"
  - "No Checkpoints section — user reviews via git diff or direct shotlist.json inspection"
  - "Pipeline-reset invariant: full regeneration only, no chapter-level regeneration in v1.3"
  - "Generic downstream references in invariant — no manifest.json named by name"
  - "Sequential shot IDs (S001...) assigned globally — rationale documented for full-regeneration requirement"

patterns-established:
  - "Stage contract first: CONTEXT.md locks skill boundary before Phase 14 prompt is authored"
  - "Deferred section split into out-of-scope-by-design vs future-enhancements-planned"

requirements-completed: [INFRA-01, INFRA-02]

# Metrics
duration: 2min
completed: 2026-03-15
---

# Phase 13 Plan 01: Stage Contract Summary

**Visual-orchestrator CONTEXT.md stage contract: Script.md + generation.md as inputs, shotlist.json as output, pipeline-reset invariant with full-regeneration requirement, pure [HEURISTIC] skill**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-15T12:57:24Z
- **Completed:** 2026-03-15T12:59:19Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Created `.claude/skills/visual-orchestrator/CONTEXT.md` as the locked stage contract for Phase 14 and 15 to build against
- Documented pipeline-reset invariant: shotlist.json is the source of truth; any Script.md change requires full regeneration with generic downstream artifact references
- Validated all 4 ROADMAP success criteria and all 5 anti-patterns confirmed absent

## Task Commits

Each task was committed atomically:

1. **Task 1: Create visual-orchestrator directory and write CONTEXT.md** - `4cc3e61` (feat)
2. **Task 2: Validate CONTEXT.md against Phase 13 success criteria** - no separate commit (validation only, no file changes)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `.claude/skills/visual-orchestrator/CONTEXT.md` - Stage contract for visual-orchestrator skill; defines inputs (Script.md, generation.md), 4-step heuristic process, pipeline-reset invariant, single output (shotlist.json), deferred scope

## Decisions Made

- VISUAL_STYLE_GUIDE.md deferred to SHOT-09 — v1.3 uses generic documentary building block vocabulary hardcoded in generation.md (Phase 14)
- No Checkpoints section — omitted by design; user can review output via git diff or direct file inspection
- Pipeline-reset invariant uses "acquisition manifests" as a generic example, not naming manifest.json specifically — keeps contract stable as downstream schema evolves
- Full regeneration only in v1.3 due to globally-sequential shot IDs (S001...) that would fragment on chapter-level regen
- Re-run behavior: always overwrites without prompt (matches writer skill convention for Script.md)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- CONTEXT.md is locked and ready for Phase 14 to author `prompts/generation.md` against it
- Phase 14 blockers remain active (from STATE.md): shot density calibration must be word-count proportional; validate generation.md against Duplessis baseline before Phase 15

---
*Phase: 13-stage-contract*
*Completed: 2026-03-15*
