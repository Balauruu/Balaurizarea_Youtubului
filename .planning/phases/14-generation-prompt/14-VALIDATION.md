---
phase: 14
slug: generation-prompt
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual quality gate — pure prompt file, no automated tests |
| **Config file** | None |
| **Quick run command** | Run generation.md against Duplessis Script V1.md, inspect output |
| **Full suite command** | Same — single quality gate |
| **Estimated runtime** | ~120 seconds (LLM generation + manual inspection) |

---

## Sampling Rate

- **After every task commit:** Visually inspect prompt structure against Duplessis shotlist.json baseline
- **After every plan wave:** Full quality gate: run generation.md against Script V1.md, compare chapter counts, shot counts, type distribution
- **Before `/gsd:verify-work`:** Full suite must pass — output matches Duplessis baseline
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | SHOT-01 | manual | Load Script V1.md + generation.md, verify chapter grouping | N/A | ⬜ pending |
| 14-01-02 | 01 | 1 | SHOT-02 | manual | Compare output shot count per chapter to baseline (8-13/ch) | N/A | ⬜ pending |
| 14-01-03 | 01 | 1 | SHOT-03 | manual | Inspect output JSON structure against 9-field schema | N/A | ⬜ pending |
| 14-01-04 | 01 | 1 | SHOT-04 | manual | Spot-check 5 random visual_need strings for cinematographer language | N/A | ⬜ pending |
| 14-01-05 | 01 | 1 | SHOT-05 | manual | Scan building_block sequence for 3+ consecutive same-type runs | N/A | ⬜ pending |
| 14-01-06 | 01 | 1 | SHOT-06 | manual | Check first shot of each chapter is establishing type | N/A | ⬜ pending |
| 14-01-07 | 01 | 1 | SHOT-07 | manual | Identify 3 abstract shots, verify shotlist_type != archival | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. This is a [HEURISTIC] phase — pure prompt file, no automated test infrastructure needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chapter grouping | SHOT-01 | Prompt output quality — no deterministic test | Run generation.md against Script V1.md, verify ## N. parsing |
| Shot boundary quality | SHOT-02 | Narrative judgment | Compare shot count per chapter to Duplessis baseline |
| Field completeness | SHOT-03 | Output structure | Inspect JSON for all 9 fields |
| visual_need specificity | SHOT-04 | Language quality | Check for era+geography+subject, no cinematographer words |
| Visual variety | SHOT-05 | Sequence pattern | Scan for 3+ consecutive same building_block |
| Establishing shots | SHOT-06 | Narrative structure | Verify first shot per chapter |
| Abstract routing | SHOT-07 | Type classification | Check abstract narration → animation/vector |

---

## Validation Sign-Off

- [x] All tasks have manual verification criteria
- [x] Sampling continuity: manual review after each task
- [x] Wave 0: no automated infrastructure needed (HEURISTIC phase)
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
