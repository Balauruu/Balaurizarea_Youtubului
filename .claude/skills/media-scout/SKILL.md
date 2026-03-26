---
name: media-scout
description: "Media discovery pipeline for documentary video topics — discovers and downloads images and documents, discovers YouTube footage leads (URLs only, no video downloads). Use this skill when the user wants to find images, photos, documents, or footage leads for a documentary. Triggers on: 'find media', 'media scout', 'search for images', 'find visuals for [topic]', or any request to discover visual assets for the channel."
---

# Media Scout

Two-pass media discovery: web images/documents with downloads (Pass 1) → YouTube footage leads as URLs only (Pass 2) → compiled `media_leads.json`. Video downloads are handled by asset-downloader.

## Dependencies

- **crawl4ai** — web crawling and image extraction. Installed in a venv — activate it before running any crawl4ai code. Use whatever version is installed; if a run fails due to API changes, update crawl4ai (`pip install -U crawl4ai`) and retry.
- **yt-dlp** — YouTube video validation and download

---

## Workflow

### Pass 1 — Web Crawl (images + document screenshots)

1. **Resolve project** — Topic is a case-insensitive substring match against `projects/` directory names. Load `entity_index.json` and `Research.md` from the project's `research/` directory. No match → error.

2. **[HEURISTIC] Generate search queries** — Build 15-30 queries using entity cross-products from `entity_index.json`. Read `@.claude/skills/media-scout/prompts/search_queries.md` for the strategy and templates.

