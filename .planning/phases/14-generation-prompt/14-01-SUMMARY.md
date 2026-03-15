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
  - 10-entry building block vocabulary (consolidated from 25 initial candidates)
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
    - "Building block vocabulary as table with Block Name, Description, and Example variants columns"
    - "Type routing as decision table — each building block maps to exactly one shotlist_type"
    - "WRONG/RIGHT anti-pattern pairs for visual_need specification"
    - "Vocabulary consolidation: merge semantically overlapping blocks, use building_block_variant for specificity"

key-files:
  created:
    - .claude/skills/visual-orchestrator/prompts/generation.md
  modified: []

key-decisions:
  - "10 building blocks selected after user review: removed 6 production-specific or redundant blocks (Keyword Stinger, Testimony Attribution Card, Credential/Authority Card, Glitch Stinger, Abstract Texture, Static Noise/Corruption); merged archival subtypes under Archival Photograph and Source Screenshot"
  - "Missing Person Card retained as distinct block for named-person profile cards (not merged into Archival Photograph)"
  - "Worked example uses synthetic Carol Marden case — not Duplessis content — to avoid memorization bias"
  - "building_block_variant populated with meaningful descriptors per shot, never null"
  - "narrative_context: soft 1-2 sentence guidance with no hard word cap"
  - "text_content: MUST be populated for all text_overlay shots, null for all others — no exceptions"
  - "Establishing shot rule: each chapter must begin with an establishing/orienting shot; Claude decides type based on chapter content"
  - "VISUAL_STYLE_GUIDE.md deferred to v1.4 — v1.3 inputs are Script.md and generation.md only"

patterns-established:
  - "Prompt structure mirrors writer/prompts/generation.md: Intro → Inputs → Schema → Building Blocks → Granularity Rules → Type Routing → Anti-Patterns → Worked Example → Output Format"
  - "Directive imperative tone throughout: MUST, Never, Always, No exceptions"

requirements-completed: [SHOT-01, SHOT-02, SHOT-03, SHOT-04, SHOT-05, SHOT-06, SHOT-07]

# Metrics
duration: ~45min
completed: 2026-03-15
---

# Phase 14 Plan 01: Generation Prompt Summary

**Self-contained 182-line visual-orchestrator generation prompt with 10 consolidated building blocks, 6 type routing rules, 9-field schema, 6 WRONG/RIGHT anti-pattern pairs, and a synthetic worked example — approved by user**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-15T13:31:17Z
- **Completed:** 2026-03-15
- **Tasks:** 2 of 2 complete
- **Files modified:** 1

## Accomplishments

- Created `.claude/skills/visual-orchestrator/prompts/generation.md` — fully self-contained, directive generation prompt
- Building block vocabulary consolidated to 10 clean, non-overlapping entries after user review
- Type routing table maps all 10 blocks to exactly one of 6 `shotlist_type` values
- 6 WRONG/RIGHT anti-pattern pairs for `visual_need` specificity
- Synthetic worked example (Carol Marden disappearance) demonstrates text_overlay, archival_photo, and animation shot types
- User reviewed and approved the prompt during Task 2 checkpoint

## Task Commits

1. **Task 1: Write prompts/generation.md** — `a80cb1f` (feat)
2. **Task 1 revision: Consolidate 25 building blocks to 10** — `6271e84` (refactor, post-checkpoint per user review)

**Plan metadata:** `925d0d9` (docs: complete plan — awaiting checkpoint)

_Task 2 was a human-verify checkpoint — no commit produced._

## Files Created/Modified

- `.claude/skills/visual-orchestrator/prompts/generation.md` — Complete generation prompt for visual-orchestrator skill

## Decisions Made

- **10 building blocks, not 25:** User review during checkpoint identified 6 blocks as too production-specific (Glitch Stinger, Static Noise/Corruption, Keyword Stinger) or redundant (Testimony Attribution Card, Credential/Authority Card, Abstract Texture). Separate archival subtypes (photos, mugshots, surveillance stills) were consolidated under Archival Photograph with variant fields. Source Screenshot absorbed Social Media Screenshot, Institutional Seal/Logo, and other document types. Missing Person Card was retained as a distinct block (named-person profile cards have a specific presentation need that warrants separation).
- **Vocabulary consolidation principle established:** Use `building_block_variant` for specificity within a block rather than creating separate blocks for each subtype. This keeps the routing table unambiguous.
- **Carol Marden synthetic example:** Worked example uses an entirely invented case to prevent the generating agent from pattern-matching on Duplessis-specific content.

## Deviations from Plan

### Post-checkpoint Revision

**User review resulted in vocabulary consolidation from 25 to 10 building blocks**
- **Found during:** Task 2 (human-verify checkpoint)
- **Issue:** Initial 25-block vocabulary included production-specific blocks (Glitch Stinger, Static Noise/Corruption) and redundant archival subtypes that would cause routing ambiguity
- **Fix:** Removed 6 blocks outright; merged archival photo subtypes under Archival Photograph; merged document/screenshot subtypes under Source Screenshot; retained Missing Person Card as distinct; updated variant examples to cover removed blocks' specificity
- **Files modified:** `.claude/skills/visual-orchestrator/prompts/generation.md`
- **Committed in:** `6271e84` (refactor)

---

**Total deviations:** 1 post-checkpoint revision (vocabulary consolidation per user review)
**Impact on plan:** Must-have truth "23-28 building block entries" superseded by user judgment. 10 non-overlapping blocks with rich variants provide equivalent routing precision with less ambiguity. All 7 SHOT requirements still fully addressed.

## Issues Encountered

- Plan must_have specified 23-28 building blocks. User review during checkpoint determined that count was inflated by redundant blocks and production-specific entries. Final count of 10 with variant fields is the deliberate outcome — user explicitly requested the consolidation.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `generation.md` is complete, consolidated, and user-approved
- Phase 15 (SKILL.md) can begin immediately
- Carry-forward concern: shot density calibration (word-count proportional vs. flat range) — validate generation.md against Duplessis Script V1.md + existing shotlist.json before finalizing SKILL.md
- STATE.md blocker "Validate generation.md against Duplessis Script V1.md + existing shotlist.json" is addressed by Task 2 user verification

---
*Phase: 14-generation-prompt*
*Completed: 2026-03-15*
