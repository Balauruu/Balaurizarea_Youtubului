# Phase 11: Style Extraction Skill - Research

**Researched:** 2026-03-14
**Domain:** HEURISTIC prompt engineering — voice/style extraction from reference scripts into behavioral ruleset
**Confidence:** HIGH

## Summary

Phase 11 creates a zero-code heuristic skill that reads reference scripts from `context/script-references/`, reconstructs auto-captions into clean prose, and extracts a behavioral ruleset into `context/channel/STYLE_PROFILE.md`. The skill replaces `context/channel/writting_style_guide.md` as the single source of truth for channel voice and style.

The skill is pure Claude reasoning — no Python, no API calls. It follows the established project pattern: SKILL.md defines invocation, CONTEXT.md defines the stage contract, and all work is done via Claude's built-in capabilities. The classification is [HEURISTIC] per Architecture.md Rule 2.

The primary challenge is extracting durable, reusable behavioral rules from a single auto-caption source that covers one narrative arc type (cult story). The profile must explicitly separate universal voice rules from topic-specific arc templates so future Writer invocations on non-cult topics are not over-constrained.

**Primary recommendation:** Build a two-pass skill (reconstruct then extract) that produces a STYLE_PROFILE.md with four mandatory sections: Universal Voice Rules, Narrative Arc Templates, Transition Phrase Library, and Open Ending Template — each illustrated with verbatim examples from the reference script.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Reference Script Processing**
- Skill includes a "reconstruct" first pass — Claude cleans auto-captions into proper prose before extracting style patterns
- Cleaned version saved to `context/script-references/` alongside original (e.g., `[Title]_clean.md`)
- Skill should detect format — only reconstruct auto-captions, skip already-clean scripts
- Strip all bracket tags (`[Music]`, `[Applause]`) during reconstruction — pure narration text only

**Profile Structure**
- Each voice rule follows: Rule definition → Do-this examples (verbatim from script) → Not-this counter-examples (generated)
- Include sentence rhythm analysis with examples — short/long patterns, paragraph cadence, emotional beat shifts
- STYLE_PROFILE.md replaces `writting_style_guide.md` entirely — single source of truth for voice and style
- Existing 6 rules from writting_style_guide.md get absorbed and expanded into the new profile
- Transition phrase library: 10-20 phrases, categorized by function (temporal, causal, contrast, escalation)

**Invocation & Workflow**
- One-shot with review: Claude reads all scripts in `context/script-references/`, does reconstruct + extract passes, writes STYLE_PROFILE.md, presents summary for human review before committing
- Processes all scripts in the directory — no file path arguments needed
- Full overwrite on re-run — each invocation produces a fresh profile from all current scripts (previous version in git history)
- Auto-wire: after writing STYLE_PROFILE.md, skill updates CLAUDE.md routing table and removes/archives `writting_style_guide.md`

**Narrative Arc Templates**
- Capture structure + pacing patterns: chapter count range, act progression (setup→escalation→resolution), pacing rules, chapter connections
- "Truth-Seeking Coda" captured as optional/conditional pattern — when topic has widespread misinformation, end with a chapter confronting it
- Dedicated "Open Ending Template" section with: when to use (unsolved cases), structure (present evidence → acknowledge unknowns → leave weight with audience), crafted examples in channel voice
- Hook pattern extracted: quote opening → compressed story overview → "this is the true story of…" formula — captured as reusable but flexible template

### Claude's Discretion
- Exact number and naming of voice rules (extracted from analysis, not predetermined)
- How to structure the format detection (auto-captions vs clean scripts)
- Internal organization of STYLE_PROFILE.md beyond the required sections
- How to handle edge cases in rhythm analysis

