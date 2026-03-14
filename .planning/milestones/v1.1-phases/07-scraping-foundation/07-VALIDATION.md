---
phase: 7
slug: scraping-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already in project) |
| **Config file** | `pytest.ini` (exists at project root) |
| **Quick run command** | `PYTHONPATH=".claude/skills/researcher/scripts" pytest tests/test_researcher/ -x --tb=short` |
| **Full suite command** | `PYTHONPATH=".claude/skills/channel-assistant/scripts:.claude/skills/researcher/scripts" pytest -x --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=".claude/skills/researcher/scripts" pytest tests/test_researcher/ -x --tb=short`
- **After every plan wave:** Run `pytest -x --tb=short` (full suite)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | SCRP-01 | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_domain_isolation -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | SCRP-02 | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_content_length_validation -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | SCRP-02 | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_retry_exhaustion -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | SCRP-03 | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_tier3_skipped -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | SCRP-03 | unit (pure Python) | `pytest tests/test_researcher/test_tiers.py::test_classify_domain -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | RSRCH-01 | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_find_project_dir -x` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 1 | RSRCH-01 | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_find_project_dir_multiple_matches -x` | ❌ W0 | ⬜ pending |
| 07-02-04 | 02 | 1 | RSRCH-01 | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_standalone_mode -x` | ❌ W0 | ⬜ pending |
| 07-02-05 | 02 | 1 | RSRCH-01 | integration | `pytest tests/test_researcher/test_cli.py::test_cmd_survey_smoke -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_researcher/__init__.py` — test package marker
- [ ] `tests/test_researcher/test_fetcher.py` — stubs for SCRP-01, SCRP-02
- [ ] `tests/test_researcher/test_tiers.py` — stubs for SCRP-03
- [ ] `tests/test_researcher/test_url_builder.py` — stubs for RSRCH-01
- [ ] `tests/test_researcher/test_cli.py` — smoke test for cmd_survey
- [ ] Update `pytest.ini` pythonpath to include `.claude/skills/researcher/scripts`
- [ ] Install crawl4ai: `pip install crawl4ai==0.8.0 && crawl4ai-setup`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DDG HTML endpoint not blocked | RSRCH-01 | Anti-bot behavior varies by network | Run `pytest tests/test_researcher/test_fetcher.py::test_ddg_live -x` on real network |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
