# Phase 13: Stage Contract - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Write the CONTEXT.md for the visual-orchestrator skill — locking inputs, outputs, process steps, and the pipeline-reset invariant. This is a documentation phase that produces a single file at `.claude/skills/visual-orchestrator/CONTEXT.md`. No Python code, no prompts, no SKILL.md — those are Phases 14 and 15.

</domain>

<decisions>
## Implementation Decisions

### VISUAL_STYLE_GUIDE Dependency
- **Deferred to SHOT-09 (future milestone)** — v1.3 does NOT require VISUAL_STYLE_GUIDE.md as an input
- CONTEXT.md lists only two inputs: Script.md (from writer) and prompts/generation.md (skill-internal)
- Building block vocabulary will be a generic documentary set hardcoded in generation.md (Phase 14)
- `building_block` field populated with generic documentary names (e.g., "Historical Footage", "Quote Card", "Map Overlay")
- `building_block_variant` field included in schema but always null for v1.3
- SHOT-09 later swaps the vocabulary source from hardcoded to guide-referenced — no schema change needed

### Pipeline-Reset Invariant
- **Document as a design principle, not a specific artifact coupling**
- State: "shotlist.json is the source of truth for the asset pipeline. Any Script.md change invalidates shotlist.json and requires full regeneration"
- Mention downstream artifacts generically ("e.g., acquisition manifests") — do NOT name manifest.json specifically
- **Full regeneration always** — no partial/chapter-level regeneration in v1.3
- Rationale: sequential shot IDs (S001...) would fragment if individual chapters are regenerated
- Chapter-level regeneration deferred to future enhancement

### Re-Run Behavior
- **Overwrite without warning** — skill always overwrites existing shotlist.json
- No confirmation prompt — user triggered the skill intentionally
- Git history serves as version control
- Matches writer skill convention for Script.md

### Checkpoint Process
- **No checkpoint section in CONTEXT.md** — omit entirely
- No automated review gate, no summary presentation
- User can review via git diff or reading shotlist.json directly if they choose
- Regenerate by re-invoking the skill

### Claude's Discretion
- Exact wording of process step descriptions in CONTEXT.md
- Level of detail in the inputs table annotations
- How to phrase the pipeline-reset invariant section heading

</decisions>

<specifics>
## Specific Ideas

- Follow style-extraction/CONTEXT.md and writer/CONTEXT.md as structural templates (inputs table, numbered process steps, outputs table, deferred section)
- The skill is pure [HEURISTIC] — zero Python code. CONTEXT.md must state this classification explicitly
- CONTEXT.md is consumed by orchestrator routing (CLAUDE.md references it) and by the planner/researcher for Phase 14

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `style-extraction/CONTEXT.md`: Direct template — zero-code skill with inputs table, process steps, checkpoints, outputs table, classification
- `writer/CONTEXT.md`: Alternate template — includes CLI aggregation step (not needed here since no Python)
- Both use consistent section ordering: Inputs → Process → Checkpoints → Outputs → Deferred

### Established Patterns
- Stage contracts use markdown tables for inputs and outputs
- Process steps are numbered, each prefixed with `[HEURISTIC]` or `[DETERMINISTIC]`
- Deferred section captures both "never planned" and "planned for later" items
- Classification line at bottom states the skill type

### Integration Points
- `CLAUDE.md` Task Routing table — Phase 15 will add the visual-orchestrator row referencing this CONTEXT.md
- `.planning/ROADMAP.md` — Phase 13 success criteria define what CONTEXT.md must contain
- `prompts/generation.md` (Phase 14) — will be authored based on the contract locked here

</code_context>

<deferred>
## Deferred Ideas

### Out of Scope (by design)
- Shot duration/timing — editor's domain (DaVinci Resolve)
- Camera angles/movement — not an acquisition pipeline, only sourcing
- Effects/transitions — post-production decisions
- Priority/importance scoring — adds complexity without clear value

### Future Enhancements
- SHOT-08: Two-pass generation (annotate beats first, then assign types)
- SHOT-09: VISUAL_STYLE_GUIDE.md integration for building block vocabulary and type decision tree
- SHOT-10: Shot density calibration based on chapter word count
- Chapter-level regeneration without full re-run
- Automatic guide selection when multiple VISUAL_STYLE_GUIDE.md files exist

</deferred>

---

*Phase: 13-stage-contract*
*Context gathered: 2026-03-15*
