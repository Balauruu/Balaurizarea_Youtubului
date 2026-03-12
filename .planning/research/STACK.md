# Stack Research

**Domain:** Web Research Agent (Agent 1.2 — The Researcher)
**Researched:** 2026-03-12
**Confidence:** HIGH

> **Scope:** This document covers stack additions and changes for Agent 1.2 only. The v1.0 stack (Python 3.14, SQLite stdlib, yt-dlp 2026.2.4, sqlite-utils, tabulate, python-dateutil) is validated and unchanged. Do not re-evaluate those decisions.

---

## What Agent 1.2 Needs That v1.0 Does Not Have

The Researcher must do three new things:

1. **Multi-source web scraping** — news archives, Wikipedia, government records, court documents, academic papers, archive.org items — across 10-30 URLs per research run
2. **Text extraction** — strip boilerplate from scraped HTML and produce clean prose for Claude to reason over
3. **Source deduplication** — detect when two scraped pages say the same thing and collapse them before passing to Claude

None of these are covered by the existing yt-dlp + crawl4ai-scraper stub (which does single-URL markdown output only).

---

## Recommended Stack Additions

### Core: Web Scraping

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| crawl4ai | 0.8.x | Multi-URL async scraping with JS rendering | Already specified in Architecture.md. Handles JS-heavy pages (news sites, paywalled article previews). `arun_many()` crawls 10-30 URLs concurrently with `MemoryAdaptiveDispatcher`. Produces clean markdown per URL — exactly what Claude needs as research input. Install: `pip install crawl4ai && crawl4ai-setup`. |
| internetarchive | 5.8.0 | archive.org item search and metadata retrieval | **Already installed** (5.8.0 confirmed in environment). Lets the agent search archive.org's catalog for historical documents, newspapers, and government records by keyword. Faster and more reliable than scraping archive.org HTML with crawl4ai because it uses the official API. |

**Installation note for crawl4ai:** `crawl4ai-setup` runs `playwright install` under the hood. This installs Chromium, Firefox, and WebKit browser binaries (~300MB). Run once, not per-project. The `crawl4ai[all]` extra (PyTorch, Transformers) is explicitly NOT needed — those are for LLM-based extraction, which the project forbids (Claude Code handles reasoning natively).

### Supporting: Text Extraction Fallback

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| trafilatura | 2.0.0 | Boilerplate-stripping text extraction from raw HTML | Use when crawl4ai's markdown output is noisy (navigation chrome, cookie banners, ads). Trafilatura achieves F1=0.958 on the ScrapingHub benchmark — highest of any open-source extractor. Accepts raw HTML strings, returns clean prose. Also extracts structured metadata: title, author, publication date, language. Install: `pip install trafilatura`. |
| beautifulsoup4 | 4.14.3 | Targeted HTML parsing for structured sources | **Already installed**. Use for Wikipedia infoboxes, government record tables, and any page where you need specific elements (e.g., extract a table of dates from a court docket). Not for general boilerplate stripping — use trafilatura for that. |

**Why trafilatura over newspaper3k:** newspaper3k has not been updated since 2018. It fails on malformed HTML and modern encoding. Trafilatura is actively maintained (v2.0.0, December 2024), outperforms newspaper3k on every benchmark metric, and handles multilingual content. The choice is clear.

### Supporting: Source Deduplication

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| difflib | stdlib | Near-duplicate detection via sequence ratio | Use `difflib.SequenceMatcher.ratio()` to compare extracted text blocks across sources. Ratio > 0.85 = near-duplicate, collapse to one entry with all source URLs noted. No install needed — already in Python stdlib. |

**Why not text-dedup or semhash:** Those are corpus-scale tools (billions of documents). The research agent scrapes 10-30 pages per run. `difflib.SequenceMatcher` is in stdlib, requires zero install, and handles this scale trivially. The project pattern of preferring stdlib (established in v1.0 Key Decisions) applies directly here.

### Supporting: Wikipedia Access

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.32.5 | MediaWiki Action API calls | **Already installed**. Use the Wikipedia REST API (`https://en.wikipedia.org/w/api.php`) directly with `requests.get()`. Fetches article text, revision history, linked pages, and categories without a third-party wrapper. No rate-limit issues at research scale (1-5 Wikipedia lookups per run). |

