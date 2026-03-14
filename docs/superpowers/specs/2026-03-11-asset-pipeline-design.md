# Asset Pipeline Design Spec

## Overview

Design for Phase 2 of the documentary video generation pipeline: the Asset Pipeline. This phase takes the output of Agent 1.4 (Visual Orchestrator) — a shot list of narrative needs — and produces a fully organized, sequentially numbered asset folder ready for import into DaVinci Resolve.

## Architecture: Sequential Pipeline

Agents run in sequence, each triggered manually by the user. No parallel coordination required.

```
Agent 1.4 (Visual Orchestrator) writes shotlist.json
    |
Agent 2.1 (Media Acquisition) — bulk scrape + gap analysis
    |
Agent 2.2 (Vector Generation) — ComfyUI prompts for gaps
    |
Agent 2.3 (Remotion Animations) — motion graphics [details deferred]
    |
Agent 2.4 (Asset Manager) — number, consolidate, final manifest
```

## Handoff Contract: shotlist.json

Agent 1.4 outputs a `shotlist.json` where each entry describes a narrative need, not a strict asset type. Agent 2.1 interprets these loosely.

```json
{
  "shots": [
    {
      "id": "S001",
      "chapter": "intro",
      "narrative_context": "Narrator describes the remote mountain commune in 1970s Mexico",
      "visual_need": "Remote rural settlement, mountainous terrain, 1970s feel",
      "suggested_types": ["archival_video", "archival_photo", "broll"]
    }
  ]
}
```

### Shot Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique shot identifier (S001, S002, ...) |
| `chapter` | string | Script chapter this shot belongs to |
| `narrative_context` | string | What the narrator is saying during this shot |
| `visual_need` | string | Free-text description of what visual is needed |
| `suggested_types` | string[] | Hints, not constraints. Agent 2.1 can use any type that fits |

### Design Principles

- `visual_need` is intentionally loose — "working man scene, industrial era feel" not "archival_video of factory workers in 1970s"
- `suggested_types` are hints. If Agent 2.1 finds a great newspaper clipping for a shot that suggested `archival_photo`, that's fine
- No duration, priority, effects, or post-production instructions — those are the editor's domain

## Agent 2.1: Media Acquisition

Two-pass design. Reads only `shotlist.json` as input (not the script — Agent 1.4 already distilled the script into shot needs). Uses Crawl4ai for web scraping and yt-dlp for video downloads.

### Pass 1: Bulk Acquisition

- Reads shotlist.json to understand the topic (era, location, key figures, events)
- Builds search queries from the topic context
- Scrapes free/public domain sources for everything relevant to the topic
- Downloads into type folders, unnumbered, with descriptive filenames
- Writes each downloaded asset as an entry in `manifest.json`

### Pass 2: Gap Analysis

- [HEURISTIC] task — Claude interprets whether acquired assets match narrative needs
- Reads shotlist.json entries
- Matches acquired assets to shots
- Updates manifest.json with shot mappings
- Outputs unmatched shots into the `gaps` section of manifest.json for downstream agents

### Source Domains (all free, public domain)

**Tier 1 — Primary (most content, best provenance):**
- `archive.org` — Internet Archive / Prelinger Archives. Archival footage, old cartoons, newsreels, photos, documents
- `loc.gov` — Library of Congress. Historical films, photos, newspapers, maps
- `archives.gov` — U.S. National Archives (NARA). Government photos, military records, historical documents
- `commons.wikimedia.org` — Wikimedia Commons. Photos, illustrations, maps, some video (check per-item license)

**Tier 2 — Specialized:**
- `publicdomainreview.org` — Curated old cartoons, historical art, cultural documents
- `images.nasa.gov` — Space footage, earth visualizations, scientific b-roll
- `nps.gov` — National Park Service. Nature b-roll, landscape establishing shots (up to 4K)
- `pdimagearchive.org` — Out-of-copyright images, historical illustrations
- `nationalarchives.gov.uk` — British historical photos, government documents

**Tier 3 — Reference/Screenshot:**
- `en.wikipedia.org` — Wiki text block screenshots
- `britannica.com` — Encyclopedia screenshots
- News sites (various) — Newspaper article screenshots, headline captures

**Old Cartoons (specific collections):**
- `archive.org/details/19201928publicdomainanimation` — 1920-1928 silent cartoons
- `publicdomainreview.org/collections/all/genre/animation/` — Curated PD animations
- LOC National Film Registry public domain list
- Wikimedia Commons animated shorts category

**Rules:**
- All footage must be free. No paid or subscription sources
- Verify soundtracks on old cartoons are also PD (video may be PD but added music may not)
- YouTube (via yt-dlp skill) can be used for CC-licensed and public domain footage

## Agent 2.2: Vector Generation (ComfyUI)

- Reads `gaps` section of manifest.json
- Filters for shots needing generated visual assets (silhouettes, figures)
- [HEURISTIC] Generates ComfyUI prompts optimized for Z-image turbo
- Outputs vector images to `assets/vectors/`
- Updates manifest.json: adds asset entries and sets corresponding gap status to `filled`

