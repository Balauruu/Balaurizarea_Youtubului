---
phase: 10-dossier-output
plan: "02"
subsystem: researcher-skill
tags: [researcher, synthesis, dossier, prompt-engineering, skill-documentation]
dependency_graph:
  requires: [10-01-PLAN.md]
  provides: [synthesis.md, updated-SKILL.md]
  affects: [researcher-workflow, writer-handoff]
tech_stack:
  added: []
  patterns: [heuristic-synthesis, narrative-first-dossier, structured-credibility-signals]
key_files:
  created:
    - .claude/skills/researcher/prompts/synthesis.md
  modified:
    - .claude/skills/researcher/SKILL.md
decisions:
  - synthesis.md defines 9 sections in narrative-first order (Subject Overview → Source Credibility)
  - Word cap ~2,000 words enforced by prompt with explicit in/out-of-cap rules
  - Source credibility uses structured signals (Type, Corroborated By, Access Quality) — no scalar scores
  - media_urls.md groups match Architecture.md asset folder categories for direct Agent 2.1 consumption
  - Writer handoff is factual with implicit narrative signals — no editorial guidance, no chapter suggestions
metrics:
  duration: 2 min
  completed_date: "2026-03-14"
  tasks_completed: 2
  files_changed: 2
---

# Phase 10 Plan 02: Synthesis Prompt and SKILL.md Workflow Summary

**One-liner:** 285-line synthesis.md prompt encodes all 9 Research.md sections with HOOK/QUOTE callout formats, ~2,000-word cap, structured credibility signals, and media_urls.md grouping; SKILL.md updated to document complete 3-pass workflow with no planned markers.

## What Was Built

### Task 1 — synthesis.md prompt

Created `.claude/skills/researcher/prompts/synthesis.md` (285 lines). This is the [HEURISTIC] prompt that instructs Claude to transform 20-50k words of aggregated source content into a ~2,000-word Research.md dossier and a separate media_urls.md.

Key sections defined in the prompt:
- All 9 Research.md sections in narrative-first order with exact format definitions
- HOOK: callout format with examples (3-5 per dossier)
- QUOTE: blockquote callout format with attribution (3-8 per dossier)
- Word cap rules: ~2,000 words of body text, with explicit list of what counts vs. does not count
- Source credibility table: Type (gov/academic/journalism/wiki/primary), Corroborated By, Access Quality — no scalar scores
- media_urls.md grouped by Archival Footage / Archival Photos / Documents / B-Roll matching Architecture.md asset categories
- Anti-patterns section: no fabrication, no editorial framing, no chapter suggestions, no scalar scores

### Task 2 — SKILL.md complete workflow

Updated `.claude/skills/researcher/SKILL.md` with:
- Status line updated to "All modules implemented. v1.1 complete."
- Invocation block cleaned (no "planned" comments)
- Phase 10 module table: `writer.py` listed as implemented with exports (`load_source_files`, `build_synthesis_input`, `write_synthesis_input`)
- New "Workflow (Pass 3 — Write Dossier)" section: cmd_write step, Claude synthesis [HEURISTIC] step, review step
- synthesis_input.md format documented in Output Schema (header fields, per-source section format)
- Key decision added: synthesis_input.md includes ALL source content, word cap enforced by prompt

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

### Created files exist
- `.claude/skills/researcher/prompts/synthesis.md` — FOUND (285 lines)
- `.claude/skills/researcher/SKILL.md` — FOUND (updated)

### Commits exist
- f36d2fc: feat(10-02): create synthesis.md dossier output prompt
- e1ace9e: feat(10-02): update SKILL.md with complete 3-pass workflow

### Must-haves verified
- synthesis.md defines all 9 Research.md sections in correct order: CONFIRMED
- synthesis.md encodes ~2,000 word cap: CONFIRMED (3 occurrences of "2,000")
- synthesis.md defines HOOK: and QUOTE: formats: CONFIRMED (3 HOOK:, 4 QUOTE: occurrences)
- synthesis.md defines source credibility table with structured signals: CONFIRMED
- synthesis.md instructs media URL extraction grouped by asset type: CONFIRMED
- SKILL.md documents complete workflow including cmd_write: CONFIRMED (9 matches)
- SKILL.md references synthesis.md path: CONFIRMED (1 match)
- No "planned" markers remain: CONFIRMED (only "Phase 10 (implemented)" found)

## Self-Check: PASSED
