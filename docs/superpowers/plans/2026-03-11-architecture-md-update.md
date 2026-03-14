# Architecture.md Phase 2 Update — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update Architecture.md to match the asset pipeline design spec at `docs/superpowers/specs/2026-03-11-asset-pipeline-design.md`

**Architecture:** Direct file edits to Architecture.md — replacing the Agent 1.4 output schema, Phase 2 agent descriptions, asset categories, and manifest schema. No code changes, no tests needed.

**Tech Stack:** Markdown only

**Spec:** `docs/superpowers/specs/2026-03-11-asset-pipeline-design.md`

**IMPORTANT:** All tasks use content anchors (quoted text) to identify replacement boundaries. Line numbers are for initial reference only — after each task, line numbers shift. Always match on the content anchors, not the line numbers. Re-read the file between tasks if needed.

---

## Chunk 1: Update Architecture.md

### Task 1: Update Agent 1.4 Output Schema

**Files:**
- Modify: `Architecture.md` — find `- **Agent 1.4: Visual Orchestrator` through the closing ` ``` ` of the shot list schema (original lines ~101-116)

- [ ] **Step 1: Replace Agent 1.4 output and shot list schema**

Find the block starting with `- **Agent 1.4: Visual Orchestrator (The Director)**` and ending with the closing backticks of the Shot List Entry code block. Replace the entire block with the content from the spec's "Handoff Contract" section. The replacement content is:

```markdown
- **Agent 1.4: Visual Orchestrator (The Director)**
    - ***Function:***  Parses the script to map visual continuity and determine the necessary media for every scene. Outputs a loose shot list of narrative needs — not strict asset types.
    - **Output:** `shotlist.json`

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

    **Shot Entry Fields:**
    - **id**: Unique shot identifier (S001, S002, ...)
    - **chapter**: Script chapter this shot belongs to
    - **narrative_context**: What the narrator is saying during this shot
    - **visual_need**: Free-text description of what visual is needed (intentionally loose)
    - **suggested_types**: Hints, not constraints — acquisition agent can use any type that fits

    **Design Principles:**
    - No duration, priority, effects, transitions, or post-production instructions — those are the editor's domain
    - `needed_assets.json` is no longer a separate output — the manifest serves this role
```

- [ ] **Step 2: Commit**

```bash
git add Architecture.md
git commit -m "docs: update Agent 1.4 output to loose narrative shotlist schema"
```

### Task 2: Replace Phase 2 Section

**Files:**
- Modify: `Architecture.md` — find `### Phase 2: Asset Pipeline` through `- **Output:** The final target. A consolidated, sequentially ordered local folder.` (original lines ~120-193)

- [ ] **Step 1: Replace the entire Phase 2 section**

Find the block starting with `### Phase 2: Asset Pipeline` and ending with Agent 2.4's output line. Replace with the content from the spec's Agent sections. The replacement content is:

```markdown
### Phase 2: Asset Pipeline

This phase translates the shot list into tangible media assets. Agents run sequentially, each triggered manually by the user.

**Architecture:** Sequential pipeline. Each agent reads/writes a shared `manifest.json` at `projects/[Video Title]/assets/manifest.json`.

**Source Policy:** All footage and media must be free (public domain, CC0, or Creative Commons). No paid or subscription sources.

**Tools:** Crawl4ai for web scraping, yt-dlp for video downloads.

```
Agent 1.4 writes shotlist.json
    |
Agent 2.1 (Media Acquisition) — bulk scrape + gap analysis
    |
Agent 2.2 (Vector Generation) — ComfyUI prompts for gaps
    |
Agent 2.3 (Remotion Animations) — motion graphics [details deferred]
    |