3. **Discover source pages** — Use `WebSearch` (Claude's built-in tool) as the primary discovery method. For each query, collect URLs of relevant source pages — news articles, Wikipedia, archives, encyclopedias — that are likely to contain images or documents.

   WebSearch handles search engine interaction reliably. crawl4ai is used in the next step to extract content from the discovered pages — not for search itself.

4. **Extract images from source pages** — Use the bundled `scripts/crawl_images.py` to batch-crawl pages and extract scored images. Do not write a new crawl script — the bundled script handles crawl4ai configuration (image scoring, cache bypass, timeouts, concurrent processing).

   **How to use:**
   1. Write the list of discovered URLs to a JSON file in `.claude/scratch/`:
      ```json
      ["https://en.wikipedia.org/wiki/Topic", "https://example.com/article"]
      ```
   2. Run the bundled script (activate crawl4ai venv first):
      ```bash
      C:/Users/iorda/venvs/crawl4ai/Scripts/python .claude/skills/media-scout/scripts/crawl_images.py \
        --input .claude/scratch/image_urls.json \
        --output .claude/scratch/crawl_results.json
      ```
   3. Read `crawl_results.json` — each URL maps to `{success, images: [{src, alt, score, desc}], error}`.

   For a quick single-page crawl (1-2 URLs), the CLI (`crwl URL -o json`) is still faster than running the batch script.

   If crawl4ai raises import errors or unexpected API errors, update it (`pip install -U crawl4ai`) and retry. The API evolves across versions.

   Never use `ddgs` for image search — the pipeline is always: WebSearch discovers URLs → crawl4ai extracts images from those pages.

5. **[HEURISTIC] Curate screenshots and documents** — This step adds `document` entries to the asset list. It is separate from Step 4 (image extraction) and both must happen — extracting images from a Wikipedia page does NOT replace screenshotting it.

   **Wikipedia articles (mandatory)** — For every Wikipedia page crawled in Step 4, add a `document` entry with `capture_type: "screenshot"`. Wikipedia pages render reliably, contain structured info + embedded images in context, and make excellent documentary B-roll. The full-page screenshot captures layout and context that individual extracted images lose.

   **Taking Wikipedia screenshots** — Use the bundled `scripts/wiki_screenshots.py`. Do not write a new screenshot script — the bundled script handles viewport sizing, PNG-to-JPEG conversion (quality 85), and size validation (discards < 10KB, skips existing).

   1. Write the URL + filename pairs to a JSON file in `.claude/scratch/`:
      ```json
      [
        ["https://en.wikipedia.org/wiki/Topic", "wiki-topic-en.jpg"],
        ["https://fr.wikipedia.org/wiki/Sujet", "wiki-sujet-fr.jpg"]
      ]
      ```
      Use `.jpg` extension to get automatic JPEG conversion (smaller files). Use `.png` if you need lossless.
   2. Run the bundled script:
      ```bash
      C:/Users/iorda/venvs/crawl4ai/Scripts/python .claude/skills/media-scout/scripts/wiki_screenshots.py \
        --input .claude/scratch/wiki_pages.json \
        --output-dir "projects/N. [Title]/assets/documents"
      ```
   3. The script prints results per file and writes a `.results.json` summary next to the input.

   **PDF primary sources** — If a crawled page links to downloadable PDFs (government reports, court filings, academic papers), download the PDF directly and add a `document` entry with `capture_type: "pdf_download"`.

   **Do not screenshot** petition sites, government info pages, archive catalog metadata pages, or any general web page. These produce useless captures (blank pages from JS-heavy sites, or oversized generic web UI). Extract their images via crawl4ai (Step 4) instead.

6. **[HEURISTIC] Evaluate and deduplicate** — The most important step. Evaluate every asset individually as if briefing a documentary editor. For each image, answer two questions:

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
   | National news outlets | High |
   | Government sources | High |
   | Academic/research | Medium |
   | Personal blogs, memorial sites | Medium |
   | Social media | Low |

7. **Download discovered assets** — After curation, download the actual image and document files:

   **Images** (photos, portraits, mugshots) → `projects/N. [Title]/assets/archival/`

   **Documents** (document images, web page captures, PDFs) → `projects/N. [Title]/assets/documents/`

   For each curated web_asset:
   - If `media_type` is `image`: download the image URL directly using crawl4ai or HTTP GET to `assets/archival/{descriptive_filename}.{ext}`
   - If `media_type` is `document` or `capture_type` is `screenshot`/`pdf_download`: save to `assets/documents/{descriptive_filename}.{ext}`
   - After download, update the entry's `local_path` field with the path relative to the project directory (e.g., `assets/archival/victim-portrait.jpg`)
   - Skip files that already exist at the target path (idempotent)
   - Validate downloaded files: discard if under 10KB (broken) or over 15MB (wrong asset)

8. **Status report** — Present summary table: count by type, download success rate, and **failed downloads with reasons** (so the user can retry or find alternatives). Auto-proceed to Pass 2.

### Pass 2 — YouTube Search (footage leads)

YouTube video discovery uses **crawl4ai for search, yt-dlp for validation only**. This separation exists because `yt-dlp "ytsearch"` returns stale video IDs (90% broken URL rate in testing), while crawl4ai extracts current live URLs from YouTube's rendered search pages.

1. **Build search queries** from `entity_index.json` key entities — persons, institutions, events. Combine entity names with terms like `documentary`, `interview`, `archival footage`, `news report`.

2. **Crawl YouTube search results via crawl4ai** — For each query, crawl `youtube.com/results?search_query=...`. Parse the returned markdown for video URLs (`/watch?v=` links), titles (from heading text), and durations (from `[MM:SS` patterns). Strip `&pp=` tracking parameters. Deduplicate by video ID.

   **crawl4ai configuration for YouTube:**
   - Set `page_timeout=60000` — YouTube is JS-heavy and slow to render search results
   - Set `wait_for="css:ytd-video-renderer"` — wait for video result elements to load before extracting
   - Set `scan_full_page=true` — scroll to load more results beyond the initial viewport
   - Use `headless=true` with a realistic `user_agent` to reduce bot detection risk

3. **[HEURISTIC] Pre-filter from crawl metadata** — Before spending yt-dlp API calls, apply hard filters using the titles and durations extracted from crawl4ai in the previous step. This typically eliminates 60-80% of results and is essential to avoid YouTube rate limiting.

   Discard immediately if:
   - **Wrong topic** — The title clearly has nothing to do with the documentary subject. YouTube search returns many false positives — a query for a specific historical event will also return similarly-named TV shows, unrelated news, or tangential content from other regions.
   - **Duration < 30 seconds** — If duration was parsed from the crawl results.
   - **AI content farm signals** — Channel names matching known patterns (see `youtube_evaluation.md`), sensationalist title reformulations.
   - **Reaction/commentary format** — Titles like "Top 10", "REACTION", "REACTS TO".

   Keep the crawl4ai-extracted title and duration for each surviving candidate — these will be verified against yt-dlp metadata in the next step.

4. **Validate remaining candidates with yt-dlp** — Run `yt-dlp --dump-json --no-download "URL"` on the pre-filtered set to confirm each video is live and extract authoritative metadata (title, duration, channel, view_count, upload_date). Drop dead URLs. Never use `yt-dlp` for search/discovery.

   **Rate limiting (critical):**
   YouTube aggressively rate-limits automated requests. Without pacing, 50+ sequential yt-dlp calls will trigger a 429 block that persists for hours — and that block will also prevent downloads later.

   - Add `--sleep-interval 2` to each yt-dlp validation call (2-second pause between requests)
   - Process in batches of 20 — pause 10 seconds between batches
   - If a 429 error occurs mid-validation, **stop immediately**. Do not retry. The remaining unvalidated URLs can be marked `"validated": false` and included in the output for manual review, but do not burn more API calls trying to push through a rate limit.
   - Video downloads are handled by asset-downloader with its own rate limiting — a 429 during validation here will also block asset-downloader later

   **Cookie fallback:** If rate-limited, try `--cookies-from-browser BROWSER` (chrome, edge, firefox, brave). This authenticates yt-dlp as the user's logged-in YouTube session and often bypasses bot detection.

5. **[HEURISTIC] Evaluate YouTube results** — Read `@.claude/skills/media-scout/prompts/youtube_evaluation.md` for detailed scoring criteria, hard filters, and AI content detection. Key rules:

   - **Discard videos with < 1,000 views** (exception: verified first-person accounts from personal channels of people directly involved in the events)
   - **Discard AI-generated content** — new channels + clickbait titles + very low views
   - **Discard wrong-topic matches** — videos that mention the search terms but aren't actually about the documentary subject
   - **Score 1 is rare** — reserve it for 3-7 videos maximum. It requires: the video is primarily about the topic, contains original footage, and comes from a credible producer
   - Write descriptions as if briefing a video editor — what to look for, where, and why it matters

6. **Present scored leads** — Present a **per-entry table for each score tier**. Every row must include:

   | URL | Title | Channel | Views | Duration | Description |
   |-----|-------|---------|-------|----------|-------------|

   The URL column must contain the full clickable YouTube link so the user can verify each video. Without the link, the user cannot make informed decisions about each lead.

   Also show: total count by tier, any flagged issues (borderline AI content, geo-restricted videos, failed validations with reasons).

   This is the final step of Pass 2. All YouTube URLs are included as leads in `media_leads.json` — asset-downloader handles downloads.

### Compile

1. Merge web assets and YouTube leads into `media_leads.json` (schema below).
2. Write to `projects/N. [Title]/visuals/media_leads.json` with `encoding='utf-8'`.
3. Run audit checks.

---

## Audit

| Check | Pass Condition |
|-------|---------------|
| Schema compliance | `media_leads.json` validates against the output schema |
| No blank screenshots | All files in `documents/` are > 10KB |
| YouTube URLs live | Every entry was validated with `yt-dlp --dump-json` |
| No duplicates | No two web_assets share the same URL or filename |
| No lazy descriptions | Zero entries with "requires manual review" or "Image from [domain]" |
| YouTube view threshold | All entries have view_count ≥ 1,000 (unless survivor channel exception documented) |
| Score 1 budget | At most 7 videos scored as Score 1 |
| Web asset downloads tracked | Every web_asset has a `local_path` (non-null if download succeeded) |
| No orphan files | Every file in `assets/archival/` and `assets/documents/` has a matching `media_leads.json` web_assets entry |

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
      "local_path": "assets/archival/victim-portrait.jpg (relative to project dir, null if download failed)",
      "capture_type": "screenshot | pdf_download (only for documents)",
      "relevance": "Why this specific image matters to the documentary"
    }
  ],
  "youtube_urls": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video title from yt-dlp validation",
      "duration": "43:12",
      "duration_sec": 2592,
      "channel": "Channel name",
      "view_count": 12345,
      "score": 2,
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
| Media leads | `projects/N. [Title]/visuals/media_leads.json` | JSON (UTF-8) with `web_assets` + `youtube_urls` arrays |
| Archival images | `projects/N. [Title]/assets/archival/` | JPG/PNG (photos, portraits, mugshots) |
| Documents | `projects/N. [Title]/assets/documents/` | PNG (screenshots), PDF (primary sources), JPG/PNG (document images) |