### Deferred Ideas (OUT OF SCOPE)
- Multi-reference blending (REFINE-03) — future requirement, not Phase 11 scope
- Automated style drift detection between generated scripts and profile — future quality gate
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STYLE-01 | Skill extracts voice and tone rules from reference scripts in `context/script-references/` | Confirmed: reference script at `context/script-references/Mexico's Most Disturbing Cult.md` (496 lines, auto-caption format). Voice patterns are identifiable: deadpan neutrality, factual escalation without editorializing, clinically neutral delivery of horror. |
| STYLE-02 | Skill extracts chapter structure patterns (count, pacing, act progression) | Confirmed: reference script has 7 numbered chapters (Intro + 6 titled chapters). Chapter titles use evocative register ("Strangers in the Jungle", "Initial Control", "Willing Sacrifices"). Act progression is setup → escalation → confrontation → truth-seeking coda. |
| STYLE-03 | Skill extracts sentence rhythm and length patterns with verbatim examples | Confirmed: script exhibits alternating short declarative sentences with longer contextual sentences. Pattern visible even in auto-caption format — standalone lines like "the scam allowed them to extract many more resources from the villagers than they were willing to spare" vs short beats. |
| STYLE-04 | Skill separates universal voice rules from topic-specific arc templates | Confirmed: the "Truth: 2024" meta-commentary chapter is clearly a topic-specific pattern (misinformation debunking). Hook formula ("it was the worst thing…" + "this is the true story of…") may be universal. Explicit separation is required to prevent cult-arc overfitting. |
| STYLE-05 | Skill outputs `context/channel/STYLE_PROFILE.md` as a reusable channel-level artifact | Confirmed: output path is `context/channel/STYLE_PROFILE.md`. Joins `channel.md` and `past_topics.md` at the same tier. Consumed by Phase 12 Writer as primary style context. |
</phase_requirements>

---

## Standard Stack

### Core

| Component | Version/Format | Purpose | Why Standard |
|-----------|----------------|---------|--------------|
| SKILL.md | Markdown | Invocation instructions for Claude | Established project pattern (channel-assistant, researcher, visual-style-extractor all use this) |
| CONTEXT.md | Markdown | Stage contract: Inputs, Process, Checkpoints, Outputs | Project convention per Architecture.md |
| prompts/extraction.md | Markdown | Extraction instructions Claude follows during invocation | Separates prompt logic from skill documentation |
| `context/channel/STYLE_PROFILE.md` | Markdown | Output artifact | Channel-level context, same tier as channel.md |

### No Dependencies

This skill has zero Python dependencies, zero pip installs, zero CLI commands. Classification is [HEURISTIC] — Claude does all reasoning natively. This is an intentional architectural constraint from Architecture.md Rule 2.

---

## Architecture Patterns

### Skill Directory Structure

```
.claude/skills/style-extraction/
├── SKILL.md           # Invocation guide (what user says, what Claude does)
├── CONTEXT.md         # Stage contract (Inputs, Process, Checkpoints, Outputs)
└── prompts/
    └── extraction.md  # Step-by-step extraction instructions
```

This matches the project's established heuristic skill pattern. The `visual-style-extractor` is a hybrid (Python + heuristic). The `channel-assistant` is the closest analog for the heuristic portions (topic generation). For a fully heuristic skill with no Python at all, `extraction.md` contains all reasoning instructions.

### Pattern 1: Two-Pass Processing

**What:** Pass 1 reconstructs raw auto-captions into clean prose. Pass 2 extracts behavioral rules from the clean prose.

**When to use:** Always. Auto-caption format (broken lines, `[Music]` tags, missing punctuation) is too noisy for reliable pattern extraction. Reconstruction first produces a higher-fidelity signal.

**Detection heuristic for Pass 1:**
```
Auto-caption signals (reconstruct needed):
- Lines end mid-sentence (wrapped at ~8-12 words)
- Presence of [Music], [Applause], [Laughter] tags
- Missing sentence-ending punctuation on most lines
- Inconsistent capitalization mid-sentence

Clean script signals (skip reconstruction):
- Full paragraph structure
- Consistent punctuation
- Lines end at natural sentence breaks
```

### Pattern 2: STYLE_PROFILE.md Mandatory Sections

**What:** The output file must have four separable sections that downstream Writer can load selectively.

