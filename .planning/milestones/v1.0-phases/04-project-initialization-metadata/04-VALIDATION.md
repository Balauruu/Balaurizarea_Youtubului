---
phase: 4
slug: project-initialization-metadata
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed) |
| **Config file** | `pytest.ini` at project root |
| **Quick run command** | `pytest tests/test_channel_assistant/test_project_init.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_channel_assistant/test_project_init.py -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_creates_numbered_directory -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_increments_past_existing -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_scaffold_subdirs -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_sanitizes_forbidden_chars -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_appends_past_topic -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | OUTP-03 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_past_topic_roundtrip -x` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 1 | OUTP-06 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_creates_metadata_file -x` | ❌ W0 | ⬜ pending |
| 04-01-08 | 01 | 1 | OUTP-06 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_variants_written -x` | ❌ W0 | ⬜ pending |
| 04-01-09 | 01 | 1 | OUTP-06 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_recommended_labeled -x` | ❌ W0 | ⬜ pending |
| 04-01-10 | 01 | 1 | OUTP-06 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_description_written -x` | ❌ W0 | ⬜ pending |
| 04-01-11 | 01 | 1 | OUTP-04 | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_title_length_check -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_channel_assistant/test_project_init.py` — stubs for OUTP-03 and OUTP-06 deterministic behaviors
- [ ] `projects/` directory — must be created by `init_project()` via `parents=True`

*Existing test infrastructure in `pytest.ini` and `tests/test_channel_assistant/` covers all other needs — no new framework setup required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Title variant generation (3-5 variants with different hook types) | OUTP-04 | Claude reasoning — no deterministic output to assert | Run `channel-assistant topics`, then `select` a topic; verify variants in chat output |
| Description generation | OUTP-05 | Claude reasoning — natural language content | Verify description quality and relevance in `metadata.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
