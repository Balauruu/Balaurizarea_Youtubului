# Phase 8: Survey Pass (Pass 1) - Research

**Researched:** 2026-03-12
**Domain:** Web scraping pipeline expansion — DDG HTML parsing, content cleaning, manifest schema, SKILL.md workflow wiring
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Source discovery:**
- DDG parse + expand: fetch DDG HTML results page, parse out top 10-12 result URLs, then fetch those actual pages
- Wikipedia stays as a guaranteed first source (constructed from topic string)
- Single broad DDG query per topic (no multi-query variations)
- DDG results page is used only for URL extraction — no src_NNN.json created for the DDG page itself
- Tier 3 URLs found in DDG results (Facebook, X.com, Instagram) are filtered out before fetching
- Reddit reclassified to Tier 2 — reddit.com and old.reddit.com moved from Tier 3 to Tier 2 (attempt once)

**Evaluation prompt:**
- Evaluation criteria priority: (1) Primary source potential, (2) Unique perspective / local journalism, (3) Contradiction signals
- Claude reads full content of each src_NNN.json during evaluation — not just manifest metadata
- Evaluation runs automatically after cmd_survey completes (SKILL.md instruction, not code)
- Output format: annotated manifest — Claude modifies source_manifest.json adding `evaluation_notes`, `deep_dive_urls`, and `verdict` per source

**Content handling:**
- Store full scraped content — no fixed word count truncation
- Strip structural noise (references/bibliography, navigation, footers, see-also) — not arbitrary word cuts
- Each src_NNN.json includes a `domain` field extracted from the URL

**Survey output:**
- Summary table to stdout: columns #, Domain, Tier, Words, Status; footer with totals
- After evaluation, Claude prints verdict summary and asks "proceed to Pass 2?"

### Claude's Discretion

