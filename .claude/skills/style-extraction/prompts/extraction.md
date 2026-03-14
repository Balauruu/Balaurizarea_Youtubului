# Style Extraction Instructions

Follow these instructions when the style-extraction skill is invoked. You will perform two passes: a conditional reconstruction pass (Pass 1) and an extraction pass (Pass 2).

---

## Pass 1: Reconstruction (Conditional)

### Detect Auto-Caption Format

Before extracting anything, inspect each reference script for these signals:

1. Lines end at word boundaries mid-sentence (no punctuation, wrapped at ~8-12 words)
2. Presence of `[Music]`, `[Applause]`, `[Laughter]` bracket tags
3. Missing sentence-ending punctuation on most lines
4. Inconsistent capitalization mid-sentence (e.g., a capitalized word in the middle of a clause)
5. Names or places incorrectly transcribed (e.g., "yba bua" instead of a proper name, phonetic approximations)

**Threshold:** If 3 or more signals are present, the script is in auto-caption format and reconstruction is required.

**Clean script signals (skip reconstruction):**
- Full paragraph structure
- Consistent punctuation at sentence ends
- Lines end at natural sentence breaks
- No bracket tags

### Reconstruction Rules

If reconstruction is needed, apply these rules in order:

1. **Rejoin broken lines** — Merge lines that continue the same sentence. A new sentence begins only when the prior line ended with punctuation OR the next line starts with an unambiguous new subject.
2. **Restore punctuation** — Add sentence-ending periods, question marks, commas where they are grammatically required. Use the surrounding context to determine placement.
3. **Strip bracket tags** — Remove `[Music]`, `[Applause]`, `[Laughter]`, and any other `[Tag]` notations. These are caption artifacts, not narration.
4. **Fix obvious proper nouns** — Correct clear transcription errors where context makes the correct spelling unambiguous (e.g., place names, known public figures). Do not guess at uncertain names.
5. **Flag uncertain phrases** — Any phrase where you are not confident the wording matches the original audio, mark with `[unclear]`. Do not invent or smooth over uncertainty.

### Critical Reconstruction Constraint

> You are transcribing, not editing. Preserve the narrator's intended phrasing, sentence length variation, and rhythm. Do NOT add conjunctions to merge short sentences. Do NOT smooth irregular rhythm. Do NOT normalize sentence length. A short declarative sentence followed by a long contextual sentence is intentional — do not join them. The reconstructed version should be minimally different from what a human professional transcriber would produce from the audio.

**Warning signs that reconstruction has failed:**
- Reconstructed sentences have noticeably uniform length compared to the source
- Short beats (under 10 words) have been absorbed into surrounding sentences
- The reconstructed version "reads better" in a generic editorial sense

**Save the output** as `context/script-references/[Original Title]_clean.md` alongside the original. All extraction work in Pass 2 is performed on this clean version.

---

## Pass 2: Extraction

Before extracting, read these two files to understand what NOT to include:

- `context/channel/channel.md` — Channel DNA (voice, tone, pillars, audience). Identity statements that already appear here should NOT be duplicated in STYLE_PROFILE.md. Translate them into syntax rules instead.
- `context/channel/writting_style_guide.md` — 6 existing rules to be absorbed and expanded. Do not simply copy them — expand each into the full rule format (see below).

### Existing Rules Absorption

The 6 rules from `writting_style_guide.md` must be absorbed and expanded as follows:

| Existing Rule | Absorption Action |
|---------------|------------------|
| No clickbait inflation | Expand into: specific vocabulary banned (intensifiers, superlatives), specific syntax allowed (declarative factual claims without modal qualifiers). Include a concrete banned words list. |
| Script is narration only | Absorb into Universal Voice Rules. Add examples of what "host commentary" looks and sounds like — so the Writer knows exactly what to avoid. |
| Chapters structure the story | Absorb into Narrative Arc Templates. Expand with extracted chapter count ranges, pacing rules, and inter-chapter connection patterns from the reference script. |
| Sources are sacred | Absorb into Universal Voice Rules. Add the syntactic pattern for labeling speculation vs fact (e.g., how to introduce a claim that is sourced vs one that is inferred). |
| Pacing through silence | Expand into specific sentence rhythm patterns: the short declarative beat after heavy information, the structural pause before a new revelation. Include verbatim examples. |
| Open endings are valid | Expand into the full `## Open Ending Template` section with: trigger condition, three-part structure, and at least one crafted example in channel voice. |