**Required sections:**
1. `## Universal Voice Rules` — tone, syntax, vocabulary, what NOT to do. Apply to every topic.
2. `## Narrative Arc Templates` — chapter structure, pacing, act progression. Labeled with topic type applicability.
3. `## Transition Phrase Library` — verbatim phrases from reference, categorized by function.
4. `## Open Ending Template` — when to use, structure, crafted examples in channel voice.

**Optional sections (Claude's discretion):**
- `## Hook Patterns` — opening formulas extracted from reference
- `## Chapter Naming Register` — evocative vs descriptive titling examples
- `## Sentence Rhythm Patterns` — short/long alternation with annotated examples

### Pattern 3: Rule Format

**What:** Each voice rule entry follows a three-part structure.

```markdown
### Rule N: [Rule Name]

**Definition:** [What the rule requires]

**Do this:**
> [Verbatim example from reference script]
> [Second verbatim example if available]

**Not this (generic documentary narration):**
> [Generated counter-example showing what to avoid]
```

**Why:** The counter-example is critical. Generic documentary narration ("furthermore, it is notable that…") is the failure mode the Writer must avoid. Showing the contrast makes the rule actionable, not just descriptive.

### Pattern 4: Invocation Workflow

**What:** One-shot with a human review checkpoint before file writes.

```
Step 1: Claude reads context/script-references/ (all .md files)
Step 2: Detect format (auto-caption vs clean)
Step 3: If auto-caption → reconstruct to clean prose in memory
         Save clean version as [Title]_clean.md
Step 4: Extract rules, arc templates, transition phrases, open ending template
Step 5: Draft STYLE_PROFILE.md
Step 6: Present summary to human (section headings + rule count + phrase count)
Step 7: Human approves → Claude writes STYLE_PROFILE.md
Step 8: Auto-wire: update CLAUDE.md routing table + archive writting_style_guide.md
```

### Anti-Patterns to Avoid

- **Extracting statistics instead of rules:** "Average sentence length: 14 words" is useless. "Alternate short declarative beats with longer contextual sentences" is actionable.
- **Duplicating channel.md:** STYLE_PROFILE.md is style mechanics, not channel identity. Don't repeat the "calm, journalistic, deadpan" identity statements — translate them into syntactic rules.
- **Over-constraining non-cult topics:** Labeling arc templates with applicability scope prevents the cult story's 7-chapter structure from being applied to, e.g., a missing person case.
- **Using generic examples for counter-examples:** Counter-examples should specifically represent the failure mode (emotional inflation, intensifiers, clickbait framing) — not just any different text.
- **Skipping the reconstruction pass:** Extracting rhythm patterns from broken auto-caption lines produces false rhythm signals. The fragmented line breaks are an artifact of the caption format, not the narrator's intended phrasing.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Style extraction | Python NLP/spaCy metrics | Claude heuristic reasoning | REQUIREMENTS.md Out of Scope — LLM reasoning is more effective than statistical analysis for this task |
| Profile storage | Database or structured JSON | Plain Markdown | Consumed by Writer as context, not queried programmatically |
| Rule validation | Automated scorer | Human review checkpoint | REQUIREMENTS.md Out of Scope — word count gates and quality scoring deferred to human review |
| Multi-script blending | Weighted averaging | Single-script per invocation | REFINE-03 is deferred; current scope is one script at a time |

---

## Common Pitfalls

### Pitfall 1: Auto-Caption Rhythm Artifacts

**What goes wrong:** Rhythm analysis performed on the raw auto-caption file produces false patterns. The lines are broken every 8-12 words by the caption renderer, not by the narrator's intended phrasing. Short "sentences" are actually mid-sentence line breaks.

**Why it happens:** Auto-captions are formatted for display, not for reading. The reference script (`Mexico's Most Disturbing Cult.md`) is in this format — lines like "the small indigenous farming community" end mid-phrase.

**How to avoid:** The reconstruction pass must come first. Rhythm analysis only runs on `[Title]_clean.md`, not the original.

**Warning signs:** If extracted "short sentences" are under 5 words and numerous, the source is being read as auto-captions.

### Pitfall 2: Cult-Arc Overfitting

**What goes wrong:** Every Narrative Arc Template is labeled as the standard arc, then Phase 12 Writer applies the cult story's 7-chapter structure (setup → escalation → willing sacrifices → murders → raid → aftermath → truth-seeking coda) to a missing person disappearance.

**Why it happens:** The profile has only one reference script — a cult story. Without explicit applicability labels, templates appear universal.

**How to avoid:** Every arc template in `## Narrative Arc Templates` must carry an applicability tag: e.g., `[Cult / Group Radicalization]`, `[Conspiracy / Cover-up]`, `[Unsolved Disappearance]`. The "Truth-Seeking Coda" must be marked explicitly `[Optional — when widespread misinformation exists]`.

**Warning signs:** Profile contains no applicability labels on arc templates.

### Pitfall 3: Duplicating channel.md

**What goes wrong:** STYLE_PROFILE.md repeats identity statements from channel.md ("calm, journalistic, deadpan tone") without translating them into actionable syntax rules.

**Why it happens:** The extraction prompt describes voice in the same terms channel.md does — resulting in a paraphrase, not an extension.

**How to avoid:** Every rule in `## Universal Voice Rules` must be syntactic or mechanical — not a tone descriptor. "Use declarative sentences with no modal qualifiers on factual claims" is syntactic. "Be calm and journalistic" is not.

**Warning signs:** Rules read like adjective descriptions ("neutral", "clinical") rather than do/don't instructions.

### Pitfall 4: Reconstruction Destroys Style

**What goes wrong:** When reconstructing auto-captions into clean prose, Claude over-normalizes sentence structure — adding conjunctions, smoothing rhythm, making every sentence a similar length. The reconstructed version loses the original pacing.

**Why it happens:** LLM tendency to produce grammatically "correct" output that deviates from the source's intended rhythm.

**How to avoid:** Reconstruction instructions must emphasize: preserve the narrator's intended phrasing, restore punctuation, strip artifacts — do NOT paraphrase or improve. The reconstructed version should be minimally different from what a human would transcribe from the audio.

**Warning signs:** Reconstructed version has noticeably more uniform sentence lengths than the original would suggest.

### Pitfall 5: Missing the Open Ending Template

**What goes wrong:** STYLE_PROFILE.md does not include a concrete template for open endings — only a general instruction like "leave the audience with the weight of not knowing." Phase 12 Writer generates artificial resolution for an unsolved case.

**Why it happens:** Open endings are harder to template than structured arcs. The extraction prompt may not force a concrete structural template to be generated.

**How to avoid:** Explicitly require the Open Ending Template to include: trigger condition (unsolved case), three-part structure (present evidence → acknowledge unknowns → leave weight), and at least one crafted example in channel voice.

---

## Code Examples

No code is produced in this phase. Verified patterns from the reference script:

### Hook Pattern (from reference script, lines 1-14 reconstructed)

```
[Opening quote from a source — direct speech, past tense]
[Compressed scene-setting: location, year, what happened next in 2 sentences]
[Scale statement: what the story became]
[Misinformation note: "the internet has been telling the story incorrectly…" — optional]
"This is the true story of [subject] and [what drove the story]."
```

### Chapter Title Register (from reference script)

```
Evocative register (USE):
- "Strangers in the Jungle"
- "Initial Control"
- "Willing Sacrifices"
- "Truth: 2024"

Descriptive register (AVOID):
- "Chapter 1: The Arrival of the Twins"
- "Background on Spiritism"
- "The Murder Sequence"
```

### Transition Phrase Categories (to be extracted in full during skill invocation)

Function categories to populate from reference:
- **Temporal:** phrases that advance time within a chapter
- **Causal:** phrases that link action to consequence
- **Contrast/Revelation:** phrases that flip expectation
- **Escalation:** phrases that signal stakes rising
- **Evidential:** phrases that introduce sourcing or testimony

### Auto-Caption Format Detection

```
Signals for auto-caption format:
1. Lines end at word boundaries without punctuation
2. Presence of [Music], [Applause] tags
3. Numbered chapter headings appear mid-file without preceding blank lines
4. Names and places are sometimes incorrectly transcribed (OCR-style errors)
   e.g., "yba bua" vs "Yibá Bua", "alizar" vs "Elizar"

Signal threshold: if 3+ signals present → reconstruct pass required
```

---

## Existing 6 Rules Absorption Plan

The existing `context/channel/writting_style_guide.md` has 6 rules that must be absorbed and expanded:

| Existing Rule | Absorption Action |
|---------------|------------------|
| No clickbait inflation | Expand to: specific vocabulary banned (intensifiers list), specific syntax allowed (declarative factual claims) |
| Script is narration only | Absorbed into Universal Voice Rules — add examples of what "host commentary" looks like to avoid |
| Chapters structure the story | Absorbed into Narrative Arc Templates — expand with extracted chapter count ranges and pacing rules |
| Sources are sacred | Absorbed into Universal Voice Rules — add syntax pattern for how to label speculation vs fact |
| Pacing through silence | Expand to: specific sentence rhythm patterns that create pause, short-sentence beat after heavy information |
| Open endings are valid | Expand to: the full Open Ending Template section with structure and examples |

---

## Integration Points

### CLAUDE.md Routing Table Updates Required

After STYLE_PROFILE.md is written, the skill must update CLAUDE.md:

1. Add row to "Task Routing" table: `| Extract channel voice style | style-extraction | SKILL.md |`
2. Update "Script writing (future)" row in "What to Load" table: add `context/channel/STYLE_PROFILE.md` to Load column
3. Archive `context/channel/writting_style_guide.md` (move to `.claude/scratch/` or delete with git history as backup)

### Phase 12 Dependency

Phase 12 (Writer Agent) consumes STYLE_PROFILE.md as primary style context. The `## Universal Voice Rules` and `## Transition Phrase Library` sections are the highest-priority inputs. The Writer should load STYLE_PROFILE.md before generating any narration.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual review — no automated tests (HEURISTIC classification) |
| Config file | None — heuristic skill |
| Quick run command | Invoke skill, inspect STYLE_PROFILE.md output sections |
| Full suite command | Run style-extraction skill, then run Phase 12 Writer on Duplessis Orphans Research.md, compare output to STYLE_PROFILE.md rules |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STYLE-01 | STYLE_PROFILE.md contains Universal Voice Rules section with named rules and verbatim examples | manual | Inspect `context/channel/STYLE_PROFILE.md` — count named rules, verify verbatim quotes present | ❌ Wave 0 |
| STYLE-02 | STYLE_PROFILE.md contains Narrative Arc Templates section with chapter count and act progression | manual | Inspect `## Narrative Arc Templates` section — verify chapter range, arc structure, applicability labels | ❌ Wave 0 |
| STYLE-03 | STYLE_PROFILE.md contains sentence rhythm patterns with verbatim examples from reference | manual | Inspect rhythm subsection — verify short/long pattern described with actual script quotes | ❌ Wave 0 |
| STYLE-04 | Universal Voice Rules section is separable from Narrative Arc Templates section | manual | Confirm two distinct H2 sections exist; confirm Universal section contains no cult-specific content | ❌ Wave 0 |
| STYLE-05 | `context/channel/STYLE_PROFILE.md` exists after skill invocation | manual | `ls context/channel/STYLE_PROFILE.md` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** Inspect STYLE_PROFILE.md sections after writing
- **Per wave merge:** Full manual review — read STYLE_PROFILE.md end-to-end, verify all 4 mandatory sections present and populated
- **Phase gate:** STYLE_PROFILE.md reviewed and approved by human before Phase 12 planning begins

### Wave 0 Gaps

- [ ] `context/channel/STYLE_PROFILE.md` — does not exist yet; created by this phase
- [ ] `context/script-references/Mexico's Most Disturbing Cult_clean.md` — clean reconstruction; created during skill invocation
- [ ] `.claude/skills/style-extraction/` directory — does not exist; created by this phase
- [ ] `.claude/skills/style-extraction/SKILL.md` — invocation instructions
- [ ] `.claude/skills/style-extraction/CONTEXT.md` — stage contract
- [ ] `.claude/skills/style-extraction/prompts/extraction.md` — extraction prompt

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 6-rule placeholder in writting_style_guide.md | Full behavioral ruleset with verbatim examples + counter-examples | Phase 11 | Writer has actionable syntax patterns, not vague adjectives |
| No arc templates | Labeled arc templates separable by topic type | Phase 11 | Non-cult topics not forced into cult story structure |
| No transition phrase library | 10-20 categorized verbatim phrases | Phase 11 | Writer uses channel-authentic connective language |

**Deprecated/outdated:**
- `context/channel/writting_style_guide.md`: Replaced by STYLE_PROFILE.md; archived after Phase 11

---

## Open Questions

1. **What if the reconstructed clean script loses phrasing accuracy?**
   - What we know: Auto-caption errors include proper noun misspellings and broken phrases
   - What's unclear: Whether the reconstruction pass can reliably restore narrator intent without source audio
   - Recommendation: Reconstruction prompt should instruct Claude to flag any phrase it is uncertain about with `[unclear]` — human can review before extraction pass

2. **One reference script is a cult topic — how broadly applicable will Universal Voice Rules be?**
   - What we know: STATE.md explicitly flags this as a known blocker: "STYLE_PROFILE.md coverage will be limited to one narrative arc type until a second reference is added"
   - What's unclear: Whether the voice rules (tone, syntax) are stable across topic types even if arc templates are not
   - Recommendation: Extraction prompt should instruct Claude to distinguish rules that are clearly independent of topic type (syntax, vocabulary) from rules that might be arc-specific

3. **How should writting_style_guide.md be archived?**
   - What we know: Git history preserves it regardless. CLAUDE.md should stop pointing to it.
   - What's unclear: Whether to delete the file or leave it with a deprecation notice
   - Recommendation: Delete the file (git history is the archive) and update CLAUDE.md routing table in the same commit. Cleaner than a stale file with a deprecation notice.

---

## Sources

### Primary (HIGH confidence)

- `context/script-references/Mexico's Most Disturbing Cult.md` — 496-line reference script (auto-caption format); direct inspection of voice patterns, chapter structure, hook formula
- `context/channel/channel.md` — Channel DNA; defines voice identity that STYLE_PROFILE.md translates into syntax rules
- `context/channel/writting_style_guide.md` — 6 existing rules to be absorbed
- `.claude/skills/researcher/CONTEXT.md` — Stage contract pattern (Inputs/Process/Checkpoints/Outputs) used as template for CONTEXT.md
- `.claude/skills/channel-assistant/SKILL.md` — Established SKILL.md format and heuristic skill pattern
- `.planning/phases/11-style-extraction-skill/11-CONTEXT.md` — All locked decisions verified directly

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — STYLE-01 through STYLE-05 requirements and Out of Scope constraints
- `.planning/STATE.md` — v1.2 decisions including single-script limitation acknowledgment
- `CLAUDE.md` — Project conventions: heuristic vs deterministic classification, skill structure, routing table

### Tertiary (LOW confidence)

- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no external dependencies; all patterns from existing project codebase
- Architecture: HIGH — directly derived from locked decisions in CONTEXT.md and established project skill patterns
- Pitfalls: HIGH — confirmed from direct inspection of reference script format and project constraints
- Validation: HIGH — manual review appropriate for heuristic skill; automated testing not applicable

**Research date:** 2026-03-14
**Valid until:** Stable — no external dependencies, no library versions to expire. Re-research only if a second reference script is added (triggers REFINE-03 scope) or if Architecture.md Rule 2 changes.
