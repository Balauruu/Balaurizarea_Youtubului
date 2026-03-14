# style-extraction — Stage Contract

Extract channel voice from reference scripts into a reusable behavioral ruleset at `context/channel/STYLE_PROFILE.md`.

## Inputs

| Source | File/Location | Scope | Why |
|--------|--------------|-------|-----|
| Reference scripts | `context/script-references/*.md` | All .md files | Source material for voice and arc extraction |
| Channel DNA | `context/channel/channel.md` | Full file | Avoid duplicating identity statements in STYLE_PROFILE.md |
| Extraction prompt | `prompts/extraction.md` | Full file | Step-by-step instructions for reconstruction and extraction passes |
| Existing rules | `context/channel/writting_style_guide.md` | Full file | 6 rules to absorb and expand (first run only; deleted after) |

## Process

1. **[HEURISTIC] Read scripts** — Load all `.md` files from `context/script-references/`
2. **[HEURISTIC] Detect format** — Check each script for auto-caption signals (broken lines, bracket tags, missing punctuation). Threshold: 3+ signals = reconstruction required
3. **[HEURISTIC] Reconstruct (conditional)** — If auto-caption: rejoin lines, restore punctuation, strip `[Music]`/`[Applause]` tags, flag uncertain phrases `[unclear]`. Save as `[Title]_clean.md`. Preserve narrator phrasing — do NOT paraphrase or smooth rhythm
4. **[HEURISTIC] Extract** — Following `prompts/extraction.md`: extract Universal Voice Rules, Narrative Arc Templates, Transition Phrase Library, Open Ending Template from clean script(s)
5. **[HEURISTIC] Draft profile** — Produce complete STYLE_PROFILE.md draft in memory

## Checkpoints

| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 5 | Summary: section headings, count of named rules, count of verbatim examples, count of transition phrases, count of arc templates | Approve (Claude writes file) or request changes (Claude revises draft) |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Behavioral ruleset | `context/channel/STYLE_PROFILE.md` | Markdown with 4 mandatory sections |
| Clean reconstruction | `context/script-references/[Title]_clean.md` | Plain markdown prose (only created if input is auto-caption) |

## Post-Write Actions

After writing STYLE_PROFILE.md (performed automatically after human approval):

| Action | Detail |
|--------|--------|
| Update CLAUDE.md routing | Add `style-extraction` row to Task Routing table |
| Update CLAUDE.md load table | Replace `writting_style_guide.md` with `STYLE_PROFILE.md` in Script writing row |
| Delete old style guide | Remove `context/channel/writting_style_guide.md` (git history is the archive) |

## Classification

**[HEURISTIC]** — Zero Python. No CLI commands. No pip installs. Claude does all reasoning natively using built-in language understanding.
