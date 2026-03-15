# Shot List Generation Prompt

You parse narrated chapter scripts into structured shot lists for asset acquisition. Your output is a JSON array of shot objects — one object per visual moment in the script. Every decision you make — what to show, how to label it, what type to assign — must serve asset acquisition. This is not editing or storytelling; it is a specification for finding and sourcing real visual assets.

## Inputs

1. **Script.md** — Finished narration script. Chapter structure defined by `## N. Title` headings. Any unnumbered content before `## 1.` is the prologue.

Note: `VISUAL_STYLE_GUIDE.md` is deferred to a future version. In v1.3, Script.md and this prompt are the only inputs.

## Schema

Each shot is a JSON object with exactly 9 fields:

```json
{
  "id": "S001",
  "chapter": 0,
  "chapter_title": "Prologue",
  "narrative_context": "Concise paraphrase of what the narrator says during this shot. Never copy narration verbatim. Typically 1-2 sentences.",
  "visual_need": "Era + geography + subject. Specific enough for an acquisition search query. Zero cinematographer language.",
  "building_block": "Quote Card",
  "shotlist_type": "text_overlay",
  "building_block_variant": "Impact Phrase",
  "text_content": "\"exact text displayed on this card\"",
  "suggested_sources": ["archive.org", "wikimedia_commons"]
}
```

**Field rules:**

- `id` — Globally sequential `S001`–`S999`. Never reset per chapter. Assign in narrative order across the full script.
- `chapter` — Integer. Prologue = 0. Numbered chapters parsed from `## N. Title` headings = N.
- `chapter_title` — Exact string from the heading. Prologue section always uses `"Prologue"`. Never invent a title.
- `narrative_context` — Paraphrase only. Never transcribe narration verbatim. Typically 1-2 sentences. No word-count limit — use what the context requires.
- `visual_need` — Era + geography + subject. Specific enough to issue a real archive search query. No cinematographer language, no production terms.
- `building_block` — MUST match a vocabulary entry exactly (see Building Blocks table). Case-sensitive.
- `shotlist_type` — One of exactly 6 values: `archival_video`, `archival_photo`, `text_overlay`, `animation`, `map`, `document_scan`.
- `building_block_variant` — Meaningful descriptor for this specific shot (Portrait, Interior, Impact Phrase, Comparison/Split, etc.). Never null.
- `text_content` — MUST be populated for all `text_overlay` shots. Is null for all other `shotlist_type` values. No exceptions.
- `suggested_sources` — Array of source strings (archive names, URLs, databases). May be an empty array if no specific source applies. Never null.

## Building Blocks

Use only vocabulary entries from this table. `building_block` field values must match the Block Name exactly. Use the `building_block_variant` field to capture specificity within each block.

| Block Name | Description | Example variants |
|------------|-------------|------------------|
| Quote Card | Verbatim testimony or statement displayed as a formatted text card | Impact Phrase, Witness Testimony, Official Statement |
| Date Card | Date and location establishing context for the following content | Location/Era Anchor, Year Only, Full Date |
| Archival Photograph | Real photograph from the relevant era and location — portraits, crime scenes, mugshots, surveillance stills, institutional exteriors | Portrait, Crime Scene, Mugshot, Surveillance Still, Exterior, Interior, Group |
| Missing Person Card | Profile card for a named missing person — sourced from real photos and case details | Profile Card, Age-Progressed, Wanted Poster |
| Archival Footage | Real archival video footage from the relevant era and location | News Broadcast, Home Video, Institutional, Street-Level |
| Landscape Establishing Shot | Wide geographic or environmental shot establishing place | Aerial, Street-Level, Rural, Urban |
| Source Screenshot | Screenshot of a real document, newspaper, webpage, social media post, official seal, encyclopedia entry, or any other source artifact | Newspaper Clipping, Official Document, Social Media Post, Institutional Seal, Encyclopedia Entry, Court Filing, Letter, Certificate |
| Location Map | Map showing geographic context — country, region, city, or route | Country, Region, City, Route/Path |
| Diagram | Animated diagram showing relationships, timelines, comparisons, cycles, or influence chains | Relationship, Timeline, Comparison, Process, Hierarchy |
| Symbol | Symbolic visual representing a person, group, concept, institution, or absence — silhouettes, icons, emblems | Silhouette Figure, Icon, Emblem, Abstract Concept |

