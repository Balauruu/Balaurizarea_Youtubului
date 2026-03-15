# Feature Research

**Domain:** Script-to-shot-list generation for narrator-led archival documentary
**Researched:** 2026-03-15
**Confidence:** HIGH (domain principles from documentary practice and Architecture.md spec) / MEDIUM (shot count estimates from reasoning over script analysis)

---

## Context: What This Skill Does

The Visual Orchestrator (Agent 1.4) reads a finished `Script.md` — pure narration, 4-7 chapters, 3,000-7,000 words — and outputs `shotlist.json`. It is a pure [HEURISTIC] skill: Claude reads the script and makes editorial judgments about what visuals are needed. No Python code. No visual style input (that comes from visual-style-extractor, a separate skill invoked separately).

The downstream consumer is Agent 2.1 (Media Acquisition), which reads `shotlist.json` as its only input. The quality of `shotlist.json` determines the quality of everything in Phase 2. If `visual_need` is vague or `suggested_types` is wrong, Agent 2.1 acquires the wrong assets.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features this skill must have. Missing any of these makes the output structurally unusable by Agent 2.1.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Chapter mapping (`chapter` field) | Agent 2.1 uses chapter grouping to understand narrative context; acquisition without chapter structure loses the story's logic | LOW | Direct read from `## N. Title` headings in Script.md; chapters become the organizing principle |
| Unique shot IDs in S001 format | Agent 2.1, 2.2, 2.3, 2.4 all reference shots by ID; gaps, mappings, and manifest.json use IDs throughout Phase 2 | LOW | Sequential integers zero-padded to 3 digits; Architecture.md defines this format |
| `visual_need` in plain searchable language | Agent 2.1 builds search queries from this field; vague or abstract needs produce irrelevant search results from archive.org and wikimedia | HIGH | Free text but must be concrete: era, location, subject. "Remote Quebec orphanage, 1950s institutional building" not "an institutional setting" |
| `suggested_types` from the 6 defined categories | Agent 2.1 routes acquisition to source domains based on type; wrong type = wrong source domain = zero useful assets | LOW | Must use Architecture.md's 6 types exactly: archival_video, archival_photo, broll, documents, vectors, animations |
| `narrative_context` per shot | Agent 2.1 needs to know what the narrator says during this shot to judge whether an acquired asset matches the moment | LOW | Short paraphrase of the narration during the shot — not a quote, not a scene description. What is being said, not what is shown |
| Shot count proportional to content | A 7-chapter, 7,000-word script needs coverage across all chapters; uniform shot density across chapters with wildly different lengths is wrong | MEDIUM | Calibrate by chapter length: short chapters (~400 words) warrant 5-8 shots; long chapters (700+ words) warrant 12-18 shots |
| Every chapter covered | Leaving a chapter without shots means Agent 2.1 has no acquisition instructions for that portion of the video — a hard gap in Phase 2 | LOW | Must iterate through every `## N.` heading and produce at minimum 5 shots per chapter |

### Differentiators (Competitive Advantage)

