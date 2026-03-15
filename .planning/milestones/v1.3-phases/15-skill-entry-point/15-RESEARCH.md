# Phase 15: Skill Entry Point - Research

**Researched:** 2026-03-15
**Domain:** Documentation authoring — SKILL.md and CLAUDE.md edits
**Confidence:** HIGH

## Summary

Phase 15 is a pure documentation phase. No Python code, no prompts, no new schema. The deliverables are two file edits: (1) create `.claude/skills/visual-orchestrator/SKILL.md`, and (2) update `CLAUDE.md` with four targeted changes. All structural decisions were locked in the context session and no external library research is required.

The SKILL.md must follow the established `writer/SKILL.md` pattern: YAML frontmatter with trigger phrases, a numbered 3-step workflow, a Prerequisites section, and an Output section. Because visual-orchestrator is a zero-code heuristic skill, Step 1 cannot use a CLI command — project resolution is described in prose instead. This is the only structural departure from the writer template.

The CLAUDE.md edits are surgical: replace two placeholder rows in existing tables, add one line to the Folder Map, and add one row to the Pipeline Skills table. The Stage Contracts convention note requires no change.

**Primary recommendation:** Model SKILL.md directly on `writer/SKILL.md` for structure; the sole deviation is replacing the `python -m writer load` CLI step with inline prose describing substring project resolution. Then execute the four CLAUDE.md edits as a single coordinated task.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**SKILL.md Structure**
- Shot-list focused frontmatter: trigger phrases include "create shot list", "generate shotlist", "parse script into shots", "visual plan for [topic]", "shotlist for [topic]"
- Numbered step workflow (3 steps): Step 1 resolve project, Step 2 read inputs, Step 3 generate + write
- Includes Prerequisites section listing Script.md and generation.md
- Includes Output section: one-liner stating path and format, notes overwrite-without-prompt behavior

**VISUAL_STYLE_GUIDE Handling**
- Completely skipped in v1.3 — no scan, no disambiguation, no placeholder logic
- Success criteria SC2 (handle multiple VISUAL_STYLE_GUIDE.md files) is removed — deferred entirely to SHOT-09
- Amended success criteria: SC1 (3-step workflow) and SC3 (CLAUDE.md routing) only

**CLAUDE.md Updates (Full Scope)**
- Task Routing table: Replace "not yet implemented" row with visual-orchestrator entry
- What to Load table: Replace "Visual planning (future)" row with v1.3 reality — load CONTEXT.md, generation.md, projects/N/Script.md; skip visual-references/ (SHOT-09), competitors/, channel.md
- Folder Map: Add visual-orchestrator to the skills tree
- Pipeline Skills table: Add visual-orchestrator as Agent 1.4 with purpose "Script → structured shot list"
- Stage Contracts convention note: Verify it still holds (no update expected)

**Project Resolution**
- Topic substring match against projects/ directory names (case-insensitive), matching writer skill convention
- Multiple matches: list all matching directories, ask user which one
- No match: error with guidance

**Error Handling**
- Missing Script.md: stop with clear error message and guidance to run the writer skill first
- No fallback to .claude/scratch/ — visual-orchestrator requires a proper project directory

### Claude's Discretion
- Exact wording of SKILL.md prose between the structural decisions above
- How to phrase the project resolution logic in Step 1
- Formatting of CLAUDE.md table entries

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
VISUAL_STYLE_GUIDE disambiguation (original SC2) explicitly deferred to SHOT-09.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-03 | CLAUDE.md updated with visual-orchestrator task routing and context loading entries | Four specific edits to CLAUDE.md identified; exact current placeholder text located (lines 63 and 74); new content fully specified in CONTEXT.md decisions |
</phase_requirements>

## Standard Stack

### Core
| Artifact | Format | Purpose | Authority |
|----------|--------|---------|-----------|
| SKILL.md | Markdown with YAML frontmatter | Skill discovery and invocation instructions | writer/SKILL.md establishes the template |
| CLAUDE.md | Markdown tables | Project-wide routing and context loading | Existing file; four surgical edits |

No libraries, packages, or installs. This phase is documentation only.

## Architecture Patterns

### Existing Skill Frontmatter Pattern
All SKILL.md files in this project use the same YAML frontmatter structure:

```yaml
---
name: [skill-name]
description: [One or two sentences + trigger phrases. Classification if [HEURISTIC].]
---
```

The `style-extraction` skill sets the model for heuristic-only frontmatter:
> "This is a [HEURISTIC] skill — zero Python, Claude does all reasoning."

