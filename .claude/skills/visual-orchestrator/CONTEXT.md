# Visual Orchestrator Skill — Stage Contract

**Phase:** 14 — Visual Orchestrator Agent
**Skill:** visual-orchestrator
**Type:** [HEURISTIC] — Reasoning done by Claude; CLI is thin stdlib context-loader only

---

## Inputs

| File | Source | Required |
|------|--------|----------|
| `projects/N. [Title]/Script.md` | writer skill | Yes |
| `context/visual-references/[Guide Name]/VISUAL_STYLE_GUIDE.md` | visual-style-extractor skill | Yes |
| `context/channel/channel.md` | project context | Yes |

---

## Process

1. **CLI aggregation** (`python -m visual_orchestrator load "[topic]"`)
   - Resolves project directory by case-insensitive substring match on `projects/`
   - Reads Script.md, VISUAL_STYLE_GUIDE.md, channel.md
   - Prints labeled context package to stdout
   - Prints output path (`shotlist.json`) and generation prompt path
   - Optional `--guide` flag selects a specific VISUAL_STYLE_GUIDE (default: first found)

2. **Claude reads generation prompt** (`.claude/skills/visual-orchestrator/prompts/generation.md`)
   - shotlist.json schema with field descriptions and valid types
   - Type Selection Decision Tree application rules (paragraph-by-paragraph processing)
   - Segment granularity guidance (group by narrative beat, target 60-100 shots)
   - Sequencing constraints as post-generation self-check
   - Text overlay handling (R002: include text_content, no asset generation)

3. **Claude generates shotlist.json**
   - Processes Script.md paragraph by paragraph
   - Applies VISUAL_STYLE_GUIDE's decision tree to select building blocks
   - Assigns shotlist_type for downstream routing
   - Populates text_content for text_overlay entries
   - Validates sequencing constraints before finalizing

4. **Claude writes shotlist.json** to the output path using the Write tool

5. **Validation** (`python -m visual_orchestrator validate "[topic]"`)
   - Reads shotlist.json and runs schema validation
   - Checks required fields, valid enums, ID format, text_content rules
   - Checks sequencing constraints (no back-to-back glitch, max 3 consecutive text, etc.)
   - Exits 0 on success, 1 with structured error list on failure

---

## Checkpoints

**Automated:** Run `python -m visual_orchestrator validate "[topic]"` after generation. Fix any schema or sequencing violations.

**Human review:** Review `shotlist.json` for visual quality and narrative coverage. Schema validation proves contract compliance, not creative quality.

---

## Outputs

| File | Location | Description |
|------|----------|-------------|
| `shotlist.json` | `projects/N. [Title]/shotlist.json` | Ordered shot array with building block assignments |

shotlist.json format:
- Top-level: `project`, `guide_source`, `generated`, `shots` array
- Each shot: `id`, `chapter`, `chapter_title`, `narrative_context`, `visual_need`, `building_block`, `shotlist_type`
- Optional: `building_block_variant`, `text_content` (required for text_overlay), `suggested_sources`
- Six valid shotlist_types: `archival_video`, `archival_photo`, `animation`, `map`, `text_overlay`, `document_scan`

---

## Deferred

- **VISUAL-01:** Multi-guide blending when multiple VISUAL_STYLE_GUIDEs exist
- **VISUAL-02:** Shot duration estimation based on narrative pacing
- **VISUAL-03:** Automatic decision tree ambiguity resolution (currently: specificity wins, quotes take precedence)