- DDG HTML parsing implementation (regex, BeautifulSoup, or crawl4ai's link extraction)
- Exact content cleaning approach for stripping structural noise
- Evaluation prompt wording and rubric details
- Annotated manifest field names and schema details beyond the agreed fields

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RSRCH-02 | Pass 1 scrapes 10-15 broad sources (Wikipedia, DuckDuckGo, news archives) and outputs a JSON source manifest | DDG URL parsing, tiers expansion, manifest schema documented below |
| RSRCH-04 | Scraped content stored in `.claude/scratch/researcher/` — never held in conversation context | Scratch-pad convention already established; src_NNN.json pattern already works |
</phase_requirements>

---

## Summary

Phase 8 expands the existing `cmd_survey` scaffold into a fully functional Pass 1 scraper. The Phase 7 infrastructure (fetcher, tiers, url_builder, cli) is already working — Phase 8 adds three capabilities on top: (1) DDG HTML result URL extraction so the survey fetches real pages rather than just the DDG results page, (2) content noise stripping in the source files, and (3) SKILL.md workflow wiring so Claude auto-evaluates after the command completes and annotates the manifest.

The critical design constraint is separation of concerns: `cmd_survey` is pure [DETERMINISTIC] code — it fetches, writes JSON files, writes the manifest, and prints the summary table. All [HEURISTIC] evaluation (reading src files, scoring sources, extracting deep-dive URLs, detecting contradictions) is done by Claude following SKILL.md instructions. The code never calls any LLM API.

The two non-trivial technical questions are: (a) how to parse result URLs from the DDG HTML page reliably, and (b) how to strip structural noise from crawl4ai markdown output. Both have straightforward answers given the existing stack.

**Primary recommendation:** Use BeautifulSoup4 with `html.parser` for DDG link extraction (already in the Python stdlib-adjacent ecosystem and handles malformed HTML well). Use a simple post-processing function in `cli.py` to strip Wikipedia-specific noise sections from markdown; crawl4ai's `word_count_threshold` option handles universal boilerplate removal.

---

## Standard Stack

### Core (already installed — no new dependencies needed for deterministic work)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| crawl4ai | 0.8.0 | Fetch pages with Playwright browser | Already validated, confirmed working |
| Python stdlib `re` | stdlib | DDG result URL extraction via regex | Zero dependency, sufficient for anchor tag href extraction |
| Python stdlib `urllib.parse` | stdlib | URL normalization, domain extraction | Already used in tiers.py and url_builder.py |

### For DDG HTML Parsing (Claude's Discretion)

| Option | Approach | Tradeoff |
|--------|----------|----------|
| `re` regex | Extract `href` attrs from `<a class="result__a">` tags | Fast, zero deps, fragile if DDG changes HTML structure |
| `html.parser` + `HTMLParser` | stdlib HTML parsing | No extra install, more robust than raw regex |
| `beautifulsoup4` | `soup.select("a.result__a")` | Cleanest API, but requires `pip install beautifulsoup4` |
| crawl4ai `links` field | `result.links["external"]` dict | Uses existing tool, returns structured URL list — **recommended** |

**Recommended approach:** crawl4ai already returns `result.links` — a dict with `"internal"` and `"external"` keys. Each entry is a list of dicts with `"href"` and `"text"` keys. This requires zero new dependencies and is the most idiomatic approach given the project's crawl4ai commitment.

**Confirmed from crawl4ai 0.8.0 docs:** `CrawlResult.links` is populated when `CrawlerRunConfig(extract_links=True)` is set. The DDG HTML page's result URLs appear as external links.

**Fallback:** If `result.links` is empty for DDG (anti-bot response), parse `result.html` with `re.findall(r'href="(/l/\?uddg=[^"]+)"', html)` — DDG HTML uses `/l/?uddg=` redirect URLs that need urllib unquoting.

### Content Noise Stripping (Claude's Discretion)

| Approach | What It Strips | When to Use |
|----------|---------------|-------------|
| crawl4ai `word_count_threshold=10` in CrawlerRunConfig | Navigation fragments, menu items under 10 words per block | Universal boilerplate — use always |
| Post-process: strip markdown section by heading | Wikipedia's References, See also, Notes, External links sections | Wikipedia-specific noise |
| Post-process: regex strip footer patterns | Common footer/nav patterns in markdown | General purpose after crawl |

**Recommended approach:** Two-layer:
1. Set `word_count_threshold=10` in `CrawlerRunConfig` — this is a crawl4ai option (confirmed in docs) that filters out short text blocks (navbars, breadcrumbs, UI chrome)
2. Post-process function `_strip_noise(markdown: str) -> str` in `cli.py` — strips Wikipedia sections by heading name match (References, Notes, See also, External links, Bibliography, Further reading)

If no good solution is found during implementation, fall back to storing full content as the user decided.

**Installation:**
```bash
# No new installs required — crawl4ai and stdlib cover all needs
# If BeautifulSoup path chosen:
pip install beautifulsoup4
```

---

## Architecture Patterns

### Recommended Structure — What Changes in Phase 8

The Phase 7 modules remain unchanged except `tiers.py` and `url_builder.py`. All new logic lands in `cli.py` (DDG parsing, noise stripping, table printing) plus a new prompt file.

```
.claude/skills/researcher/
├── scripts/researcher/
│   ├── tiers.py          # MODIFY: move reddit.com/old.reddit.com to TIER_2
│   ├── url_builder.py    # MODIFY: build_survey_urls returns [wikipedia] only (DDG handled in cli)
│   ├── fetcher.py        # NO CHANGE
│   ├── cli.py            # MODIFY: DDG URL parsing, noise stripping, table output, manifest domain field
│   └── __main__.py       # NO CHANGE
└── prompts/
    └── survey_evaluation.md   # NEW: evaluation prompt for Claude's heuristic step

SKILL.md                       # MODIFY: add workflow step for auto-evaluation after cmd_survey
```

### Pattern 1: DDG URL Extraction via crawl4ai links field

**What:** Fetch DDG HTML page, use `result.links["external"]` to extract result URLs, filter by tier.
**When to use:** Primary path — avoids regex brittleness and needs no new dependencies.

```python
# In cmd_survey, after fetching DDG page:
# Source: crawl4ai 0.8.0 CrawlResult.links dict
from researcher.tiers import classify_domain, TIER_3_DOMAINS

def _parse_ddg_result_urls(ddg_result, max_urls: int = 12) -> list[str]:
    """Extract top result URLs from a crawl4ai DDG fetch result.

    Filters Tier 3 domains (social media). Returns up to max_urls.
    """
    external_links = ddg_result.get("links", {}).get("external", [])
    urls = []
    for link in external_links:
        href = link.get("href", "")
        if not href.startswith("http"):
            continue
        if classify_domain(href) == 3:
            continue
        # Skip DDG's own redirect/utility URLs
        if "duckduckgo.com" in href:
            continue
        urls.append(href)
        if len(urls) >= max_urls:
            break
    return urls
```

**NOTE:** The `fetcher.py` `fetch_with_retry` function currently returns only `success/content/error/fetch_status/attempts_used`. To access `result.links`, the DDG fetch needs to either (a) return the raw crawl4ai result alongside, or (b) be a separate fetch call that passes `extract_links=True` in `CrawlerRunConfig`. Option (b) is cleaner — add a `fetch_for_links(url)` function in `fetcher.py`, or handle DDG parsing as a special path in `cmd_survey` directly.

### Pattern 2: Wikipedia Noise Stripping

**What:** Post-process crawl4ai markdown to remove Wikipedia structural sections.
**When to use:** After fetching Wikipedia pages; harmless to run on non-Wikipedia pages.

```python
# Source: project convention — post-process in cli.py
import re

_WIKI_NOISE_HEADINGS = {
    "references", "see also", "notes", "external links",
    "bibliography", "further reading", "citations",
}

def _strip_wiki_noise(markdown: str) -> str:
    """Remove Wikipedia structural noise sections from markdown.

    Strips from the first occurrence of a known noise heading to end of doc.
    Handles both ## and ### heading levels.
    """
    lines = markdown.splitlines()
    cutoff = len(lines)
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip().lower()
        if stripped in _WIKI_NOISE_HEADINGS:
            cutoff = i
            break
    return "\n".join(lines[:cutoff])
```

### Pattern 3: Summary Table Output

**What:** Print structured table to stdout after fetching.
**When to use:** At end of `cmd_survey`, before Claude evaluation step.

```
#   Domain                  Tier   Words   Status
--  ----------------------  ----  ------  --------
1   en.wikipedia.org           1    4523  ok
2   bbc.com                    2    1240  ok
3   reddit.com/r/history       2    3100  ok
4   facebook.com               3       0  skipped
...
--------------------------------------------------
Total: 14 sources — 11 succeeded, 2 failed, 1 skipped
```

Columns: `#` (index), `Domain` (extracted from URL), `Tier`, `Words`, `Status`.

### Pattern 4: Annotated Manifest Schema

The manifest written by `cmd_survey` (base) and annotated by Claude (evaluation step):

```json
{
  "topic": "Jonestown Massacre",
  "run_timestamp": "2026-03-12T10:00:00Z",
  "sources": [
    {
      "index": 1,
      "filename": "src_001.json",
      "url": "https://en.wikipedia.org/wiki/Jonestown",
      "domain": "en.wikipedia.org",
      "tier": 1,
      "word_count": 4523,
      "fetch_status": "ok",
      "evaluation_notes": "Strong overview, links to primary sources. FBI vault documents referenced.",
      "deep_dive_urls": ["https://vault.fbi.gov/jonestown", "https://archive.org/details/jonestown"],
      "verdict": "recommended"
    }
  ]
}
```

**Fields written by `cmd_survey` (deterministic):**
- `index`, `filename`, `url`, `domain`, `tier`, `word_count`, `fetch_status`

**Fields added by Claude evaluation (heuristic):**
- `evaluation_notes` (string) — what was found, why it's useful
- `deep_dive_urls` (array of strings) — URLs extracted from source content for Pass 2
- `verdict` (string) — `"recommended"` | `"skip"`

**Phase 9 contract:** `cmd_deepen` reads `source_manifest.json`, iterates sources where `verdict == "recommended"`, collects all `deep_dive_urls`, and fetches them.

### Anti-Patterns to Avoid

- **DDG page as src_NNN.json:** The DDG results page itself is NOT saved as a source file — it's used only for URL extraction. The per-source files are the actual pages found in results.
- **Calling LLM API from cmd_survey:** All evaluation is [HEURISTIC] — handled by Claude following SKILL.md instructions after the command completes. No LLM calls in Python code.
- **Fixed word-count truncation:** Strip structural noise instead of cutting at N words — the user explicitly rejected truncation.
- **Importing crawl4ai at module level:** Keep deferred imports (already established pattern in fetcher.py) so tests can mock without crawl4ai installed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fetching with browser | Custom HTTP client | `fetch_with_retry` (already exists) | Handles tier logic, retry, content validation |
| DDG URL extraction | Custom HTML parser | crawl4ai `result.links["external"]` | Zero deps, already in the stack |
| URL domain extraction | String splitting | `urllib.parse.urlparse().hostname` | Already used in tiers.py |
| URL tier classification | Inline conditionals | `classify_domain()` from `tiers.py` | Already handles www. prefix stripping |
| Tier 3 filtering | Re-implement in cmd_survey | Call `classify_domain()` in filter | Single source of truth |

---

## Common Pitfalls

### Pitfall 1: DDG anti-bot returns empty links list

**What goes wrong:** `result.links["external"]` returns empty list when DDG serves minimal anti-bot response. `result.markdown` also has minimal content.
**Why it happens:** DDG increasingly fingerprints automated fetches.
**How to avoid:** Check `len(result.links.get("external", [])) < 3` and fall back to `ddgs` library (`from ddgs import DDGS; DDGS().text(topic, max_results=12)`). Integration test `test_ddg_library_fallback` already validates this path.
**Warning signs:** DDG fetch returns < 500 chars in content, or result count < 3 links.

### Pitfall 2: crawl4ai `extract_links=True` not set

**What goes wrong:** `result.links` is empty or missing even for pages with links, because link extraction is opt-in.
**Why it happens:** Default `CrawlerRunConfig` doesn't extract links. Must set `extract_links=True`.
**How to avoid:** Create a separate `CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extract_links=True)` specifically for the DDG fetch. Regular source fetches don't need it.
**Warning signs:** `result.links` returns `{}` or `{"internal": [], "external": []}` on DDG.

### Pitfall 3: Reddit classification not updated in TIER_3_DOMAINS

**What goes wrong:** Reddit URLs from DDG results get skipped as Tier 3 even after the user reclassified them to Tier 2.
**Why it happens:** `tiers.py` still has `reddit.com` and `old.reddit.com` in `TIER_3_DOMAINS`.
**How to avoid:** Remove both from `TIER_3_DOMAINS`, add to `TIER_2_DOMAINS`. Update tests accordingly.
**Warning signs:** Reddit URLs in DDG results show `skipped` in summary table.

### Pitfall 4: src_NNN.json index gap from DDG-only step

**What goes wrong:** If DDG page fetch is counted as index 1 but not saved, src numbering starts at 2 and there's a gap.
**Why it happens:** The DDG fetch happens but produces no src file.
**How to avoid:** Wikipedia is index 1 (always saved). DDG fetch uses a separate code path that extracts URLs but does not produce a src file. Numbering of src files starts from the URLs discovered (Wikipedia = src_001.json, first DDG result = src_002.json).

### Pitfall 5: `crawl4ai[torch]` accidentally installed

**What goes wrong:** `pip install crawl4ai[torch]` installs PyTorch, which violates Architecture.md Rule 1 (no LLM API wrappers/runtimes).
**Why it happens:** Copy-paste from docs or autocomplete.
**How to avoid:** Always `pip install crawl4ai==0.8.0` — bare install only. Documented in SKILL.md.

### Pitfall 6: Noise stripping cuts real content

**What goes wrong:** A source page uses "References" as a real content heading (not a bibliography), and everything after it is stripped.
**Why it happens:** The noise stripping is heuristic and keyword-based.
**How to avoid:** Check stripped word count. If `stripped_words < 0.5 * original_words`, skip stripping for that source and store full content. Log a warning.

---

## Code Examples

### DDG URL Extraction (with extract_links path)

```python
# Source: crawl4ai 0.8.0 CrawlerRunConfig docs
async def _fetch_with_links(url: str) -> dict:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    browser_conf = BrowserConfig(browser_type="chromium", headless=True,
                                  use_persistent_context=False, verbose=False)
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extract_links=True)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)
    return {
        "success": result.success,
        "links": result.links if result.success else {},
        "content": result.markdown.raw_markdown if result.success else "",
        "error": result.error_message or "",
    }
```

### tiers.py Modification (Reddit reclassification)

```python
# Move from TIER_3_DOMAINS to TIER_2_DOMAINS:
TIER_2_DOMAINS: frozenset[str] = frozenset({
    "britannica.com",
    "bbc.com",
    "theguardian.com",
    "nytimes.com",
    "reuters.com",
    "apnews.com",
    "html.duckduckgo.com",
    "duckduckgo.com",
    "reddit.com",        # added Phase 8
    "old.reddit.com",    # added Phase 8
})

TIER_3_DOMAINS: frozenset[str] = frozenset({
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    # reddit.com removed Phase 8
})
```

### build_survey_urls Refactor

```python
# url_builder.py — Phase 8 change:
# build_survey_urls returns only [wikipedia_url]
# DDG expansion is done in cmd_survey after DDG fetch + link extraction

def build_survey_urls(topic: str) -> list[str]:
    """Return base URL list. Wikipedia only — DDG URLs added dynamically in cmd_survey."""
    wiki_query = urllib.parse.quote(topic.replace(" ", "_"))
    return [f"https://en.wikipedia.org/wiki/{wiki_query}"]
```

### survey_evaluation.md prompt structure

```markdown
# Survey Evaluation Prompt

You have just run `cmd_survey` for topic: {topic}

Source files are in: {output_dir}

## Your Task

Read each src_NNN.json file listed in source_manifest.json. For each source:

1. **Primary source potential** (highest priority): Does this source reference or link to
   primary documents — court records, government reports, archive.org documents, .gov URLs?
   Extract those URLs into `deep_dive_urls`.

2. **Unique perspective**: Does this source offer angles not in Wikipedia?
   Prioritize: local journalism (details mainstream outlets miss), firsthand accounts,
   academic analysis, Reddit community discussions.

3. **Contradiction signals**: Does this source contradict other sources you've read?
   Note contradictions in `evaluation_notes` — these become DOSS-02 material.

## Output

Annotate source_manifest.json by adding these fields to each source entry:
- `evaluation_notes`: 1-3 sentences on what was found and why it's useful or not
- `deep_dive_urls`: list of URLs extracted from content for Pass 2 targeted fetch
- `verdict`: "recommended" or "skip"

After annotating, print a verdict summary table and ask: "Proceed to Pass 2 (cmd_deepen)?"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `build_survey_urls` returns [wiki, ddg] | `build_survey_urls` returns [wiki] + DDG expansion in cli | Phase 8 | Enables 10-15 real source pages vs 2 |
| `tiers.py` reddit in TIER_3 | reddit in TIER_2 | Phase 8 | Reddit now attempted once |
| No `domain` field in src_NNN.json | `domain` field extracted from URL | Phase 8 | Enables per-source filtering in evaluation |
| No evaluation step | Auto-evaluation after cmd_survey via SKILL.md | Phase 8 | Pass 1 produces actionable manifest for Pass 2 |

**Deprecated/outdated after Phase 8:**
- `build_survey_urls` returning DDG URL — DDG is now an intermediate step, not a survey source

---

## Open Questions

1. **crawl4ai `result.links` behavior on DDG HTML page**
   - What we know: `extract_links=True` in CrawlerRunConfig is documented to populate `result.links`
   - What's unclear: Whether DDG's static HTML endpoint (`html.duckduckgo.com/html/`) returns link hrefs as absolute URLs or DDG redirect URLs (`/l/?uddg=...`)
   - Recommendation: During Wave 0, write an integration test that fetches DDG and inspects `result.links["external"][0]` to confirm URL format. If they're redirect URLs, add a decode step using `urllib.parse.parse_qs`.

2. **How many DDG results are "real" result links vs. DDG UI links**
   - What we know: DDG HTML page contains result links plus UI/navigation links
   - What's unclear: Whether `result.links["external"]` filters DDG internal links automatically
   - Recommendation: Filter out any href containing `duckduckgo.com` as part of URL extraction. Integration test should assert >= 5 non-DDG URLs returned.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` or `pyproject.toml` (check root) |
| Quick run command | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"` |
| Full suite command | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSRCH-02 | DDG page parsed into 10-12 result URLs | unit | `pytest tests/test_researcher/test_url_builder.py -x --tb=short` | ❌ Wave 0 |
| RSRCH-02 | Reddit URLs classified as Tier 2 (not skipped) | unit | `pytest tests/test_researcher/test_tiers.py -x --tb=short` | ❌ Wave 0 (add to existing file) |
| RSRCH-02 | cmd_survey produces summary table with #/Domain/Tier/Words/Status columns | unit | `pytest tests/test_researcher/test_cli.py -x --tb=short` | ❌ Wave 0 |
| RSRCH-02 | src_NNN.json includes `domain` field | unit | `pytest tests/test_researcher/test_cli.py -x --tb=short` | ❌ Wave 0 |
| RSRCH-02 | source_manifest.json has correct schema (index, filename, url, domain, tier, word_count, fetch_status) | unit | `pytest tests/test_researcher/test_cli.py -x --tb=short` | ❌ Wave 0 |
| RSRCH-04 | Scraped content written to scratch dir, not returned to conversation | unit | `pytest tests/test_researcher/test_cli.py -x --tb=short` | ✅ (smoke test covers this) |
| RSRCH-02 | DDG link extraction integration | integration | `pytest tests/test_researcher/test_integration.py -x --tb=short -m integration` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"`
- **Per wave merge:** `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_researcher/test_tiers.py` — add tests for reddit.com Tier 2 reclassification and old.reddit.com
- [ ] `tests/test_researcher/test_url_builder.py` — add tests for DDG URL parsing helper (if moved to url_builder.py) or test `_parse_ddg_result_urls` in test_cli.py
- [ ] `tests/test_researcher/test_cli.py` — add: table output format test, `domain` field in src_NNN.json, manifest schema completeness test
- [ ] `tests/test_researcher/test_integration.py` — add integration test for `result.links["external"]` on DDG page to confirm URL format

---

## Sources

### Primary (HIGH confidence)

- Existing codebase (`fetcher.py`, `tiers.py`, `url_builder.py`, `cli.py`) — all Phase 7 behavior verified by reading source directly
- `.planning/phases/08-survey-pass/08-CONTEXT.md` — locked decisions read directly
- `.planning/REQUIREMENTS.md` — RSRCH-02, RSRCH-04 requirements read directly

### Secondary (MEDIUM confidence)

- `tests/test_researcher/test_integration.py` — DDG HTML endpoint confirmed working, `result.markdown.raw_markdown` confirmed, ddgs library fallback confirmed
- crawl4ai 0.8.0 `CrawlerRunConfig` `extract_links` parameter — documented in crawl4ai source and mentioned in project STATE.md as known-working version

### Tertiary (LOW confidence — flag for validation)

- `result.links["external"]` format on DDG HTML page: behavior inferred from crawl4ai docs, not directly tested against DDG. Integration test in Wave 0 should validate URL format before relying on it.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and validated in Phase 7
- Architecture: HIGH — phase boundary, module responsibilities, and schema all locked in CONTEXT.md
- Pitfalls: HIGH for known ones (DDG anti-bot, Tier 3 reddit, crawl4ai imports) — MEDIUM for content noise stripping edge cases
- Open questions: LOW — DDG link format needs integration test validation

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (crawl4ai 0.8.0 is pinned; DDG HTML structure is volatile — re-validate if DDG scraping breaks)
