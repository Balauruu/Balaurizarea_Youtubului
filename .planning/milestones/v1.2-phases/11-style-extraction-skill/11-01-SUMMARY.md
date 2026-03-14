---
phase: 11-style-extraction-skill
plan: "01"
subsystem: style-extraction skill
tags: [heuristic, prompts, style, voice-extraction]
dependency_graph:
  requires: []
  provides: [style-extraction-skill]
  affects: [phase-12-writer-agent]
tech_stack:
  added: []
  patterns: [heuristic-skill, two-pass-extraction, rule-format-with-counter-examples]
key_files:
  created:
    - .claude/skills/style-extraction/SKILL.md
    - .claude/skills/style-extraction/CONTEXT.md
    - .claude/skills/style-extraction/prompts/extraction.md
  modified: []
decisions:
  - "[HEURISTIC] classification enforced — zero Python files in skill directory"
  - "Two-pass structure: reconstruction pass preserves narrator phrasing before extraction pass"
  - "4 mandatory STYLE_PROFILE.md sections guard against cult-arc overfitting and missing templates"
  - "Applicability labels on all arc templates prevent forcing cult-story structure onto non-matching topics"
  - "Human approval checkpoint before any file writes — skill presents summary first"
metrics:
  duration: "3 minutes"
  completed: "2026-03-14"
  tasks_completed: 2
  files_created: 3
---

# Phase 11 Plan 01: Style Extraction Skill Infrastructure Summary

Zero-code heuristic skill infrastructure (SKILL.md + CONTEXT.md + extraction.md) that instructs Claude to reconstruct auto-caption scripts and extract a four-section behavioral ruleset into STYLE_PROFILE.md.

## What Was Built

The `style-extraction` skill directory at `.claude/skills/style-extraction/` with exactly three files:

1. **SKILL.md** — 8-step invocation workflow, post-write auto-wiring instructions (CLAUDE.md updates + writting_style_guide.md deletion), and file locations table. A fresh Claude session can read this file and know exactly what to do.

2. **CONTEXT.md** — Stage contract following the researcher/CONTEXT.md pattern. Defines inputs (all scripts in `context/script-references/`, channel.md, extraction.md, writting_style_guide.md on first run), 5-step process, single checkpoint (draft summary before file write), and outputs (STYLE_PROFILE.md + optional clean reconstruction).

3. **prompts/extraction.md** — Core extraction instructions with two-pass structure:
   - Pass 1 (conditional reconstruction): auto-caption detection (5 signals, 3+ threshold), reconstruction rules with critical constraint against paraphrase, saves `[Title]_clean.md`
   - Pass 2 (extraction): 4 mandatory output sections, absorption plan for all 6 existing rules from writting_style_guide.md, human approval summary format

## STYLE_PROFILE.md Sections Defined

| Section | Status | Addresses |
|---------|--------|-----------|
| Universal Voice Rules | Mandatory — 5+ required categories, counter-example format | STYLE-01, STYLE-03, STYLE-04 |
| Narrative Arc Templates | Mandatory — applicability labels, hook pattern, title register | STYLE-02, STYLE-04 |
| Transition Phrase Library | Mandatory — 10-20 verbatim phrases, 5 categories | STYLE-01, STYLE-03 |
| Open Ending Template | Mandatory — trigger condition, 3-part structure, crafted example | STYLE-01 |
| Hook Patterns | Optional | — |
| Chapter Naming Register | Optional | — |
| Sentence Rhythm Patterns | Optional (or subsection of Universal Voice Rules) | STYLE-03 |

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

### Files exist:

- `.claude/skills/style-extraction/SKILL.md` — FOUND
- `.claude/skills/style-extraction/CONTEXT.md` — FOUND
- `.claude/skills/style-extraction/prompts/extraction.md` — FOUND

### Python files in skill directory: 0 (HEURISTIC classification enforced)

### Commits:

- `e719dd6` — feat(11-01): create SKILL.md and CONTEXT.md for style-extraction skill
- `5c3533e` — feat(11-01): create extraction.md prompt for style-extraction skill

### Key link verification:

- SKILL.md references `prompts/extraction.md` — CONFIRMED (Step 5: "Read prompts/extraction.md in full")
- CONTEXT.md references `context/channel/STYLE_PROFILE.md` in Outputs — CONFIRMED

## Self-Check: PASSED
