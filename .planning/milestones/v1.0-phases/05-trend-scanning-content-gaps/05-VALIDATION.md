---
phase: 5
slug: trend-scanning-content-gaps
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` (pythonpath = .claude/skills/channel-assistant/scripts, testpaths = tests) |
| **Quick run command** | `pytest tests/test_channel_assistant/test_trend_scanner.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_channel_assistant/test_trend_scanner.py -x`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | ANLZ-05,06,07 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | ANLZ-05 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeAutocomplete -x` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | ANLZ-05 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeAutocomplete::test_jsonp_parsing -x` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | ANLZ-06 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeSearchResults -x` | ❌ W0 | ⬜ pending |
| 05-01-05 | 01 | 1 | ANLZ-06 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeSearchResults::test_missing_path_returns_empty -x` | ❌ W0 | ⬜ pending |
| 05-01-06 | 01 | 1 | ANLZ-07 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestConvergenceDetection -x` | ❌ W0 | ⬜ pending |
| 05-01-07 | 01 | 1 | ANLZ-07 | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestConvergenceDetection::test_null_dates_excluded -x` | ❌ W0 | ⬜ pending |
| 05-01-08 | 01 | 1 | All | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestUpdateAnalysis -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | All | smoke | `pytest tests/test_channel_assistant/test_trend_scanner.py::test_cmd_trends_registered -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_channel_assistant/test_trend_scanner.py` — stubs for ANLZ-05, ANLZ-06, ANLZ-07
- [ ] All crawl4ai calls mocked (patch `channel_assistant.trend_scanner.AsyncWebCrawler`) — no live network in tests
- [ ] All urllib calls mocked (patch `channel_assistant.trend_scanner.urllib.request.urlopen`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| crawl4ai renders YouTube search JS correctly | ANLZ-06 | Requires live YouTube access; anti-bot detection is external | Run `cmd_trends` with a single keyword; verify non-empty results |
| Autocomplete endpoint not rate-limited | ANLZ-05 | Rate limits depend on external Google servers | Run with 5-10 keywords; check for HTTP errors or empty responses |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