Features that make the shot list genuinely useful for asset acquisition, not just structurally correct.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Narrative-beat granularity (not paragraph-level) | Shot boundaries drawn where the visual subject actually changes, not at paragraph breaks. A paragraph about a legal mechanism and a paragraph quoting a survivor need different visuals even if they share a paragraph boundary in the script. | HIGH | The core editorial judgment. Breaks happen when: era shifts, location shifts, key figure introduced, evidence type shifts (systemic → personal), emotional register shifts. Claude must read for these, not count paragraphs. |
| Era and location specificity in `visual_need` | "Remote Quebec orphanage, 1950s" is a workable archive.org search query. "An institutional setting" returns nothing useful. | MEDIUM | Extract the most specific geographic and temporal markers the narration provides before writing `visual_need`. The script already contains this information. |
| Shot type selection logic | Documents for bureaucratic evidence and paperwork. archival_photo for named key figures. broll for atmosphere, geography, everyday life of an era. vectors for figures/silhouettes when no archival image exists. animations for events that have no visual record at all. | MEDIUM | Different narrative situations require different acquisition strategies. Routing the wrong type wastes Agent 2.1's time and produces gaps that could have been filled. |
| Visual variety across a chapter | A chapter of 12 shots should not use archival_photo for all 12. Professional documentary editing alternates types to maintain visual rhythm: establishing wide, detail, document, figure, atmospheric broll. | MEDIUM | After generating shots for a chapter, review the type distribution. If monotonous, revise to introduce variety. This mirrors how documentary editors build visual rhythm. |
| Establishing shot at chapter start | Documentary chapters open with a visual that orients the viewer to the new setting, era, or subject. Diving immediately into detail shots without orientation is disorienting. | LOW | The first shot of each chapter should be geographic, temporal, or contextual — something that answers "where/when are we now?" before the narration drills into specifics. |
| Handling abstract narration correctly | Some narration has no literal visual: "The diagnosis made the impairment real in every subsequent transaction." Literal illustration fails here. A document shot, a conceptual vector, or an archival photograph of a relevant bureaucratic process can carry the weight of the abstraction. | HIGH | This is where shot planning requires genuine editorial judgment. The Duplessis Orphans script has many such moments. The wrong response is to try to illustrate the abstraction literally. The right response is to ask: what visual texture or object represents this system? |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Shot duration / timing | "8 seconds for this shot" seems useful for editor planning | Duration is determined in the edit from available assets and pacing decisions — not predictable before assets exist. Assets may be 3 seconds or 45 seconds; the editor decides. Architecture.md explicitly excludes duration. | Leave duration out entirely. Editor owns timing in DaVinci Resolve. |
| Camera angle / framing instructions | Professional shot lists for live shoots include these | This is an acquisition pipeline, not a live shoot. Assets are found, not captured. Camera angles are whatever the archival material contains. Prescribing "wide shot" produces requirements that cannot be filled. | Describe what the visual should show ("aerial view of rural Quebec settlement"), not how it was framed. |
| Effects or transition types | "Ken Burns pan left" seems like useful production context | Post-production instructions belong to the editor in DaVinci Resolve, not the acquisition pipeline. Architecture.md explicitly excludes effects, transitions, and production instructions. | Let the editor apply effects at cut time from acquired assets. |
| Priority ranking between shots | "Shot S003 is more important than S002" seems useful for acquisition triage | Creates false hierarchy. Agent 2.1 acquires by topic context, not shot priority. Priority at this stage adds complexity with no acquisition benefit. | All shots are equal in `shotlist.json`. Unmatched shots go to gaps and are handled by Agent 2.2/2.3/2.4. |
| One shot per paragraph, mechanically | Paragraphs are natural units; seems systematic | Script.md paragraphs vary wildly in scope. Some contain a single visual idea. Others contain two or three topic shifts. Mechanical paragraph-to-shot mapping over-covers narrow paragraphs and under-covers dense ones. | Draw shot boundaries at narrative beat shifts: era, location, figure, evidence type, emotional register. Not at paragraph breaks. |
| One shot per sentence | Finer granularity seems safer | 3,000-7,000 words at ~15 words per sentence = 200-466 shots. Agent 2.1 cannot acquire 400+ distinct assets in one pass. Diminishing returns on granularity below the narrative-beat level. | Narrative beat is the right unit. Multiple sentences within the same visual context = one shot. |
| Exact image composition description | "Man walking from left to right in foreground" | We find assets, not shoot them. Composition of archival material is fixed. Composition descriptions waste `visual_need` space on properties that cannot be specified in acquisition. | Describe subject and context: "man leaving Quebec courthouse, 1950s." Not composition. |
| Dialogue attribution per shot | Script seems to have dialogue | Script.md is pure narration. There is no dialogue — survivor quotes in the script are narrated by the documentary voice, not delivered on camera. Attributing quotes to on-screen speakers confuses the acquisition agent. | Use `narrative_context` to indicate the subject of the narration, not to claim a person is on screen. |

---

## Shot Granularity: The Core Decision

**Recommendation: Narrative beat, not structural unit (paragraph or sentence).**

