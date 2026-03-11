# Phase 05 Deferred Items

## Pre-existing Issues (Out of Scope for This Plan)

### scraper.py working-tree modification breaks test_scraper.py

**File:** `.claude/skills/channel-assistant/scripts/channel_assistant/scraper.py`
**Test:** `tests/test_channel_assistant/test_scraper.py::TestScrapeChannel::test_raises_scrape_error_after_retries_exhausted`
**Status:** Pre-existing modification in working tree (present before 05-01 execution began)
**Symptom:** `mock_run.call_count == 6` instead of expected 3 — the fallback flat-playlist path adds a second set of retries
**Note:** The committed version of scraper.py passes this test. The working-tree version has uncommitted changes that trigger the fallback path twice. This predates Plan 05-01 and is unrelated to trend_scanner work.
**Action needed:** Review and commit/revert scraper.py working-tree changes in a separate session.
