---
name: broll-curator
description: "B-roll discovery pipeline for documentary video projects. Searches Internet Archive collections and the local Asset Library for atmospheric/conceptual footage matching shotlist themes. Use this skill when the user wants to find b-roll, search IA, search archive, run the b-roll curator, or find atmospheric footage for a project."
---

# B-Roll Curator

Two-source b-roll discovery: Internet Archive + local Asset Library → `broll_candidates.json`.

## Setup (first run only)

```bash
pip install internetarchive
```

The Asset Library requires a LanceDB index at `D:/VideoLibrary/index/`. If missing, run `asset-manager-v2 index` first.

## Workflow

### 1. Resolve Project

Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches → list and ask. No match → error. Load `projects/N. [Title]/visuals/shotlist.json` and extract the `broll_themes` array. Missing shotlist → tell user to run visual-orchestrator first.

### 2. Internet Archive Search

For each theme, read its `concept`, `mood`, `search_direction`, and `cartoon_angle` fields.

**[HEURISTIC] Generate 2–4 IA queries per theme** using the rules below:

**Filters:**
- Always include `mediatype:(movies)` to restrict to video content
- Optionally add `collection:(name)` when targeting a known collection, but don't restrict by default — let IA search broadly

**Keyword strategy:**
- Derive from `search_direction` — break compound descriptions into individual terms. Use `OR` for variants: `(institutional OR factory OR dormitory)`
- For cartoon themes → use `cartoon_angle` keywords
- Use `subject:` field for tag-specific searches: `subject:(corridor OR industrial)`

**Critical:** IA indexes titles, descriptions, and subjects — NOT video frames. Query for what items are *about*, not visual contents.

**Conceptual matching:** The match is metaphorical. "Institutional confinement" → factory footage, dormitories, military barracks — NOT the documentary's specific subject. The theme's mood drives the search.

Execute each query via `ia.search_items(query)`. Collect identifier, title, description, collection, mediatype.

**Present** IA results summary per theme (items found, top 3 per theme, collection distribution). **Ask:** "Accept IA results, refine queries, or expand search?"

### 3. Asset Library Search

For each theme:
1. Embed `concept` + `search_direction` as a text query
2. Search LanceDB at `D:/VideoLibrary/index/` (`top_k=10` per theme)
3. Record `video_path`, `start_sec`, `end_sec`, and similarity `score`

### 4. Evaluate & Compile

**[HEURISTIC] Evaluate candidates** — assess each IA item and Asset Library match for conceptual fit (metaphorical, not literal). Recommend 1–5 IA items per theme; for Asset Library matches include timestamps.

Compile into `projects/N. [Title]/broll_candidates.json` per the schema below.

**Audit before writing:**
- Every `broll_theme` has ≥1 candidate
- Zero references to commercial stock sites or YouTube
- Every candidate has a non-empty `license` field ("unknown" is OK, blank is not)
- JSON validates against the schema below

**Present** full candidates summary by theme with match reasoning. **Ask:** "Accept candidates?"

---

## Output Schema — broll_candidates.json

```json
{
  "candidates": [
    {
      "theme_id": "T1",
      "source": "internet_archive",
      "source_url": "https://archive.org/details/...",
      "title": "Item title",
      "collection": "collection_name",
      "description": "What's in the item and how it maps to the theme",
      "match_reasoning": "Conceptual/metaphorical connection",
      "license": "PD"
    },
    {
      "theme_id": "T1",
      "source": "asset_library",
      "video_path": "channels/prelinger-archives/video_042.mp4",
      "start_sec": 45.2,
      "end_sec": 52.8,
      "score": 0.82,
      "description": "Clip content description",
      "license": "PD"
    }
  ]
}
```

**internet_archive fields:** `theme_id`, `source` (always "internet_archive"), `source_url`, `title`, `collection`, `description`, `match_reasoning`, `license` — all required.

**asset_library fields:** `theme_id`, `source` (always "asset_library"), `video_path` (relative within Asset Library), `start_sec`, `end_sec`, `score` (0.0–1.0), `description`, `license` — all required.
