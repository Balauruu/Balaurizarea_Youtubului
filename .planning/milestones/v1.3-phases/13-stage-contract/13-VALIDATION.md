---
phase: 13
slug: stage-contract
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | N/A — documentation-only phase |
| **Config file** | none |
| **Quick run command** | N/A |
| **Full suite command** | `pytest -x --tb=short` (existing suite, no new tests) |
| **Estimated runtime** | ~0 seconds (no automated tests for this phase) |

---

## Sampling Rate

- **After every task commit:** Manual review of output file
- **After every plan wave:** Verify CONTEXT.md against success criteria
- **Before `/gsd:verify-work`:** Human review of all 4 success criteria
- **Max feedback latency:** Immediate (file read)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | INFRA-01 | manual | N/A | N/A | ⬜ pending |
| 13-01-02 | 01 | 1 | INFRA-02 | manual | N/A | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test files needed — this phase produces only documentation.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CONTEXT.md classifies skill as pure [HEURISTIC] with zero Python code | INFRA-01 | Documentation content — no executable behavior | Read CONTEXT.md, verify [HEURISTIC] classification and no Python references |
| Inputs/outputs/process documented | INFRA-01 | Documentation structure — no executable behavior | Read CONTEXT.md, verify inputs (Script.md, prompts/generation.md), process steps, outputs (shotlist.json) |
| Pipeline-reset invariant section present | INFRA-02 | Documentation content — no executable behavior | Read CONTEXT.md, verify standalone invariant section exists |
| Deferred items listed | INFRA-01 | Documentation content — no executable behavior | Read CONTEXT.md, verify deferred items section lists shot duration, timing, camera movement, effects, transitions |

---

## Validation Sign-Off

- [x] All tasks have manual verify (documentation phase — no automated tests applicable)
- [x] Sampling continuity: documentation phase exemption
- [x] Wave 0 covers all MISSING references (none needed)
- [x] No watch-mode flags
- [x] Feedback latency: immediate (file read)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
