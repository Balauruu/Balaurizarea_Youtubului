# Visual Style Guide

*This document governs how the Visual Orchestrator (Agent 1.4) and downstream asset agents make visual decisions. It defines the channel's visual language, equilibrium rules, and hard constraints. Post-production treatment (color grading, effects, overlays, fills, CRT/VHS treatments, inversion, glow) is handled manually in DaVinci Resolve and is NOT part of this guide or the pipeline.*

---

## Channel Visual Identity

**Tone:** Dark, unsettling. The channel covers true crime, cults, corruption, and horror-adjacent subjects. The visual language should feel heavy, uneasy, and deliberate — never clean, corporate, or reassuring.

**Pacing:** Medium pace. Shots typically hold 4-8 seconds. Mix of static holds and cuts. The rhythm is not frenetic — it gives the viewer time to absorb an image before moving on, but never lingers so long that momentum dies.

**Screen-time distribution target (approximate):**
- Primary footage (archival photos, video clips, documents): ~30%
- Vector generations (silhouette compositions): ~30%
- B-roll (old cartoons, atmospheric footage, conceptual clips): ~30%
- Text cards, transitions, and other editor-created elements: ~10%

This is a target, not a hard rule. Topics with abundant primary footage will skew toward it. Topics with little documentation will lean heavier on vectors and b-roll. The orchestrator should aim for this balance but adapt to what exists.

---

## Visual Asset Types

### Primary Footage
Photographs, archival video, document scans, screenshots, press clippings — anything that directly documents the subject.

**When to use:** Whenever the narration references specific people, places, events, or evidence. Primary footage grounds the viewer in reality. It says "this happened, here is proof."

**Orchestrator guidance:**
- Preferred for `grounding` and `emotional` visual registers
- Every chapter should include at least one primary asset to anchor the narrative in reality
- If primary footage exists for a moment, prefer it over all other types

### Vector Generations
Flat silhouette compositions generated via ComfyUI. These depict scenes, actions, and interactions described in the narration. The pipeline generates the composition only — subject, pose, framing, spatial arrangement. All post-production treatment (inversion, glow, color fills, effects) is handled by the editor.

#### Vector Generation Role

Vectors are the channel's primary tool for depicting scenes that have no photographic record. They fill the gap between "real documentation" and "abstract mood" — they show specific actions, relationships, and emotional states as composed silhouettes.

**Generate → Edit workflow:** Each vector starts as a base generation from a composition brief. The editor may request up to **2 edits** per base generation (pose adjustment, spatial rearrangement, element addition/removal). If the composition isn't working after 2 edits, generate a new base instead of continuing to iterate. This keeps the pipeline moving and prevents diminishing-returns editing loops.

**Composition-only briefs:** Generation briefs describe ONLY the composition — subjects, poses, spatial relationships, and scene framing. Never include color, lighting, effects, texture, or post-production treatment in a generation brief. The brief answers: "Who is in the frame, what are they doing, and where are they relative to each other?"

**When to use:** Vectors are the most versatile visual tool. They serve three roles:
1. **Scene depiction** — When the narration describes a specific action or interaction and no primary footage exists (a figure addressing a group, a person fleeing, two people meeting)
2. **Emotional abstraction** — When the narration reaches emotional moments (grief, fear, isolation, confrontation) and a composed silhouette conveys feeling better than found footage
3. **Gap filling** — When neither primary footage nor appropriate b-roll exists for a shot

**Orchestrator guidance:**
- Preferred for `emotional` and `conceptual` visual registers
- Suitable as fallback for any register when primary footage is unavailable
- Mini-narratives: vectors often come in 1-3 beat sequences depicting a change in state (sitting → standing, alone → surrounded, calm → agitated). The orchestrator should think in terms of these beats when a shot describes a transformation or progression.
- Compositions should be described in terms of subject, pose, and spatial arrangement. Do NOT specify color, effects, lighting treatment, or background — only the figures and their relationships.

**Composition principles for generation briefs:**
- High contrast, minimal detail — silhouettes should read instantly at a glance
- No facial features — figures are archetypes, not individuals
- Clear spatial relationships — who is dominant, who is subordinate, who is isolated
- Simple environments — a hut frame, a doorway, a horizon line. Enough context to ground the scene, no more.

### Old Cartoons
Public domain animated shorts (Fleischer-era, early Disney PD, industrial/educational animations). Used as b-roll.

**When to use:** Cartoons serve a strictly **metaphorical** role — they are never literal depictions of the subject. The cartoon depicts the *concept* the narration is discussing, not the actual people, places, or events. When the narrator discusses labor exploitation, a cartoon character working a machine conveys the idea. When authority is the topic, a cartoon character looming over others carries the metaphor. The value of cartoons is in this conceptual abstraction: they externalize ideas through familiar visual shorthand while the juxtaposition of innocent/playful aesthetics against dark subject matter creates deliberate tonal tension.

**Orchestrator guidance:**
- Preferred for `conceptual` and `atmospheric` visual registers
- The cartoon should match the **concept**, not the **period or location** of the subject
- Never use cartoons for `grounding` register — they abstract rather than anchor
- The juxtaposition of innocent/playful cartoon aesthetics against dark subject matter is intentional and central to the visual language. Do not avoid cartoons because the topic is serious — that contrast is the point.

### Atmospheric B-Roll
Non-specific footage that sets mood without depicting the subject directly. Empty corridors, institutional interiors, landscapes, mechanical processes, environmental textures.

**When to use:** When the narration needs visual breathing room — establishing mood, bridging sections, or providing texture between more specific shots.

