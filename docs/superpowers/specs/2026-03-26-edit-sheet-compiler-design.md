# Edit Sheet Compiler — Design Spec

**Date:** 2026-03-26
**Status:** Implemented
**Scope:** New skill: edit-sheet-compiler (pipeline terminal step)

---

## Problem Statement

After the full pipeline runs (research → writing → media-scout → shot-planner → asset-downloader → asset-analyzer), the editor has to cross-reference four separate files to figure out what asset goes with which shot. There's no single document that maps the shotlist to actual acquired assets, and no organized project folder where all assets are numbered and ready to drag into DaVinci Resolve.

## Purpose

edit-sheet-compiler is the pipeline's terminal step. It reads all upstream outputs, copies and renames every asset into a flat project folder numbered by shot order, and produces a beautifully formatted edit sheet — the editor's single reference document for the entire video.

---

## Pipeline Position

```
asset-analyzer → edit-sheet-compiler (terminal)
```

Reads from every upstream skill's output. Writes to the project directory. Nothing consumes its output — the human editor does.

## Inputs

| Source | File | What it provides |
|--------|------|-----------------|
| shot-planner | `visuals/shotlist.json` | Every shot: ID, chapter, action, form, text_content, composition_brief, search_query, known_assets, broll_leads, fallback |
| media-scout | `visuals/media_leads.json` | Images and documents with `local_path` (in `assets/archival/` and `assets/documents/`) |
| asset-downloader | `visuals/download_manifest.json` | Downloaded videos with `local_path`, `shot_refs`, `context` |
| asset-analyzer | `visuals/video_analysis.json` | Analyzed segments with extracted clip paths, shot relevance citations |

## Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Organized assets | `projects/N. [Title]/assets/` | Flat directory with all assets renamed to `S{NNN}_{name}.ext` |
| Edit sheet | `projects/N. [Title]/edit_sheet.md` | Formatted Markdown — the editor's companion document |

---

## Classification

**[HEURISTIC]** — Claude reads the data sources, matches assets to shots, decides naming, and composes the edit sheet. One **[DETERMINISTIC]** helper script handles file copying/renaming.

---

## Workflow

### Step 1: Load all data sources

