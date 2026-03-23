---
name: media-scout
description: "Media discovery pipeline for documentary video topics. Use this skill when the user wants to find images, photos, documents, or footage for a documentary. Triggers on: 'find media', 'media scout', 'search for images', 'search for footage', 'find visuals for [topic]', or any request to discover visual assets for the channel."
---

# Media Scout

Two-pass media discovery: web images/documents (Pass 1) → YouTube footage leads (Pass 2) → compiled `media_leads.json`.

## Setup (first run only)

```bash
pip install crawl4ai==0.8.0 yt-dlp
python -m playwright install chromium
```


## Windows Encoding

crawl4ai produces Unicode errors on Windows. Prefix every Python/crawl4ai bash command with:

```
set PYTHONUTF8=1 && set PYTHONIOENCODING=utf-8 && python ...
```

Always open files with `encoding='utf-8'`. This is non-negotiable on Windows.

---

## Workflow

### Pass 1 — Web Crawl (images + document screenshots)

1. **Resolve project** — Topic is a case-insensitive substring match against `projects/` directory names. Load `entity_index.json` and `Research.md` from the project's `research/` directory.

2. **[HEURISTIC] Generate search queries** — Build 15-30 queries using entity cross-products from `entity_index.json`. Read `@.claude/skills/media-scout/prompts/search_queries.md` for the strategy and templates.

