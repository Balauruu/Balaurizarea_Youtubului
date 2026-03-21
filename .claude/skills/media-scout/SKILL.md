---
name: media-scout
description: "Media discovery pipeline for documentary video topics. Use this skill when the user wants to find images, photos, documents, or footage for a documentary. Triggers on: 'find media', 'media scout', 'search for images', 'search for footage', 'find visuals for [topic]', or any request to discover visual assets for the channel."
---

# Media Scout Skill

Two-pass media discovery pipeline that finds web images, document screenshots, and YouTube footage leads for documentary scripts.

## Setup (first run only)

```bash
pip install crawl4ai==0.8.0 ddgs
python -m playwright install chromium
pip install yt-dlp
export PYTHONUTF8=1
```

> crawl4ai and yt-dlp are already installed if you've run the researcher skill.

## Invocation

```bash
# Future implementation — not yet available
PYTHONPATH=.claude/skills/media-scout/scripts python -m media_scout search "Topic"
PYTHONPATH=.claude/skills/media-scout/scripts python -m media_scout compile "Topic"
```

> Until implemented, the agent executes the workflow below manually using crawl4ai and yt-dlp directly.

---

## Workflow

### Pass 1 — Web Crawl (images, documents, screenshots)

1. Load `entity_index.json` and `Research.md` from the project's `research/` directory.
2. **[HEURISTIC] Generate search queries** — read the prompt at `@.claude/skills/media-scout/prompts/search_queries.md`, then build 15-30 targeted queries using entity cross-products from entity_index.json.
3. Execute queries via crawl4ai. For each result page:
   - Extract embedded images from `CrawlResult.media["images"]` (use `image_score_threshold` to filter noise).
   - Capture screenshots of document-like pages via `CrawlerRunConfig(screenshot=True)` — newspaper articles, government reports, Wikipedia sections with useful layouts.
   - Skip screenshots for pages where the embedded images are the real asset.
4. **[HEURISTIC] Evaluate web assets** — classify media_type, note license signals, write relevance descriptions.
5. Print web assets summary table. Ask: "Proceed to Pass 2?"

### Pass 2 — YouTube Search (footage leads)

1. Build YouTube search queries from entity_index.json key entities (persons, institutions, events).
2. Run `yt-dlp "ytsearch5:query" --flat-playlist --dump-json` for each query. Collect structured metadata.
3. **[HEURISTIC] Evaluate YouTube leads** — read the prompt at `@.claude/skills/media-scout/prompts/youtube_evaluation.md`, then score each result for documentary relevance.
4. Print YouTube leads summary table. Ask: "Accept leads?"

### Compile

1. Merge `web_assets` and `youtube_urls` arrays into `media_leads.json`.
2. Write to `projects/N. [Title]/research/media_leads.json`.
3. Run audit checks below.

---

## Checkpoints

| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Pass 1, Step 4 | Web assets summary table (count by media_type, top 5 by relevance) | Accept web assets, request additional queries, or remove false positives |
| Pass 2, Step 3 | YouTube leads summary table (count, top 5 by relevance, total estimated footage) | Accept leads, request additional searches, or flag duplicates/low-quality |

## Audit (after Compile, before writing final output)

| Check | Pass Condition |
|-------|---------------|
| Entity coverage | ≥3 of 5 entity_index.json categories produced at least one media lead |
| No prohibited sources | Zero references to IA/archive sites (B-Roll Curator domain) or commercial image marketplaces in media_leads.json |
| License signals present | Every web_assets entry has a non-empty `license` field (not fabricated — "unknown" is acceptable, blank is not) |
| Schema compliance | media_leads.json validates against the output schema below |

---

## Scope Boundaries

- **Web crawl + YouTube only.** This skill searches the open web and YouTube.
- **No IA/archive site search** — that belongs to the B-Roll Curator skill, which has specialized IA API integration.
- **No commercial image marketplaces** — all media must be sourced from real-world references, not licensed asset libraries.
- **No video downloading** — Pass 2 produces a URL list with metadata. The user handles actual extraction and trimming of YouTube content.

---

## Output Schema — media_leads.json

```json
{
  "web_assets": [
    {
      "url": "https://example.com/image.jpg",
      "description": "Description of what the asset shows",
      "source_page": "https://example.com/article",
      "media_type": "image",
      "license": "PD-Canada",
      "relevance": "Why this matters to the documentary"
    },
    {
      "url": "https://example.com/report",
      "capture_type": "screenshot",
      "description": "Screenshot of document page",
      "media_type": "document",
      "relevance": "Resolution chapter visual"
    }
  ],
  "youtube_urls": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video title from yt-dlp",
      "description": "Agent-written description with timestamps if identifiable",
      "relevance": "Why this video matters, what footage is usable",
      "license_notes": "Channel type + licensing consideration"
    }
  ]
}
```

### web_assets fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| url | string | yes | Direct URL to image/document or screenshot file path |
| description | string | yes | What the asset shows, in documentary context |
| source_page | string | for images | Page the image was extracted from |
| capture_type | string | for documents | "screenshot" when page was captured as document asset |
| media_type | string | yes | "image" or "document" |
| license | string | yes | License signal — PD-Canada, fair dealing review, unknown, etc. |
| relevance | string | yes | Why this asset matters to the documentary narrative |

### youtube_urls fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| url | string | yes | YouTube video URL |
| title | string | yes | Video title from yt-dlp metadata |
| description | string | yes | Agent-written description of usable content with timestamps if identifiable |
| relevance | string | yes | Why this video matters, what footage is usable |
| license_notes | string | yes | Channel type + licensing consideration |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Media leads | `projects/N. [Title]/research/media_leads.json` | JSON with `web_assets` + `youtube_urls` arrays |

Falls back to `.claude/scratch/media-scout/` if no project directory matches.