**Scope:** Vector/figure generation only. Realistic b-roll generation (AI-generated footage) is out of scope for this pipeline version. Gaps requiring realistic imagery that wasn't found during acquisition remain unfilled and are available in the final manifest for the editor to address manually.

**Note:** SVG scraping from svgrepo.com (mentioned in Architecture.md) is not part of this pipeline. Vector assets are generated, not scraped.

## Agent 2.3: Remotion Animations

**Details deferred to later design session.**

Interface contract only:
- Reads shotlist.json for animation needs (maps, motion graphics, animated sequences)
- Can use vectors from Agent 2.2 as inputs, but doesn't have to
- Outputs to `assets/animations/`
- Updates manifest.json

## Agent 2.4: Asset Manager

Final consolidation step.

- Reads manifest.json (all assets now mapped to shots)
- Assigns sequential prefixes based on order of appearance in shotlist.json (e.g., `001_compound_aerial.mp4`)
- Assets mapped to multiple shots get the number of their first appearance
- Moves unmatched assets to `_pool/` (unnumbered)
- Writes final manifest.json with numbered filenames

## Manifest Location

`manifest.json` lives at `projects/1. [Video Title]/assets/manifest.json` from the moment Agent 2.1 creates it. All subsequent agents (2.2, 2.3, 2.4) read and write it in place.

## Output: Folder Structure

```
projects/1. [Video Title]/
  shotlist.json
  assets/
    archival_footage/     # 001_compound_aerial.mp4, 005_crowd_gathering.mp4
    archival_photos/      # 002_leader_portrait.jpg, 008_compound_photo.jpg
    documents/            # 003_wikipedia_article.png, 007_newspaper_headline.jpg
    broll/                # 004_rural_workers.mp4, 006_old_cartoon_forest.mp4 (old cartoons go here)
    vectors/              # 009_silhouette_leader.png, 011_figure_crowd.png
    animations/           # 010_map_mexico.mp4, 012_silhouette_intro.mp4
    _pool/                # unmatched extras (unnumbered)
    manifest.json
```

## Manifest Schema

```json
{
  "project": "The Cult of XYZ",
  "assets": [
    {
      "filename": "compound_aerial.mp4",
      "numbered_filename": null,
      "folder": "archival_footage",
      "description": "Aerial view of remote mountain settlement, 1970s film stock",
      "mapped_shots": ["S001", "S014"],
      "acquired_by": "agent_2.1"
    }
  ],
  "gaps": [
    {
      "shot_id": "S002",
      "visual_need": "Portrait or silhouette of male authority figure",
      "status": "pending_generation"
    }
  ]
}
```

### Manifest Field Reference

**Asset entry:**

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Original descriptive filename |
| `numbered_filename` | string/null | Sequential filename assigned by Agent 2.4. Null until then |
| `folder` | string | Which type folder the asset lives in |
| `description` | string | What the asset depicts |
| `mapped_shots` | string[] | Shot IDs this asset is assigned to (can be multiple) |
| `acquired_by` | string | Which agent produced this asset |

**Gap entry:**

| Field | Type | Description |
|-------|------|-------------|
| `shot_id` | string | The unmatched shot ID |
| `visual_need` | string | What visual is still needed |
| `status` | string | `pending_generation`, `filled`, or `unfilled` |

**Gap status lifecycle:**
- Agent 2.1 creates gaps as `pending_generation`
- Agent 2.2 sets to `filled` when it generates a matching vector asset
- Agent 2.3 sets to `filled` when it creates a matching animation
- Agent 2.4 sets remaining `pending_generation` gaps to `unfilled` (terminal state — editor handles these manually)

**`acquired_by` valid values:** `agent_2.1`, `agent_2.2`, `agent_2.3`

## Architecture.md Changes Required

The following sections of Architecture.md need updating:

1. **Agent 1.4 output** — Shot list uses loose narrative needs, not strict visual types
2. **Agent 2.1** — Two-pass design (bulk acquire then gap analysis), reads only shotlist.json
3. **Agent 2.2** — Generates vectors via ComfyUI (Z-image turbo), not generic "generative visuals"
4. **Agent 2.3** — Details deferred
5. **Agent 2.4** — Handles sequential numbering as final consolidation step
6. **Source policy** — All sources must be free/public domain, no paid footage
7. **Asset categories** — Simplified to: archival_footage, archival_photos, documents, broll, vectors, animations, _pool
8. **Post-production** — All text elements, effects, overlays, color grading, glitch effects are manual (editor's domain)
9. **Manifest.json** — Central coordination artifact between all Phase 2 agents

## Supersedes

This spec supersedes the Phase 2 sections of Architecture.md. Where they conflict, this spec is authoritative. Architecture.md should be updated to match as part of implementation.

## What This Design Does NOT Cover

- Agent 1.4 (Visual Orchestrator) implementation — that's Phase 1
- Remotion agent specifics — deferred
- Script writing pipeline — Phase 1 scope
- Visual style extraction — separate skill, already implemented
- ComfyUI setup/configuration — infrastructure concern
- Realistic AI-generated b-roll footage — out of scope, handled manually by editor
- SVG scraping from svgrepo.com — replaced by ComfyUI vector generation
