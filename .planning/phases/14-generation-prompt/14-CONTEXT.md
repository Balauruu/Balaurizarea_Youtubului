# Phase 14: Generation Prompt - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Write `prompts/generation.md` for the visual-orchestrator skill — the prompt that encodes all reasoning to turn a Script.md into a valid shotlist.json. Covers schema definition, building block vocabulary with type routing, shot granularity rules, and anti-patterns. This phase produces a single prompt file. No Python code, no SKILL.md, no CONTEXT.md changes.

</domain>

<decisions>
## Implementation Decisions

### Building Block Vocabulary
- **Curated broader generic set** — start from the 18 blocks in the Duplessis shotlist, then add 5-10 blocks covering gaps for other channel topics (true crime, unsolved cases, modern events)
- Claude curates the additional blocks based on channel scope (dark mysteries, true crime, unsolved cases, institutional scandals)
- Each block gets a description but NOT individual When/When Not routing rules — routing is at the **shotlist_type level** instead
- Type-level routing: rules like "use `animation` for abstract concepts with no visual record", "use `archival_photo` when a real photograph exists"
- `building_block_variant` IS populated with meaningful variants (Portrait, Interior, Impact Phrase, etc.) — not null. The Phase 13 "always null" decision applied to VISUAL_STYLE_GUIDE-derived variants specifically; generic variants are fair game

### Shot Granularity Rules
- **Primary trigger: narrative beat changes** — new shot when the visual subject changes (different era, location, figure, evidence type)
- The 450-word cap is a safety net, not the primary boundary mechanism
- NOT word-count proportional or paragraph-boundary based
- **Soft density guardrails** — minimum 2 shots per chapter (hard, from success criteria), no hard max, guidance that typical chapters produce 8-15 shots
- `narrative_context` — soft guidance to keep it brief and paraphrased, not a hard 50-word cap. "Concise paraphrase of what the narrator is saying during this shot. Never copy narration verbatim."
- **Establishing shots** — each chapter must begin with an establishing/orienting shot, but Claude decides the type (date card, map, landscape, archival, etc.) based on content

### Anti-Patterns
- **Standalone section** — dedicated "Anti-Patterns" or "Common Mistakes" section near the end of the prompt
- **4-6 WRONG/RIGHT side-by-side pairs** for `visual_need` descriptions, covering: cinematographer language, vague descriptions, era/geography omission, production terms
- Additional anti-patterns explicitly called out:
  - Repeated building blocks (e.g., 5 consecutive Historical Photographs — enforce visual variety)
  - Paragraph-boundary shots (splitting at paragraph breaks instead of narrative beats)
  - Narration transcription (copying script text verbatim into narrative_context)
  - Missing text_content (forgetting to populate for text_overlay shots like Quote Cards, Keyword Stingers, Date Cards)

### Prompt Structure & Tone
- **Mirror writer's generation.md structure** — self-contained, ~200 lines, consistent section ordering
- Sections: Intro → Inputs → Schema → Building Blocks → Granularity Rules → Type Routing → Anti-Patterns → Output Format
- **Equally directive tone** — match the writer prompt's imperative style ("Each chapter MUST begin with an establishing shot", "Never use cinematographer language")
- **1 worked example** — synthetic 3-4 sentence narration excerpt mapped to 2-3 shot entries. Not from Duplessis to avoid memorization
- `suggested_sources` — **open, Claude decides** per shot. No predefined domain list. Claude suggests whatever sources seem relevant to the visual need

### Claude's Discretion
- Exact set of additional building blocks beyond Duplessis baseline
- Type routing rule wording and specificity
- Establishing shot type selection per chapter
- Worked example content (synthetic, not from any real project)
- Prompt section ordering within the overall structure

</decisions>

<specifics>
## Specific Ideas

- The Duplessis shotlist (73 shots, 8 chapters, 18 blocks, 6 types) is the validated baseline — the prompt should produce output consistent with that quality level
- Shotlist types from baseline: `archival_video`, `archival_photo`, `text_overlay`, `animation`, `map`, `document_scan`
- Building blocks from baseline: Quote Card, Keyword Stinger, Silhouette Figure, Concept Diagram, Date Card, Historical Photograph, Wiki/Encyclopedia Text Block, Testimony Attribution Card, Location Map, Glitch Stinger, Newspaper Clipping, Credential/Authority Card, Abstract Texture, Symbolic Icon, Static Noise/Corruption, Landscape Establishing Shot, Document Scan, Archival Footage
- STATE.md blocker: "Validate generation.md against Duplessis Script V1.md + existing shotlist.json — this is the quality gate before SKILL.md is written"

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `writer/prompts/generation.md`: Direct structural template — same prompt-as-specification pattern, directive tone, self-contained
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json`: 73-shot validated baseline for schema and building block reference
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script V1.md`: Input reference for testing generation.md against known-good output

### Established Patterns
- Prompt files are self-contained specifications — all rules, schema, and examples in one file
- Skills use `prompts/` subdirectory for generation prompts
- Directive tone with explicit constraints: "No exceptions", "Never", "MUST"

### Integration Points
- `visual-orchestrator/CONTEXT.md` references `prompts/generation.md` as an input in the Process section
- SKILL.md (Phase 15) will instruct Claude to read this prompt before generating
- The prompt must produce JSON matching the schema already established in the Duplessis shotlist

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-generation-prompt*
*Context gathered: 2026-03-15*
