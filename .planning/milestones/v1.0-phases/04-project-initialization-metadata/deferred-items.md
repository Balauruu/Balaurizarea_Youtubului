# Deferred Items - Phase 04

## Pre-existing Issues (Out of Scope)

### test_scraper.py::TestScrapeChannel::test_raises_scrape_error_after_retries_exhausted

**Discovered during:** Plan 04-01 full suite run
**Status:** Pre-existing failure caused by uncommitted changes to scraper.py
**Issue:** `scraper.py` has unstaged changes introducing `_run_ytdlp()` helper that calls `subprocess.run` internally. The test expects `mock_run.call_count == 3` (1 initial + 2 retries) but counts 6 because each yt-dlp invocation now makes 2 subprocess calls.
**Not caused by:** project_init.py or test_project_init.py
**Recommendation:** Investigate and fix the scraper.py changes or update the test mock expectations to match the new internal call structure. This is a separate task outside Phase 04 scope.
