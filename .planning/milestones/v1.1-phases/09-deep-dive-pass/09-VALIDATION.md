---
phase: 9
slug: deep-dive-pass
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | existing project config |
| **Quick run command** | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` |
| **Full suite command** | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short`
- **After every plan wave:** Run `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 0 | RSRCH-03 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | RSRCH-03 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | RSRCH-03 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | RSRCH-03 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_researcher/test_cli.py` — add `test_cmd_deepen_*` test stubs for RSRCH-03 behaviors
- [ ] No new test files needed — deepen tests fit in existing test_cli.py

*Existing infrastructure: test_cli.py has `_install_crawl4ai_mock()` pattern — new tests follow same approach.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
