---
phase: 3
slug: topic-generation-scoring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | `pytest.ini` (root) — `pythonpath = .claude/skills/channel-assistant/scripts` |
| **Quick run command** | `pytest tests/test_channel_assistant/test_topics.py -x` |
| **Full suite command** | `pytest tests/test_channel_assistant/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_channel_assistant/test_topics.py -x`
- **After every plan wave:** Run `pytest tests/test_channel_assistant/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | ANLZ-04 | unit | `pytest tests/test_channel_assistant/test_topics.py::TestScoringRubric -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | OUTP-01 | unit | `pytest tests/test_channel_assistant/test_topics.py::TestWriteTopicBriefs -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | OUTP-02 | unit | `pytest tests/test_channel_assistant/test_topics.py::TestDeduplication -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 0 | OUTP-02 | unit | `pytest tests/test_channel_assistant/test_topics.py::TestLoadPastTopics -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 0 | OUTP-01 | unit | `pytest tests/test_channel_assistant/test_topics.py::TestWriteTopicBriefs::test_creates_directory -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_channel_assistant/test_topics.py` — stubs for ANLZ-04, OUTP-01, OUTP-02
- [ ] `.claude/skills/channel-assistant/scripts/channel_assistant/topics.py` — new module (must exist before tests can import)

*Note: pytest and conftest.py already exist from Phase 2.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Topic generation quality | ANLZ-04 | [HEURISTIC] — Claude generates topics via reasoning, not testable code | Run `channel-assistant topics`, inspect briefs for schema compliance and rubric adherence |
| Tavily web research integration | ANLZ-04 | External API, live results vary | Verify tavily-mcp queries return relevant results during generation |
| Dedup against real past_topics.md | OUTP-02 | Requires populated past_topics.md | Add known topic, regenerate, verify rejection |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
