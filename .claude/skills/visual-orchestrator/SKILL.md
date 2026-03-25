---
name: visual-orchestrator
description: Generate structured shot lists from finished documentary scripts. Use this skill when the user wants to create a shot list, generate a shotlist, plan visuals for a video, or says things like "create shot list", "shotlist for [topic]", "visual plan for [topic]", "parse script into shots". This is a heuristic skill — Claude does all reasoning, no Python. Requires a completed Script.md in the project directory.
---

# Visual Orchestrator

Script → structured shot list (`shotlist.json`) for the asset pipeline.

## Workflow

1. **Resolve project** — Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches → list all and ask. No match → error. Found → read `projects/N. [Title]/script/Script.md`. Missing Script.md → tell user to run the writer skill first.

2. **Load references** — Read `channel/visuals/VISUAL_STYLE_GUIDE.md` (building block vocabulary, visual registers, equilibrium rules, asset type guidance). Also read `projects/N. [Title]/visuals/media_leads.json` if it exists (known primary assets for source field decisions).

3. **Generate** — Parse the script chapter by chapter, create shot objects per the schema below, and write `projects/N. [Title]/visuals/shotlist.json`. Overwrite without prompting.

## Output

`shotlist.json` — A JSON object with two keys:

```json
{
  "broll_themes": [...],
  "shots": [...]
}
```

Full overwrite on re-run. Any change to Script.md invalidates the existing shotlist and requires full regeneration.

---

## B-Roll Themes

Define 2–5 broad conceptual themes for the project. Each theme is a mood pool that multiple shots reference. Construction rules live in `VISUAL_STYLE_GUIDE.md` — key principles:

- Themes describe a **feeling and concept**, never a historical period or specific location
- `search_direction` → broad visual keywords, no year constraints
- `cartoon_angle` → what cartoon activity/dynamic maps to the concept
- Themes should be reusable across subjects with similar dynamics

```json
{
  "id": "T1",
  "concept": "Institutional confinement",
  "mood": "oppressive, cold, bureaucratic",
  "search_direction": "Institutional interiors, dormitories, long corridors, regimented environments",
  "cartoon_angle": "Characters trapped, confined spaces, authority figures looming"
}
```

## Shot Schema

Each shot has exactly 12 fields:

| Field | Type | Rules |
|-------|------|-------|
| `id` | string | Sequential `S001`–`S999`. Never reset per chapter. |
| `chapter` | int | `0` = prologue (content before `## 1.`), else N from `## N. Title` |
| `chapter_title` | string | Exact heading text. Prologue = `"Prologue"`. |
| `narrative_context` | string | 1–2 sentence paraphrase. **Never copy narration verbatim.** |
| `visual_need` | string | Era + geography + subject. Specific enough for an archive search query. No cinematographer or production language. |
| `building_block` | string | Must match a Block Name from the Building Blocks table in `VISUAL_STYLE_GUIDE.md` exactly (case-sensitive). |
| `building_block_variant` | string | Meaningful descriptor for this shot. Never null. |
| `visual_register` | enum | One of: `grounding`, `conceptual`, `atmospheric`, `emotional`, `transitional` |
| `broll_theme` | string\|null | Theme ID (e.g. `"T1"`) or `null`. Typically non-null when preferred_sources includes `broll` or `cartoon_broll`. |
| `preferred_sources` | array | Ordered. First = most preferred. Valid: `archival`, `document`, `broll`, `cartoon_broll`, `vector`, `motion_graphics`. Keep short (1–3). |
| `fallback_sources` | array | Alternatives if preferred yields nothing. Same valid values. No overlap with preferred. |
| `text_content` | string\|null | **Required** for Quote Card and Date Card. `null` for everything else. No exceptions. |
| `suggested_sources` | array | Archive names, URLs, databases. May be empty `[]`, never null. |

### Visual Register Definitions

- **grounding** — Establishes facts, evidence, reality. Anchors in documented truth.
- **conceptual** — Illustrates ideas, systems, mechanisms, abstract relationships.
- **atmospheric** — Sets mood, visual breathing room, section bridges.
- **emotional** — Conveys feeling, human impact, psychological weight.
- **transitional** — Bridges between chapters or major narrative shifts.

## Source Assignment

Before assigning sources, check `visuals/media_leads.json` for what primary assets exist. This prevents the pipeline from searching for assets that don't exist.

**Decision logic:**
- Subject has photos/video in media_leads → prefer `archival`
- No primary assets for subject → prefer `vector` or `broll`
- Documents found (reports, clippings, filings) → prefer `document`
- No media_leads file → rely on register-to-source affinities below

