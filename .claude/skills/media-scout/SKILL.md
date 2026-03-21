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
export PYTHONUTF8=1
```

## Workflow

### Pass 1 — Web Crawl (images + document screenshots)

1. **Resolve project** — Topic is a case-insensitive substring match against `projects/` directory names. Load `entity_index.json` and `Research.md` from the project's `research/` directory.

2. **[HEURISTIC] Generate search queries** — Build 15-30 queries using entity cross-products from `entity_index.json`. Read `@.claude/skills/media-scout/prompts/search_queries.md` for the strategy and templates.

3. **Execute queries via crawl4ai.** For each result page:
   - Extract embedded images from `CrawlResult.media["images"]` (use `image_score_threshold` to filter noise).
   - **Screenshot document-like pages** (newspaper articles, government reports, official documents) via `CrawlerRunConfig(screenshot=True)` — only when the page layout itself conveys information (headlines, letterheads, timelines). If the page is just a container for photos, extract the image URLs instead.

4. **[HEURISTIC] Evaluate web assets** — For each asset, classify `media_type` (image/document), note license signals (see table below), and write a relevance description explaining why it matters to the documentary.

   | Source Type | License Signal |
   |-------------|---------------|
   | Government sites (.gc.ca, .gouv.qc.ca) | Likely PD-Canada / Crown copyright |
   | News sites (cbc.ca, radio-canada.ca) | Fair dealing review needed |
   | Wikimedia Commons | Check individual file page |
   | Academic/research | Check page footer — often CC-BY |
   | Personal blogs, memorial sites | Unknown — flag for review |
   | Social media | Skip entirely |

5. **Present summary table** (count by media_type, top 5 by relevance). Ask: "Proceed to Pass 2?"

### Pass 2 — YouTube Search (footage leads)

1. Build YouTube search queries from `entity_index.json` key entities — persons, institutions, events. Focus on combining entity names with terms like `documentary`, `interview`, `archival footage`, `news report`.

2. Run `yt-dlp "ytsearch5:query" --flat-playlist --dump-json` for each query. Collect structured metadata.

3. **[HEURISTIC] Evaluate YouTube results** — Read `@.claude/skills/media-scout/prompts/youtube_evaluation.md` for scoring criteria. Skip content farms, re-uploads, reaction videos, and clips under 30 seconds. Score remaining results 1-4 (primary source → marginal).

4. **Present summary table** (count, top 5 by relevance). Ask: "Accept leads?"

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
| No prohibited sources | Zero IA/archive sites (B-Roll Curator domain) or commercial image marketplaces |
| License signals present | Every `web_assets` entry has a non-empty `license` field ("unknown" is acceptable, blank is not) |
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
      "license": "PD-Canada | fair dealing review | unknown | ...",
      "relevance": "Why this matters to the documentary"
    }
  ],
  "youtube_urls": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video title from yt-dlp",
      "description": "What usable footage exists, with timestamps if identifiable",
      "relevance": "Score N — brief justification",
      "license_notes": "Channel type + licensing consideration"
    }
  ]
}
```

For document screenshots, add `"capture_type": "screenshot"` to the web_assets entry.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Media leads | `projects/N. [Title]/research/media_leads.json` | JSON with `web_assets` + `youtube_urls` arrays |

Falls back to `.claude/scratch/media-scout/` if no project directory matches.