---

## STYLE_PROFILE.md Output Format

Produce a `STYLE_PROFILE.md` file with the following structure. The four sections marked **[MANDATORY]** must always be present. Optional sections are at your discretion based on what the reference script reveals.

---

### [MANDATORY] `## Universal Voice Rules`

**Purpose:** Voice and tone rules that are INDEPENDENT of topic type. These apply when writing about cults, missing persons, conspiracies, or any other topic. No cult-specific content belongs here.

**Rule format — use this for every rule:**

```
### Rule N: [Rule Name]

**Definition:** [A syntactic or mechanical instruction — NOT a tone adjective. Bad: "Be calm". Good: "Use declarative sentences without modal qualifiers on factual claims."]

**Do this:**
> [Verbatim blockquote from the clean reference script — exact words, exact punctuation]
> [Second verbatim example if available — prefer examples from different chapters]

**Not this (generic documentary narration):**
> [A generated counter-example showing the failure mode: emotional inflation, intensifiers, clickbait framing, host commentary, or hedging language that the rule forbids]
```

**Quality test for every rule:** If the definition reads like an adjective ("neutral", "clinical", "calm"), rewrite it as a do/don't instruction. Rules must be syntactic or mechanical, not descriptive.

**Required rule categories to cover (names are yours to choose):**

1. A rule covering vocabulary constraints — banned words/phrases (intensifiers, superlatives, clickbait language) and what replaces them
2. A rule covering narration scope — no host commentary, no fourth-wall breaks, no "stay tuned" construction
3. A rule covering source attribution syntax — how to label sourced claims vs inferred claims vs speculation
4. A rule covering sentence rhythm — short declarative beats after heavy information; short/long alternation patterns
5. Any additional rules extracted from the reference script's patterns

**Sentence rhythm analysis subsection:**

Include a subsection `### Sentence Rhythm Patterns` within Universal Voice Rules. This subsection must:
- Describe the short/long alternation pattern observed in the clean script
- Describe the paragraph cadence (how paragraphs begin and end)
- Describe emotional beat shifts (where does the script pause vs accelerate)
- Include at least 2 verbatim multi-sentence examples showing the rhythm in action

---

### [MANDATORY] `## Narrative Arc Templates`

**Purpose:** Chapter structure and pacing patterns derived from the reference script(s). Every template must carry an applicability tag so the Writer does not apply a cult-story arc to an unrelated topic.

**Required elements:**

1. **Applicability label** on every template — e.g., `[Cult / Group Radicalization]`, `[Conspiracy / Cover-up]`, `[Unsolved Disappearance]`
2. **Chapter count range** — e.g., "6-8 numbered chapters"
3. **Act progression** — e.g., setup → escalation → confrontation → aftermath → coda
4. **Chapter-to-chapter connection patterns** — how does one chapter end and the next begin?
5. **Hook pattern** (extracted from reference, marked as reusable but flexible):
   - Quote opening (direct speech from a source, past tense)
   - Compressed story overview (location, year, what happened next — 2 sentences)
   - Scale or stakes statement
   - Optional: misinformation note ("the internet has been telling this story incorrectly…")
   - Closing formula: "This is the true story of [subject] and [what drove the story]."
6. **Chapter title register:**
   - DO: evocative titles (name what the chapter *feels like*, not what happens)
   - DON'T: descriptive titles (summarize the events)
   - Include examples from the reference script in both columns
