---
phase: 8
slug: survey-pass
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` or `pyproject.toml` (check root) |
| **Quick run command** | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"` |
| **Full suite command** | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"`
- **After every plan wave:** Run `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 0 | RSRCH-02 | unit | `pytest tests/test_researcher/test_tiers.py -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 0 | RSRCH-02 | unit | `pytest tests/test_researcher/test_url_builder.py -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 0 | RSRCH-02 | unit | `pytest tests/test_researcher/test_cli.py -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 0 | RSRCH-02 | integration | `pytest tests/test_researcher/test_integration.py -x --tb=short -m integration` | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 1 | RSRCH-02 | unit | `pytest tests/test_researcher/test_tiers.py::test_reddit_tier2 -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-06 | 01 | 1 | RSRCH-02 | unit | `pytest tests/test_researcher/test_cli.py::test_summary_table -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-07 | 01 | 1 | RSRCH-02 | unit | `pytest tests/test_researcher/test_cli.py::test_domain_field -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-08 | 01 | 2 | RSRCH-02 | unit | `pytest tests/test_researcher/test_cli.py::test_manifest_schema -x --tb=short` | ❌ W0 | ⬜ pending |
| 08-01-09 | 01 | 2 | RSRCH-04 | unit | `pytest tests/test_researcher/test_cli.py::test_scratch_dir -x --tb=short` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_researcher/test_tiers.py` — add tests for reddit.com Tier 2 reclassification and old.reddit.com
- [ ] `tests/test_researcher/test_url_builder.py` — add tests for DDG URL parsing helper
- [ ] `tests/test_researcher/test_cli.py` — add: table output format test, `domain` field in src_NNN.json, manifest schema completeness test
- [ ] `tests/test_researcher/test_integration.py` — add integration test for `result.links["external"]` on DDG page to confirm URL format

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DDG HTML page structure stable | RSRCH-02 | Depends on external DDG service | Run `cmd_survey "test topic"` and verify DDG results are extracted |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
