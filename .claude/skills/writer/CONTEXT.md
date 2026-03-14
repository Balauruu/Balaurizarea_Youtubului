# Writer Skill — Stage Contract

**Phase:** 12 — Writer Agent
**Skill:** writer
**Type:** [HEURISTIC] — Reasoning done by Claude; CLI is thin stdlib context-loader only

---

## Inputs

| File | Source | Required |
|------|--------|----------|
| `projects/N. [Title]/research/Research.md` | researcher skill | Yes |
| `context/channel/STYLE_PROFILE.md` | style-extraction skill | Yes |
| `context/channel/channel.md` | project context | Yes |

---

## Process

1. **CLI aggregation** (`python -m writer load "[topic]"`)
   - Resolves project directory by case-insensitive substring match on `projects/`
   - Reads Research.md, STYLE_PROFILE.md, channel.md
   - Prints labeled context package to stdout
   - Prints output path (`Script.md`) and generation prompt path

2. **Claude reads generation prompt** (`.claude/skills/writer/prompts/generation.md`)
   - All script-writing instructions: hook formula, HOOK/QUOTE rules, chapter structure,
     Universal Voice Rules, output format, Open Ending Template

3. **Claude generates Script.md**
   - Opens with 4-part hook formula
   - Derives chapter structure from Research.md content
   - Applies all 5 Universal Voice Rules
   - 4–7 chapters, 3,000–7,000 words total
   - Applies Open Ending Template if topic qualifies

4. **Claude writes Script.md** to the output path using the Write tool

---

## Checkpoints

**Human review:** After generation, review `Script.md` via `git diff`. No automated review gate in Phase 12. Chapter-level revision deferred to REFINE-01 (future milestone).

---

## Outputs

| File | Location | Description |
|------|----------|-------------|
| `Script.md` | `projects/N. [Title]/Script.md` | Narrated chapter script, pure prose |

Script format:
- Starts directly with `## 1. [Chapter Title]`
- No header, metadata, table of contents, bullet points, stage directions, or production notes
- Chapter titles use evocative register (what it feels like), not descriptive (what happens)

---

## Deferred

- **REFINE-01:** Chapter-level iteration without full regeneration
- **REFINE-02:** Word count adjustment to hit target runtime
- **REFINE-03:** Multi-reference style blending when multiple script references exist
