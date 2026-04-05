---
name: shot-planner
description: "Generate structured shot lists from finished documentary scripts. Use this skill when the user wants to create a shot list, plan visuals, or says things like 'create shot list', 'shotlist for [topic]', 'visual plan for [topic]', 'parse script into shots', 'shot plan'. This is a heuristic skill — Claude does all reasoning. Requires a completed Script.md in the project directory."
---

# Shot Planner

Script → structured shot list (`shotlist.json`) + editor reference (`shotlist_edit_sheet.md`).

## Workflow

### Step 1 — Resolve Project

Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches → list all and ask. No match → error. Found → read `projects/N. [Title]/script/Script.md`. Missing Script.md → tell user to run the writer skill first.

### Step 2 — Load References

Read `channel/visuals/VISUAL_STYLE_GUIDE.md` (form vocabulary, visual registers, equilibrium rules, asset guidance).

Read `projects/N. [Title]/visuals/media_leads.json` if it exists. This tells you what primary assets are already available — photos, footage, documents. Without it, you're guessing what exists; with it, you can assign `known_assets` and avoid sending asset-analyzer on searches for things already downloaded.

### Step 3 — Asset Inventory

Before generating any shots, build a mental inventory:

1. **Catalog available assets** — scan `media_leads.json` and note what exists: which people have photos, which institutions have exterior/interior shots, which documents are captured, which YouTube videos are staged.
2. **Identify coverage gaps** — which key subjects, locations, or events have NO primary assets? These will need vectors, b-roll, or cartoons.
3. **Note the distribution target** — approximately 30% primary, 30% vector, 30% b-roll (atmospheric + cartoon), 10% text cards. The actual split depends on what assets exist, but start with this as a guide.

### Step 4 — Generate Shots

Parse the script chapter by chapter. For each narrative beat, create a shot object per the schema below. Think in sequences — a passage about escalating abuse might be: archival photo (grounding) → cartoon clip (conceptual) → vector silhouette (emotional) → document scan (grounding). That four-shot sequence tells a visual story through register shifts.

**Granularity rules:**

- **Primary trigger:** narrative beat changes. New shot when the visual subject changes — different era, location, figure, or evidence type. Never split at paragraph/sentence boundaries for their own sake.
- **Safety net:** No single shot should span more than ~450 words of narration.
- **Density:** Hard minimum 2 shots/chapter. Typical range 8–15. Short chapters may fall below 8.
- **Establishing shot:** Each chapter MUST begin with an orienting shot (text card, landscape, archival footage, or archival photo) — never a detail shot.
- **No consecutive repetition:** Max 2 consecutive shots with the same `form`.

### Step 5 — Validate

After generating all shots, run these checks and fix violations:

**Equilibrium rules:**
1. No more than 3 consecutive shots with the same action type (`find`, `find`, `find` → break the streak)
2. Every chapter must include at least one `find` shot (primary asset anchors the narration in reality)
3. `generate` and `curate` shots with `broll_cartoon` should not appear back-to-back without a `find` shot between them (both are "constructed" visuals — stacking them loses grounding)
4. The opening shot should be a `find` or `curate` shot when possible (ground the viewer in reality before abstraction). If no primary footage exists for the opening, use atmospheric b-roll — not vectors.

**Distribution check:**
- `curate` shots (broll_atmospheric + broll_cartoon) should be at least 15% of total shots
- `broll_cartoon` specifically should appear in at least 10% of shots — cartoons are central to the channel's visual language, not a last resort
- If below these thresholds, revise `conceptual` and `atmospheric` register shots to prefer cartoon/broll forms

**`known_assets` logic:**
- For `create` shots: field is absent (text cards ARE the asset — nothing to find)
- For `find` shots with a matching asset in media_leads: populate `known_assets` with the local path
- For shots where `known_assets` is non-empty: asset-analyzer will skip these (already covered)

### Step 6 — B-Roll Matching

For each `curate` shot, find specific archive.org footage that serves that shot's narrative beat. This is the critical step where the script's content drives the b-roll selection — not abstract themes, but the actual moment the shot needs to illustrate.

