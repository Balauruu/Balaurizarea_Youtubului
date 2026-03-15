---
phase: 15
slug: skill-entry-point
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — existing tests/ directory |
| **Quick run command** | `pytest -x --tb=short` |
| **Full suite command** | `pytest --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Read SKILL.md and changed CLAUDE.md sections to confirm content matches plan
- **After every plan wave:** Confirm all four CLAUDE.md edit locations are updated and SKILL.md is present
- **Before `/gsd:verify-work`:** Both files readable and correct
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | INFRA-03 | manual-only | n/a — file content inspection | n/a | ⬜ pending |
| 15-01-02 | 01 | 1 | INFRA-03 | manual-only | n/a — file content inspection | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.claude/skills/visual-orchestrator/SKILL.md` — the file this phase creates (does not exist yet)

*Note: This is a documentation-only phase. No test stubs needed — correctness is verified by reading the files and confirming success criteria.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SKILL.md exists with 3-step invocation workflow | INFRA-03 | Documentation artifact, not executable code | Read SKILL.md, verify steps: (1) resolve project + disambiguate guide, (2) read Script.md + guide, (3) generate shotlist.json |
| SKILL.md handles multiple VISUAL_STYLE_GUIDE.md files | INFRA-03 | Behavioral instruction, not testable logic | Verify SKILL.md contains explicit disambiguation step |
| CLAUDE.md task routing table updated | INFRA-03 | Static file content check | Verify "Create shot list" row exists pointing to visual-orchestrator |
| CLAUDE.md What to Load table updated | INFRA-03 | Static file content check | Verify "Visual planning" row specifies visual-references/ and project script |

---

## Validation Sign-Off

- [ ] All tasks have manual verification instructions
- [ ] Sampling continuity: manual review at each commit
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
