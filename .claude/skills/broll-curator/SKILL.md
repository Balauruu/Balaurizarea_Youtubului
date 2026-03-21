---
name: broll-curator
description: "B-roll discovery pipeline for documentary video projects. Searches Internet Archive collections and the local Asset Library for atmospheric/conceptual footage matching shotlist themes. Use this skill when the user wants to find b-roll, search IA, search archive, run the b-roll curator, or find atmospheric footage for a project."
---

# B-Roll Curator Skill

Two-source b-roll discovery pipeline that searches Internet Archive collections and the local Asset Library for atmospheric footage matching `broll_themes` from a project's shotlist.

## Setup (first run only)

```bash
pip install internetarchive
```

> The `internetarchive` package provides `ia.search_items()` for metadata queries against IA's Advanced Search API.

The Asset Library requires a LanceDB index at `D:/VideoLibrary/index/`. If the index doesn't exist, run the asset-manager-v2 `index` command first to build it from downloaded video files.

## Invocation

> This skill is agent-executed. The agent reads the SKILL.md and follows the workflow below, using the `internetarchive` Python package and LanceDB queries.

---

## Workflow

### Source 1 — Internet Archive Search

1. Load `shotlist.json` from the project directory, extract the `broll_themes` array.
2. For each theme, read its `concept`, `mood`, `search_direction`, and `cartoon_angle` fields.
3. **[HEURISTIC] Generate IA queries** — read the prompt at `@.claude/skills/broll-curator/prompts/ia_search.md`, then build 2-4 IA Advanced Search queries per theme using collection filters, mediatype filters, and conceptual keywords derived from the theme's `search_direction` and `cartoon_angle`.
4. Execute each query via `internetarchive` Python package: `ia.search_items(query)`. Collect item metadata (identifier, title, description, collection, mediatype).
5. Print IA results summary per theme. Ask: "Accept IA results, refine queries, or expand search?"

### Source 2 — Asset Library Search

1. For each theme, embed `concept` + `search_direction` as a text query.
2. Search LanceDB at `D:/VideoLibrary/index/` for semantically similar indexed clips (`top_k=10` per theme).
3. For each match, record `video_path`, `start_sec`, `end_sec`, and similarity `score`.

### Evaluate & Compile

1. **[HEURISTIC] Evaluate candidates** — assess each IA item and Asset Library match for conceptual fit. The match is metaphorical, not literal — "Institutional confinement" maps to factory footage, dormitory footage, military barracks, NOT the documentary's specific subject.
2. Recommend 1-5 IA videos/collections per theme. For Asset Library matches, include specific timestamps.
3. Compile all recommendations into `broll_candidates.json`.
4. Run audit checks below.
5. Print full candidates summary. Ask: "Accept candidates?"

---

## Checkpoints

| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Source 1, Step 5 | IA search results summary: items found per theme, top 3 by relevance per theme, collection distribution | Accept results, refine queries, or expand search to additional collections |
| Evaluate & Compile, Step 5 | Full candidates summary: all IA recommendations + Asset Library matches, organized by theme with match reasoning | Accept candidates, request more searches for under-served themes, or remove false positives |

## Audit (after Compile, before writing final output)

| Check | Pass Condition |
|-------|---------------|
| Theme coverage | Every `broll_theme` in shotlist.json has ≥1 candidate in broll_candidates.json |
| No prohibited sources | Zero references to commercial footage marketplaces or Media Scout domain (web crawl, YouTube) in broll_candidates.json |
| License fields present | Every candidate has a non-empty `license` field (not fabricated — "unknown" is acceptable, blank is not) |
| Schema compliance | broll_candidates.json validates against the output schema below |

---

## Scope Boundaries

- **Owns Internet Archive search.** All IA interaction goes through this skill — no other skill queries archive.org.
- **Owns Asset Library search.** Semantic search against the LanceDB video index for b-roll matching.
- **No web crawl or YouTube.** Web search and YouTube discovery belong to the Media Scout skill.
- **No stock sites.** Commercial footage marketplaces are excluded. All media must come from real-world archival sources or the local Asset Library.
- **No video downloading.** This skill recommends sources for user scrubbing (human-in-the-loop). It does not download or extract video content.
- **No asset extraction.** The user extracts clips manually or via the `asset-manager-v2 extract` command after reviewing recommendations.

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

### internet_archive candidate fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| theme_id | string | yes | References a broll_theme `id` from shotlist.json |
| source | string | yes | Always `"internet_archive"` |
| source_url | string | yes | Direct URL to the IA item page |
| title | string | yes | Item title from IA metadata |
| collection | string | yes | IA collection the item belongs to |
| description | string | yes | Agent-written description of what's in the item and how it maps to the theme |
| match_reasoning | string | yes | Explains the conceptual/metaphorical connection between the item and the theme |
| license | string | yes | License from IA metadata (e.g., "PD", "CC-BY", "unknown") |

### asset_library candidate fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| theme_id | string | yes | References a broll_theme `id` from shotlist.json |
| source | string | yes | Always `"asset_library"` |
| video_path | string | yes | Relative path within the Asset Library |
| start_sec | number | yes | Start timestamp of the matching clip segment |
| end_sec | number | yes | End timestamp of the matching clip segment |
| score | number | yes | Semantic similarity score from LanceDB (0.0-1.0) |
| description | string | yes | Agent-written description of the clip content |
| license | string | yes | License of the source video |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| B-roll candidates | `projects/N. [Title]/broll_candidates.json` | JSON with `candidates` array (schema above) |
