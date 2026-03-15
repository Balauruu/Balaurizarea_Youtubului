# Phase 13: Stage Contract - Research

**Researched:** 2026-03-15
**Domain:** Skill documentation / stage contract authoring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**VISUAL_STYLE_GUIDE Dependency**
- Deferred to SHOT-09 (future milestone) — v1.3 does NOT require VISUAL_STYLE_GUIDE.md as an input
- CONTEXT.md lists only two inputs: Script.md (from writer) and prompts/generation.md (skill-internal)
- Building block vocabulary will be a generic documentary set hardcoded in generation.md (Phase 14)
- `building_block` field populated with generic documentary names (e.g., "Historical Footage", "Quote Card", "Map Overlay")
- `building_block_variant` field included in schema but always null for v1.3
- SHOT-09 later swaps the vocabulary source from hardcoded to guide-referenced — no schema change needed

**Pipeline-Reset Invariant**
- Document as a design principle, not a specific artifact coupling
- State: "shotlist.json is the source of truth for the asset pipeline. Any Script.md change invalidates shotlist.json and requires full regeneration"
- Mention downstream artifacts generically ("e.g., acquisition manifests") — do NOT name manifest.json specifically
- Full regeneration always — no partial/chapter-level regeneration in v1.3
- Rationale: sequential shot IDs (S001...) would fragment if individual chapters are regenerated
- Chapter-level regeneration deferred to future enhancement

**Re-Run Behavior**
- Overwrite without warning — skill always overwrites existing shotlist.json
- No confirmation prompt — user triggered the skill intentionally
- Git history serves as version control
- Matches writer skill convention for Script.md

**Checkpoint Process**
- No checkpoint section in CONTEXT.md — omit entirely
- No automated review gate, no summary presentation
- User can review via git diff or reading shotlist.json directly if they choose
- Regenerate by re-invoking the skill

### Claude's Discretion

- Exact wording of process step descriptions in CONTEXT.md
- Level of detail in the inputs table annotations
- How to phrase the pipeline-reset invariant section heading

### Deferred Ideas (OUT OF SCOPE)

**Out of Scope (by design)**
- Shot duration/timing — editor's domain (DaVinci Resolve)
- Camera angles/movement — not an acquisition pipeline, only sourcing
- Effects/transitions — post-production decisions
- Priority/importance scoring — adds complexity without clear value

**Future Enhancements**
- SHOT-08: Two-pass generation (annotate beats first, then assign types)
- SHOT-09: VISUAL_STYLE_GUIDE.md integration for building block vocabulary and type decision tree
- SHOT-10: Shot density calibration based on chapter word count
- Chapter-level regeneration without full re-run
- Automatic guide selection when multiple VISUAL_STYLE_GUIDE.md files exist
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Pure [HEURISTIC] skill — SKILL.md + CONTEXT.md + prompts/generation.md, zero Python code | Confirmed by template analysis: style-extraction/CONTEXT.md is the direct structural model for a zero-code heuristic skill |
| INFRA-02 | CONTEXT.md documents pipeline-reset invariant (shotlist.json + downstream artifacts atomically coupled) | Confirmed by existing shotlist.json schema and manifest.json coupling pattern; invariant wording locked in CONTEXT.md decisions |
</phase_requirements>

---

## Summary

Phase 13 produces exactly one file: `.claude/skills/visual-orchestrator/CONTEXT.md`. This is a documentation-only phase — no Python, no prompts, no SKILL.md. The entire task is writing a well-structured stage contract that locks the skill's inputs, outputs, process, and the pipeline-reset invariant.

The project already has two authoritative templates for this exact document type: `style-extraction/CONTEXT.md` (the closest match — zero-code heuristic skill with the same section structure) and `writer/CONTEXT.md` (includes a CLI aggregation step that does not apply here). The output schema is also fully known from the existing `projects/1. The Duplessis Orphans/shotlist.json`, which is the canonical v1.3 schema to reference.

The only decisions left to Claude's discretion are prose-level choices: exact wording of process steps, annotation depth in the inputs table, and how to phrase the pipeline-reset invariant heading. All structural, scope, and schema decisions are locked in CONTEXT.md.