**Orchestrator guidance:**
- Preferred for `atmospheric` and `transitional` visual registers
- B-roll is atmospheric, never literal. "Institutional corridor footage" works for any story about institutions — it doesn't need to be the specific institution from the subject.
- Avoid bright, modern, or clean-looking footage. B-roll should feel aged, heavy, or desaturated even before any post-production treatment.

### Documents & Screenshots
Web page captures, newspaper clippings, report pages, Wikipedia sections — evidence and context presented as visual assets.

**When to use:** When the narration references specific evidence, dates, rulings, publications, or written records.

**Orchestrator guidance:**
- Preferred for `grounding` and `transitional` visual registers
- Documents provide credibility and pacing variety — a shift from motion to static
- Best used in short holds (3-5 seconds) rather than extended displays

---

## Building Blocks

The canonical vocabulary of compositional forms. Every shot in the shotlist must use a `building_block` value from this table exactly (case-sensitive). The `building_block_variant` field captures specificity within each block.

| Block Name | Description | Example Variants |
|------------|-------------|------------------|
| Quote Card | Verbatim testimony or statement displayed as a formatted text card | Impact Phrase, Witness Testimony, Official Statement |
| Date Card | Date and location establishing context | Location/Era Anchor, Year Only, Full Date |
| Archival Photograph | Real photograph from the relevant era — portraits, crime scenes, mugshots, institutional exteriors | Portrait, Crime Scene, Mugshot, Interior, Group |
| Missing Person Card | Profile card for a named missing person | Profile Card, Age-Progressed, Wanted Poster |
| Archival Footage | Real archival video footage | News Broadcast, Home Video, Institutional, Street-Level |
| Landscape Establishing Shot | Wide geographic or environmental shot | Aerial, Street-Level, Rural, Urban |
| Source Screenshot | Screenshot of a real document, newspaper, webpage, or text artifact | Newspaper Clipping, Official Document, Social Media Post, Encyclopedia Entry |
| Diagram | Animated diagram showing relationships, timelines, comparisons, or hierarchies | Relationship, Timeline, Comparison, Process, Hierarchy |
| Symbol | Symbolic visual — silhouettes, icons, emblems representing concepts or people | Silhouette Figure, Icon, Emblem, Abstract Concept |

**Note:** Map generation is intentionally excluded from the pipeline (D029). Maps are handled manually in DaVinci Resolve.

---

## B-Roll Theme Rules

The orchestrator identifies 2-5 broad conceptual themes per project. These are abstract mood pools that multiple shots draw from.

**Theme construction rules:**
- Themes describe a **feeling and concept**, never a historical period or specific location
- `search_direction` provides broad visual keywords without year constraints. "Institutional interiors, dormitories, long corridors, regimented environments" — NOT "1940s Quebec orphanage footage"
- `cartoon_angle` describes what kind of cartoon activity or dynamic maps to the concept. "Characters trapped, confined spaces, authority figures looming" — NOT "a specific cartoon title"
- The LLM reasoning in downstream agents decides which specific assets fit — the theme provides direction, not constraints
- Themes should be reusable: a theme like "Institutional confinement" could apply to cults, prisons, orphanages, or authoritarian regimes across different projects

---

## Equilibrium Rules

These rules prevent visual monotony and maintain the channel's distinctive mixed-media feel.

1. **No more than 3 consecutive shots of the same source type.** Three primary photos in a row starts to feel like a slideshow. Three vectors in a row starts to feel like an animation. The mix is what makes the visual language distinctive.

2. **Every chapter must include at least one primary asset.** Even in chapters where vectors and b-roll dominate, one piece of real documentation anchors the narration in reality.

3. **Vectors and cartoons should not appear back-to-back without a primary or document shot between them.** Both are "constructed" visuals — stacking them loses the grounding effect. Insert a real photo or document to break the sequence.

4. **B-roll themes should be distributed across the video, not clustered.** If a project has 3 themes, each should appear in multiple chapters rather than being confined to one section.

5. **The opening shot should be primary footage or a document when possible.** The first visual should ground the viewer in reality before abstraction begins. If no primary footage exists for the opening, use atmospheric b-roll — not vectors.

---

## Hard Constraints (Never Do This)

- **Never use bright, colorful, or corporate-feeling stock footage.** Anything that looks like it belongs in a business presentation or explainer video breaks the aesthetic entirely.
- **Never use AI-generated realistic human faces or photorealistic scenes.** The channel's generated content is deliberately stylized (flat silhouettes, vectors). Attempting photorealism with AI crosses into uncanny territory and undermines credibility.
- **Never use cartoons for grounding register.** If the narration is presenting facts, evidence, or establishing reality, cartoons are the wrong visual type. Save them for conceptual and atmospheric moments.
- **Never specify post-production treatment in the shotlist.** The orchestrator describes what the viewer should see in terms of content and composition. Color, effects, grain, glow, inversion, and all other treatment decisions belong to the editor.

---

## Notes for the Orchestrator Agent

When generating `shotlist.json`, think like a documentary director doing a read-through of the script:

1. **Read the script chapter by chapter.** Identify what each passage is doing — establishing facts? building emotion? introducing a character? transitioning between topics?

2. **Assign visual registers based on narrative function**, not subject matter. The same event (e.g., a government policy) might be `grounding` when first introduced (show the document) and `emotional` when its consequences are described (show a vector of affected people).

3. **Check available media_leads before assigning preferred sources.** If research found 15 archival photos of a location, lean on them. If a key figure has no photos, plan vectors for scenes involving them.

4. **Think in sequences, not isolated shots.** A passage about escalating abuse might be: primary photo (grounding) → cartoon of authority figure (conceptual) → vector of isolated figure (emotional) → document scan of a report (grounding). That four-shot sequence tells a visual story through the register shifts.

5. **Aim for the ~30/30/30 distribution** but don't force it. Adapt to the available material and the story's needs.
