# Phase 14: Generation Prompt - Research

**Researched:** 2026-03-15
**Domain:** Prompt engineering for shotlist generation — schema specification, building block vocabulary, type routing, anti-patterns
**Confidence:** HIGH (all findings drawn from live project artifacts, no external sources needed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Building Block Vocabulary**
- Curated broader generic set — start from the 18 blocks in the Duplessis shotlist, then add 5-10 blocks covering gaps for other channel topics (true crime, unsolved cases, modern events)
- Claude curates the additional blocks based on channel scope (dark mysteries, true crime, unsolved cases, institutional scandals)
- Each block gets a description but NOT individual When/When Not routing rules — routing is at the shotlist_type level instead
- Type-level routing: rules like "use `animation` for abstract concepts with no visual record", "use `archival_photo` when a real photograph exists"
- `building_block_variant` IS populated with meaningful variants (Portrait, Interior, Impact Phrase, etc.) — not null. The Phase 13 "always null" decision applied to VISUAL_STYLE_GUIDE-derived variants specifically; generic variants are fair game

**Shot Granularity Rules**
- Primary trigger: narrative beat changes — new shot when the visual subject changes (different era, location, figure, evidence type)
- The 450-word cap is a safety net, not the primary boundary mechanism
- NOT word-count proportional or paragraph-boundary based
- Soft density guardrails — minimum 2 shots per chapter (hard), no hard max, guidance that typical chapters produce 8-15 shots
- `narrative_context` — soft guidance to keep it brief and paraphrased, not a hard 50-word cap. "Concise paraphrase of what the narrator is saying during this shot. Never copy narration verbatim."
- Establishing shots — each chapter must begin with an establishing/orienting shot, but Claude decides the type (date card, map, landscape, archival, etc.) based on content

**Anti-Patterns**
- Standalone section — dedicated "Anti-Patterns" or "Common Mistakes" section near the end of the prompt
- 4-6 WRONG/RIGHT side-by-side pairs for `visual_need` descriptions, covering: cinematographer language, vague descriptions, era/geography omission, production terms
- Additional anti-patterns explicitly called out:
  - Repeated building blocks (e.g., 5 consecutive Historical Photographs — enforce visual variety)
  - Paragraph-boundary shots (splitting at paragraph breaks instead of narrative beats)
  - Narration transcription (copying script text verbatim into narrative_context)
  - Missing text_content (forgetting to populate for text_overlay shots like Quote Cards, Keyword Stingers, Date Cards)

**Prompt Structure and Tone**
- Mirror writer's generation.md structure — self-contained, ~200 lines, consistent section ordering
- Sections: Intro → Inputs → Schema → Building Blocks → Granularity Rules → Type Routing → Anti-Patterns → Output Format
- Equally directive tone — match the writer prompt's imperative style ("Each chapter MUST begin with an establishing shot", "Never use cinematographer language")
- 1 worked example — synthetic 3-4 sentence narration excerpt mapped to 2-3 shot entries. Not from Duplessis to avoid memorization
- `suggested_sources` — open, Claude decides per shot. No predefined domain list. Claude suggests whatever sources seem relevant to the visual need

### Claude's Discretion
- Exact set of additional building blocks beyond Duplessis baseline
- Type routing rule wording and specificity
- Establishing shot type selection per chapter
- Worked example content (synthetic, not from any real project)
- Prompt section ordering within the overall structure

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SHOT-01 | Skill parses Script.md chapter structure (## N. Title) and generates shots grouped by chapter | Chapter parsing logic documented; chapter 0 prologue pattern confirmed from Duplessis (no `## N.` prefix, treated as chapter 0) |
| SHOT-02 | Shot boundaries follow narrative beats (visual subject changes: era, location, figure, evidence type) — not paragraphs or sentences | Beat-change trigger confirmed as primary rule; Duplessis shows 8-13 shots/chapter on content density, not paragraph count |
| SHOT-03 | Each shot has sequential ID (S001, S002...), chapter number, narrative_context, visual_need, and suggested_types | Full schema confirmed from Duplessis shotlist.json — 9-field schema documented below |
| SHOT-04 | `visual_need` descriptions are specific enough for acquisition search queries (era + location + subject, no production terms) | Duplessis examples confirm pattern; wrong/right pair analysis documented below |
| SHOT-05 | Visual variety enforced — mix of asset types across the shot list, not repeated suggested_types | Duplessis confirms mixed-type runs; consecutive same-block anti-pattern explicitly required in CONTEXT.md |
| SHOT-06 | Each chapter begins with an establishing/orienting shot (geographic, temporal, or contextual) | All 8 chapters in Duplessis confirm this; type varies (Date Card, Glitch Stinger, Archival Footage) |
| SHOT-07 | Abstract narration with no visual record routes to vector/animation types, not archival | Duplessis confirms: Concept Diagram, Silhouette Figure, Abstract Texture, Symbolic Icon, Static Noise/Corruption all route to `animation`; never `archival_photo` or `archival_video` |
</phase_requirements>

---

## Summary

Phase 14 produces a single file: `.claude/skills/visual-orchestrator/prompts/generation.md`. This prompt is the complete specification Claude reads before generating a shot list from a Script.md. It must be entirely self-contained — no external references, no runtime lookups. Everything the generating agent needs to produce correct output lives in this file.

The research domain is pure internal artifact analysis. The Duplessis shotlist.json (73 shots, 8 chapters, 18 building blocks, 6 types) is the ground truth for schema and vocabulary. The writer's generation.md is the structural and tonal template. No external library research is needed — this is a prompt-authoring task against a fully specified schema already proven in production.

The primary planning risk is completeness: the prompt must cover schema, vocabulary, routing logic, granularity rules, anti-patterns, and a worked example in approximately 200 lines. Each section has decisions locked in CONTEXT.md. The planner's job is to organize those decisions into a coherent, testable document spec.

**Primary recommendation:** Write generation.md as a single atomic task. The file is ~200 lines of Markdown prose — no code, no dependencies. The success gate is running the prompt against Duplessis Script V1.md and verifying the output matches the known-good shotlist.json in structure and quality.

---

## Standard Stack

### Core Artifacts (no installation required)

| Artifact | Location | Purpose |
|----------|----------|---------|
| writer/prompts/generation.md | `.claude/skills/writer/prompts/generation.md` | Structural and tonal template — mirror this pattern |
| Duplessis shotlist.json | `projects/1. The Duplessis Orphans.../shotlist.json` | Schema ground truth, 73-shot validated baseline |
| visual-orchestrator/CONTEXT.md | `.claude/skills/visual-orchestrator/CONTEXT.md` | Integration contract — generation.md is referenced here |
| Duplessis Script V1.md | `projects/1. The Duplessis Orphans.../Script V1.md` | Quality gate test input |

This phase produces one new file:
- `.claude/skills/visual-orchestrator/prompts/generation.md`

No pip installs. No Python. No SKILL.md changes. No CONTEXT.md changes.

---

## Architecture Patterns

### Recommended File Structure for generation.md

```
## [Intro — one paragraph role statement]
## Inputs
## Schema
## Building Blocks
## Granularity Rules
## Type Routing
## Anti-Patterns
## Output Format
```

This mirrors writer/prompts/generation.md: role statement up front, inputs enumerated, rules in declarative sections, output format last.

### Pattern 1: Directive Imperative Tone

**What:** Every rule is a command, not a suggestion. "MUST", "Never", "Always", "No exceptions."
**When to use:** Throughout the entire prompt. Matches the writer prompt's voice.
**Example (from writer/prompts/generation.md):**
```markdown
Every video opens with this 4-part hook. No exceptions.
```
Apply the same voice to shot rules:
```markdown
Each chapter MUST begin with an establishing or orienting shot. Never begin with a detail shot.
```

### Pattern 2: Schema as JSON Example

**What:** Define the schema by showing a single complete shot object with all 9 fields annotated.
**When to use:** In the Schema section, before the building block vocabulary.
**Critical detail:** The schema has 9 fields — not the 5 listed in SHOT-03 (REQUIREMENTS.md uses a simplified description; the actual schema is richer):

```json
{
  "id": "S001",
  "chapter": 0,
  "chapter_title": "Prologue",
  "narrative_context": "Concise paraphrase of what the narrator says. Never verbatim.",
  "visual_need": "Specific description for asset search: era + geography + subject",
  "building_block": "Quote Card",
  "shotlist_type": "text_overlay",
  "building_block_variant": "Impact Phrase",
  "text_content": "\"exact text for the card\"",
  "suggested_sources": ["archive.org"]
}
```

Field rules to specify explicitly:
- `id`: globally sequential `S001`–`S999`, never reset per chapter
- `chapter`: integer, prologue = 0, chapters parsed from `## N.` headings = N
- `chapter_title`: exact string from the `## N. Title` heading
- `narrative_context`: paraphrase only, never transcription
- `visual_need`: era + geography + subject, zero cinematographer language
- `building_block`: must match an entry from the vocabulary table exactly
- `shotlist_type`: one of exactly 6 values
- `building_block_variant`: meaningful string based on the shot (not null)
- `text_content`: populated for all text_overlay shots; null for all others
- `suggested_sources`: array of source strings, may be empty

### Pattern 3: Building Block Vocabulary as Table

**What:** A two-column table — block name + one-line description. No routing rules per block (routing lives in Type Routing section).
**When to use:** Building Blocks section.
**Known 18 blocks from Duplessis baseline:**

| Building Block | Description |
|----------------|-------------|
| Quote Card | Verbatim testimony or statement displayed as a formatted text card |
| Keyword Stinger | High-impact phrase, statistic, or question displayed in bold isolation |
| Date Card | Date and location establishing context for the following content |
| Testimony Attribution Card | Speaker identification card preceding or following a quote |
| Silhouette Figure | Symbolic figure silhouette representing a person, group, or institution |
| Concept Diagram | Animated diagram showing relationships, comparisons, cycles, or influence chains |
| Location Map | Map showing geographic context — country, region, city, or route |
| Historical Photograph | Real archival photograph from the relevant era and location |
| Archival Footage | Real archival video footage from the relevant era and location |
| Document Scan | Scanned real document — letter, order, form, record, certificate |
| Newspaper Clipping | Scanned newspaper article or headline from the relevant era |
| Wiki/Encyclopedia Text Block | Reference-style text excerpt, optionally with highlighted keywords |
| Credential/Authority Card | Institutional identification card for a named expert, official, or researcher |
| Glitch Stinger | Digital corruption/glitch visual used as chapter transition |
| Abstract Texture | Non-representational texture used for mood — violence, absence, dread |
| Symbolic Icon | Single graphic symbol representing a concept, institution, or absence |
| Static Noise/Corruption | TV static or signal corruption representing destroyed or missing records |
| Landscape Establishing Shot | Wide geographic or environmental shot establishing place |

**Additional blocks needed for channel scope** (Claude's discretion — examples to consider):
- Crime Scene Photograph (true crime: physical evidence scenes)
- Mugshot/Identification Photograph (true crime: suspects, victims in official custody)
- Timeline Diagram (unsolved cases: chronological event mapping)
- Missing Person Card (missing persons: profile card format)
- Social Media Screenshot (modern events: online artifacts)
- Security Footage Frame (modern events/true crime: surveillance stills)
- Institutional Seal/Logo (institutional scandals: organization identification)

### Pattern 4: Type Routing as Decision Rules

**What:** 6 shotlist_type values with explicit assignment rules.
**When to use:** Type Routing section, after building blocks.

**Type assignment rules (derived from Duplessis analysis):**

| shotlist_type | Assign when | Building blocks that use it |
|---------------|-------------|----------------------------|
| `archival_video` | Real video footage exists for this era/subject | Archival Footage, Landscape Establishing Shot |
| `archival_photo` | A real photograph exists or plausibly exists | Historical Photograph |
| `text_overlay` | Content is rendered as displayed text — no source image needed | Quote Card, Keyword Stinger, Date Card, Testimony Attribution Card |
| `animation` | Abstract concept, emotional state, or subject with no visual record | Silhouette Figure, Concept Diagram, Abstract Texture, Symbolic Icon, Static Noise/Corruption, Glitch Stinger |
| `map` | Geographic context — always a generated/rendered map, never archival | Location Map |
| `document_scan` | A real document, newspaper, or text artifact exists or plausibly exists | Document Scan, Newspaper Clipping, Wiki/Encyclopedia Text Block, Credential/Authority Card |

**Critical routing rule (SHOT-07):** When the narration describes a concept, emotion, or systemic mechanism with no photographic record, route to `animation`. Never use `archival_photo` or `archival_video` for abstract content.

### Pattern 5: Establishing Shot Rule

**What:** Each chapter's first shot must orient the viewer in time, place, or context before detail shots begin.
**Observed in Duplessis:**
- Ch 0 (Prologue): Quote Card (thematic anchor)
- Ch 1: Date Card (temporal)
- Ch 2: Concept Diagram (conceptual framing)
- Ch 3: Glitch Stinger (chapter transition)
- Ch 4: Glitch Stinger (chapter transition)
- Ch 5: Date Card (temporal)
- Ch 6: Silhouette Figure (institutional framing)
- Ch 7: Glitch Stinger (chapter transition)

The prompt should name valid establishing shot types and give Claude latitude to choose based on chapter content.

### Anti-Patterns to Avoid (Required Section)

The CONTEXT.md mandates 4-6 WRONG/RIGHT pairs for `visual_need`. Analysis of the Duplessis shotlist reveals the specific failure modes to illustrate:

**1. Cinematographer language in visual_need**
- WRONG: `"Slow dolly push into a close-up of Duplessis's face, shallow depth of field"`
- RIGHT: `"Historical photograph of Maurice Duplessis, Quebec politician, circa 1940s-1950s"`

**2. Era and geography omitted**
- WRONG: `"Photo of a politician at a podium"`
- RIGHT: `"Historical photograph of Maurice Duplessis at the Quebec National Assembly, 1940s-1950s"`

**3. Vague subject description**
- WRONG: `"Image of buildings"`
- RIGHT: `"Archival photograph of a Catholic orphanage exterior in Montreal, Quebec, 1940s-1950s era"`

**4. Production terms**
- WRONG: `"B-roll of an empty hospital corridor, handheld feel"`
- RIGHT: `"Archival footage of a psychiatric hospital interior corridor, Quebec, 1950s era"`

**5. Abstract content routed to archival**
- WRONG: `building_block: "Archival Footage", visual_need: "Footage of the psychological impact of false diagnosis"` (no such footage exists)
- RIGHT: `building_block: "Concept Diagram", shotlist_type: "animation", visual_need: "Animated diagram showing cascade from diagnosis to employment and credibility effects"`

**6. Narration transcribed into narrative_context**
- WRONG: `"Duplessis returned to power in Quebec in 1944, backed by the Union Nationale party and its long-standing alliance with the Roman Catholic Church, which had administered social welfare in the province for generations, running hospitals, orphanages, and schools through its religious orders."`
- RIGHT: `"Duplessis returns to power, backed by Church-state alliance that controlled social welfare."`

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Prompt structure | Custom ordering different from writer/prompts/generation.md | Mirror the writer prompt's section ordering exactly |
| Building block list | Invent new blocks freely | Start from the 18 validated Duplessis blocks; add only for clear channel gaps |
| Type routing logic | Invent routing heuristics | Use the 6-type taxonomy already proven in production |
| Worked example | Use Duplessis content | Write a synthetic example from a different topic domain |
| Variant population | Leave `building_block_variant` null | Populate with contextually meaningful variants matching Duplessis patterns |

---

## Common Pitfalls

### Pitfall 1: Overspecifying narrative_context
**What goes wrong:** The prompt sets a hard 50-word cap, causing Claude to truncate useful context or count words while generating.
**Why it happens:** CONTEXT.md decision says this is "soft guidance, not a hard cap."
**How to avoid:** Write as "concise paraphrase — typically 1-2 sentences. Never copy narration verbatim." No word count.
**Warning signs:** Prompt says "maximum 50 words" — remove this.

### Pitfall 2: Chapter 0 prologue parsing ambiguity
**What goes wrong:** Scripts may begin with a prologue section without a `## N.` heading. Claude assigns it chapter 1 instead of chapter 0.
**Why it happens:** The `## N. Title` regex doesn't match unnumbered sections.
**How to avoid:** Add an explicit rule: "Any content before the first `## 1.` heading is treated as chapter 0 with chapter_title 'Prologue'."
**Warning signs:** In Duplessis, shots S001-S003 are chapter 0. The script begins with a prologue hook before the first numbered chapter.

### Pitfall 3: Establishing shot as rigid formula
**What goes wrong:** Claude always uses a Date Card as the establishing shot even when the chapter doesn't have a temporal anchor.
**Why it happens:** Examples only show Date Card establishing shots.
**How to avoid:** Name the valid types (Date Card, Location Map, Landscape Establishing Shot, Archival Footage, Glitch Stinger) and describe when each applies.
**Warning signs:** All chapters have Date Cards as first shots.

### Pitfall 4: text_content null for text_overlay shots
**What goes wrong:** Claude leaves `text_content` null on Quote Cards and Keyword Stingers.
**Why it happens:** The null convention for other types leaks into text_overlay shots.
**How to avoid:** Explicit rule: "`text_content` MUST be populated for all `text_overlay` shots. It is null for all other shotlist_types."
**Warning signs:** Any Quote Card or Keyword Stinger with `text_content: null`.

### Pitfall 5: Consecutive repeated building blocks
**What goes wrong:** 4-5 consecutive Historical Photographs in a chapter about a well-documented historical period.
**Why it happens:** Natural tendency to match building block to content without considering variety.
**How to avoid:** Anti-pattern rule: "No more than 2 consecutive shots using the same building block. Enforce variety across a chapter."
**Warning signs:** Runs of 3+ identical building blocks.

### Pitfall 6: Document_scan type for animation building blocks
**What goes wrong:** Wiki/Encyclopedia Text Block assigned `document_scan` type — but Concept Diagram or Silhouette Figure also assigned `document_scan` erroneously.
**Why it happens:** Type naming implies "documents" which overlaps with "text blocks."
**How to avoid:** The type routing table must be explicit about which blocks map to which types. Wiki/Encyclopedia Text Block is `document_scan` by convention; Concept Diagram and Silhouette Figure are always `animation`.
**Warning signs:** Concept Diagram or Silhouette Figure with `shotlist_type: "document_scan"`.

---

## Code Examples

### Complete Schema (9-field shot object from Duplessis ground truth)

```json
{
  "id": "S005",
  "chapter": 1,
  "chapter_title": "The Arithmetic of Abandonment",
  "narrative_context": "Introduction of Maurice Duplessis and the Union Nationale's structural alliance with the Roman Catholic Church.",
  "visual_need": "Historical photograph of Maurice Duplessis, circa 1940s-1950s",
  "building_block": "Historical Photograph",
  "shotlist_type": "archival_photo",
  "building_block_variant": "Portrait",
  "text_content": null,
  "suggested_sources": ["wikimedia_commons"]
}
```

### Animation-type shot (abstract content, no visual record)

```json
{
  "id": "S008",
  "chapter": 1,
  "chapter_title": "The Arithmetic of Abandonment",
  "narrative_context": "Federal funding differential: orphanage child $0.70/day vs. psychiatric patient $2.25/day.",
  "visual_need": "Concept diagram showing funding differential between orphanage and psychiatric hospital categories",
  "building_block": "Concept Diagram",
  "shotlist_type": "animation",
  "building_block_variant": "Comparison/Split",
  "text_content": null,
  "suggested_sources": []
}
```

### text_overlay shot with populated text_content

```json
{
  "id": "S016",
  "chapter": 1,
  "chapter_title": "The Arithmetic of Abandonment",
  "narrative_context": "The financial scale: $70 million in subsidies, 20,000 children reclassified.",
  "visual_need": "Keyword stinger displaying the financial figure and scale",
  "building_block": "Keyword Stinger",
  "shotlist_type": "text_overlay",
  "building_block_variant": "Impact Phrase",
  "text_content": "$70 MILLION — 20,000 CHILDREN",
  "suggested_sources": []
}
```

### Worked example template (synthetic — NOT from Duplessis)

The worked example in generation.md must use synthetic content from a different domain. Suggested structure:
- 3-4 sentence narration excerpt from a plausible (but invented) true crime or unsolved case
- Maps to 2-3 shot entries covering at least 2 different shotlist_types
- Demonstrates: a text_overlay establishing shot, an archival_photo or archival_video detail shot, and one animation-type shot

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Architecture.md schema (`suggested_types` array) | Extended schema: `building_block`, `shotlist_type`, `building_block_variant`, `text_content`, `suggested_sources` as separate scalar fields | More precise asset acquisition targeting |
| No prologue handling | Chapter 0 for pre-numbered content | Duplessis Prologue correctly grouped |
| No visual variety rule | Anti-pattern: consecutive same-block runs prohibited | Forces tonal and visual diversity |
| Variants always null (Phase 13 Stage Contract) | Variants populated for generic building blocks (Phase 14 decision) | More specific acquisition context |

---

## Open Questions

1. **Duplessis word count per chapter vs. shot density**
   - What we know: STATE.md blocker says "express shot density as word-count proportional; validate against Duplessis baseline before Phase 15"
   - What's unclear: The specific calibration (words/shot ratio) hasn't been computed
   - Recommendation: During plan execution, compute words-per-chapter from Script V1.md and shots-per-chapter from shotlist.json to derive the ratio. The prompt should express guidance proportionally (e.g., "1 shot per approximately 80-120 words of narration") rather than as a flat range.

2. **Additional building blocks beyond the 18**
   - What we know: 5-10 additional blocks are needed; Claude has discretion on exact set
   - What's unclear: Whether the 7 candidate blocks listed above (Crime Scene Photograph, Mugshot, Timeline Diagram, etc.) represent the right coverage
   - Recommendation: Accept Claude's discretion per CONTEXT.md. The planner should not over-specify — the prompt author decides the final vocabulary during writing.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual quality gate — no automated test suite for prompt files |
| Config file | None |
| Quick run command | Run generation.md against Duplessis Script V1.md, inspect output |
| Full suite command | Same — single quality gate |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SHOT-01 | Chapter structure parsed, shots grouped by chapter | manual | Load Script V1.md + generation.md, verify chapter grouping in output | ❌ Wave 0 |
| SHOT-02 | Shot boundaries at narrative beats, not paragraphs | manual | Compare output shot count per chapter to Duplessis baseline (8-13/chapter) | ❌ Wave 0 |
| SHOT-03 | All 9 fields present on every shot | manual | Inspect output JSON structure against schema | ❌ Wave 0 |
| SHOT-04 | visual_need contains era + geography + subject | manual | Spot-check 5 random visual_need strings for cinematographer language | ❌ Wave 0 |
| SHOT-05 | No 3+ consecutive same building_block runs | manual | Scan building_block sequence in output JSON | ❌ Wave 0 |
| SHOT-06 | First shot of each chapter is establishing type | manual | Check shot N where chapter number changes | ❌ Wave 0 |
| SHOT-07 | Abstract narration routes to animation, not archival | manual | Identify 3 abstract-content shots in output, verify shotlist_type | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** Visually inspect output against Duplessis shotlist.json — does structure match?
- **Per wave merge:** Full quality gate: run generation.md against Script V1.md, compare chapter counts, shot counts, type distribution
- **Phase gate:** Quality gate must pass before Phase 15 (SKILL.md) begins

### Wave 0 Gaps

- [ ] No automated test infrastructure — this is a [HEURISTIC] skill, all validation is manual
- [ ] The quality gate process should be documented in the plan so the executor knows exactly how to validate

*(Note: Automated testing is not applicable to pure prompt files. The quality gate is manual comparison of generated output against the known-good Duplessis shotlist.json.)*

---

## Sources

### Primary (HIGH confidence)

- `projects/1. The Duplessis Orphans.../shotlist.json` — 73-shot ground truth for schema, building blocks, type routing, variant patterns, establishing shot examples
- `.claude/skills/visual-orchestrator/CONTEXT.md` — integration contract, confirms inputs and process
- `.claude/skills/writer/prompts/generation.md` — structural template, tonal model
- `.planning/phases/14-generation-prompt/14-CONTEXT.md` — locked decisions for this phase

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — SHOT-01 through SHOT-07 requirements mapped
- `.planning/STATE.md` — blockers and accumulated decisions

---

## Metadata

**Confidence breakdown:**
- Schema specification: HIGH — derived directly from 73-shot production artifact
- Building block vocabulary: HIGH — 18 blocks enumerated from production; 7 additional candidates are LOW (Claude's discretion)
- Type routing rules: HIGH — 6 types, all routing derived from production data
- Anti-patterns: HIGH — derived from Duplessis analysis plus explicit CONTEXT.md requirements
- Shot density calibration: MEDIUM — Duplessis data exists but word-count ratio not yet computed

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable — no external dependencies, all internal artifacts)
