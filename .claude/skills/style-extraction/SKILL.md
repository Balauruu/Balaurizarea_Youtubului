---
name: style-extraction
description: Extract channel voice and style from reference scripts into a reusable behavioral ruleset. Use this skill when the user wants to extract style, update the style profile, analyze reference scripts, refresh voice rules, or build a writing style guide from existing scripts. Also use when the user says "extract style from scripts", "update the style profile", "analyze reference scripts", "refresh voice rules", or "what does our style look like". This is a [HEURISTIC] skill — zero Python, Claude does all reasoning.
---

# style-extraction

## How It Works

This skill is a [HEURISTIC] skill — zero Python code, no CLI commands. Claude does all reasoning natively. One-shot invocation that reads all scripts in `channel/scripts/`, performs a reconstruct pass (if needed) then an extract pass, and writes `channel/voice/WRITTING_STYLE_PROFILE.md`.

## Workflow

### Step 1: Read all reference scripts

Read every `.md` file in `channel/scripts/`. These are the source material. Process all scripts found — no file path arguments needed.

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

Save the clean version as `[Original Title]_clean.md` in `channel/scripts/` alongside the original.

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

Also read `channel/channel.md` — know what NOT to duplicate. Identity statements belong in channel.md, not in WRITTING_STYLE_PROFILE.md.

### Step 7: Draft and present for review

Draft the full `WRITTING_STYLE_PROFILE.md` content in memory. Then present a summary to the human:

- List each section heading (H2 and H3)
- Count of named rules in Universal Voice Rules
- Count of verbatim examples used
- Count of transition phrases extracted
- Count of arc templates defined

Wait for human approval before writing the file.

### Step 8: Write WRITTING_STYLE_PROFILE.md (after approval)

Write `channel/voice/WRITTING_STYLE_PROFILE.md` with the approved content.

## Checkpoints

| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 7 | Summary: section headings, count of named rules, count of verbatim examples, count of transition phrases, count of arc templates | Approve (Claude writes file) or request changes (Claude revises draft) |

## File Locations

| File | Purpose |
|------|---------|
| `channel/scripts/*.md` | Input reference scripts (all .md files processed) |
| `channel/scripts/[Title]_clean.md` | Reconstructed clean prose (created if input is auto-caption) |
| `channel/voice/WRITTING_STYLE_PROFILE.md` | Output: behavioral ruleset |
| `channel/channel.md` | Channel DNA — read to avoid duplication |
| `prompts/extraction.md` | Extraction instructions Claude follows during Step 6 |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Behavioral ruleset | `channel/voice/WRITTING_STYLE_PROFILE.md` | Markdown with 4 mandatory sections |
| Clean reconstruction | `channel/scripts/[Title]_clean.md` | Plain markdown prose (only created if input is auto-caption) |

## Re-Run Behavior

Full overwrite on re-run. Each invocation reads all current scripts in `channel/scripts/` and produces a fresh profile from scratch. Previous version is preserved in git history.

To add a new reference script: drop a `.md` file into `channel/scripts/` and re-run the skill.