**For each `curate` shot:**

1. Read the shot's `narrative_context` and `search_query`
2. Reason about what specific archival footage or cartoon would serve this moment — think metaphorically for cartoons, atmospherically for b-roll
3. Search archive.org using one of:
   - **WebSearch** scoped to archive.org: `"archive.org prelinger [concrete visual subject derived from narrative]"`
   - **IA script**: `python .claude/skills/shot-planner/scripts/ia_search.py "<query>" --limit 5` (add `--collection prelinger` for historical footage)
4. Attach 1-2 leads directly to the shot as `broll_leads`

**Rules:**
- **archive.org only** — no stock footage sites. The channel aesthetic demands aged, archival material.
- **`broll_cartoon` shots must have a specific cartoon episode** — point to a particular film by name (e.g., "The Cobweb Hotel (1936) — flies trapped by a spider-innkeeper" not "Fleischer Color Classics collection"). The cartoon must metaphorically serve the narrative beat.
- **`broll_atmospheric` shots get 1-2 documentary/footage leads** from archive.org that match the mood and era.
- `match_reasoning` must explain the conceptual link between the footage and the specific narrative beat, not just restate the title.

**B-roll lead filtering criteria — apply before adding any `broll_leads` entry:**

1. **Visual concreteness over thematic abstraction.** When recommending cartoons or animations as conceptual b-roll, the source must contain concrete scenes that a viewer would associate with the narrative concept *without explanation*. The visual metaphor must be immediately legible. A cartoon about a spider trapping flies works for "institutional entrapment" because the visual itself depicts entrapment. A cartoon about vegetables being processed through a machine does NOT work for "children trapped in a bureaucratic system" — the connection requires a caption to make sense. If you have to explain the metaphor, the b-roll fails.

2. **Scene availability assessment.** Before recommending an archive.org source, assess whether it likely contains at least 5-10 seconds of footage directly matching the shot intent. A 7-minute cartoon with ONE potentially relevant moment is a poor recommendation — the asset-analyzer will spend time embedding and searching the entire video for minimal return. Prefer sources where the relevant visual concept is central to the content (e.g., the entire premise involves the concept), not incidental to it.

3. **Tone compatibility.** Comedy and slapstick cartoons should be deprioritized for documentary b-roll about serious topics (institutional abuse, child suffering, death) unless the specific scenes clearly transcend the comedic context. A dunce cap scene from *Education for Death* works because the scene itself is somber despite being animated. A slapstick chase scene from a cartoon about vegetables does not — the comedic framing undermines the gravity of the narrative. The test: would a viewer feel the tonal shift as jarring or as intentional juxtaposition?

### Step 7 — Write Outputs

Write two files (full overwrite on re-run):

1. **`projects/N. [Title]/visuals/shotlist.json`** — the structured data (schema below)
2. **`projects/N. [Title]/visuals/shotlist_edit_sheet.md`** — human-readable companion for the editor (format below)

---

## Output Schema — shotlist.json

```json
{
  "shots": [...]
}
```

### Shot Schema

Every shot has these **common fields**:

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Sequential `S001`–`S999`. Never reset per chapter. |
| `chapter` | int | `0` = prologue (content before `## 1.`), else N from `## N. Title` |
| `chapter_title` | string | Exact heading text. Prologue = `"Prologue"`. |
| `narrative_context` | string | 1–2 sentence paraphrase. **Never copy narration verbatim.** |
| `visual_register` | enum | One of: `grounding`, `conceptual`, `atmospheric`, `emotional`, `transitional` |
| `action` | enum | One of: `create`, `find`, `generate`, `curate` |
| `form` | enum | See Form Values table below. |
| `variant` | string | Free-form descriptor for this specific shot. Always present. |

**Action-specific fields** (only present when relevant):