3. **Discover source pages** — For each query, use crawl4ai (via the `crawl4ai` skill) to crawl search engine result pages and extract relevant source URLs. You can also use `web_search` (Claude's built-in tool) as a supplement. The goal is to collect URLs of relevant source pages — news articles, Wikipedia, archives, encyclopedias — that are likely to contain images or documents.

4. **Crawl source pages via crawl4ai** — For each promising URL from step 3, use the `crawl4ai` skill or crawl4ai directly to extract images from `CrawlResult.media["images"]`. Use `image_score_threshold` to filter decorative noise. Never use `ddgs` for image search — the pipeline is always: discover source page URLs → crawl4ai extracts images from those pages.

5. **[HEURISTIC] Curate screenshots** — Screenshots are only for two specific cases:

   **Wikipedia articles** — Always screenshot relevant Wikipedia article pages. They render reliably, contain structured info + embedded images, and make excellent documentary B-roll.

   **PDF primary sources** — If a crawled page links to downloadable PDFs (government reports, court filings, academic papers), download the PDF directly instead of screenshotting the web page.

   **Do not screenshot** petition sites, government info pages, archive catalog metadata pages, or any general web page. These produce useless captures (blank pages from JS-heavy sites, or 10MB+ generic web UI). Extract their images via crawl4ai instead.

   **After saving any screenshot**, check file size: discard if under 10KB (blank) or over 10MB (generic full-page capture).

6. **[HEURISTIC] Evaluate and deduplicate** — This is the most important step. Evaluate every asset individually as if briefing a documentary editor. For each image, answer two questions:

   **"What specifically does this image show?"** — Write a concrete description. If you can only write "Image from [domain]" or "A building", the image is not specific enough to include. Discard it.

   **"Why does the documentary need this specific image?"** — Write a relevance justification tied to the narrative. "Requires manual review" is never acceptable — it means you skipped evaluation.

   **Deduplication rules:**
   - Remove exact URL duplicates
   - When crawling a page with many images (e.g., a Wikipedia biography), do not bulk-import everything. Select only images directly relevant to the documentary topic
   - Keep at most 2-3 portraits of any single person — pick the most iconic ones for the documentary era
   - Infrastructure named after the subject (highways, bridges, parks, street signs) is not relevant
   - Aerial/geographic photos of cities or regions are not relevant unless they show a specific institution involved in the events
   - If multiple images from the same source have identical or near-identical descriptions, you are bulk-importing — stop and evaluate each individually

   | Source Type | Priority |
   |-------------|----------|
   | Wikimedia Commons | High |
   | News sites (cbc.ca, radio-canada.ca) | High |
   | Government sites (.gc.ca, .gouv.qc.ca) | High |
   | Academic/research | Medium |
   | Personal blogs, memorial sites | Medium |
   | Social media | Low |

7. **Present summary table** (count by type, top 5 by relevance). Ask: "Proceed to Pass 2?"

### Pass 2 — YouTube Search (footage leads)

YouTube video discovery uses **crawl4ai for search, yt-dlp for validation only**. This separation exists because `yt-dlp "ytsearch"` returns stale video IDs (90% broken URL rate in testing), while crawl4ai extracts current live URLs from YouTube's rendered search pages.

1. **Build search queries** from `entity_index.json` key entities — persons, institutions, events. Combine entity names with terms like `documentary`, `interview`, `archival footage`, `news report`.

2. **Crawl YouTube search results via crawl4ai** — For each query, crawl `youtube.com/results?search_query=...`. Parse the returned markdown for video URLs (`/watch?v=` links), titles (from heading text), and durations (from `[MM:SS` patterns). Strip `&pp=` tracking parameters. Deduplicate by video ID.

3. **Validate each URL with yt-dlp** — Run `yt-dlp --dump-json --no-download "URL"` to confirm the video is live and extract metadata (title, duration, channel, view_count, upload_date). Drop dead URLs. Never use `yt-dlp` for search/discovery.

4. **[HEURISTIC] Evaluate YouTube results** — Read `@.claude/skills/media-scout/prompts/youtube_evaluation.md` for detailed scoring criteria, hard filters, and AI content detection. Key rules:

   - **Discard videos with < 1,000 views** (exception: verified survivor personal channels)
   - **Discard AI-generated content** — new channels + clickbait titles + very low views
   - **Discard wrong-topic matches** — videos that mention the search terms but aren't actually about the documentary subject
   - **Score 1 is rare** — reserve it for 3-7 videos maximum. It requires: the video is primarily about the topic, contains original footage, and comes from a credible producer
   - Write descriptions as if briefing a video editor — what to look for, where, and why it matters

5. **Present summary table** (count, top 5 by relevance). Ask: "Accept leads?"

### Compile

1. Merge web assets and YouTube leads into `media_leads.json` (schema below).
2. Write to `projects/N. [Title]/research/media_leads.json` with `encoding='utf-8'`.
3. Run audit checks.

---

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Pass 1 | Web assets summary (count by type, top 5) | Accept, request more queries, remove false positives |
| Pass 2 | YouTube leads summary (count, top 5) | Accept, request more searches, flag low-quality |

## Audit

| Check | Pass Condition |
|-------|---------------|
| Schema compliance | `media_leads.json` validates against the output schema |
| No blank screenshots | All files in `screenshots/` are > 10KB |
| YouTube URLs live | Every entry was validated with `yt-dlp --dump-json` |
| No duplicates | No two web_assets share the same URL or filename |
| No lazy descriptions | Zero entries with "requires manual review" or "Image from [domain]" |
| YouTube view threshold | All entries have view_count ≥ 1,000 (unless survivor channel exception documented) |
| Score 1 budget | At most 7 videos scored as Score 1 |

## Scope

- **Web + YouTube only.** No Internet Archive (B-Roll Curator's domain). No commercial marketplaces.
- **No video downloading** — Pass 2 produces URL leads with metadata. The user handles extraction.

---

## Output Schema — media_leads.json

```json
{
  "web_assets": [
    {
      "url": "https://example.com/image.jpg",
      "source_page": "https://example.com/article",
      "media_type": "image | document",
      "description": "What the asset specifically shows in documentary context",
      "local_path": "screenshots/filename.png (only for screenshot/pdf captures)",
      "capture_type": "screenshot | pdf_download (only for documents)",
      "relevance": "Why this specific image matters to the documentary"
    }
  ],
  "youtube_urls": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video title from yt-dlp validation",
      "duration": "43:12",
      "channel": "Channel name",
      "view_count": 12345,
      "description": "What usable footage exists — briefing for video editor",
      "relevance": "Score N — brief justification",
      "validated": true
    }
  ]
}
```

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Media leads | `projects/N. [Title]/research/media_leads.json` | JSON (UTF-8) with `web_assets` + `youtube_urls` arrays |
| Screenshots | `projects/N. [Title]/research/screenshots/` | PNG (Wikipedia), PDF (primary sources) |

Falls back to `.claude/scratch/media-scout/` if no project directory matches.
