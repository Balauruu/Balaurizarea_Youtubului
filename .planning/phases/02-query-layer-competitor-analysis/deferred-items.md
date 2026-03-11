# Deferred Items -- Phase 02

## Pre-existing Test Failure

- **File:** `tests/test_channel_assistant/test_scraper.py::TestScrapeChannel::test_raises_scrape_error_after_retries_exhausted`
- **Issue:** Test expects `mock_run.call_count == 3` but gets 6. Scraper retry logic calls subprocess.run more times than expected (likely 2 calls per attempt: playlist then channel).
- **Discovered during:** 02-03 verification
- **Not fixed:** Pre-existing, unrelated to 02-03 changes