Professional documentary editors describe a "beat" as the smallest unit of meaning that requires a visual change. In practice for an archival narration documentary:

**Draw a new shot when any of the following shift:**
- Time period changes ("In 1944..." vs. "By 1961...")
- Geographic location changes (Quebec City vs. Montreal asylum)
- A new named key figure is introduced (needs their own archival visual)
- Evidence type shifts (systemic bureaucratic argument → personal survivor account)
- Emotional register shifts (analytical exposition → testimony of harm)
- A pivotal event or turning point is described that warrants its own visual emphasis

**Do NOT draw a new shot for:**
- Each new paragraph within the same visual context
- Each new sentence
- Transitions between related ideas in the same setting

**Shot count estimate for this channel's scripts:**
- 7-chapter, 7,000-word script: approximately 70-90 shots total
- 4-chapter, 3,000-word script: approximately 40-55 shots total
- Per-chapter range: 5-18 shots, calibrated to chapter word count
- Maps to a 20-50 minute documentary at 1-3 shots per minute of narration, consistent with archival documentary pacing

This is a calibrated estimate based on analyzing the Duplessis Orphans Script V1.md (7 chapters, ~4,000 words) against professional documentary practice. Actual count will vary by how densely the narration shifts subjects.

---

## Feature Dependencies

```
Script.md chapter headings (## N. Title)
    └──required by──> Chapter mapping (groups all shots)
                          └──required by──> Shot ID assignment (S001 sequential)

Narrative beat identification
    └──enables──> visual_need specificity (what to search for)
    └──enables──> suggested_types selection (how to acquire it)
    └──enables──> visual variety enforcement (what types have been used)
    └──enables──> establishing shot placement (what orients each chapter)

Era/location extraction from narration
    └──feeds into──> visual_need field quality
                          └──determines──> Agent 2.1 search query quality

Abstract narration recognition
    └──triggers──> vectors or animations type (rather than archival)
                       └──prevents──> unfillable gaps in Agent 2.1 pass
```

### Dependency Notes

- **Chapter mapping is the skeleton:** All other features attach to it. Shots without chapter assignment are useless to Agent 2.1.
- **Narrative beat granularity enables everything else:** You cannot enforce visual variety until you have the right number of distinct shots. You cannot establish chapters until you know where beats fall within chapters.
- **Era/location specificity is the highest-leverage quality investment:** Agent 2.1 translates `visual_need` directly to search queries. Specificity here has a multiplier effect across all of Phase 2.
- **Abstract narration routing prevents phantom gaps:** If abstract narration is given archival_photo type, Agent 2.1 will search for a photo that doesn't exist, creating a gap that Agent 2.2 will then try to generate — wasting two agents. Routing it to vectors/animations upfront is correct.

---

## MVP Definition

### Launch With (v1)

Minimum viable output that Agent 2.1 can operate from.

- [ ] Parse all chapter headings from Script.md and organize shots by chapter — chapter structure is the organizing principle for the entire Phase 2 pipeline
- [ ] Generate one shot per distinct narrative beat (not per paragraph) — draw boundaries at era/location/person/evidence-type shifts
- [ ] Write `visual_need` in plain language with era and location specificity — this is what Agent 2.1 searches for in archive.org and wikimedia
- [ ] Assign `suggested_types` from the 6 defined Architecture.md categories based on what narrative situation each shot represents
- [ ] Write `narrative_context` as a brief paraphrase of what the narrator says during the shot — enough for Agent 2.1 to judge whether an acquired asset matches
- [ ] Cover every chapter — no chapter in the script left without shots

### Add After Validation (v1.x)

Add once a first shot list has been generated and reviewed against the script.

- [ ] Visual variety enforcement — after generating shots for each chapter, review type distribution and revise any chapter that uses a single type for all shots
- [ ] Establishing shot verification — confirm that the first shot of each chapter is geographic, temporal, or contextual rather than a detail shot

### Future Consideration (v2+)

Defer until core is validated against real asset acquisition.