**Primary recommendation:** Follow `style-extraction/CONTEXT.md` section-for-section, substituting visual-orchestrator's inputs/process/outputs. Add a dedicated pipeline-reset invariant section (not a checkpoint) between Process and Outputs.

---

## Standard Stack

This phase has no software stack. It produces a markdown documentation file.

### Authoring Conventions (established in this project)

| Element | Convention | Source |
|---------|-----------|--------|
| Inputs table | 4 columns: Source, File/Location, Scope, Why | style-extraction/CONTEXT.md |
| Outputs table | 3 columns: Artifact, Location, Format | style-extraction/CONTEXT.md |
| Process steps | Numbered, each prefixed `[HEURISTIC]` or `[DETERMINISTIC]` | Both template CONTEXT.md files |
| Classification line | Final line: `**[HEURISTIC]** — Zero Python. No CLI commands. No pip installs.` | style-extraction/CONTEXT.md |
| Deferred section | Flat list of out-of-scope and future items, reason included | writer/CONTEXT.md |
| No checkpoints | Omit checkpoint table entirely — locked decision | 13-CONTEXT.md decisions |

---

## Architecture Patterns

### Recommended Section Order

The planner should produce a CONTEXT.md with exactly this section order, derived from style-extraction/CONTEXT.md (the direct template):

```
# Visual Orchestrator — Stage Contract

[one-line description]

## Inputs
[table]

## Process
[numbered steps, each [HEURISTIC]-prefixed]

## Pipeline-Reset Invariant
[prose paragraph — NOT a checkpoint table]

## Outputs
[table]

## Deferred
[list of out-of-scope and future items]

## Classification
**[HEURISTIC]** — Zero Python. No CLI commands. No pip installs.
```

### Input Table: Exactly Two Rows

Per locked decisions, v1.3 has exactly two inputs:

| Source | File/Location | Scope | Why |
|--------|--------------|-------|-----|
| Writer skill | `projects/N. [Title]/Script.md` | Full file | Source material for chapter parsing and shot generation |
| Skill prompt | `.claude/skills/visual-orchestrator/prompts/generation.md` | Full file | Schema definition, granularity rules, building block vocabulary, anti-patterns |

Note: VISUAL_STYLE_GUIDE.md is explicitly NOT an input for v1.3 — this must be stated in the Deferred section.

### Process Steps: What the Planner Should Write

The visual-orchestrator process is simpler than writer (no CLI step). Suggested steps:

1. **[HEURISTIC] Read inputs** — Load Script.md and prompts/generation.md
2. **[HEURISTIC] Parse chapter structure** — Identify chapters by `## N. Title` headings; treat unnumbered prologue as chapter 0
3. **[HEURISTIC] Generate shots** — For each chapter, identify narrative beats and assign shots following prompts/generation.md rules
4. **[HEURISTIC] Write shotlist.json** — Write to `projects/N. [Title]/shotlist.json`, overwriting any existing file without prompt

These are suggestions — exact wording is Claude's discretion.

### Pipeline-Reset Invariant: Wording Guidance

This is a standalone section (not a checkpoint table). Recommended framing:

> **shotlist.json is the source of truth for the asset pipeline.** Any change to Script.md — including chapter additions, removals, or reordering — invalidates the existing shotlist.json and all downstream artifacts (e.g., acquisition manifests). Full regeneration is always required; no partial or chapter-level update is supported in v1.3.
>
> Sequential shot IDs (S001, S002...) are assigned globally across the full script. Chapter-level regeneration would fragment the ID sequence, breaking downstream asset mapping. Re-invoke the skill to regenerate in full; git history preserves the previous shotlist.

The exact heading and prose are Claude's discretion. The invariant must express: (1) shotlist.json is source of truth, (2) Script.md change = full regeneration, (3) downstream artifacts generically mentioned, (4) no partial regeneration, (5) reason (sequential IDs).

### Output Table: One Row

| Artifact | Location | Format |
|----------|----------|--------|
| Shot list | `projects/N. [Title]/shotlist.json` | JSON array of shot objects |

The schema detail (field names) belongs in prompts/generation.md (Phase 14), not in CONTEXT.md.

### Deferred Section Content

The deferred section must capture two categories, sourced directly from locked decisions:

