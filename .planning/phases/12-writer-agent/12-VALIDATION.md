---
phase: 12
slug: writer-agent
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed) |
| **Config file** | none — runs with `pytest -x --tb=short` from project root |
| **Quick run command** | `PYTHONPATH=.claude/skills/writer/scripts pytest tests/test_writer/ -x --tb=short` |
| **Full suite command** | `pytest -x --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=.claude/skills/writer/scripts pytest tests/test_writer/ -x --tb=short`
- **After every plan wave:** Run `pytest -x --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | SCRIPT-01 | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_research -x` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | SCRIPT-03 | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_style_profile -x` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 1 | SCRIPT-04 | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_hooks -x` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 1 | SCRIPT-07 | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_output_path -x` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 2 | SCRIPT-02 | manual | Human review of Script.md against Research.md | N/A | ⬜ pending |
| 12-02-02 | 02 | 2 | SCRIPT-05 | manual | Human review of Script.md ending | N/A | ⬜ pending |
| 12-02-03 | 02 | 2 | SCRIPT-06 | manual | Human review for absence of stage directions | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_writer/__init__.py` — package marker
- [ ] `tests/test_writer/test_cli.py` — stubs for SCRIPT-01, SCRIPT-03, SCRIPT-04, SCRIPT-07

*Existing infrastructure covers framework installation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Every factual claim traces to Research.md | SCRIPT-02 | Tests heuristic output quality, not code | Read Script.md, verify no facts absent from Research.md |
| Open Ending Template applied when topic qualifies | SCRIPT-05 | Prompt-level reasoning, not code | Check final chapter for open-ended framing per STYLE_PROFILE.md |
| Pure narration — no stage directions or production notes | SCRIPT-06 | Output format is prompt-enforced | Scan Script.md for brackets, parenthetical directions, visual cues |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
