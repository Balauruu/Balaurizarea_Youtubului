---
name: style-extraction
description: Extract channel voice and style from reference scripts into a reusable behavioral ruleset. Use this skill when the user wants to extract style, update the style profile, analyze reference scripts, refresh voice rules, or build a writing style guide from existing scripts. Also use when the user says "extract style from scripts", "update the style profile", "analyze reference scripts", "refresh voice rules", or "what does our style look like". This is a [HEURISTIC] skill — zero Python, Claude does all reasoning.
---

# style-extraction

## How It Works

This skill is a [HEURISTIC] skill — zero Python code, no CLI commands. Claude does all reasoning natively. One-shot invocation that reads all scripts in `context/script-references/`, performs a reconstruct pass (if needed) then an extract pass, and writes `context/channel/STYLE_PROFILE.md`.

The skill replaces `context/channel/writting_style_guide.md` entirely. After writing STYLE_PROFILE.md, it auto-wires CLAUDE.md and removes the old guide.

## Workflow

### Step 1: Read all reference scripts

Read every `.md` file in `context/script-references/`. These are the source material. Process all scripts found — no file path arguments needed.

### Step 2: Detect format

For each script, check for auto-caption signals:

- Lines end mid-sentence at word boundaries without punctuation
- Presence of `[Music]`, `[Applause]`, `[Laughter]` tags
- Missing sentence-ending punctuation on most lines
- Inconsistent capitalization mid-sentence (e.g., capitalized word mid-clause)
- Names or places incorrectly transcribed (OCR-style errors)

**Threshold:** If 3+ signals are present, the script is auto-caption format — reconstruction required.

If signals are absent (full paragraph structure, consistent punctuation, lines end at natural sentence breaks) — skip to Step 5.

### Step 3: Reconstruct auto-caption to clean prose (conditional)

If reconstruction is needed:

- Rejoin broken lines into natural sentences
- Restore sentence-ending punctuation
- Strip all bracket tags: `[Music]`, `[Applause]`, `[Laughter]` — pure narration only
- Fix obvious proper noun errors where context makes the correct spelling clear
- Flag uncertain phrases with `[unclear]` — do NOT guess

**Critical constraint:** You are transcribing, not editing. Preserve the narrator's intended phrasing, sentence length variation, and rhythm. Do NOT add conjunctions to merge short sentences. Do NOT smooth irregular rhythm. Do NOT normalize sentence length. The reconstructed version should be minimally different from what a human would transcribe from the audio.

Read the full reconstruction and extraction instructions: `prompts/extraction.md`

Save the clean version as `[Original Title]_clean.md` in `context/script-references/` alongside the original.

### Step 4: Skip reconstruction (if already clean)

If the script already has clean paragraph structure, proceed directly to Step 5 using the original file.

### Step 5: Read the extraction prompt

Read `prompts/extraction.md` in full. This file contains the complete extraction instructions you will follow during Step 6.

### Step 6: Extract from clean script(s)

Using the instructions in `prompts/extraction.md`, extract:

- Universal Voice Rules (tone, syntax, vocabulary — apply to every topic)
- Narrative Arc Templates (chapter structure, pacing — labeled by topic type)
- Transition Phrase Library (10-20 verbatim phrases, categorized by function)
- Open Ending Template (when to use, structure, crafted examples)

Also read `context/channel/channel.md` — know what NOT to duplicate. Identity statements belong in channel.md, not in STYLE_PROFILE.md.

### Step 7: Draft and present for review

Draft the full `STYLE_PROFILE.md` content in memory. Then present a summary to the human:

- List each section heading (H2 and H3)
- Count of named rules in Universal Voice Rules
- Count of verbatim examples used
- Count of transition phrases extracted
- Count of arc templates defined

Wait for human approval before writing the file.

### Step 8: Write STYLE_PROFILE.md (after approval)

Write `context/channel/STYLE_PROFILE.md` with the approved content.

## Post-Write Wiring

After writing STYLE_PROFILE.md, perform these three additional steps:

1. **Update CLAUDE.md Task Routing table:** Add row `| Extract channel voice style | style-extraction | SKILL.md |`
2. **Update CLAUDE.md "What to Load" table:** Change "Script writing (future)" row to add `context/channel/STYLE_PROFILE.md` to the Load column (replacing `writting_style_guide.md`)
3. **Delete `context/channel/writting_style_guide.md`:** Git history is the archive. Do not leave a stale file with a deprecation notice.

## File Locations

| File | Purpose |
|------|---------|
| `context/script-references/*.md` | Input reference scripts (all .md files processed) |
| `context/script-references/[Title]_clean.md` | Reconstructed clean prose (created if input is auto-caption) |
| `context/channel/STYLE_PROFILE.md` | Output: behavioral ruleset |
| `context/channel/channel.md` | Channel DNA — read to avoid duplication |
| `prompts/extraction.md` | Extraction instructions Claude follows during Step 6 |

## Re-Run Behavior

Full overwrite on re-run. Each invocation reads all current scripts in `context/script-references/` and produces a fresh profile from scratch. Previous version is preserved in git history.

To add a new reference script: drop a `.md` file into `context/script-references/` and re-run the skill.