**Why not the `wikipedia` PyPI package:** The `wikipedia` library wraps the MediaWiki API but has known disambiguation bugs and hasn't been updated recently. Direct `requests` calls to the MediaWiki API give full control (extract sections, follow disambiguation links, get citation lists) with zero extra dependency.

### Supporting: PDF Handling

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pymupdf | 1.25.x | PDF text extraction for government records, court docs | Use when archive.org or government sites return PDF URLs. PyMuPDF is 60x faster than pdfminer.six and preserves formatting better than PyPDF2. It handles both text-based and mixed PDFs. Install: `pip install pymupdf`. Skip if no PDF sources are found in practice — add reactively. |

**Confidence: MEDIUM.** PyMuPDF's speed advantage (42ms vs 2.5s for pdfminer) is verified across multiple 2025 benchmarks. The `pymupdf` package installs cleanly on Windows. However, if government record PDFs turn out to be scanned images rather than text-based, PyMuPDF cannot extract text without an OCR step — crawl4ai's built-in PDF strategy has the same limitation. Flag for validation when first PDFs are encountered.

---

## Installation

```bash
# New dependencies for Agent 1.2

# Primary scraping engine (one-time setup, installs Playwright browsers ~300MB)
pip install crawl4ai
crawl4ai-setup

# Text extraction fallback
pip install trafilatura

# PDF extraction (install reactively when PDF sources appear)
pip install pymupdf

# Already installed — no action needed:
# internetarchive==5.8.0 (confirmed)
# beautifulsoup4==4.14.3 (confirmed)
# requests==2.32.5 (confirmed)
# difflib (stdlib)
```

**Total new hard dependencies: 2** (crawl4ai, trafilatura). pymupdf is reactive — install when PDFs appear. Everything else is already in the environment.

---

## How These Tools Compose in the Two-Pass Research Pattern

**Pass 1 — Broad Survey:**
1. Build 8-12 search queries from the topic (Claude heuristic)
2. Scrape search results pages and Wikipedia with crawl4ai `arun_many()` — 10-15 URLs concurrently
3. For archive.org: use `internetarchive` to search catalog, get item metadata and download URLs
4. Strip boilerplate from each result with trafilatura (accept crawl4ai markdown as primary, trafilatura as fallback for noisy pages)
5. Dedup with `difflib.SequenceMatcher` — collapse sources that say the same thing
6. Output: cleaned text blocks with source URLs, ready for Claude to synthesize into a topic map

**Pass 2 — Deep Primary Source Dive:**
1. Claude identifies 5-8 high-value URLs from Pass 1 output (heuristic)
2. crawl4ai fetches full content of those URLs, including JS-rendered content
3. MediaWiki API fetches Wikipedia article text and citation list for cross-referencing
4. PyMuPDF extracts text from any PDF documents in the source list
5. Output: primary source text blocks, structured into the Research.md schema

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| crawl4ai 0.8.x | Scrapy | If the agent needed to crawl entire site hierarchies (e.g., scrape every page of a news archive). Scrapy has a steeper setup curve and is overkill for targeted 10-30 URL research runs. |
| crawl4ai 0.8.x | httpx + playwright directly | If crawl4ai proves too heavyweight or has Windows compatibility issues. httpx handles async HTTP; playwright handles JS rendering. More code, same result. |
| trafilatura | newspaper4k (newspaper3k fork) | newspaper4k is an active fork of newspaper3k, updated in 2024. If trafilatura misses content on a specific site type, newspaper4k is the fallback. Do not use newspaper3k (2018, unmaintained). |
| difflib (stdlib) | datasketch MinHash | If the research agent scales to 100+ sources per run. datasketch MinHash handles corpus-scale dedup efficiently. At 10-30 sources, it's complete overkill. |
| internetarchive (already installed) | crawl4ai on archive.org HTML | Crawling archive.org HTML is brittle — the site's structure changes. The official Python client uses the stable S3-like API. Always prefer the official client when it exists. |
| PyMuPDF | pdfminer.six | pdfminer.six is 60x slower and produces equivalent accuracy. Only choose it if PyMuPDF has a Windows install failure (its C extension sometimes has issues). |
| requests + MediaWiki API | `wikipedia` PyPI package | The `wikipedia` package is easier but has disambiguation bugs and is unmaintained. Direct MediaWiki API calls with `requests` give the same result with full control. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain / LlamaIndex | Architecture.md Rule 1: zero LLM API wrappers. These frameworks exist to orchestrate LLMs — Claude Code is already doing that natively. They add 50+ transitive dependencies for zero benefit. | Claude Code native orchestration |
| SerpAPI / Serper / Google Search API | Paid services with quotas. Search results are obtainable by scraping DuckDuckGo or using site-specific search endpoints. | crawl4ai on DuckDuckGo HTML or site-specific search APIs |
| crawl4ai[torch] / crawl4ai[transformer] | These extras enable LLM-based extraction (embedding models, cosine similarity). Claude Code handles semantic reasoning — these just add PyTorch to the dependency graph. | Core crawl4ai only (no extras beyond base install) |
| Scrapy | Enterprise crawl framework. Async, middleware-based, spider-based design. Massive setup overhead for targeted research runs. | crawl4ai `arun_many()` |
| newspaper3k | Unmaintained since 2018. Fails on malformed HTML. Superseded by trafilatura and newspaper4k. | trafilatura |
| spaCy / NLTK | NLP pipelines for entity recognition, tokenization. The research agent does not need NLP — it produces raw text for Claude to reason over. | Claude Code native reasoning |
| Any async task queue (Celery, RQ) | Research runs are single-session, synchronous from Claude's perspective. crawl4ai's internal `MemoryAdaptiveDispatcher` handles concurrency inside a single async session. | crawl4ai built-in concurrency |