Agent 2.4 (Asset Manager) — number, consolidate, final manifest
```

- **Agent 2.1: Media Acquisition**
    - **Function:** Two-pass design. Sources all relevant media for the topic.
    - **Input:** Reads only `shotlist.json` (not the script — Agent 1.4 already distilled the script into shot needs).
    - **Pass 1 — Bulk Acquisition:**
        - Reads shotlist.json to understand the topic (era, location, key figures, events)
        - Builds search queries from the topic context
        - Scrapes free/public domain sources for everything relevant
        - Downloads into type folders, unnumbered, with descriptive filenames
        - Writes each asset as an entry in `manifest.json`
    - **Pass 2 — Gap Analysis [HEURISTIC]:**
        - Matches acquired assets to shot list entries
        - Updates manifest.json with shot mappings
        - Outputs unmatched shots into the `gaps` section for downstream agents
    - **Output:** Downloaded assets in type folders + manifest.json with mappings and gaps
    - **Source Domains:**
        - Tier 1: archive.org, loc.gov, archives.gov, commons.wikimedia.org
        - Tier 2: publicdomainreview.org, images.nasa.gov, nps.gov, pdimagearchive.org, nationalarchives.gov.uk
        - Tier 3 (screenshots): en.wikipedia.org, britannica.com, news sites
        - Old cartoons: archive.org/details/19201928publicdomainanimation, publicdomainreview.org, LOC National Film Registry PD list, Wikimedia Commons animated shorts category
        - YouTube (via yt-dlp) for CC-licensed and public domain footage
    - **Rules:** Verify soundtracks on old cartoons are also PD (video may be PD but added music may not)
- **Agent 2.2: Vector Generation (ComfyUI)**
    - **Function:** Generates vector assets for shots that couldn't be filled by acquisition.
    - **Logic:** Reads `gaps` section of manifest.json. [HEURISTIC] Generates ComfyUI prompts optimized for Z-image turbo. Updates manifest and marks gaps as filled.
    - **Scope:** Vector/figure generation only. Realistic AI-generated b-roll is out of scope — gaps requiring realistic imagery remain unfilled for the editor to address manually.
    - **Output:** Vector images in `assets/vectors/`, manifest.json updated.
- **Agent 2.3: Animation Agent (Remotion)**
    - **Function:** Renders motion graphics (maps, silhouettes, diagrams, other animations).
    - **Logic:** Details deferred to later design session.
    - **Interface:** Reads shotlist.json, can use vectors from Agent 2.2, outputs to `assets/animations/`, updates manifest.json.
    - **Output:** `.mp4` or `.mov` files.
- **Agent 2.4: Asset Manager**
    - **Function:** Final consolidation and sequential numbering.
    - **Logic:** Reads manifest.json. Assigns sequential prefixes based on order of appearance in shotlist.json (e.g., `001_compound_aerial.mp4`). Assets mapped to multiple shots get the number of their first appearance. Moves unmatched assets to `_pool/`. Sets remaining gaps to `unfilled`.
    - **Output:** Numbered assets in type folders + final manifest.json.
```

- [ ] **Step 2: Commit**

```bash
git add Architecture.md
git commit -m "docs: replace Phase 2 with sequential asset pipeline design"
```

### Task 3: Replace Asset Categories and Manifest Schema

**Files:**
- Modify: `Architecture.md:196-225` (the Assets section)

- [ ] **Step 1: Replace the Assets section**

Replace lines 196-225 (from `### Assets:` through `- Effects`) with:

```markdown
### Asset Categories

**Pipeline-acquired (Agent 2.1):**
- `archival_footage/` — Video clips from the era/event
- `archival_photos/` — Period photographs, mugshots, press photos
- `documents/` — Newspaper clippings, document scans, wiki screenshots, web page captures
- `broll/` — Atmospheric/illustrative footage including old cartoons

**Pipeline-generated (Agent 2.2):**
- `vectors/` — ComfyUI Z-image turbo generated figures and assets

**Pipeline-generated (Agent 2.3):**
- `animations/` — Remotion-rendered motion graphics (maps, silhouettes, diagrams)

**Unmatched:**
- `_pool/` — Assets acquired but not mapped to any shot (kept for manual use)

**Editor handles manually (DaVinci Resolve):**
- All text elements (quote cards, testimony cards, date cards, keyword stingers, warning cards)
- Backgrounds, overlays, effects
- Color grading, film grain, vignettes, CRT/VHS effects
- All glitch/distortion effects

### Output Folder Structure

```
projects/1. [Video Title]/
  shotlist.json
  assets/
    archival_footage/     # 001_compound_aerial.mp4
    archival_photos/      # 002_leader_portrait.jpg
    documents/            # 003_wikipedia_article.png
    broll/                # 004_rural_workers.mp4 (old cartoons go here)
    vectors/              # 009_silhouette_leader.png
    animations/           # 010_map_mexico.mp4
    _pool/                # unmatched extras (unnumbered)
    manifest.json
```

### Manifest Schema

The manifest is the central coordination artifact between all Phase 2 agents. It lives at `assets/manifest.json` from the moment Agent 2.1 creates it.

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

**Gap status lifecycle:** `pending_generation` → `filled` (by Agent 2.2 or 2.3) → or `unfilled` (set by Agent 2.4 as terminal state)
```

- [ ] **Step 2: Commit**

```bash
git add Architecture.md
git commit -m "docs: update asset categories, folder structure, and manifest schema"
```

### Task 4: Verify and Final Commit

- [ ] **Step 1: Read the full Architecture.md and verify consistency**

Scan for any remaining references to:
- `needed_assets.json` (removed)
- `svgrepo.com` (removed)
- `visual_type` in shot list (replaced by `visual_need` + `suggested_types`)
- `source_url` in manifest (removed)
- Old asset manifest schema with `id`, `type`, `chapter`, `file`, `status`
- `compositions.json` or `npx remotion render` (old Agent 2.3 specifics, now deferred)
- `context/Styles/` (old Agent 2.2 context reference, removed)
- `opus.pro` or `hera.video` quality target URLs (removed)

- [ ] **Step 2: Fix any remaining inconsistencies found**

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
git add Architecture.md
git commit -m "docs: clean up remaining Phase 2 references in Architecture.md"
```
