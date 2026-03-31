# Visual Style Guide

*This document governs how the Shot Planner and downstream asset agents make visual decisions. It defines the channel's visual language, equilibrium rules, and hard constraints. Post-production treatment (color grading, effects, overlays, fills, CRT/VHS treatments, inversion, glow) is handled manually in DaVinci Resolve and is NOT part of this guide or the pipeline.*

---

## Channel Visual Identity

**Tone:** Dark, unsettling. The channel covers true crime, cults, corruption, and horror-adjacent subjects. The visual language should feel heavy, uneasy, and deliberate — never clean, corporate, or reassuring.

**Pacing:** Medium pace. Shots typically hold 4-8 seconds. Mix of static holds and cuts. The rhythm is not frenetic — it gives the viewer time to absorb an image before moving on, but never lingers so long that momentum dies.

**Screen-time distribution target (approximate):**
- Primary footage (archival photos, video clips, documents): ~30%
- Vector generations (silhouette compositions): ~30%
- B-roll (old cartoons, atmospheric footage, conceptual clips): ~30%
- Text cards, diagrams, and other editor-created elements: ~10%

This is a target, not a hard rule. Topics with abundant primary footage will skew toward it. Topics with little documentation will lean heavier on vectors and b-roll. The shot planner should aim for this balance but adapt to what exists.

---

## Visual Asset Types

### Primary Footage
Photographs, archival video, document scans, screenshots, press clippings — anything that directly documents the subject.

**When to use:** Whenever the narration references specific people, places, events, or evidence. Primary footage grounds the viewer in reality. It says "this happened, here is proof."

**Shot planner guidance:**
- Use `action: "find"` with forms `archival_photo`, `archival_video`, or `document`
- Preferred for `grounding` and `emotional` visual registers
- Every chapter should include at least one primary asset to anchor the narrative in reality
- If primary footage exists for a moment (check `media_leads.json`), prefer it over all other types and populate `known_assets`

### Vector Generations
Flat silhouette compositions generated via ComfyUI. These depict scenes, actions, and interactions described in the narration. The pipeline generates the composition only — subject, pose, framing, spatial arrangement. All post-production treatment (inversion, glow, color fills, effects) is handled by the editor.

**ComfyUI generation flow:** Each vector starts as a base generation from a composition brief, then gets refined through up to **2 edit-model passes** (pose adjustment, spatial rearrangement, element addition/removal). If the composition isn't working after 2 edit passes, regenerate a new base instead of continuing to iterate.

**Composition-only briefs:** The `composition_brief` field describes ONLY the composition — subjects, poses, spatial relationships, and scene framing. Never include color, lighting, effects, texture, or post-production treatment. The brief answers: "Who is in the frame, what are they doing, and where are they relative to each other?"

**When to use:** Vectors serve three roles:
1. **Scene depiction** — When the narration describes a specific action or interaction and no primary footage exists
2. **Emotional abstraction** — When the narration reaches emotional moments and a composed silhouette conveys feeling better than found footage
3. **Gap filling** — When neither primary footage nor appropriate b-roll exists

**Shot planner guidance:**
- Use `action: "generate"` with form `vector_silhouette`
- Preferred for `emotional` and `conceptual` visual registers
- Suitable as fallback for any register when primary footage is unavailable
- Mini-narratives: vectors often come in 1-3 beat sequences depicting a change in state (sitting → standing, alone → surrounded, calm → agitated). Think in beats when a shot describes a transformation.

**Composition principles:**
- High contrast, minimal detail — silhouettes should read instantly at a glance
- No facial features — figures are archetypes, not individuals
- Clear spatial relationships — who is dominant, who is subordinate, who is isolated
- Simple environments — a hut frame, a doorway, a horizon line. Enough context to ground the scene, no more.

### Old Cartoons
Public domain animated shorts (Fleischer-era, early Disney PD, industrial/educational animations). Used as b-roll.

**When to use:** Cartoons serve a strictly **metaphorical** role — they are never literal depictions of the subject. The cartoon depicts the *concept* the narration is discussing, not the actual people, places, or events. The value of cartoons is in this conceptual abstraction: they externalize ideas through familiar visual shorthand while the juxtaposition of innocent/playful aesthetics against dark subject matter creates deliberate tonal tension.