---

## Version Compatibility

| Package | Version | Python 3.14 Status | Notes |
|---------|---------|-------------------|-------|
| crawl4ai | 0.8.x | Requires >=3.10 | Test `crawl4ai-doctor` on first install to verify Playwright setup on Windows |
| trafilatura | 2.0.0 | Requires >=3.8 | No known Python 3.14 issues |
| internetarchive | 5.8.0 | Already installed, confirmed working | Uses `requests` which is also installed |
| pymupdf | 1.25.x | Requires >=3.8 | C extension — verify Windows build on install. `pip install pymupdf` installs pre-built wheel on Windows. |
| beautifulsoup4 | 4.14.3 | Already installed | No compatibility concerns |
| requests | 2.32.5 | Already installed | No compatibility concerns |
| difflib | stdlib | Always available | No install needed |

**Windows-specific risk:** crawl4ai runs Playwright (Chromium) as a subprocess. On Windows, this requires the `PYTHONUTF8=1` environment variable or `chcp 65001` to handle UTF-8 output correctly, particularly for non-Latin source content (which historical research frequently encounters). Set `PYTHONUTF8=1` in the skill's run environment.

---

## Sources

- [Crawl4AI Documentation v0.8.x](https://docs.crawl4ai.com/) — Features, installation, `arun_many()`, MemoryAdaptiveDispatcher — HIGH confidence
- [Crawl4AI PyPI](https://pypi.org/project/Crawl4AI/) — Version 0.8.0 (January 16, 2026) confirmed — HIGH confidence
- [Trafilatura PyPI](https://pypi.org/project/trafilatura/) — Version 2.0.0 (December 3, 2024) confirmed — HIGH confidence
- [Trafilatura Evaluation](https://trafilatura.readthedocs.io/en/latest/evaluation.html) — F1=0.958, benchmark methodology — HIGH confidence
- [ScrapingHub Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark) — Newspaper3k vs Trafilatura F1 scores — HIGH confidence
- [PyMuPDF Features Comparison](https://pymupdf.readthedocs.io/en/latest/about.html) — Speed benchmarks vs pdfminer — MEDIUM confidence (benchmarks from official docs, cross-verified with independent 2025 test)
- [internetarchive PyPI](https://pypi.org/project/internetarchive/) — Version 5.8.0 (February 18, 2026) confirmed — HIGH confidence
- [MediaWiki API:Query](https://www.mediawiki.org/wiki/API:Query) — Wikipedia API endpoint reference — HIGH confidence

---
*Stack research for: Agent 1.2 Web Research (documentary video pipeline)*
*Researched: 2026-03-12*
