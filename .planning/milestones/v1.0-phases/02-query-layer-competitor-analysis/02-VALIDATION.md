---
phase: 02
slug: query-layer-competitor-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — pytest runs from project root |
| **Quick run command** | `python -m pytest tests/test_channel_assistant/ -x -q` |
| **Full suite command** | `python -m pytest tests/test_channel_assistant/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_channel_assistant/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/test_channel_assistant/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DATA-05 | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestComputeChannelStats -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DATA-05 | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestFormatStatsTable -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | ANLZ-01 | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestDetectOutliers -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | ANLZ-01 | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestDetectOutliersEdgeCases -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | ANLZ-02 | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestSerializeVideos -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | ANLZ-03 | unit | Same as ANLZ-02 (shared serialization) | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | ANLZ-02 | manual-only | Claude reasoning quality — verified by reading analysis.md | N/A | ⬜ pending |
| 02-02-02 | 02 | 2 | ANLZ-03 | manual-only | Claude reasoning quality — verified by reading analysis.md | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_channel_assistant/test_analyzer.py` — stubs for DATA-05, ANLZ-01, data serialization
- [ ] Update `tests/test_channel_assistant/conftest.py` — add multi-channel, multi-video fixtures with varied view counts for stats/outlier testing

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Topic clustering output correctness | ANLZ-02 | Claude reasoning quality — not deterministic | Read analysis.md, verify clusters are sensible groupings |
| Title pattern extraction correctness | ANLZ-03 | Claude reasoning quality — not deterministic | Read analysis.md, verify patterns match actual title structures |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
