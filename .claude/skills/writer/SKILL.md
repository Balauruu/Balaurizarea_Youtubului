# Writer Skill

**Agent:** Writer
**Purpose:** Generate narrated chapter scripts from research dossiers

---

## Prerequisites

Before invoking this skill, verify:

1. Project has `research/Research.md` (produced by the researcher skill)
2. `context/channel/STYLE_PROFILE.md` exists (produced by style-extraction skill)
3. `context/channel/channel.md` exists

---

## Invocation Workflow

### Step 1: Load context

```bash
PYTHONPATH=.claude/skills/writer/scripts python -m writer load "[topic]"
```

Replace `[topic]` with the topic string that matches the project directory (e.g. `"Duplessis Orphans"`). The CLI performs a case-insensitive substring match against `projects/` directory names.

The command prints:
- Research Dossier (full Research.md content)
- Style Profile (full STYLE_PROFILE.md content)
- Channel DNA (full channel.md content)
- Output path: `projects/N. [Title]/Script.md`
- Generation prompt path: `.claude/skills/writer/prompts/generation.md`

### Step 2: Read the generation prompt

Read `.claude/skills/writer/prompts/generation.md`. This prompt contains all script-writing instructions: hook formula, HOOK/QUOTE rules, chapter structure, all 5 Universal Voice Rules, output format constraints, and the Open Ending Template.

### Step 3: Generate Script.md

Following the generation prompt instructions:
- Open with the 4-part hook formula
- Derive chapter structure from Research.md content (not from arc templates unless topic is cult/group radicalization)
- Apply all 5 Universal Voice Rules throughout
- Write 4–7 chapters (soft guardrail), targeting 3,000–7,000 words total
- Apply Open Ending Template if the topic qualifies

### Step 4: Write Script.md

Write the completed script to the output path printed in Step 1. Use the Write tool. Do not print to stdout.

---

## Output

```
projects/N. [Title]/Script.md
```

Script starts directly with `## 1. [Chapter Title]` — no header, no metadata, no table of contents.

---

## Fallback Behavior

If no matching project directory is found, the CLI falls back to `.claude/scratch/writer/[topic]/`. The script will be written there. Research.md must still exist at that location.