- [ ] Abstract narration guidance section in the generation prompt — a dedicated prompt section that explicitly addresses how to handle conceptual/systemic narration with no literal visual analog
- [ ] Two-pass generation: read full script and annotate narrative beats, then generate shots from the annotation — separates analysis from generation for better beat identification

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Chapter mapping | HIGH | LOW | P1 |
| Unique shot IDs (S001 format) | HIGH | LOW | P1 |
| `narrative_context` per shot | HIGH | LOW | P1 |
| `visual_need` with era/location specificity | HIGH | MEDIUM | P1 |
| `suggested_types` from 6 defined categories | HIGH | LOW | P1 |
| Narrative beat granularity (not paragraph) | HIGH | HIGH | P1 |
| Shot type selection logic per narrative situation | HIGH | MEDIUM | P1 |
| Every chapter covered | HIGH | LOW | P1 |
| Visual variety enforcement within chapters | MEDIUM | MEDIUM | P2 |
| Establishing/orienting shot at chapter starts | MEDIUM | LOW | P2 |
| Abstract narration routing to vectors/animations | MEDIUM | HIGH | P2 |
| Shot count calibrated to chapter length | MEDIUM | LOW | P2 |

**Priority key:**
- P1: Must have for Agent 2.1 to function at all
- P2: Improves acquisition quality significantly; add in first review pass after generation
- P3: Nice to have, future consideration

---

## Script.md Format Dependencies

The Visual Orchestrator's output quality is directly constrained by what Script.md contains. Identified dependencies and signals:

| Script.md Property | How It Feeds Shot List |
|--------------------|------------------------|
| Chapter headings (`## N. Title`) | Primary structure signal — shots group by chapter |
| Era markers in narration ("In 1944...", "By 1961...") | Time-period specificity for `visual_need` |
| Geographic markers ("Quebec", "St. Jean de Dieu asylum in Montreal") | Location specificity for `visual_need` |
| Named key figures ("Maurice Duplessis", "Paul St. Aubain") | Signal to assign archival_photo type; figure needs own visual |
| Survivor quote / testimony paragraph | Signal to shift suggested_types toward archival_photo or broll (personal visual, not systemic document) |
| Abstract systemic claim ("The diagnosis made the impairment real...") | Signal to use vectors or animations — no literal visual exists |
| Statistical or financial evidence ("$70 million in subsidies") | Signal to use documents type — a scanned document or record screenshot |
| Government report or official record referenced | Signal to use documents type |
| Paragraph length variation | Does NOT determine shot count — beat shifts do |

The Script.md format (pure narration, no stage directions, no visual cues) is intentionally clean per Architecture.md and the Writer skill contract. The Visual Orchestrator must extract all visual signals from narrative content alone. This is the correct design. The skill should not require a modified Script.md format.

---

## Sources

- [How To Create A Shot List For Your Documentary — Desktop Documentaries](https://www.desktop-documentaries.com/create-a-shot-list.html)
- [Bringing History to Life: The Art of Using Archival Footage in Documentaries](https://danielclarksonfisher.com/bringing-history-to-life-the-art-of-using-archival-footage-in-documentaries/)
- [Pacing and Rhythm — Narrative Documentary Production, Fiveable](https://fiveable.me/narrative-documentary-production/unit-6/pacing-rhythm/study-guide/wA0rkICSeb7KoDNi)
- [Narrative Structure in Documentary Editing — Fiveable](https://fiveable.me/documentary-production/unit-12/narrative-structure-documentary-editing/study-guide/ImaHZdcuYc8nDo5i)
- [How to Create a Documentary Shot List — StudioBinder](https://www.studiobinder.com/blog/documentary-shot-list-template/)
- `Architecture.md` — shotlist.json schema definition, 6 asset types, Phase 2 pipeline design, Agent 2.1 input contract
- `projects/1. The Duplessis Orphans.../Script V1.md` — analyzed as primary example: chapter structure, narrative beat density, abstract vs. concrete narration patterns

---

*Feature research for: Visual Orchestrator (Agent 1.4) — script-to-shot-list generation*
*Researched: 2026-03-15*
