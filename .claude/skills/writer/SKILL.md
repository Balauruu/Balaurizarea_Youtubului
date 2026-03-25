---
name: writer
description: Generate narrated documentary scripts from research dossiers. Use this skill when the user wants to write a script, generate narration, turn research into a documentary script, or says things like "write the script for [topic]", "generate script", "create narration". Requires a completed research dossier (Research.md) in the project directory.
---

# Writer Skill

Research dossier → narrated chapter script. Pure prose, read aloud as-is.

## Workflow

1. Load context:
   ```bash
   PYTHONPATH=.claude/skills/writer/scripts python -m writer load "[topic]"
   ```
   Topic is a case-insensitive substring match against `projects/` directory names.

2. Read the generation prompt: `.claude/skills/writer/prompts/generation.md`

3. Generate the script following the prompt instructions. Write to the output path printed by the CLI.

## Prerequisites

- `projects/N. [Title]/research/Research.md` — from the researcher skill
- `channel/voice/WRITTING_STYLE_PROFILE.md` — from the style-extraction skill
- `channel/channel.md` — channel DNA

## Output

`projects/N. [Title]/script/Script.md` — starts with `## 1. [Chapter Title]`, no header or metadata.

Script format:
- Starts directly with `## 1. [Chapter Title]`
- No header, metadata, table of contents, bullet points, stage directions, or production notes
- Chapter titles use evocative register (what it feels like), not descriptive (what happens)
- 4–7 chapters, 3,000–7,000 words total

Falls back to `.claude/scratch/writer/[topic]/` if no project directory matches.

## Checkpoints

**Human review:** After generation, review `Script.md` via `git diff`. No automated review gate. Chapter-level revision deferred to REFINE-01.

## Deferred

- **REFINE-01:** Chapter-level iteration without full regeneration
- **REFINE-02:** Word count adjustment to hit target runtime
- **REFINE-03:** Multi-reference style blending when multiple script references exist
