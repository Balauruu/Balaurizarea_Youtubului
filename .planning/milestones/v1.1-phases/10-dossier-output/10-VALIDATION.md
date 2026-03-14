---
phase: 10
slug: dossier-output
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — tests run from project root |
| **Quick run command** | `pytest tests/test_researcher/ -x --tb=short -k "writer or write"` |
| **Full suite command** | `pytest tests/test_researcher/ -x --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_researcher/ -x --tb=short -k "writer or write"`
- **After every plan wave:** Run `pytest tests/test_researcher/ -x --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 0 | (structural) | unit | `pytest tests/test_researcher/ -x --tb=short -k "writer"` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | (structural) | unit | `pytest tests/test_researcher/ -x --tb=short -k "writer"` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | (structural) | unit | `pytest tests/test_researcher/ -x --tb=short -k "write"` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | DOSS-01–DOSS-09 | manual/heuristic | N/A — Claude synthesis | N/A | ⬜ pending |
| 10-02-02 | 02 | 1 | MEDIA-01, MEDIA-02 | manual/heuristic | N/A — Claude synthesis | N/A | ⬜ pending |
| 10-03-01 | 03 | 1 | (structural) | unit | `pytest tests/test_researcher/ -x --tb=short -k "write"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_researcher/test_writer.py` — stubs for writer.py (load_source_files, build_synthesis_input, write_synthesis_input) and cmd_write (smoke test, no-pass2 graceful handling)

*Existing pytest infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Research.md content structure | DOSS-01–DOSS-09 | Claude synthesis output, not deterministic code | Run cmd_write on a real project, read Research.md, verify schema sections present |
| media_urls.md structure | MEDIA-01, MEDIA-02 | Claude synthesis output, not deterministic code | Run cmd_write on a real project, read media_urls.md, verify URL+description+type per entry |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