**Shot planner guidance:**
- Use `action: "curate"` with form `broll_cartoon`
- Preferred for `conceptual` and `atmospheric` visual registers
- The cartoon should match the **concept**, not the **period or location** of the subject
- Never use cartoons for `grounding` register — they abstract rather than anchor
- The juxtaposition of innocent/playful cartoon aesthetics against dark subject matter is intentional and central to the visual language. Do not avoid cartoons because the topic is serious — that contrast is the point.
- **Allocation target:** At least 10% of total shots should use `broll_cartoon`. This is a floor, not a ceiling.

### Atmospheric B-Roll
Non-specific footage that sets mood without depicting the subject directly. Empty corridors, institutional interiors, landscapes, mechanical processes, environmental textures.

**When to use:** When the narration needs visual breathing room — establishing mood, bridging sections, or providing texture between more specific shots.

**Shot planner guidance:**
- Use `action: "curate"` with form `broll_atmospheric`
- Preferred for `atmospheric` and `transitional` visual registers
- B-roll is atmospheric, never literal. "Institutional corridor footage" works for any story about institutions — it doesn't need to be the specific institution from the subject.
- Avoid bright, modern, or clean-looking footage. B-roll should feel aged, heavy, or desaturated even before any post-production treatment.

### Environment B-Roll
Wide establishing and scenic footage that orients the viewer geographically. Nature, cityscapes, rural landscapes, bodies of water.

**When to use:** When the narration moves to a new location or needs a geographic anchor — establishing shots, transitions between settings, or scene-setting before specific content.

**Shot planner guidance:**
- Use `action: "curate"` with form `broll_environment`
- Preferred for `atmospheric` and `transitional` visual registers
- Distinct from `broll_atmospheric`: environment shots establish location, atmospheric shots establish mood
- Source the same way as atmospheric — archive.org footage with aged, documentary quality

### Documents & Screenshots
Web page captures, newspaper clippings, report pages, Wikipedia sections — evidence and context presented as visual assets.

**When to use:** When the narration references specific evidence, dates, rulings, publications, or written records.

**Shot planner guidance:**
- Use `action: "find"` with form `document`
- Preferred for `grounding` and `transitional` visual registers
- Documents provide credibility and pacing variety — a shift from motion to static
- Best used in short holds (3-5 seconds) rather than extended displays

---

## Shot Forms

The canonical vocabulary of visual forms used in `shotlist.json`. Every shot must use a `form` value from this table. The `variant` field (free-form string) captures specificity.

### Editor-Created Forms (`action: "create"`)

| Form | Description | Example Variants |
|------|-------------|------------------|
| `text_card` | Any text overlay — quotes, dates, names, locations, character intros, statistics | quote, date_location, character_intro, statistic, statement |
| `diagram` | Animated diagram showing relationships, timelines, comparisons, or hierarchies | relationship, timeline, comparison, process, hierarchy, flow |

### Found Asset Forms (`action: "find"`)

| Form | Description | Example Variants |
|------|-------------|------------------|
| `archival_photo` | Real photograph from the relevant era — portraits, scenes, mugshots, institutional interiors/exteriors | portrait, scene, mugshot, interior, group, profile |
| `archival_video` | Real archival video footage | news_broadcast, home_video, institutional, street_level |
| `document` | Screenshot of a real document, newspaper, webpage, or text artifact | newspaper_clipping, official_document, encyclopedia_entry, book_cover |
| `landscape` | Wide geographic or environmental shot (can also be `curate` if using b-roll) | aerial, street_level, rural, urban |

### Generated Forms (`action: "generate"`)

| Form | Description | Example Variants |
|------|-------------|------------------|
| `vector_silhouette` | Flat silhouette composition — figures, scenes, symbolic imagery | scene_depiction, emotional_beat, symbolic_figure, group_dynamic |

### Curated B-Roll Forms (`action: "curate"`)

