# S01: Visual Orchestrator Skill — Research

**Date:** 2026-03-15

## Summary

The Visual Orchestrator is a [HEURISTIC] skill that transforms Script.md + VISUAL_STYLE_GUIDE.md into shotlist.json. It follows the established context-loader CLI pattern (D002): a thin Python CLI aggregates inputs and prints them to stdout, then Claude applies the VISUAL_STYLE_GUIDE's Type Selection Decision Tree to every narrative segment, producing an ordered array of shot entries.

The VISUAL_STYLE_GUIDE is comprehensive — 25 building blocks across 4 categories (B-Roll, Graphics & Animation, Text Elements, Evidence & Documentation), each with a `shotlist_type`, usage rules, production specs, weights, and a 16-rule decision tree. The orchestrator's job is mechanical application of this decision tree to script prose, not creative invention. The sequencing rules (no back-to-back glitch elements, max 3 consecutive text elements, etc.) add a validation layer.

The shotlist.json schema evolves from Architecture.md's 5-field design to include `building_block` and `shotlist_type` fields that downstream skills filter on. Text overlay entries (R002) appear in the shotlist for placement guidance but generate no assets.

## Recommendation

Build as a [HEURISTIC] skill with context-loader CLI, matching the writer skill pattern exactly:

1. **CLI** (`python -m visual_orchestrator load "<topic>"`) — loads Script.md, VISUAL_STYLE_GUIDE.md, and channel.md; prints labeled context + output path + generation prompt path
2. **Generation prompt** (`prompts/generation.md`) — encodes the shotlist.json schema, decision tree application rules, sequencing validation, and text overlay handling
3. **Schema validation script** (`scripts/visual_orchestrator/schema.py`) — validates shotlist.json against the contract (valid IDs, required fields, valid shotlist_types, sequencing rule checks)
4. **Tests** — pytest for CLI resolution, schema validation, and sequencing rule enforcement

Claude reads the prompt, processes Script.md paragraph-by-paragraph through the decision tree, and writes shotlist.json. The schema validator runs post-generation to catch contract violations.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Project directory resolution | `writer/cli.py::resolve_project_dir()` | Identical logic needed — resolve by topic substring match |
| Project root discovery | `writer/cli.py::_get_project_root()` | Walk-up-to-CLAUDE.md pattern, reusable |
| JSON schema validation | `jsonschema` stdlib-compatible or manual validation | shotlist.json has a fixed schema — validate structurally |

## Existing Code and Patterns