**Register-to-source affinities** (guidelines, not rules):

| Register | Typical preferred | Why |
|----------|-------------------|-----|
| grounding | archival, document | Facts need evidence |
| conceptual | vector, cartoon_broll, broll | Ideas need abstraction |
| atmospheric | broll, cartoon_broll | Mood needs texture |
| emotional | vector, archival | Feeling needs composed imagery or real faces |
| transitional | broll, document | Bridges need neutral pacing |

## Granularity Rules

**Primary trigger: narrative beat changes.** New shot when the visual subject changes — different era, location, figure, or evidence type. Never split at paragraph/sentence boundaries for their own sake.

- **Safety net:** No single shot should span more than ~450 words of narration.
- **Density:** Hard minimum 2 shots/chapter. Typical range 8–15. Short chapters may fall below 8.
- **Establishing shot:** Each chapter MUST begin with an orienting shot (Date Card, Landscape, Archival Footage, or Quote Card for prologue) — never a detail shot.
- **No consecutive repetition:** Max 2 consecutive shots with the same `building_block`.

## Anti-Patterns

### `visual_need` — WRONG vs RIGHT

**Cinematographer language:**
- ✗ `"Slow dolly push into a close-up of the suspect's face, shallow depth of field"`
- ✓ `"Historical photograph of suspect James Halcott, United States, 1972"`

**Missing era/geography:**
- ✗ `"Photo of a detective at a crime scene"`
- ✓ `"Archival photograph of a detective at an outdoor crime scene, rural England, 1983"`

**Abstract content routed to archival:**
- ✗ `building_block: "Archival Footage"` + `"Footage of the psychological effects of isolation"` — no such footage exists
- ✓ `building_block: "Diagram"` + `"Animated diagram showing psychological cascade from isolation to cognitive decline"`

### `narrative_context` — paraphrase, never transcribe

- ✗ Copying a sentence verbatim from the script
- ✓ Condensing the beat into 1–2 original sentences

## Worked Example

**Narration (synthetic):**

> In the summer of 1971, nurse Carol Marden disappeared from the Ashfield Rest Home in rural Shropshire. She was twenty-six. No resignation letter. The facility's director, Dr. Voss, produced a signed form — later found to be backdated by three months.

**Output:**

```json
{
  "broll_themes": [
    {
      "id": "T1",
      "concept": "Institutional concealment",
      "mood": "sterile, evasive, bureaucratic",
      "search_direction": "Empty hospital corridors, institutional filing cabinets, closed doors",
      "cartoon_angle": "Characters hiding things, authority figures behind desks"
    }
  ],
  "shots": [
    {
      "id": "S001", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Summer 1971: nurse Carol Marden vanishes from a Shropshire care facility.",
      "visual_need": "Date and location card: Summer 1971, Shropshire, England",
      "building_block": "Date Card", "building_block_variant": "Location/Era Anchor",
      "visual_register": "grounding", "broll_theme": null,
      "preferred_sources": ["archival"], "fallback_sources": ["broll"],
      "text_content": "SUMMER 1971 — SHROPSHIRE, ENGLAND", "suggested_sources": []
    },
    {
      "id": "S002", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Carol Marden, 26, disappears without notice — institutional silence follows.",
      "visual_need": "Missing person photograph of Carol Marden, female, age 26, England, 1971",
      "building_block": "Missing Person Card", "building_block_variant": "Profile Card",
      "visual_register": "emotional", "broll_theme": "T1",
      "preferred_sources": ["archival"], "fallback_sources": ["vector"],
      "text_content": null, "suggested_sources": ["national_archives_uk"]
    },
    {
      "id": "S003", "chapter": 1, "chapter_title": "The Missing Nurse",
      "narrative_context": "Dr. Voss presents a resignation form later found backdated by three months.",
      "visual_need": "Diagram showing document forgery: form date vs. disappearance date",
      "building_block": "Diagram", "building_block_variant": "Timeline Discrepancy",
      "visual_register": "conceptual", "broll_theme": "T1",
      "preferred_sources": ["vector"], "fallback_sources": ["cartoon_broll"],
      "text_content": null, "suggested_sources": []
    }
  ]
}
```

## Deferred

- **SHOT-08:** Two-pass generation — annotate narrative beats first, then assign shot types
- **SHOT-10:** Shot density calibration proportional to chapter word count
- Chapter-level regeneration without full re-run
