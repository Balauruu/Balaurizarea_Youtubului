# Phase 15: Skill Entry Point - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Write SKILL.md for the visual-orchestrator skill and update CLAUDE.md routing — making the skill discoverable and invocable. This is a documentation phase that produces SKILL.md and edits CLAUDE.md. No Python code, no new prompts.

</domain>

<decisions>
## Implementation Decisions

### SKILL.md Structure
- Shot-list focused frontmatter: trigger phrases include "create shot list", "generate shotlist", "parse script into shots", "visual plan for [topic]", "shotlist for [topic]"
- Numbered step workflow (3 steps): Step 1 resolve project, Step 2 read inputs, Step 3 generate + write
- Includes Prerequisites section listing Script.md and generation.md
- Includes Output section: one-liner stating path and format, notes overwrite-without-prompt behavior

### VISUAL_STYLE_GUIDE Handling
- **Completely skipped in v1.3** — no scan, no disambiguation, no placeholder logic
- Success criteria SC2 (handle multiple VISUAL_STYLE_GUIDE.md files) is **removed** — deferred entirely to SHOT-09
- Amended success criteria: SC1 (3-step workflow) and SC3 (CLAUDE.md routing) only

### CLAUDE.md Updates (Full Scope)
- **Task Routing table**: Replace "not yet implemented" row with visual-orchestrator entry
- **What to Load table**: Replace "Visual planning (future)" row with v1.3 reality — load CONTEXT.md, generation.md, projects/N/Script.md; skip visual-references/ (SHOT-09), competitors/, channel.md
- **Folder Map**: Add visual-orchestrator to the skills tree
- **Pipeline Skills table**: Add visual-orchestrator as Agent 1.4 with purpose "Script → structured shot list"
- **Stage Contracts convention note**: Verify it still holds (no update expected)

### Project Resolution
- Topic substring match against projects/ directory names (case-insensitive), matching writer skill convention
- Multiple matches: list all matching directories, ask user which one
- No match: error with guidance

### Error Handling
- Missing Script.md: stop with clear error message and guidance to run the writer skill first
- No fallback to .claude/scratch/ — visual-orchestrator requires a proper project directory

### Claude's Discretion
- Exact wording of SKILL.md prose between the structural decisions above
- How to phrase the project resolution logic in Step 1
- Formatting of CLAUDE.md table entries

</decisions>

<specifics>
## Specific Ideas

- Follow writer/SKILL.md and style-extraction/SKILL.md as structural templates (frontmatter, workflow steps, prerequisites, output)
- SKILL.md description must state "Requires a completed Script.md in the project directory"
- Error message for missing Script.md should suggest the writer skill invocation phrase

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `writer/SKILL.md`: Direct template — numbered workflow, prerequisites section, output section, CLI context-loader pattern (adapted to no-CLI for visual-orchestrator)
- `style-extraction/SKILL.md`: Alternate template — zero-code heuristic skill with numbered steps, longer workflow
- `visual-orchestrator/CONTEXT.md`: Already complete — defines inputs, process, outputs, pipeline-reset invariant
- `visual-orchestrator/prompts/generation.md`: Already complete — schema, building blocks, rules, anti-patterns

### Established Patterns
- Skill frontmatter uses `name` and `description` fields
- Description includes trigger phrases for skill discovery
- [HEURISTIC] classification stated in description or body
- Prerequisites list upstream skill outputs as dependencies

### Integration Points
- `CLAUDE.md` Task Routing table — row 8 placeholder "Create shot list | not yet implemented"
- `CLAUDE.md` What to Load table — row 6 placeholder "Visual planning (future)"
- `CLAUDE.md` Folder Map — missing visual-orchestrator entry under skills/
- `CLAUDE.md` Pipeline Skills table — missing visual-orchestrator row

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

VISUAL_STYLE_GUIDE disambiguation (original SC2) explicitly deferred to SHOT-09.

</deferred>

---

*Phase: 15-skill-entry-point*
*Context gathered: 2026-03-15*