The `writer` skill omits the classification from frontmatter but states it implicitly through the CLI step. Since visual-orchestrator has no CLI, the [HEURISTIC] classification should appear explicitly in the description, matching `style-extraction`.

### Writer SKILL.md Structure (Direct Template)

```
--- frontmatter ---
# [Skill Name]

[One-liner tagline]

## Workflow
1. [Step 1: load/resolve]
2. [Step 2: read prompt file]
3. [Step 3: generate + write]

## Prerequisites
- [upstream output file]
- [config/prompt file]

## Output
[path and format, one line. Re-run behavior.]
```

### Key Deviation: No CLI in Step 1

`writer/SKILL.md` Step 1 uses:
```bash
PYTHONPATH=.claude/skills/writer/scripts python -m writer load "[topic]"
```

`visual-orchestrator` has zero Python. Step 1 must describe project resolution in prose:
- Case-insensitive substring match against `projects/` directory names
- Multiple matches → list them, ask user to specify
- No match → error, instruct user to check spelling or use `cmd_init_project`
- Found → read `projects/N. [Title]/Script.md`; if missing → stop and tell user to run the writer skill first

### CLAUDE.md Edit Map

All four changes are localized and non-overlapping:

| Location | Current Text | New Text |
|----------|-------------|----------|
| Task Routing table, row 8 | `\| Create shot list \| *(not yet implemented)* \| — \|` | `\| Create shot list \| visual-orchestrator \| SKILL.md invocation \|` |
| What to Load table, row 6 | `\| Visual planning *(future)* \| visual-references/..., projects/N/script.md \| competitors/, channel.md... \|` | `\| Visual planning \| visual-orchestrator/CONTEXT.md, generation.md, projects/N/Script.md \| visual-references/ (SHOT-09), competitors/, channel.md \|` |
| Folder Map, under skills/ | `crawl4ai-scraper/` is the last skills entry | Add `visual-orchestrator/` line after `writer/` |
| Pipeline Skills table | `writer` is Agent 1.3, last row | Add `visual-orchestrator \| 1.4 \| Script → structured shot list` |

### Anti-Patterns to Avoid

- **Copying style-extraction's multi-step detail:** style-extraction SKILL.md is 108 lines because it documents a complex 8-step detection+reconstruction+extraction workflow. visual-orchestrator's 3-step workflow is simple — keep SKILL.md short (writer is 33 lines; aim for similar length).
- **Adding VISUAL_STYLE_GUIDE references:** CONTEXT.md explicitly says "completely skipped in v1.3." Do not add any mentions of `context/visual-references/` as an input or prerequisite.
- **Fallback to .claude/scratch/:** Writer skill falls back to scratch. visual-orchestrator must not — the CONTEXT.md states it requires a proper project directory.
- **Updating the Stage Contracts note in CLAUDE.md:** CONTEXT.md says "Verify it still holds (no update expected)." The existing text reads correctly for visual-orchestrator. Leave unchanged.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Project resolution wording | Custom new pattern | Match writer skill convention exactly | Consistency across skill docs; users learn one mental model |
| CLAUDE.md table structure | New table format | Edit existing rows in-place | Tables already formatted; row surgery is cleaner than full rewrites |

## Common Pitfalls

### Pitfall 1: Wrong Output Path Capitalization
**What goes wrong:** Writing `projects/N. [Title]/shotlist.json` vs `Script.md` (capital S) — casing must match actual files.
**Why it happens:** Casual documentation drift.
**How to avoid:** Check CONTEXT.md Outputs table — path is `projects/N. [Title]/shotlist.json`.
**Warning signs:** If prerequisites mention `script.md` (lowercase), that's wrong.

### Pitfall 2: Including generation.md Path Incorrectly
**What goes wrong:** Writing the prompt path as `prompts/generation.md` without the skill prefix.
**Why it happens:** Relative paths look cleaner but are ambiguous.
**How to avoid:** Use the full relative path from project root: `.claude/skills/visual-orchestrator/prompts/generation.md`.

### Pitfall 3: CLAUDE.md What to Load Row — Wrong File Names
**What goes wrong:** Listing `SKILL.md` instead of `CONTEXT.md` in the "Load" column of "What to Load."
**Why it happens:** Confusion between the two files. The convention (documented in CLAUDE.md itself) is: "When invoking a skill as an agent, load CONTEXT.md for routing — load SKILL.md only when the user needs usage help."
**How to avoid:** The What to Load entry must list `visual-orchestrator/CONTEXT.md`, not `SKILL.md`.