Read the four input files from the project's `visuals/` directory. If `video_analysis.json` doesn't exist (asset-analyzer hasn't run), proceed with just images/docs from media_leads.

### Step 2: Match assets to shots

Walk every shot in `shotlist.json` in order. For each shot, find matching assets:

**`create` shots (text_card, diagram):**
- No asset file. The edit sheet shows the `text_content` field as copy-paste ready text.

**`generate` shots (vector_silhouette):**
- No asset file (ComfyUI not yet implemented). The edit sheet shows the `composition_brief`.

**`find` shots (archival_photo, archival_video, document, landscape):**
- Check `known_assets` array — these are local paths to images/docs already downloaded by media-scout.
- Check `video_analysis.json` segments — any segment whose `relevance` field cites this shot's ID.
- Show all matches equally.

**`curate` shots (broll_atmospheric, broll_cartoon, landscape):**
- Check `video_analysis.json` segments — clips extracted from broll_leads downloads, linked via `shot_refs` in the download manifest.
- Show all matches equally.

**Unmatched shots:**
- `find`/`curate` shots with no matching asset are marked as unfulfilled in the edit sheet.

### Step 3: Identify global-worthy unmatched segments

After matching, some analyzed segments from `video_analysis.json` won't be tied to any shot. These are candidates for the global asset library — but only if they meet strict criteria:

**Include as global if ALL of these are true:**
- `scope` is `"global"` (set by asset-analyzer — generic, not topic-specific)
- The content is clearly reusable across multiple projects (not a specific person, event, or location from this documentary's topic)
- Falls into a recognizable global category: atmospheric b-roll (corridors, weather, textures), cartoon clips with broad metaphorical use, generic archival footage (industrial, urban, institutional)

**Exclude from global:**
- Anything with named people, specific locations, or topic-specific events
- Anything that only makes sense in the context of this documentary
- Segments marked `scope: "project"` by asset-analyzer

### Step 4: Copy and rename assets

Run a script that:

1. For each matched shot-asset pair, copy the asset into `projects/N. [Title]/assets/` with the naming convention:
   - `S{NNN}_{descriptive_name}.ext` — shot number prefix, 5 words max in the descriptive part
   - Example: `S002_carol_marden_portrait.jpg`, `S004_cobweb_hotel_spider_trap.mp4`
   - When multiple assets match one shot: `S007a_cbc_survivor_interview.mp4`, `S007b_radio_canada_testimony.mp4`

2. For global-worthy segments, copy to both:
   - The project's `assets/` dir (with shot-numbered name, or `G001_` prefix if unmatched)
   - The global dir `D:/Youtube/D. Mysteries Channel/3. Assets/{subject_category}/` with a descriptive name

The script takes a JSON instruction file (produced by Claude in Step 2-3) and executes the copies/renames.

### Step 5: Produce the edit sheet

Write `projects/N. [Title]/edit_sheet.md` — a beautifully formatted Markdown document.

**Format:**

```markdown
# Edit Sheet — [Project Title]

> Generated [date]. [total shots] shots, [matched] with assets, [unfulfilled] unfulfilled.

---

## Chapter 1: [Chapter Title]

---

### S001 | text_card | grounding
> **SUMMER 1971 — SHROPSHIRE, ENGLAND**

_Date/location anchor. White text on dark background._

---

### S002 | archival_photo | emotional

**Carol Marden, 26, disappears without notice.**

| # | Asset | File |
|---|-------|------|
| 1 | Portrait of Carol Marden, England, ~1970 | `S002_carol_marden_portrait.jpg` |

---

### S003 | diagram | conceptual
> **Diagram: form date vs. disappearance date — 3-month backdating**

_Timeline discrepancy visualization. Animate in Resolve: two dates, arrow showing 3-month gap._

---

### S004 | broll_cartoon | conceptual

**Authority figure concealing information behind procedure.**

| # | Asset | File |
|---|-------|------|
| 1 | Cobweb Hotel (1936) — spider preparing trap | `S004a_cobweb_hotel_spider_trap.mp4` |
| 2 | Cobweb Hotel (1936) — fly entering hotel | `S004b_cobweb_hotel_fly_enters.mp4` |

Fallback: broll_atmospheric

---

### S005 | vector_silhouette | emotional

**Composition:** Solitary figure in hospital gown, small against institutional wall. Window with bars casts shadow grid across floor.

_⚠ Generate with ComfyUI — not yet implemented._

---

### S006 | archival_video | grounding

**News footage of the Ashfield Rest Home investigation.**

⚠ **Unfulfilled** — no matching asset found.
Search query: _"Ashfield Rest Home investigation news footage, Shropshire, 1972"_

---
```

**Formatting rules:**

- Horizontal rules (`---`) between every shot for clear visual separation
- `create` shots: text content in blockquote (`>`), formatting notes in italic below
- `generate` shots: composition brief in bold, warning note about ComfyUI
- `find`/`curate` shots with assets: narrative context in bold, asset table with all matches
- Unfulfilled shots: warning emoji, the original search query in italic so the editor can try manually
- Chapter headers with horizontal rule above
- Asset tables use `#`, `Asset` (brief description), `File` (filename only, not full path — all files are in the same `assets/` folder)

---

## Global Asset Directory Structure

When the compiler places clips in the global directory, it uses this subject-based structure:

```
D:/Youtube/D. Mysteries Channel/3. Assets/
├── locations/
│   ├── urban/
│   ├── rural/
│   ├── interiors/
│   └── aerial/
├── nature/
│   ├── weather/
│   ├── water/
│   ├── forests/
│   └── landscapes/
├── people/
│   ├── crowds/
│   ├── silhouettes/
│   └── hands_details/
├── objects/
│   ├── documents/
│   ├── artifacts/
│   └── symbols/
├── textures/
│   ├── film_grain/
│   ├── light/
│   ├── particles/
│   └── surfaces/
├── cartoons/           # PD animation clips (Fleischer, etc.)
├── transitions/
│   ├── establishing/
│   ├── time_passage/
│   └── movement/
├── backgrounds/        # loops, abstract motion
├── effects/            # VHS overlay, ink reveal, etc.
└── gifs/
```

The compiler decides which subject category a global clip belongs to based on the segment's `description`, `category`, and `tags` from video_analysis.json.

**Global clip naming:** `{descriptive_name}.mp4` — 5 words max, no shot numbers (these are project-independent). Example: `foggy_hospital_corridor.mp4`, `cobweb_hotel_spider_scene.mp4`.

---

## Skill Structure

```
.claude/skills/edit-sheet-compiler/
├── SKILL.md
└── scripts/
    └── organize_assets.py    # copies/renames files per instruction JSON
```

---

## Dependencies

- `visuals/shotlist.json` (from shot-planner) — required
- `visuals/media_leads.json` (from media-scout) — required
- `visuals/download_manifest.json` (from asset-downloader) — optional
- `visuals/video_analysis.json` (from asset-analyzer) — optional
- `data/asset_catalog.db` — for recording global asset entries

---

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 3 (global candidates) | List of segments proposed for global library with target categories | Approve/reject global candidates, adjust categories |
| Step 5 (edit sheet) | Preview of the edit sheet | Any corrections before finalizing |

---

## Out of Scope

- Searching the global catalog for unfulfilled shots (that's shot-planner's job)
- ComfyUI vector generation
- Audio/music assets