7. **"Truth-Seeking Coda" pattern** — mark as `[Optional — when widespread misinformation exists]`. Describe: final chapter confronting the dominant false narrative, what evidence it presents, how it closes.

**Explicit caveat to include at the bottom of this section:**

> "These templates are derived from [N] reference script(s). Topics that do not match the labeled arc types should apply Universal Voice Rules but create their own arc structure from scratch rather than forcing the reference arc onto the new topic."

---

### [MANDATORY] `## Transition Phrase Library`

**Purpose:** 10-20 transition phrases extracted verbatim from the reference script(s). These carry the channel's specific voice — not generic connective language.

**Extraction rule:** Do NOT include generic connective language (furthermore, notably, in addition, however). Only include phrases that carry the channel's specific rhythm or framing. If a phrase could appear in any documentary narration, exclude it.

**Format:**

```
### [Category Name]

Phrases that [describe the function]:

- "[Verbatim phrase]" — [brief usage note: when/why this transition works]
- "[Verbatim phrase]" — [brief usage note]
```

**Required categories (extract phrases for each):**

| Category | Function |
|----------|---------|
| Temporal | Advance time within a chapter |
| Causal | Link action to consequence |
| Contrast / Revelation | Flip expectation or introduce a fact that contradicts what was established |
| Escalation | Signal that stakes are rising |
| Evidential | Introduce sourcing, testimony, or a cited claim |

---

### [MANDATORY] `## Open Ending Template`

**Purpose:** Concrete template for endings where the case is unsolved, ambiguous, or contested. Without this template, the Writer will generate artificial resolution.

**Required elements:**

1. **Trigger condition:** When to use this template (unsolved case, ambiguous resolution, contested evidence — specify exactly)
2. **Three-part structure:**
   - Part 1: Present the final known evidence — what is factually established as of the script's present
   - Part 2: Acknowledge the unknowns — what is missing, disputed, or unresolvable; do not soften
   - Part 3: Leave weight with the audience — one or two sentences that deliver the existential or moral weight without resolving it
3. **At least one crafted example** in channel voice — generated in the channel's extracted style, not verbatim from reference unless a suitable passage exists. The example must not provide artificial resolution, consolation, or a silver lining.

**Anti-pattern to include:**

> "Do NOT provide artificial resolution, consolation, or a 'silver lining' ending. Do NOT close with: 'Though we may never know the full truth, the victims' stories remind us…' or any equivalent that reframes tragedy as lesson. The weight of not knowing must land without relief."

---

### [OPTIONAL] Additional Sections

Include these sections at your discretion, based on what the reference script reveals:

**`## Hook Patterns`** — If the reference script's opening formula is distinctive enough to merit a standalone section (beyond the summary in Narrative Arc Templates), extract it in full with annotated structure.

**`## Chapter Naming Register`** — If the chapter title contrast (evocative vs descriptive) is rich enough in the reference to merit its own section, expand it here with more examples and explicit rules.

**`## Sentence Rhythm Patterns`** — If the rhythm analysis in Universal Voice Rules is insufficient to capture all patterns observed in the reference, add a dedicated section here with extended annotated examples.

---

## Final Instruction

After drafting the complete STYLE_PROFILE.md content, present a summary to the human before writing the file:

```
## Style Profile Draft Ready

**Sections drafted:**
- Universal Voice Rules: [N] named rules, [N] verbatim examples
  - Subsection: Sentence Rhythm Patterns — [N] examples
- Narrative Arc Templates: [N] templates (labeled by topic type)
- Transition Phrase Library: [N] phrases across [N] categories
- Open Ending Template: [N] crafted examples
- Optional sections included: [list or "none"]

**Summary of absorbed existing rules:**
[One line per existing rule: "Rule X: [name] — absorbed as [where it appears in STYLE_PROFILE.md]"]

**Clean reconstruction created:** [Yes — saved as context/script-references/[Title]_clean.md | No — script was already clean]

Approve to write context/channel/STYLE_PROFILE.md, or request changes.
```

**Wait for explicit human approval before writing any files.**