| Field | Present when | Type | Rules |
|-------|-------------|------|-------|
| `text_content` | action = `create` | string | The text the editor puts on screen. |
| `search_query` | action = `find` or `curate` | string | Era + geography + subject for `find`. Mood/concept keywords for `curate`. No cinematographer language. |
| `composition_brief` | action = `generate` | string | Subjects, poses, spatial arrangement. No color, lighting, or effects. |
| `known_assets` | action = `find` (optional) | array | Pre-matched local paths from media_leads. Empty `[]` if none. Absent for `create`. |
| `broll_leads` | action = `curate` (optional) | array | Archive.org URLs matched to this shot. Added in Step 6. |
| `fallback` | any action except `create` (optional) | object | `{"action": "...", "form": "..."}` — mini-shot that fires if primary fails. Max 1 level deep. |

### `broll_leads` Schema

```json
{
  "broll_leads": [
    {
      "url": "https://archive.org/details/...",
      "title": "The Cobweb Hotel (1936) — Fleischer Color Classic",
      "source": "internet_archive",
      "description": "Flies check into a hotel run by a spider. The protector is the predator.",
      "match_reasoning": "The institution as trap — the orphanage meant to protect became the hospital that confined."
    }
  ]
}
```

### Form Values

| `form` | Valid actions | What it is |
|--------|-------------|------------|
| `text_card` | create | Any text overlay — quotes, dates, names, locations, character intros, statistics |
| `diagram` | create | Animated diagrams, timelines, comparisons (motion design in Resolve) |
| `archival_photo` | find | Photos, portraits, mugshots, institutional interiors/exteriors, missing person cards |
| `archival_video` | find | Real footage — news broadcasts, home video, institutional footage |
| `document` | find | Screenshots, newspaper clippings, official documents, encyclopedia entries |
| `landscape` | find, curate | Wide establishing shots — could be archival or atmospheric b-roll |
| `vector_silhouette` | generate | ComfyUI compositions — figures, scenes, symbolic imagery |
| `broll_atmospheric` | curate | Non-specific mood footage (empty corridors, industrial textures, environmental) |
| `broll_cartoon` | curate | Public domain cartoons used metaphorically (Fleischer-era, early PD animation) |
| `broll_environment` | curate | Wide establishing/scenic footage — nature, cityscapes, rural landscapes, water |

### Visual Register Definitions

- **grounding** — Establishes facts, evidence, reality. Anchors in documented truth.
- **conceptual** — Illustrates ideas, systems, mechanisms, abstract relationships.
- **atmospheric** — Sets mood, visual breathing room, section bridges.
- **emotional** — Conveys feeling, human impact, psychological weight.
- **transitional** — Bridges between chapters or major narrative shifts.

### Action-to-Register Affinities

These are guidelines, not rules. Override when the specific shot demands it.

| Register | Typical action/form | Why |
|----------|-------------------|-----|
| grounding | find (archival_photo, document) | Facts need evidence |
| conceptual | curate (broll_cartoon), generate (vector_silhouette) | Ideas need abstraction |
| atmospheric | curate (broll_atmospheric, broll_cartoon) | Mood needs texture |
| emotional | generate (vector_silhouette), find (archival_photo) | Feeling needs composed imagery or real faces |
| transitional | curate (broll_atmospheric), find (document) | Bridges need neutral pacing |

---

## Anti-Patterns

### `search_query` — WRONG vs RIGHT

**Cinematographer language:**
- Bad: `"Slow dolly push into a close-up of the suspect's face, shallow depth of field"`
- Good: `"Historical photograph of suspect James Halcott, United States, 1972"`

**Missing era/geography:**
- Bad: `"Photo of a detective at a crime scene"`
- Good: `"Archival photograph of a detective at an outdoor crime scene, rural England, 1983"`

**Abstract content routed to `find`:**
- Bad: `action: "find"` + `"Footage of the psychological effects of isolation"` — no such footage exists
- Good: `action: "create", form: "diagram"` + `"Animated diagram showing psychological cascade from isolation to cognitive decline"`

### `narrative_context` — paraphrase, never transcribe

- Bad: Copying a sentence verbatim from the script
- Good: Condensing the beat into 1–2 original sentences

### Cartoons — don't avoid them because the topic is serious

