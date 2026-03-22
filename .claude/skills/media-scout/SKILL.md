---
name: media-scout
description: "Media discovery pipeline for documentary video topics. Use this skill when the user wants to find images, photos, documents, or footage for a documentary. Triggers on: 'find media', 'media scout', 'search for images', 'search for footage', 'find visuals for [topic]', or any request to discover visual assets for the channel."
---

# Media Scout

Two-pass media discovery: web images/documents (Pass 1) → YouTube footage leads (Pass 2) → compiled `media_leads.json`.

## Setup (first run only)

```bash
pip install crawl4ai==0.8.0 ddgs yt-dlp
python -m playwright install chromium
```

## Workflow

### Pass 1 — Web Crawl (images + document screenshots)

1. **Resolve project** — Topic is a case-insensitive substring match against `projects/` directory names. Load `entity_index.json` and `Research.md` from the project's `research/` directory.

2. **[HEURISTIC] Generate search queries** — Build 15-30 queries using entity cross-products from `entity_index.json`. Read `@.claude/skills/media-scout/prompts/search_queries.md` for the strategy and templates.

3. **Execute queries via crawl4ai.** For each result page:
   - Extract embedded images from `CrawlResult.media["images"]` (use `image_score_threshold` to filter noise).
   - **Screenshot document-like pages** (newspaper articles, government reports, official documents) via `CrawlerRunConfig(screenshot=True)` — only when the page layout itself conveys information (headlines, letterheads, timelines). If the page is just a container for photos, extract the image URLs instead.
   - **Saving screenshots:** When `screenshot=True` is used, the screenshot data is in `CrawlResult.screenshot` (base64-encoded PNG). Decode and save it to `projects/N. [Title]/research/screenshots/{sanitized_source_name}.png`. Set the `local_path` field in the web_assets entry to the relative path (e.g., `screenshots/change_org_duplessis_petition.png`). Create the `screenshots/` directory if it doesn't exist.

4. **[HEURISTIC] Evaluate web assets** — For each asset, classify `media_type` (image/document) and write a relevance description explaining why it matters to the documentary.

   | Source Type | Description |
   |-------------|---------------|
   | Government sites (.gc.ca, .gouv.qc.ca) | |
   | News sites (cbc.ca, radio-canada.ca) | |
   | Wikimedia Commons | |
   | Academic/research | |
   | Personal blogs, memorial sites | |
   | Social media | |

5. **Present summary table**. Ask: "Proceed to Pass 2?"

### Pass 2 — YouTube Search (footage leads)

1. Build YouTube search queries from `entity_index.json` key entities — persons, institutions, events. Focus on combining entity names with terms like `documentary`, `interview`, `archival footage`, `news report`.

2. Run `yt-dlp "ytsearch5:query" --flat-playlist --dump-json` for each query. Collect structured metadata (title, duration, channel, view count).

3. **Re-resolve URLs by title.** The `--flat-playlist` flag returns video IDs from YouTube's search index, which can be stale — videos get taken down and re-uploaded under different IDs. For every result, re-resolve the URL using the exact title:
   ```bash
   yt-dlp "ytsearch1:<exact video title>" --dump-json --no-download
   ```
   This fetches the current live URL for that title. Confirm it's the same video by checking that the duration and channel match the original metadata. If no match is found, drop the entry.

4. **[HEURISTIC] Evaluate YouTube results** — Read `@.claude/skills/media-scout/prompts/youtube_evaluation.md` for scoring criteria. Skip content farms, re-uploads, reaction videos, and clips under 30 seconds. Score remaining results 1-4 (primary source → marginal).

5. **Present summary table** (count, top 5 by relevance). Ask: "Accept leads?"

### Compile

1. Merge web assets and YouTube leads into `media_leads.json` (schema below).
2. Write to `projects/N. [Title]/research/media_leads.json`.
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
| Schema compliance | `media_leads.json` validates against the output schema below |

## Scope

- **Web + YouTube only.** No Internet Archive (that's the B-Roll Curator's domain). No commercial marketplaces.
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
      "description": "What the asset shows in documentary context",
      "local_path": "screenshots/filename.png (only for capture_type: screenshot)",
      "relevance": "Why this matters to the documentary"
    }
  ],
  "youtube_urls": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video title from yt-dlp",
      "duration": "43:12",
      "channel": "Channel name",
      "description": "What usable footage exists, with timestamps if identifiable",
      "relevance": "Score N — brief justification"
    }
  ]
}
```

For document screenshots, add `"capture_type": "screenshot"` and `"local_path"` to the web_assets entry. The `local_path` is relative to the project's `research/` directory.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Media leads | `projects/N. [Title]/research/media_leads.json` | JSON with `web_assets` + `youtube_urls` arrays |

Falls back to `.claude/scratch/media-scout/` if no project directory matches.
