---
phase: 14-generation-prompt
plan: 01
subsystem: prompts
tags: [visual-orchestrator, shotlist, prompt-engineering, building-blocks, type-routing]

# Dependency graph
requires:
  - phase: 13-stage-contract
    provides: visual-orchestrator CONTEXT.md with Process section referencing prompts/generation.md
provides:
  - .claude/skills/visual-orchestrator/prompts/generation.md — complete self-contained generation prompt
  - 25-entry building block vocabulary (18 Duplessis baseline + 7 channel additions)
  - 6-type routing rules with complete block-to-type mapping
  - 9-field shot schema with inline field-level rules
  - 6 WRONG/RIGHT anti-pattern pairs for visual_need
  - Synthetic 3-shot worked example (Carol Marden)
affects: [15-skill-md, visual-orchestrator skill invocations, asset acquisition pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Self-contained prompt file with all rules, schema, vocabulary, and examples — no external references needed at generation time"
    - "Building block vocabulary as two-column table — names must match exactly (case-sensitive)"
    - "Type routing as decision table — each building block maps to exactly one shotlist_type"
    - "WRONG/RIGHT anti-pattern pairs for visual_need specification"

key-files:
  created:
    - .claude/skills/visual-orchestrator/prompts/generation.md
  modified: []

key-decisions:
  - "25 building blocks selected: 18 Duplessis baseline + 7 additions (Crime Scene Photograph, Mugshot/Identification Photograph, Timeline Diagram, Missing Person Card, Social Media Screenshot, Security Footage Frame, Institutional Seal/Logo)"
  - "Worked example uses synthetic Carol Marden case — not Duplessis content — to avoid memorization bias"
  - "building_block_variant populated with meaningful descriptors per shot, never null"
  - "narrative_context: soft 1-2 sentence guidance with no hard word cap"
  - "text_content: MUST be populated for all text_overlay shots, null for all others — no exceptions"
  - "Establishing shot rule: each chapter must begin with an establishing/orienting shot; Claude decides type based on chapter content"

patterns-established:
  - "Prompt structure mirrors writer/prompts/generation.md: Intro → Inputs → Schema → Building Blocks → Granularity Rules → Type Routing → Anti-Patterns → Output Format"
  - "Directive imperative tone throughout: MUST, Never, Always, No exceptions"

requirements-completed: [SHOT-01, SHOT-02, SHOT-03, SHOT-04, SHOT-05, SHOT-06, SHOT-07]

# Metrics
duration: 15min
completed: 2026-03-15
---

# Phase 14 Plan 01: Generation Prompt Summary

**Self-contained 197-line visual-orchestrator generation prompt encoding 25 building blocks, 6 type routing rules, 9-field schema, 6 WRONG/RIGHT anti-pattern pairs, and a synthetic worked example**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-15T13:31:17Z
- **Completed:** 2026-03-15T13:45:00Z
- **Tasks:** 1 of 2 complete (Task 2 is checkpoint:human-verify — awaiting user approval)
- **Files modified:** 1

## Accomplishments

- Created `.claude/skills/visual-orchestrator/prompts/generation.md` — 197 lines, fully self-contained
- Building block vocabulary: 25 entries (18 Duplessis baseline + 7 additions covering true crime, missing persons, modern events, institutional scandals)
- Type routing table maps all 25 blocks to exactly one of 6 `shotlist_type` values
- 6 WRONG/RIGHT anti-pattern pairs for `visual_need` specificity
- Synthetic worked example (Carol Marden disappearance) demonstrates text_overlay, archival_photo, and animation shot types
- Automated verification passed: all sections present, 25 building blocks (within 23-28 range), 6 WRONG/RIGHT pairs

## Task Commits

1. **Task 1: Write prompts/generation.md** — `a80cb1f` (feat)

**Plan metadata:** pending (final commit after Task 2 checkpoint resolution)

## Files Created/Modified

- `.claude/skills/visual-orchestrator/prompts/generation.md` — Complete generation prompt for visual-orchestrator skill

## Decisions Made

- 7 additional building blocks selected beyond Duplessis baseline: Crime Scene Photograph, Mugshot/Identification Photograph, Timeline Diagram, Missing Person Card, Social Media Screenshot, Security Footage Frame, Institutional Seal/Logo — covers true crime, unsolved cases, modern events, and institutional scandals
- Worked example uses synthetic "Carol Marden" case (invented, not from any real project) to avoid the generating agent memorizing Duplessis-specific patterns
- Directive tone maintained throughout — every rule is a command, not a suggestion

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `generation.md` is ready for user review (Task 2 checkpoint)
- After approval, Phase 15 (SKILL.md) can begin immediately
- Quality gate: user should mentally walk through a Duplessis chapter and verify the rules would produce output consistent with the existing shotlist.json
- STATE.md blocker "Validate generation.md against Duplessis Script V1.md + existing shotlist.json" is addressed by Task 2 user verification

---
*Phase: 14-generation-prompt*
*Completed: 2026-03-15*