Cartoons serve a strictly **metaphorical** role. The juxtaposition of innocent/playful aesthetics against dark subject matter is intentional and central to the visual language. A cartoon character working a machine can represent labor exploitation. An authority figure looming over small characters can represent institutional power. The contrast is the point.

- Bad: Using `vector_silhouette` for every conceptual shot because the topic is heavy
- Good: Using `broll_cartoon` when the shot needs to illustrate a *concept* (power, confinement, deception) rather than depict a specific person or event

---

## Worked Example

**Narration (synthetic):**

> In the summer of 1971, nurse Carol Marden disappeared from the Ashfield Rest Home in rural Shropshire. She was twenty-six. No resignation letter. The facility's director, Dr. Voss, produced a signed form — later found to be backdated by three months.

**Output:**

```json
{
  "shots": [
    {
      "id": "S001", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Summer 1971: nurse Carol Marden vanishes from a Shropshire care facility.",
      "visual_register": "grounding",
      "action": "create", "form": "text_card", "variant": "date_location",
      "text_content": "SUMMER 1971 — SHROPSHIRE, ENGLAND"
    },
    {
      "id": "S002", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Carol Marden, 26, disappears without notice — institutional silence follows.",
      "visual_register": "emotional",
      "action": "find", "form": "archival_photo", "variant": "missing_person_profile",
      "search_query": "Missing person photograph of Carol Marden, female, age 26, England, 1971",
      "known_assets": [],
      "fallback": {"action": "generate", "form": "vector_silhouette"}
    },
    {
      "id": "S003", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Dr. Voss presents a resignation form later found backdated by three months.",
      "visual_register": "conceptual",
      "action": "create", "form": "diagram", "variant": "timeline_discrepancy",
      "text_content": "Diagram: form date vs. disappearance date — 3-month backdating"
    },
    {
      "id": "S004", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "The facility director conceals information behind administrative procedure.",
      "visual_register": "conceptual",
      "action": "curate", "form": "broll_cartoon", "variant": "authority_concealment",
      "search_query": "Authority figure hiding documents behind a desk, concealing evidence",
      "broll_leads": [
        {
          "url": "https://archive.org/details/the_cobweb_hotel",
          "title": "The Cobweb Hotel (1936) — Fleischer Color Classic",
          "source": "internet_archive",
          "description": "A spider runs a hotel for flies — the host who promises shelter is the predator. Scenes of the spider preparing traps behind a welcoming facade.",
          "match_reasoning": "The facility director presenting a legitimate document while concealing a disappearance — the Cobweb Hotel's spider-innkeeper is the authority figure whose hospitality is the trap."
        }
      ],
      "fallback": {"action": "curate", "form": "broll_atmospheric"}
    }
  ]
}
```

---

## Output — Edit Sheet Format

`shotlist_edit_sheet.md` is a human-readable companion for editing in DaVinci Resolve. Format:

```markdown
# Shot List — [Project Title]

---

## Chapter 1: The Missing Nurse

### S001 | text_card | grounding
> **SUMMER 1971 — SHROPSHIRE, ENGLAND**
_Date/location anchor._

### S002 | archival_photo | emotional
Missing person photograph of Carol Marden, female, age 26, England, 1971
Known: _(none)_ | Fallback: vector_silhouette

### S003 | diagram | conceptual
> **Diagram: form date vs. disappearance date — 3-month backdating**
_Timeline discrepancy visualization._

### S004 | broll_cartoon | conceptual
Authority figure hiding documents behind a desk, concealing evidence
Lead: [The Cobweb Hotel (1936)](https://archive.org/details/the_cobweb_hotel) — spider-innkeeper as concealing authority
Fallback: broll_atmospheric
```

**Key formatting rules:**
- Text content (text_card, diagram) rendered as blockquotes — visually prominent for the editor
- `find`/`curate`/`generate` shots show the search_query or composition_brief as plain text
- `known_assets` listed when non-empty; "_(none)_" when empty
- `broll_leads` shown as linked titles with brief reasoning
- Fallback shown on its own line
- Chapter headers with shot count

---
