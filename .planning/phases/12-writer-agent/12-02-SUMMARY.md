---
phase: 12-writer-agent
plan: "02"
subsystem: writer-end-to-end
tags: [writer, script-generation, duplessis-orphans, routing]
dependency_graph:
  requires: [.claude/skills/writer/, context/channel/STYLE_PROFILE.md, projects/1/research/Research.md]
  provides: [projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md, CLAUDE.md routing]
  affects: [CLAUDE.md]
tech_stack:
  added: []
  patterns: [writer-skill-invocation, open-ending-template, hook-formula]
key_files:
  created:
    - "projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md"
  modified:
    - CLAUDE.md
decisions:
  - "Script.md is gitignored (projects/ is pipeline output) — commit only covers CLAUDE.md routing update"
  - "7 chapters selected (within 4-7 soft guardrail) based on research timeline arc"
  - "4 HOOKs selected: subsidy loophole (ch1), unremovable diagnosis (ch2), bodies/registry (ch3), waiver (ch5)"
  - "Open Ending Template applied: missing registries, no Church apology, waiver blocks further litigation"
  - "Template A (Cult arc) correctly excluded — institutional corruption topic uses research-derived structure"
metrics:
  duration: "~10 minutes"
  completed_date: "2026-03-15"
  tasks_completed: 1
  files_created: 1
  tests_added: 0
---

# Phase 12 Plan 02: Generate Duplessis Orphans Script — Summary

**One-liner:** End-to-end writer skill run producing a 7-chapter, 3,006-word narrated script for the Duplessis Orphans topic using the 4-part hook formula, 4 HOOKs/4 QUOTEs from Research.md, and Open Ending Template; CLAUDE.md routing table updated.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Generate Duplessis Orphans script and update CLAUDE.md | c41f02f | CLAUDE.md (Script.md gitignored) |

---

## What Was Built

### Task 1: Script.md

Generated narrated documentary script at `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md`:

- **7 chapters** (soft guardrail: 4-7): derived from research timeline, not Template A
- **3,006 words** (target: 3,000-7,000)
- **Opening hook**: Nestor's "garbage can" quote (recommended in plan), 4-part formula applied
- **Misinformation flag**: omitted (no dominant false public narrative requiring correction)
- **HOOKs selected** (4 of 5 available):
  - "The Subsidy Loophole" — anchors Chapter 1 (the entire mechanism)
  - "The Unremovable Diagnosis" — anchors Chapter 2 (what classification did to lives)
  - "The Bodies in the Cemetery" — anchors Chapter 3 (missing registries)
  - "The Waiver" — anchors Chapter 5 (settlement conditions)
- **QUOTEs used** (4 of 5 available):
  - Nestor: "When you are a bastard..." (opening hook, no attribution)
  - Nestor: "I have trouble to cry..." (Chapter 2, attributed)
  - Paul St. Aubain: "I wasn't ill..." (Chapter 2, attributed)
  - Albert Sylvio: "I undressed them..." (Chapter 3, attributed)
  - Martin Lecuyer: "It's not for the government..." (Chapter 5, attributed)
- **Open Ending Template**: applied in Chapter 7 — missing registries, no Church apology, waiver blocks remaining litigation
- **Voice compliance**: 5 Universal Voice Rules observed; no banned vocabulary, no host commentary, no stage directions

### Task 1: CLAUDE.md Updates

- Task Routing table: `Write script | writer | cmd_load + Claude heuristic`
- Pipeline Skills table: `writer | 1.3 | Research dossier → narrated chapter script`
- Folder map: `writer/` entry added under `.claude/skills/`
- What to Load table: removed `*(Phase 12)*` placeholder tag from Script writing row

---

## Script Structure

| Chapter | Title | HOOKs/QUOTEs | Function |
|---------|-------|--------------|----------|
| 1 | The Arithmetic of Abandonment | HOOK: Subsidy Loophole | Mechanism — how the reclassification worked |
| 2 | What the Diagnosis Did | HOOK: Unremovable Diagnosis; QUOTE: Nestor (crying), St. Aubain (lobotomy) | Impact — what the classification did to individual lives |
| 3 | The Record That Disappeared | HOOK: Bodies in Cemetery; QUOTE: Sylvio (bodies) | The missing evidence — registry disappearance, exhumation petition |
| 4 | The Report No One Acted On | — | Bedard Report 1962 — official confirmation, no individual remedy |
| 5 | Thirty Years Later | HOOK: The Waiver; QUOTE: Lecuyer (accomplice) | Settlement 1991-2001 — compensation with Church waiver condition |
| 6 | The Absence of Accountability | — | Church non-apology, rejected class actions, UN appeal |
| 7 | What Remains | — | Open Ending: missing registries, no Church apology, waiver in force |

---

## Deviations from Plan

### Notes

**1. projects/ is gitignored**
- **Found during:** Task 1 commit attempt
- **Issue:** `.gitignore` explicitly excludes `projects/` as pipeline output. Script.md cannot be committed.
- **Fix:** Committed only CLAUDE.md. Script.md exists on disk at the correct output path.
- **Impact:** None on plan success criteria — Script.md exists and meets all must_have conditions.

---

## Status

Task 1: COMPLETE (c41f02f)
Task 2: AWAITING HUMAN VERIFY — checkpoint:human-verify (blocking gate)

The script has been generated and is ready for review at:
`projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md`

---

## Self-Check: PARTIAL

- `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md` — EXISTS (gitignored, not committed)
- `CLAUDE.md` — routing table updated — VERIFIED
- Commit `c41f02f` — FOUND
- Task 2 checkpoint not yet passed — human verification pending