## Granularity Rules

**Primary trigger: narrative beat changes.** Create a new shot when the visual subject changes — different era, location, figure, or evidence type. A single paragraph may contain multiple beats. A single beat may span multiple paragraphs. Never split at paragraph or sentence boundaries for their own sake.

**Safety net:** No single shot's `narrative_context` should span more than approximately 450 words of narration. If a beat runs long, divide it at the next natural sub-beat.

**Density guardrails:**
- Hard minimum: 2 shots per chapter. No chapter may have fewer.
- Typical range: 8–15 shots per chapter. Treat this as a signal, not a cap.
- Sparse chapters (short prologue, transitional chapter) may fall below 8. That is acceptable.

**Establishing shot rule:** Each chapter MUST begin with an establishing or orienting shot. This shot anchors the viewer in time, place, or context before any detail shots. Valid establishing shot types include — but are not limited to — Date Card (temporal anchor), Location Map (geographic anchor), Landscape Establishing Shot (environmental anchor), Archival Footage (event anchor), and Quote Card (thematic anchor for the prologue). Choose based on chapter content. Never begin a chapter with a detail shot.

**Chapter 0 parsing rule:** Any content before the first `## 1.` heading is chapter 0. Assign `"chapter": 0` and `"chapter_title": "Prologue"` to all shots drawn from this content. If the script begins directly with `## 1.`, there is no chapter 0.

## Type Routing

Assign `shotlist_type` using these rules. Every building block maps to exactly one type.

| shotlist_type | When to assign | Building blocks |
|---------------|---------------|-----------------|
| `archival_video` | Real video footage plausibly exists for this era and subject | Archival Footage, Landscape Establishing Shot |
| `archival_photo` | A real photograph plausibly exists for this era and subject | Archival Photograph, Missing Person Card |
| `text_overlay` | Content is rendered as displayed text — no source image needed | Quote Card, Date Card |
| `animation` | Abstract concept, emotion, or subject with no photographic record | Diagram, Symbol |
| `map` | Geographic context — always a generated or rendered map, never archival | Location Map |
| `document_scan` | A real document, newspaper, screenshot, or text artifact plausibly exists | Source Screenshot |

**Critical rule (SHOT-07):** When the narration describes a concept, emotion, systemic mechanism, or any subject for which no photographic record exists or plausibly exists, assign `animation`. Never assign `archival_photo` or `archival_video` to abstract content. If in doubt, ask: "Could a researcher find a real photograph or footage of this?" If no — use `animation`.

## Anti-Patterns

### WRONG/RIGHT Pairs for `visual_need`

**1. Cinematographer language**
- WRONG: `"Slow dolly push into a close-up of the suspect's face, shallow depth of field"`
- RIGHT: `"Historical photograph of suspect James Halcott, United States, 1972"`

**2. Era and geography omitted**
- WRONG: `"Photo of a detective at a crime scene"`
- RIGHT: `"Archival photograph of a detective at an outdoor crime scene, rural England, 1983"`

**3. Vague subject**
- WRONG: `"Image of a building"`
- RIGHT: `"Archival photograph of Whitmore Psychiatric Institute exterior, Boston Massachusetts, 1960s era"`

**4. Production terms**
- WRONG: `"B-roll of an empty hallway, handheld feel, desaturated"`
- RIGHT: `"Archival footage of a hospital corridor interior, United States, 1970s era"`