| Form | Description | Example Variants |
|------|-------------|------------------|
| `broll_atmospheric` | Non-specific mood footage — empty spaces, textures, environments | institutional, industrial, urban, interior |
| `broll_cartoon` | Public domain cartoon used metaphorically | authority_figure, confinement, deception, mechanical_process |
| `broll_environment` | Wide establishing or scenic footage — geographic and environmental context | nature, urban, rural, water |

**Note:** Map generation is intentionally excluded from the pipeline. Maps are handled manually in DaVinci Resolve.

---

## B-Roll Matching Rules

B-roll is matched directly to individual shots based on each shot's narrative beat — not through abstract theme pools. The shot planner reads each `curate` shot's narrative context and finds specific archive.org footage that serves that moment.

**Source rules:**
- **archive.org only** — no stock footage sites (Pixabay, Pexels, etc.). The channel aesthetic demands aged, archival material.
- **Cartoon shots get specific episodes** — point to a particular film by name (e.g., "The Cobweb Hotel (1936)") not a collection. The cartoon must metaphorically serve the narrative beat.
- **Atmospheric shots get documentary/archival footage** — Prelinger Archives films, asylum documentaries, institutional footage from the relevant era.
- Leads are URLs only — asset-downloader handles downloads and asset-analyzer handles clip extraction downstream.

---

## Equilibrium Rules

These rules prevent visual monotony and maintain the channel's distinctive mixed-media feel.

1. **No more than 3 consecutive shots with the same action type.** Three `find` shots in a row starts to feel like a slideshow. Three `generate` shots in a row starts to feel like an animation. The mix is what makes the visual language distinctive.

2. **Every chapter must include at least one `find` shot (primary asset).** Even in chapters where vectors and b-roll dominate, one piece of real documentation anchors the narration in reality.

3. **`generate` and `curate` (cartoon) shots should not appear back-to-back without a `find` shot between them.** Both are "constructed" visuals — stacking them loses the grounding effect. Insert a real photo or document to break the sequence.

4. **B-roll shots should be distributed across the video, not clustered.** Curate shots should appear in multiple chapters rather than being confined to one section.

5. **The opening shot should use `find` or `curate` (atmospheric) when possible.** The first visual should ground the viewer in reality before abstraction begins. If no primary footage exists for the opening, use atmospheric b-roll — not vectors.

6. **Curated b-roll (atmospheric + cartoon) should total at least 15% of shots.** Cartoons specifically should be at least 10%. These forms are central to the channel aesthetic, not fallbacks.

---

## Hard Constraints (Never Do This)

- **Never use bright, colorful, or corporate-feeling stock footage.** Anything that looks like it belongs in a business presentation or explainer video breaks the aesthetic entirely.
- **Never use AI-generated realistic human faces or photorealistic scenes.** The channel's generated content is deliberately stylized (flat silhouettes, vectors). Attempting photorealism with AI crosses into uncanny territory and undermines credibility.
- **Never use cartoons for grounding register.** If the narration is presenting facts, evidence, or establishing reality, cartoons are the wrong visual type. Save them for conceptual and atmospheric moments.
- **Never specify post-production treatment in the shotlist.** The shot planner describes what the viewer should see in terms of content and composition. Color, effects, grain, glow, inversion, and all other treatment decisions belong to the editor.

---

## Notes for the Shot Planner

When generating `shotlist.json`, think like a documentary director doing a read-through of the script:

1. **Read the script chapter by chapter.** Identify what each passage is doing — establishing facts? building emotion? introducing a character? transitioning between topics?

2. **Assign visual registers based on narrative function**, not subject matter. The same event (e.g., a government policy) might be `grounding` when first introduced (show the document) and `emotional` when its consequences are described (show a vector of affected people).

3. **Check available media_leads before assigning actions.** If research found 15 archival photos of a location, lean on `find` with `known_assets`. If a key figure has no photos, use `generate` (vector) for scenes involving them.

4. **Think in sequences, not isolated shots.** A passage about escalating abuse might be: archival photo (grounding) → cartoon of authority figure (conceptual) → vector of isolated figure (emotional) → document scan of a report (grounding). That four-shot sequence tells a visual story through the register shifts.

5. **Aim for the ~30/30/30 distribution** but don't force it. Adapt to the available material and the story's needs.