**Out of scope by design:**
- Shot duration/timing — editor's domain (DaVinci Resolve)
- Camera angles/movement — not an acquisition pipeline, only sourcing
- Effects/transitions — post-production decisions
- Priority/importance scoring — acquisition gets all shots regardless

**Future enhancements (planned):**
- SHOT-09: VISUAL_STYLE_GUIDE.md as input for building block vocabulary and type decision tree
- SHOT-08: Two-pass generation (annotate beats first, then assign types)
- SHOT-10: Shot density calibration based on chapter word count
- Chapter-level regeneration without full re-run

---

## Don't Hand-Roll

This phase produces documentation, not code. The "don't hand-roll" principle applies to document structure: do not invent a new section format or table schema. Use the existing template exactly.

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Section structure | Novel headings or ordering | style-extraction/CONTEXT.md section order verbatim | Consistency across skill CONTEXT.md files matters for CLAUDE.md routing |
| Input table columns | Fewer or different columns | The 4-column format (Source, File/Location, Scope, Why) | The orchestrator reads these tables to determine what to load |
| Classification line | Descriptive prose footer | The exact `**[HEURISTIC]** — Zero Python...` format | Used by routing logic |

---

## Common Pitfalls

### Pitfall 1: Including VISUAL_STYLE_GUIDE.md as an Input

**What goes wrong:** ROADMAP.md Phase 13 success criteria (line 59) says CONTEXT.md documents inputs including "VISUAL_STYLE_GUIDE.md" — this contradicts the locked CONTEXT.md decision.
**Why it happens:** ROADMAP.md was written before the Phase 13 discuss session locked the deferred decision.
**How to avoid:** CONTEXT.md locked decisions are authoritative. The v1.3 CONTEXT.md has exactly two inputs: Script.md and prompts/generation.md. VISUAL_STYLE_GUIDE.md goes in Deferred.
**Warning signs:** If the planner's inputs table has three rows, it has included the wrong source.

### Pitfall 2: Adding a Checkpoint Table

**What goes wrong:** The style-extraction/CONTEXT.md template includes a `## Checkpoints` section. Copying the template verbatim would include it.
**Why it happens:** Template-following without reading the locked decisions.
**How to avoid:** Omit the Checkpoints section entirely. Locked decision: no automated review gate, no summary presentation.

### Pitfall 3: Naming manifest.json Specifically in the Invariant

**What goes wrong:** The invariant names `manifest.json` as the coupled downstream artifact.
**Why it happens:** The Duplessis project has a manifest.json and it's tempting to be specific.
**How to avoid:** Use generic language: "downstream artifacts (e.g., acquisition manifests)". The manifest.json name is an implementation detail of the media-acquisition skill, not the orchestrator's concern.

### Pitfall 4: Schema Detail in CONTEXT.md

**What goes wrong:** Listing shotlist.json field names (id, chapter, narrative_context, etc.) in the Outputs table or Process steps.
**Why it happens:** The schema is well-known from the Duplessis shotlist.json, so it's tempting to document it here.
**How to avoid:** Schema belongs in prompts/generation.md (Phase 14). CONTEXT.md only names the output file path and format (JSON).

### Pitfall 5: Treating the Deferred Section as Optional

**What goes wrong:** Omitting the Deferred section or making it vague ("future work TBD").
**Why it happens:** The deferred items feel self-evident.
**How to avoid:** The Deferred section is a first-class contract element. It tells future contributors what is explicitly out of scope by design versus what is planned for later. Both categories must be present and specific.

---

## Code Examples

### Canonical shotlist.json Schema (from Duplessis project)

This is the output format the CONTEXT.md must reference. Not for inclusion in CONTEXT.md itself — this is reference for the planner to understand what the skill produces.

```json
{
  "project": "The Duplessis Orphans Quebec's Stolen Children",
  "guide_source": "Lemmino Consumed by the Climb",
  "generated": "2026-03-15T01:18:00Z",
  "shots": [
    {
      "id": "S001",
      "chapter": 0,
      "chapter_title": "Prologue",
      "narrative_context": "Opening survivor quote about being born into a garbage can, never having a happy life.",
      "visual_need": "Quote card with survivor's testimony against dark background",
      "building_block": "Quote Card",
      "shotlist_type": "text_overlay",
      "building_block_variant": null,
      "text_content": "\"When you are a bastard...\"",
      "suggested_sources": []
    }
  ]
}
```