### Pitfall 4: Overwriting Stage Contracts Convention
**What goes wrong:** Editing the Stage Contracts note because it doesn't mention visual-orchestrator by name.
**Why it happens:** Impulse to make it "complete."
**How to avoid:** The convention is generic by design. No edit needed.

## Code Examples

### SKILL.md Frontmatter (locked structure)
```yaml
---
name: visual-orchestrator
description: Generate structured shot lists from finished documentary scripts. Use this skill when the user wants to create a shot list, generate a shotlist, parse a script into shots, or says things like "create shot list", "generate shotlist", "parse script into shots", "visual plan for [topic]", "shotlist for [topic]". This is a [HEURISTIC] skill — zero Python, Claude does all reasoning. Requires a completed Script.md in the project directory.
---
```

### Step 1 Prose Pattern (project resolution)
Match the writer skill's documented behavior: "Topic is a case-insensitive substring match against `projects/` directory names."

### CLAUDE.md Task Routing Row
```
| Create shot list | visual-orchestrator | SKILL.md invocation |
```

### CLAUDE.md What to Load Row
```
| Visual planning | visual-orchestrator/CONTEXT.md, .claude/skills/visual-orchestrator/prompts/generation.md, projects/N/Script.md | visual-references/ (deferred to SHOT-09), competitors/, channel.md — director needs script + generation rules only |
```

### CLAUDE.md Folder Map Addition
Under `.claude/skills/`:
```
│   │   ├── visual-orchestrator/      # Agent 1.4: Script → structured shot list
```

### CLAUDE.md Pipeline Skills Row
```
| `visual-orchestrator` | 1.4 | Script → structured shot list |
```

## State of the Art

| Old State | Current State | Impact |
|-----------|---------------|--------|
| "Create shot list \| *(not yet implemented)*" | visual-orchestrator skill built (Phases 13-14) | Phase 15 closes the gap |
| "Visual planning *(future)*" | v1.3 inputs are Script.md + generation.md only | Update removes "(future)" qualifier |
| visual-orchestrator absent from Folder Map | Directories exist at `.claude/skills/visual-orchestrator/` | Add to map for discoverability |

## Open Questions

None. All structural decisions are locked in CONTEXT.md. The only open areas (wording of prose passages) are left to Claude's discretion.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none detected at root; tests/ directory exists |
| Quick run command | `pytest -x --tb=short` |
| Full suite command | `pytest --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-03 | CLAUDE.md task routing row added for visual-orchestrator | manual-only | n/a — file content inspection | n/a |
| INFRA-03 | CLAUDE.md What to Load row updated for visual planning | manual-only | n/a — file content inspection | n/a |
| INFRA-03 | SKILL.md exists at correct path with 3-step workflow | manual-only | n/a — file existence + content inspection | ❌ Wave 0 |

**Note:** INFRA-03 is a documentation requirement. There is no automatable test — correctness is verified by reading the files and confirming the success criteria. Nyquist validation applies: reviewer reads SKILL.md and CLAUDE.md at phase close.

### Sampling Rate
- **Per task commit:** Read SKILL.md and changed CLAUDE.md sections to confirm content matches plan
- **Per wave merge:** Confirm all four CLAUDE.md edit locations are updated and SKILL.md is present
- **Phase gate:** Both files readable and correct before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `.claude/skills/visual-orchestrator/SKILL.md` — the file this phase creates (does not exist yet)

## Sources

### Primary (HIGH confidence)
- `writer/SKILL.md` — direct structural template; read in full
- `style-extraction/SKILL.md` — alternate template for heuristic classification wording; read in full
- `visual-orchestrator/CONTEXT.md` — authoritative inputs/outputs/process spec; read in full
- `CLAUDE.md` — current file state, exact placeholder text at lines 63 and 74; read in full
- `15-CONTEXT.md` — all structural decisions locked; read in full

### Secondary (MEDIUM confidence)
- `REQUIREMENTS.md` — confirms INFRA-03 scope and "Pending" status

### Tertiary (LOW confidence)
None.

## Metadata

**Confidence breakdown:**
- SKILL.md structure: HIGH — direct template exists in writer/SKILL.md; all structural decisions locked in CONTEXT.md
- CLAUDE.md edits: HIGH — exact placeholder text identified, exact replacement content specified in CONTEXT.md
- Pitfalls: HIGH — derived from reading existing patterns and noting where drift could occur

**Research date:** 2026-03-15
**Valid until:** Stable — documentation phase with no external dependencies
