# Visual Orchestrator — Stage Contract

Parses finished scripts into structured shot lists for the asset pipeline.

## Inputs

| Source | File/Location | Scope | Why |
|--------|--------------|-------|-----|
| Writer skill | `projects/N. [Title]/Script.md` | Full file | Source material for chapter parsing and shot generation |
| Skill prompt | `.claude/skills/visual-orchestrator/prompts/generation.md` | Full file | Schema definition, granularity rules, building block vocabulary, anti-patterns |

## Process

1. **[HEURISTIC] Read inputs** — Load Script.md and prompts/generation.md into context
2. **[HEURISTIC] Parse chapter structure** — Identify chapters by `## N. Title` headings; treat any unnumbered prologue section as chapter 0
3. **[HEURISTIC] Generate shots** — For each chapter, identify narrative beats and assign shots following the rules, granularity guidance, and building block vocabulary in prompts/generation.md
4. **[HEURISTIC] Write shotlist.json** — Write the complete shot list to `projects/N. [Title]/shotlist.json`, overwriting any existing file without prompt

## Pipeline-Reset Invariant

`shotlist.json` is the source of truth for the asset pipeline. Any change to `Script.md` — including edits to chapter structure, shot-bearing prose, or scene intent — invalidates the existing `shotlist.json` and requires full regeneration. Downstream artifacts (e.g., acquisition manifests) derived from the shot list are likewise stale and must be rebuilt from the new `shotlist.json`.

There is no partial or chapter-level regeneration in v1.3. All shots are regenerated in a single pass because sequential shot IDs (`S001`, `S002`, ...) are assigned globally across the entire script — chapter-level regeneration would fragment the ID sequence and break downstream referencing.

Re-invoking the skill always regenerates in full. Git history preserves previous versions of `shotlist.json` if rollback is needed.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Shot list | `projects/N. [Title]/shotlist.json` | JSON array of shot objects |

## Deferred

### Out of scope by design

- **Shot duration/timing** — editor's domain (DaVinci Resolve); not determined at acquisition planning stage
- **Camera angles and movement** — not an acquisition pipeline; sourcing decisions only
- **Effects and transitions** — post-production decisions made in the edit
- **Priority/importance scoring** — acquisition gets all shots regardless of perceived importance

### Future enhancements (planned)

- **SHOT-09:** VISUAL_STYLE_GUIDE.md as an additional input for building block vocabulary and type decision tree
- **SHOT-08:** Two-pass generation — annotate narrative beats first, then assign shot types
- **SHOT-10:** Shot density calibration proportional to chapter word count
- Chapter-level regeneration without requiring a full re-run

## Classification

**[HEURISTIC]** — Zero Python. No CLI commands. No pip installs.