Key v1.3 schema fields vs. Architecture.md baseline:
- `building_block` and `shotlist_type` are separate fields (not `suggested_types` array from Architecture.md)
- `building_block_variant` is always present but may be null
- `text_content` present for text_overlay shots, null for others
- `suggested_sources` is a string array (can be empty)
- `guide_source` is a top-level metadata field (populated with "generic" for v1.3, since no style guide)

### style-extraction/CONTEXT.md (Direct Template)

Source: `.claude/skills/style-extraction/CONTEXT.md`

Structure (verified):
- `# style-extraction — Stage Contract` (title line with description)
- `## Inputs` (4-column markdown table)
- `## Process` (numbered steps with [HEURISTIC] prefix)
- `## Checkpoints` (OMIT this for visual-orchestrator)
- `## Outputs` (3-column markdown table)
- `## Post-Write Actions` (OMIT — not needed for visual-orchestrator)
- `## Classification` (bold [HEURISTIC] statement)

For visual-orchestrator: keep Inputs, Process, Outputs, Classification. Add Pipeline-Reset Invariant between Process and Outputs. Add Deferred before Classification.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Architecture.md `suggested_types` string array | `building_block` + `shotlist_type` as separate fields | Acquisition skill can route by type, UI can display by block name independently |
| VISUAL_STYLE_GUIDE drives vocabulary | Generic hardcoded documentary vocabulary (v1.3) | Skill works without style guide; SHOT-09 adds guide integration later with no schema change |
| Checkpoint gate in CONTEXT.md | No checkpoint — overwrite on re-invoke | Matches writer/Script.md convention; git history is the review mechanism |

---

## Open Questions

None — all design decisions are locked in CONTEXT.md. The planner has full information to produce the output file.

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`. However, this phase produces a single markdown documentation file (`.claude/skills/visual-orchestrator/CONTEXT.md`). There is no executable code, no runtime behavior, and no functions to unit-test.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (project standard) |
| Config file | none — existing pytest.ini or inferred |
| Quick run command | N/A — documentation phase |
| Full suite command | `pytest -x --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| INFRA-01 | CONTEXT.md classifies skill as pure [HEURISTIC] with zero Python code | manual | N/A | Verified by reading the output file |
| INFRA-02 | Pipeline-reset invariant section present and correct | manual | N/A | Verified by reading the output file |

### Wave 0 Gaps

None — no test files needed. This phase produces only documentation. Validation is by human review of the output CONTEXT.md against the success criteria in ROADMAP.md.

---

## Sources

### Primary (HIGH confidence)

- `13-CONTEXT.md` — all locked decisions, deferred items, template references
- `.claude/skills/style-extraction/CONTEXT.md` — direct template (verified full read)
- `.claude/skills/writer/CONTEXT.md` — alternate template (verified full read)
- `projects/1. Duplessis/shotlist.json` — canonical v1.3 output schema (verified full read, first 60 lines)
- `.planning/REQUIREMENTS.md` — INFRA-01 and INFRA-02 definitions (verified full read)
- `.planning/ROADMAP.md` — Phase 13 success criteria (verified full read)

### Secondary (MEDIUM confidence)

- `docs/superpowers/specs/2026-03-11-asset-pipeline-design.md` — original Architecture.md baseline schema showing `suggested_types` (superseded by Duplessis canonical schema)

### Tertiary (LOW confidence)

None — all findings are from internal project files with HIGH confidence.

---

## Metadata

**Confidence breakdown:**
- Document structure: HIGH — direct template available, verified by full read
- Input list: HIGH — locked decision in CONTEXT.md (two inputs, not three)
- Schema reference: HIGH — canonical example in Duplessis shotlist.json
- Pitfalls: HIGH — all identified from concrete contradictions in project files (ROADMAP.md vs CONTEXT.md decisions)
- Validation: HIGH — documentation phase, no automated tests apply

**Research date:** 2026-03-15
**Valid until:** Phase 14 start — decisions are locked and stable