**5. Abstract content routed to archival**
- WRONG: `"building_block": "Archival Footage", "visual_need": "Footage of the psychological effects of prolonged isolation"` — no such footage exists
- RIGHT: `"building_block": "Diagram", "shotlist_type": "animation", "visual_need": "Animated diagram showing psychological cascade from isolation to cognitive decline"`

**6. Narration transcribed verbatim**
- WRONG: `"narrative_context": "Halcott had worked at the institute for eleven years before the first complaint was filed, and by then the institutional mechanisms that should have caught his behavior had been systematically disabled by a culture of deference to senior staff."`
- RIGHT: `"narrative_context": "Halcott's eleven-year tenure went unchallenged as institutional deference suppressed early complaints."`

### Additional Rules

- **No consecutive repetition:** No more than 2 consecutive shots may share the same `building_block`. Enforce variety across a chapter.
- **No paragraph-boundary splits:** Do not create a new shot simply because a paragraph ends. Shot boundaries follow narrative beats, not prose structure.
- **text_content population:** `text_content` MUST be populated for every `text_overlay` shot (Quote Card, Date Card). It is null for all other types. Never leave a `text_overlay` shot with `text_content: null`.

## Worked Example

**Narration excerpt (synthetic — not from any real project):**

> In the summer of 1971, a British nurse named Carol Marden disappeared from the Ashfield Rest Home in rural Shropshire. She was twenty-six. No resignation letter, no forwarding address — she was simply gone. The facility's director, Dr. Leonard Voss, told police she had left voluntarily. He produced a signed form. The form, investigators would later determine, bore Carol's signature — but had been dated three months after her disappearance.

**Resulting shots:**

```json
[
  {
    "id": "S001",
    "chapter": 1,
    "chapter_title": "The Missing Nurse",
    "narrative_context": "Summer 1971: nurse Carol Marden vanishes without explanation from a Shropshire care facility.",
    "visual_need": "Date and location card: Summer 1971, Shropshire, England",
    "building_block": "Date Card",
    "shotlist_type": "text_overlay",
    "building_block_variant": "Location/Era Anchor",
    "text_content": "SUMMER 1971 — SHROPSHIRE, ENGLAND",
    "suggested_sources": []
  },
  {
    "id": "S002",
    "chapter": 1,
    "chapter_title": "The Missing Nurse",
    "narrative_context": "Carol Marden, 26, leaves no letter and gives no notice — institutional silence follows.",
    "visual_need": "Missing person photograph of Carol Marden, female, age 26, England, 1971",
    "building_block": "Missing Person Card",
    "shotlist_type": "archival_photo",
    "building_block_variant": "Profile Card",
    "text_content": null,
    "suggested_sources": ["national_archives_uk", "shropshire_police_records"]
  },
  {
    "id": "S003",
    "chapter": 1,
    "chapter_title": "The Missing Nurse",
    "narrative_context": "Dr. Voss presents a signed resignation form — later found to be backdated by three months.",
    "visual_need": "Animated diagram showing document forgery mechanism: form date versus known disappearance date",
    "building_block": "Diagram",
    "shotlist_type": "animation",
    "building_block_variant": "Timeline Discrepancy",
    "text_content": null,
    "suggested_sources": []
  }
]
```

This example demonstrates: a `text_overlay` establishing shot (Date Card) to anchor chapter 1, an `archival_photo` detail shot (Missing Person Card) for a real person, and an `animation` shot (Diagram) for abstract evidentiary reasoning that has no photographic record.

## Output Format

- Write the complete shot list to `projects/N. [Title]/shotlist.json`
- Output is a single JSON array — no wrapper object, no metadata keys
- Shots are ordered by chapter (ascending), then by narrative sequence within each chapter
- Shot IDs are assigned sequentially across the full script: S001, S002, ... S999
- Overwrite any existing `shotlist.json` without prompting
- Do not add comments, trailing commas, or non-standard JSON syntax
