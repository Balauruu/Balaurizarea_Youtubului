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
- `context/channel/STYLE_PROFILE.md` — from the style-extraction skill
- `context/channel/channel.md` — channel DNA

## Output

`projects/N. [Title]/Script.md` — starts with `## 1. [Chapter Title]`, no header or metadata.

Falls back to `.claude/scratch/writer/[topic]/` if no project directory matches.