- `.claude/skills/writer/scripts/writer/cli.py` — Context-loader CLI pattern to replicate. `resolve_project_dir()` and `_get_project_root()` can be extracted or duplicated (they're small). The `cmd_load()` function is the template: read files, print labeled sections, print output/prompt paths.
- `.claude/skills/writer/CONTEXT.md` — Stage contract format to follow (Inputs → Process → Checkpoints → Outputs → Deferred)
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — The decision framework the orchestrator applies. 25 building blocks, each with a `> Shotlist type:` annotation. The Type Selection Decision Tree (16 IF-THEN rules) is the core logic.
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md` — Test input. 7 chapters (`## N. Title`), pure prose, ~4,500 words. No stage directions, no visual cues. The orchestrator must infer visual needs from narrative content.
- `Architecture.md` lines 126-154 — Original shotlist.json schema (5 fields: id, chapter, narrative_context, visual_need, suggested_types). M002 roadmap extends this.

## Constraints

- **Python only** for all scripts (no Node.js)
- **No LLM API wrappers** — Claude Code runtime handles all reasoning; CLI is data-in, data-out
- **Context-loader pattern (D002)** — CLI prints context, Claude reasons, Claude writes output file
- **VISUAL_STYLE_GUIDE is the authority** — the orchestrator applies its decision tree, not its own heuristics. Different reference videos produce different guides; the orchestrator must work with any valid guide.
- **shotlist.json is the contract** — every downstream skill (S02-S05) reads it and filters by `shotlist_type`. Schema must be stable.
- **Text overlays produce no assets (D009)** — entries appear in shotlist for editorial placement guidance only
- **Raw delivery (D008)** — production specs in the guide describe final look, not what the orchestrator outputs
- **Multiple VISUAL_STYLE_GUIDEs may exist** — `context/visual-references/` can contain guides from different reference videos. The CLI should accept a guide path or default to the first/only one.

## Common Pitfalls

- **Over-granular shot segmentation** — Splitting every sentence into a shot produces 200+ entries and overwhelms downstream agents. Group by narrative beat (2-4 sentences that share a visual context), not by sentence. A 20-minute script should produce roughly 60-100 shots.
- **Ignoring sequencing rules** — The VISUAL_STYLE_GUIDE has explicit sequencing constraints (no back-to-back glitch, max 3 consecutive text, silhouettes max 3 in a row). The generation prompt must encode these as validation rules, and the schema validator should check them post-generation.
- **Hardcoding building blocks** — The VISUAL_STYLE_GUIDE varies per reference video. The orchestrator must parse the guide's Quick Reference table and decision tree dynamically, not assume the 25 blocks from the Mexico cult guide.
- **Confusing shotlist_type with building_block** — `shotlist_type` is the category for downstream routing (archival_video, archival_photo, animation, map, text_overlay, document_scan). `building_block` is the specific visual element (Silhouette Figure, Concept Diagram, etc.). Multiple building blocks share the same shotlist_type.
- **Schema drift** — Architecture.md has `suggested_types` (array). M002 roadmap has `shotlist_type` (single value) + `building_block`. Need to pick one schema and make it the contract. Recommend the M002 version: single `shotlist_type` + `building_block` is cleaner for downstream filtering.

## Open Risks

- **Guide variability** — Only one VISUAL_STYLE_GUIDE exists (Mexico cult). The orchestrator design must work with any guide, but can only be tested against one. Risk: assumptions about guide structure that break with a differently-structured guide.
- **Segment granularity heuristic** — How finely to segment the script into shots is a judgment call. Too few = gaps in visual coverage. Too many = noise for downstream agents. The prompt needs clear guidance (target range, grouping rules) but the right granularity will need iteration.
- **Decision tree ambiguity** — Some narrative passages could match multiple decision tree rules (e.g., a passage that introduces a person AND describes a ritual). The prompt must specify precedence or allow multi-assignment.
- **Schema evolution** — Architecture.md's schema and M002's schema differ. The first shotlist.json this skill produces becomes the de facto contract. Any mismatch discovered in S02 will require schema changes.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Storyboard/shotlist generation | `inferen-sh/skills@storyboard-creation` (1.7K installs) | Available but not relevant — generic storyboarding doesn't apply the project's VISUAL_STYLE_GUIDE decision framework |
| Video production | `travisjneuman/.claude@video-production` (44 installs) | Available but too generic — this project has its own methodology |

No professional skills recommended for installation. The orchestrator is project-specific — it applies a custom decision framework that no generic skill can replicate.

## Shotlist.json Schema (Proposed)

Evolving Architecture.md's schema per M002 roadmap requirements:

```json
{
  "project": "The Duplessis Orphans Quebec's Stolen Children",
  "guide_source": "Mexico's Most Disturbing Cult",
  "generated": "2026-03-15T01:00:00Z",
  "shots": [
    {
      "id": "S001",
      "chapter": 1,
      "chapter_title": "The Arithmetic of Abandonment",
      "narrative_context": "Narrator describes Quebec in the 1940s under Premier Duplessis, the Church's administrative control over welfare",
      "visual_need": "Historical Quebec government/church buildings, 1940s era establishing shot",
      "building_block": "Archival Footage",
      "shotlist_type": "archival_video",
      "building_block_variant": "Rural/Landscape",
      "text_content": null,
      "suggested_sources": ["archive.org", "loc.gov"]
    },
    {
      "id": "S045",
      "chapter": 3,
      "chapter_title": "The Record That Disappeared",
      "narrative_context": "Direct quote from Albert Sylvio about preparing bodies",
      "visual_need": "Quote card displaying survivor testimony",
      "building_block": "Quote Card",
      "shotlist_type": "text_overlay",
      "building_block_variant": "Testimony Excerpt",
      "text_content": "I undressed them and washed them and prepared them for burial. We put them in cardboard boxes. Some of them were children.",
      "suggested_sources": []
    }
  ]
}
```

Key schema decisions:
- `chapter` is integer (matches `## N.` numbering in Script.md)
- `shotlist_type` is single string, not array — one routing category per shot
- `building_block_variant` captures the specific variant from the guide (optional)
- `text_content` populated only for `text_overlay` entries (R002)
- `suggested_sources` hints for media acquisition, empty for non-acquired types

## Requirement Coverage

| Req | What This Slice Must Deliver | Risk |
|-----|------------------------------|------|
| R001 | Parse Script.md + apply decision tree → shotlist.json with building block assignments for every segment | Medium — decision tree ambiguity for multi-matching passages |
| R002 | Text overlay entries (quote cards, date cards, keyword stingers, warning cards) with text content | Low — clear building block types, straightforward extraction from script quotes/dates |

## Sources

- Architecture.md lines 126-154 — original shotlist schema and Agent 1.4 spec
- M002 Roadmap boundary map — extended schema with building_block and shotlist_type fields
- VISUAL_STYLE_GUIDE.md — 25 building blocks, decision tree, sequencing rules (source: visual-style-extractor output)
- Writer skill (`cli.py`, `CONTEXT.md`) — context-loader CLI pattern reference
