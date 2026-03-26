---
name: edit-sheet-compiler
description: "Pipeline terminal step — compiles all upstream outputs into a formatted edit sheet and organizes assets in the project directory. Use when the user says 'compile edit sheet', 'organize assets', 'prepare for editing', 'create edit sheet for [topic]', or after asset-analyzer completes and the user wants to start editing in DaVinci Resolve."
---

# Edit Sheet Compiler

Reads all upstream pipeline outputs, matches assets to shotlist entries, copies and renames everything into a flat numbered project folder, and produces a formatted edit sheet for DaVinci Resolve.

**Classification:** [HEURISTIC] — Claude matches assets to shots and composes the edit sheet. One script handles file operations.

## Inputs

| Source | File | Required |
|--------|------|----------|
| shot-planner | `visuals/shotlist.json` | Yes |
| media-scout | `visuals/media_leads.json` | Yes |
| asset-downloader | `visuals/download_manifest.json` | No |
| asset-analyzer | `visuals/video_analysis.json` | No |

## Outputs

- `projects/N. [Title]/assets/` — flat directory, all assets renamed `S{NNN}_{name}.ext`
- `projects/N. [Title]/edit_sheet.md` — formatted Markdown edit sheet

---

## Workflow

### Step 1: Resolve project and load data

Resolve project directory (case-insensitive substring match). Read all four input files from `visuals/`. If optional files are missing, proceed with what's available.

### Step 2: Match assets to shots

Walk every shot in `shotlist.json` in order. For each shot, find matching assets:

- **`create` shots** — no asset file. Record `text_content` for the edit sheet.
- **`generate` shots** — no asset file. Record `composition_brief` for the edit sheet.
- **`find` shots** — check `known_assets` array (image/doc paths from media-scout). Check `video_analysis.json` segments whose `relevance` cites this shot's ID.
- **`curate` shots** — check `video_analysis.json` segments linked via `shot_refs` in the download manifest.

Collect all matches per shot. Record unmatched `find`/`curate` shots.

### Step 3: Identify global-worthy unmatched segments

Segments from `video_analysis.json` not tied to any shot are global candidates — but only if strict criteria are met:

**Include as global if ALL true:**
- `scope` is `"global"`
- Content is generic — no named people, specific locations, or topic-specific events
- Clearly reusable across unrelated projects
- Falls into a recognizable subject category (locations, nature, people, objects, textures, cartoons, transitions)

Present global candidates to the user with proposed target categories. User approves/rejects and adjusts categories.

### Step 4: Build instruction JSON and run organize_assets.py

Build the instruction JSON mapping each asset to its project filename:

**Naming convention:**
- Shot-matched: `S{NNN}_{descriptive_name}.ext` — 5 words max
- Multiple matches for one shot: `S{NNN}a_`, `S{NNN}b_`, etc.
- Global unmatched: `G{NNN}_{descriptive_name}.ext`

```bash
python .claude/skills/edit-sheet-compiler/scripts/organize_assets.py \
  --instructions .claude/scratch/asset_instructions.json
```

Global assets are copied to both the project dir and `D:/Youtube/D. Mysteries Channel/3. Assets/{subject}/{subcategory}/`.

For global clips, also insert into `data/asset_catalog.db`:
```python
from data.catalog import get_connection, insert_clip
conn = get_connection()
insert_clip(conn, path=global_path, source_type=source_type,
            scope="global", description=description,
            mood=mood, era=era, tags=tags, category=category,
            duration_sec=duration_sec)
```

### Step 5: Produce the edit sheet

Write `projects/N. [Title]/edit_sheet.md`. This is the editor's single companion document.

**Structure:**

```markdown
# Edit Sheet — [Project Title]

> Generated [date]. [total] shots, [matched] with assets, [unfulfilled] unfulfilled, [global] global assets saved.

---

## Chapter N: [Title]

---

### S001 | text_card | grounding
> **TEXT CONTENT HERE**

_Formatting notes from variant field._

---

### S002 | archival_photo | emotional

**Narrative context from shotlist.**

| # | Asset | File |
|---|-------|------|
| 1 | Description of asset | `S002_filename.jpg` |

---

### S003 | vector_silhouette | emotional

**Composition:** composition_brief text here.

_Generate with ComfyUI — not yet implemented._

---

### S004 | archival_video | grounding

**Narrative context.**

⚠ **Unfulfilled** — no matching asset found.
Search: _"original search_query from shotlist"_

---
```

**Formatting rules:**
- `---` between every shot
- `create` shots: `text_content` in blockquote, variant as italic note
- `generate` shots: `composition_brief` in bold, ComfyUI warning
- Shots with assets: `narrative_context` in bold, asset table showing all matches equally
- Unfulfilled shots: warning, original `search_query` in italic
- Chapter headers matching script structure
- Asset table: `#`, `Asset` (brief description), `File` (filename only — all in same `assets/` dir)

Present the edit sheet preview to the user. Apply any corrections.

---

## Global Asset Directory

```
D:/Youtube/D. Mysteries Channel/3. Assets/
├── locations/      (urban, rural, interiors, aerial)
├── nature/         (weather, water, forests, landscapes)
├── people/         (crowds, silhouettes, hands_details)
├── objects/        (documents, artifacts, symbols)
├── textures/       (film_grain, light, particles, surfaces)
├── cartoons/
├── transitions/    (establishing, time_passage, movement)
├── backgrounds/
├── effects/
└── gifs/
```

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 3 | Global candidates with proposed categories | Approve/reject, adjust categories |
| Step 5 | Edit sheet preview | Corrections before finalizing |

## Dependencies

- `data/catalog.py` — SQLite CRUD for global asset catalog entries
- `organize_assets.py` — file copy/rename script
