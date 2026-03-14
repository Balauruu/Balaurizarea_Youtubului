# Pitfalls Research

**Domain:** Style Extraction and Script Generation — Agentic Documentary Pipeline (v1.2 "The Writer")
**Researched:** 2026-03-14
**Confidence:** HIGH (based on direct analysis of the existing codebase, the reference script at `context/script-references/`, Architecture.md constraints, and established patterns for prompt-driven LLM pipelines)

---

## Critical Pitfalls

### Pitfall 1: Style Extraction Implemented as NLP Code Instead of a Prompt

**What goes wrong:**
The style extraction skill gets implemented as deterministic Python: sentence-length counters, readability scores (Flesch-Kincaid), vocabulary frequency tables, regex-based transition phrase extraction. The code ships, it produces numbers, and those numbers are useless to the Writer because they describe surface statistics rather than the actual narrative craft patterns that make the channel's voice distinctive. The STYLE_PROFILE.md ends up full of "average sentence length: 14.2 words" instead of "sentences fragment mid-thought at moments of revelation to force a beat before the next clause."

**Why it happens:**
Style analysis feels like a data problem — you have text, you want to quantify it. Developers default to code for anything that involves processing text files. The Architecture.md classification rule (HEURISTIC vs. DETERMINISTIC) is the explicit guard against this, but the temptation is strong because NLP code looks objective.

**How to avoid:**
Style extraction is entirely [HEURISTIC]. The deliverable is a prompt file that Claude reads against the reference scripts. No code written. The prompt should ask for:
- Sentence rhythm pattern (how clauses are assembled, where they break)
- Chapter opening conventions (how scenes are entered — environment, character, event)
- Tension-building technique (what the narrator withholds vs. reveals and when)
- Vocabulary register (clinical, journalistic, conversational — with specific examples)
- Structural template (act count, act function, pacing ratio between exposition and tension)
- Explicit prohibitions (what the reference scripts never do)

The output (STYLE_PROFILE.md) is a writing brief with examples, not a statistics report.

**Warning signs:**
- A Python file named `style_extractor.py` or similar is created.
- The STYLE_PROFILE.md contains numerical metrics without prose examples.
- The profile describes what the text IS (sentence count) rather than how it WORKS (narrative function).

**Phase to address:** Phase 1 (Style Extraction Skill Design). Classify before touching a keyboard. If the classification comes out DETERMINISTIC, that is a classification error, not a code opportunity.

---

### Pitfall 2: The Generated Script Loses Channel Voice Within the First Chapter

**What goes wrong:**
The script generation prompt provides the research dossier, the STYLE_PROFILE.md, and channel DNA — and the Writer still produces generic documentary narration. Sentences like "This case shocked the nation" and "Let us examine the events that unfolded." The voice is competent but indistinct. It sounds like Wikipedia read aloud, not the channel's clinical deadpan that lets facts deliver their own horror.

**Why it happens:**
LLMs default to the mode of "competent documentary narrator" when given research + generic style instructions. The style profile needs to be specific enough to override the LLM's prior. Vague instructions ("be neutral and journalistic") are already the LLM's default — they add nothing. What breaks the default is concrete behavioral rules with examples pulled from the actual reference scripts.

**How to avoid:**
The synthesis prompt for script generation must include:
- Three or four verbatim excerpts from the reference script showing the channel's actual voice in action, labeled with what they demonstrate ("Note: revelation withheld until the end of the paragraph — the worst detail comes last").
- Explicit prohibitions extracted from what the reference script never does: no rhetorical questions directed at the audience, no "imagine if you will," no meta-commentary about the documentary itself.
- The channel's specific deadpan device: stating a grotesque fact in the same register as a logistical detail. This must be named and demonstrated, not just described.
- A chapter opener template from the reference script — because chapter openings are where generic narration most reliably creeps in.

**Warning signs:**
- Script chapter 1 opens with a broad historical context paragraph (the LLM's default frame).
- The script uses second-person address ("you might wonder," "consider this").
- Facts are introduced with emotional signposting ("shockingly," "horrifyingly") rather than stated plainly.
- The script reads naturally in isolation but sounds wrong next to the reference script.

**Phase to address:** Phase 1 (Script Generation Prompt Engineering). Build and test the voice constraints before wiring up the full pipeline. Test the prompt against the existing reference topic (The Duplessis Orphans) — if it cannot reconstruct a plausible version of a known documentary topic in the channel's voice, the prompt is not ready.

---

### Pitfall 3: STYLE_PROFILE.md Is Written Once and Never Validated Against New Topics

**What goes wrong:**
The style extraction runs once against "Mexico's Most Disturbing Cult" and produces a STYLE_PROFILE.md. The profile works well for that reference. Then The Duplessis Orphans is scripted — a completely different topic (Canadian institutional abuse vs. Mexican cult) — and the profile's chapter structure template (built on the cult narrative arc) produces a mismatch. The profile says "open with the physical setting and atmosphere" which works for cult content but forces an awkward geography intro onto an institutional corruption story.

**Why it happens:**
A single reference script is a sample of one. Style patterns that are universal to the channel's voice get mixed with patterns specific to that topic's narrative arc. The style profile inherits both without distinguishing them.

**How to avoid:**
- If more than one reference script exists, run style extraction across all of them and derive only the patterns that appear in all references. Topic-specific structural patterns are excluded from STYLE_PROFILE.md.
- Structure STYLE_PROFILE.md with two explicit sections: "Universal Voice Rules" (apply to every script) and "Narrative Arc Templates" (optional templates by story type — cult/group, institutional corruption, disappearance, etc.). The Writer picks the matching template for the topic type.
- The current single reference ("Mexico's Most Disturbing Cult") should be labeled as providing a "cult/group narrative arc template" — not the universal structure template.

**Warning signs:**
- Every generated script begins with an atmospheric physical setting description regardless of topic type.
- The profile has only one chapter structure template with no variation by story type.
- A script about institutional corruption opens with geography or weather (borrowed from the cult reference).

**Phase to address:** Phase 1 (Style Extraction Design). Acknowledge the single-reference limitation upfront. Design the profile format to accommodate multiple arc templates. Flag in STYLE_PROFILE.md which sections are "universal voice" vs. "one reference script only."

---

### Pitfall 4: Research.md → Script Handoff Loses Narrative Hooks

**What goes wrong:**
Agent 1.2 (The Researcher) produces Research.md with a narrative-first structure that includes explicit HOOK and QUOTE callouts. Agent 1.3 (The Writer) reads the file but treats it as a fact database — pulling timeline events and key figures while ignoring the callouts. The script that results is factually complete but lacks the "hook quality" that makes the channel's content work. The best quotes end up buried in chapter 4. The most disturbing contradiction never surfaces.

**Why it happens:**
The Writer's synthesis prompt focuses on "convert research into a script" and the LLM interprets that as "organize the facts into chapters." The narrative tension signals embedded in the research dossier are not referenced in the writing prompt, so they get ignored.

**How to avoid:**
The Writer's synthesis prompt must explicitly instruct how to use Research.md's structure:
- "The HOOK callout in Research.md is the story's entry point — build the introduction around it, do not bury it in chapter 2."
- "QUOTE callouts are primary source moments — they anchor the chapter they appear in, not summarize it."
- "The 'unanswered_questions' section is the documentary's engine — each one should either drive a chapter's tension or be withheld as the final revelation."
- "The 'contradictions' section provides the points of unease. Use them where the narration needs to shift register."

The handoff is not a file path. It is a structured reading instruction.

**Warning signs:**
- Script introduction is a broad historical overview rather than the Research.md HOOK.
- The most impactful quote from Research.md appears late or is paraphrased rather than quoted directly.
- Script chapters map to timeline sections rather than narrative tension arcs.

**Phase to address:** Phase 2 (Script Generation Prompt Engineering — Research Integration). The reading instructions for Research.md belong in the synthesis prompt, not in a comment or readme.

---

### Pitfall 5: LLM API Wrapper Introduced for "Script Quality" Evaluation

**What goes wrong:**
After the Writer produces a script, a temptation arises to add automated quality evaluation: "does this sound like the channel?" The solution proposed is a second LLM call using the Anthropic SDK to score the script against the style profile. Code is written. An `@anthropic-ai/sdk` or `anthropic` Python import appears. This violates Architecture.md Rule 1 (ZERO LLM API WRAPPERS) and breaks the pipeline's foundational design.

**Why it happens:**
Quality evaluation feels like it needs another "agent" — and the reflex is to implement agents as API calls. The architecture rule is explicit, but when building iteratively it is easy to rationalize "just one evaluation call." The violation compounds: once one API wrapper exists, the pattern propagates.

**How to avoid:**
Script quality evaluation is [HEURISTIC] and belongs to Claude Code natively. After the Writer produces the script:
1. Claude reads the output script and STYLE_PROFILE.md in the same session.
2. Claude performs the quality check using its native reasoning.
3. If the script fails the check, Claude revises in-context or flags specific sections for re-generation.

No Python code evaluates script quality. No API calls. The runtime IS the evaluator.

**Warning signs:**
- Any file in the writer skill directory imports `anthropic`, `openai`, or any LLM SDK.
- A `evaluate_script.py` or `score_voice.py` script is created.
- The SKILL.md mentions "API call" in the quality check step.

**Phase to address:** Phase 1 (Architecture Classification). Before writing any writer code, classify every step. Evaluation = HEURISTIC = no code.

---

### Pitfall 6: Script Generation Prompt Tries to Enforce Structure Through Formatting Rules Alone

**What goes wrong:**
The script generation prompt instructs the Writer to "produce 4-7 chapters, each 600-900 words, with a chapter title on its own line followed by the narration." The LLM complies with the format but not the narrative logic — chapters are split at arbitrary word count thresholds rather than natural tension breaks. Chapter 3 ends mid-revelation because the word count was hit. Chapter 5 is mostly recap filler because there was quota to fill.

**Why it happens:**
Formatting constraints are easier to specify than narrative logic constraints. Developers reach for word counts and structural templates because those are measurable. But for narrative content, format compliance is not quality.

**How to avoid:**
Chapter boundaries must be defined by narrative logic, not word count:
- "Each chapter ends when a new question is introduced or a revelation is made — not before."
- "A chapter may be 300 words if the narrative beat is complete, or 1,200 words if the tension arc requires it."
- Provide the channel's chapter function template from the reference script: Intro (hook + thesis), Act 1 (establish world), Act 2 (introduce threat), Act 3 (escalation), Act 4 (peak horror), Act 5 (aftermath/open question).
- Word count targets belong in the SKILL.md as a post-generation check ("if total script word count is outside 3,000-7,000 words, flag for review") — not as a constraint inside the generation prompt.

**Warning signs:**
- Chapters end at suspiciously similar word counts (600-900 words each, uniformly).
- A chapter's final sentence does not complete a narrative thought — it trails.
- The script has uniform chapter lengths regardless of topic complexity.

**Phase to address:** Phase 2 (Script Generation Prompt Engineering — Chapter Structure). Specify narrative logic constraints before formatting constraints. Test with the Duplessis Orphans research dossier and verify chapter breaks land on narrative beats.

---

### Pitfall 7: STYLE_PROFILE.md Becomes a Living Document That Drifts

**What goes wrong:**
After the first script is generated, the user edits the script manually (natural — they are the creator). The style extraction skill gets re-run to "update the profile" based on the edited script. Then a second reference script is added to `context/script-references/`. The profile is updated again. After three scripts, STYLE_PROFILE.md contains contradictory rules because each update layered new observations without reconciling them with the old. The Writer receives a profile that says "keep sentences short" in section 2 and "use long, subordinate-clause-heavy sentences for historical exposition" in section 5.

**Why it happens:**
Style profiles are tempting to maintain continuously. Each new reference or manual edit feels like new signal to incorporate. There is no reconciliation step.

**How to avoid:**
- STYLE_PROFILE.md is a versioned artifact, not a living document. It is regenerated from scratch when new reference material warrants it — never patched in-place.
- Style extraction runs only on scripts that are explicitly marked as "reference quality" in `context/script-references/`. Not on drafts, not on generated output.
- Each STYLE_PROFILE.md regeneration includes a reconciliation step: "Does any rule in the new profile contradict a rule in the previous profile? If so, which takes precedence and why?" The answer is written into the profile explicitly.
- Version the profile: `STYLE_PROFILE_v1.md`, `STYLE_PROFILE_v2.md`. The Writer's SKILL.md specifies which version to load.

**Warning signs:**
- STYLE_PROFILE.md contains contradictory instructions with no resolution.
- The profile has been edited in-place more than twice.
- Generated scripts produce inconsistent voice quality across topics even when research quality is consistent.

**Phase to address:** Phase 1 (Style Extraction Design). Design the versioning and regeneration policy before the first profile is written.

---

### Pitfall 8: Writer Skill Reads Too Much Context, Degrades Output

**What goes wrong:**
The Writer's invocation loads: Research.md (2,000+ words), ResearchArchive.md (5,000+ words), STYLE_PROFILE.md (1,500+ words), channel.md (1,000+ words), the full reference script (5,000+ words as few-shot example), and past_topics.md. Total context load: 15,000+ words before any script generation begins. The LLM's output quality degrades in the latter chapters because attention is distributed across too many inputs. Chapter 5 is measurably worse than Chapter 2 because the context is saturated.

**Why it happens:**
The instinct is "more context = better output." Each file seems individually justified. The aggregate cost is not considered until the degradation appears in output.

**How to avoid:**
The Writer loads a curated context package, not everything available:
- Research.md (curated dossier, target 2,000 words) — required.
- STYLE_PROFILE.md — required, but trimmed to the sections most relevant to this topic type.
- A single verbatim excerpt from the reference script (the intro + one full chapter), not the full script. The excerpt demonstrates voice; the full script is not needed.
- channel.md executive summary only (first 200 words), not the full file.
- Past topics: not needed at script generation time. Deduplication happens upstream.

The ResearchArchive.md is available for targeted lookups (specific dates, quotes) but is not loaded into the generation context by default.

**Warning signs:**
- SKILL.md instructs the Writer to load more than four files at script generation time.
- Chapter quality is inconsistent across the script (early chapters richer than late chapters).
- Generation prompt includes the full text of a reference script rather than a curated excerpt.

**Phase to address:** Phase 2 (Writer Context Engineering). Define the exact context package before writing the generation prompt. Test with a token count estimate and verify it stays under 8,000 words of total context.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Implementing style extraction as Python NLP code | Feels objective, ships fast | Produces statistics, not craft insight; useless to the Writer | Never — this is a HEURISTIC task |
| Single STYLE_PROFILE.md with no versioning | Simpler file management | Profile drifts and contradicts itself after second reference added | Never |
| Loading all research files into Writer context | Maximum information | Context saturation degrades chapter quality in second half of script | MVP only — define a curated context package before v1 ships |
| Formatting constraints (word count per chapter) as quality gate | Easy to measure | Chapters split on word count thresholds, not narrative beats | Never for content quality; acceptable as a secondary range check only |
| One narrative arc template for all topic types | Simpler STYLE_PROFILE.md | Cult arc template forces wrong structure onto institutional corruption topics | MVP only if only one topic type is planned |
| Writing research integration instructions in readme rather than synthesis prompt | Keeps the prompt "clean" | Writer ignores HOOK callouts and narrative signals in Research.md | Never — instructions belong in the prompt the Writer uses |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Research.md → Writer handoff | Passing the file path; Writer treats it as a fact dump | Pass a structured reading instruction in the synthesis prompt specifying how each Research.md section maps to script structure |
| STYLE_PROFILE.md → Writer handoff | Loading the full profile verbatim in every generation | Load only the sections relevant to the topic type; trim universal rules to the five most constraining ones |
| Reference script as few-shot example | Including the full reference script in the Writer's context | Include intro + one chapter only as a verbatim voice example; label what it demonstrates |
| Style extraction timing | Running style extraction once at project start and treating it as permanent | Re-run from scratch when new reference scripts are added; version the output |
| channel.md in Writer context | Loading the full channel.md file | Load executive summary only (voice, tone, audience in 200 words); the Writer does not need competitive analysis or pipeline docs |
| Script output location | Writing to `.claude/scratch/` | Write to `projects/N. [Video Title]/Script.md` — it is a first-class production artifact, not a scratch file |

---

## "Looks Done But Isn't" Checklist

- [ ] **Style profile is craft-oriented:** STYLE_PROFILE.md contains behavioral rules with verbatim examples from the reference script — not statistical summaries. Verify no Flesch-Kincaid scores or sentence-length averages appear.
- [ ] **Voice persists to the end:** Read the generated script's final chapter. Verify the channel's deadpan register is intact — it should not drift into summary mode or emotional signposting in the closing act.
- [ ] **Narrative hooks are used:** Cross-reference the Research.md HOOK callout against the script introduction. Verify the hook is the entry point, not buried in chapter 2.
- [ ] **No LLM API imports:** Search for `import anthropic`, `from anthropic`, `import openai`, `from openai` in all writer skill scripts. Any match is a violation.
- [ ] **Chapter breaks are narrative:** Read chapter boundaries — the last sentence of each chapter should complete a thought or land a revelation. Verify no chapter ends mid-sentence or mid-argument because a word count threshold was hit.
- [ ] **Script word count is in range:** Total script word count should fall between 3,000 and 7,000 words. Outside this range, flag for review before the script moves to visual orchestration.
- [ ] **Context package is bounded:** Count the total words loaded into the Writer's context at generation time. It should not exceed 8,000 words across all input files.
- [ ] **Output path is correct:** Script.md lands in `projects/N. [Video Title]/` — not in `.claude/scratch/` or the researcher's output directory.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Style profile contains statistics, not craft rules | LOW | Delete profile; re-run extraction with corrected HEURISTIC prompt; no code changes needed |
| Generated script loses channel voice | LOW | Revise synthesis prompt with stronger voice constraints and verbatim examples; re-generate |
| Style profile has contradictory rules | MEDIUM | Re-run full extraction from scratch against all reference scripts; reconcile conflicts explicitly in the new profile |
| Research.md hooks ignored in script | LOW | Add explicit reading instructions to synthesis prompt; re-generate script |
| LLM API wrapper introduced | MEDIUM | Remove all API wrapper code; re-classify the task as HEURISTIC; rebuild the evaluation step as a Claude Code in-session check |
| Context saturation degrades chapter quality | LOW | Define and enforce the curated context package; re-generate with trimmed inputs |
| Script output written to wrong location | LOW | Update SKILL.md output path; move existing output to correct directory |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Style extraction as NLP code (Pitfall 1) | Phase 1: Skill Design — classify as HEURISTIC before any code is written | No `.py` file created for style extraction; STYLE_PROFILE.md contains craft rules with examples |
| Script loses channel voice (Pitfall 2) | Phase 1: Script Generation Prompt Engineering | Run pilot against Duplessis Orphans research; compare voice against reference script excerpt |
| Single-reference profile generalizes badly (Pitfall 3) | Phase 1: Style Extraction Design | STYLE_PROFILE.md distinguishes "universal voice rules" from "topic arc template" |
| Research hooks lost in handoff (Pitfall 4) | Phase 2: Writer Prompt — Research Integration | Script introduction uses Research.md HOOK callout; best quotes anchor chapters, not summaries |
| LLM API wrapper introduced (Pitfall 5) | Phase 1: Architecture Classification | `grep -r "import anthropic\|import openai"` on writer skill directory returns no results |
| Formatting constraints override narrative logic (Pitfall 6) | Phase 2: Script Generation Prompt Engineering | Chapter breaks fall on narrative beats; chapter lengths vary based on act complexity |
| STYLE_PROFILE.md drifts with in-place edits (Pitfall 7) | Phase 1: Style Extraction Design | Profile is versioned; no in-place edits after generation; regeneration policy documented in SKILL.md |
| Context saturation degrades output (Pitfall 8) | Phase 2: Writer Context Engineering | Context package defined and word-count-budgeted; tested with token estimate before generation |

---

## Sources

- Direct analysis: `context/script-references/Mexico's Most Disturbing Cult.md` — existing reference script showing actual channel voice patterns
- Direct analysis: `Architecture.md` — Rule 1 (zero LLM API wrappers), Rule 2 (HEURISTIC vs. DETERMINISTIC classification)
- Direct analysis: `context/channel/channel.md` — channel DNA, voice rules, audience profile
- Direct analysis: `.claude/skills/researcher/SKILL.md` — existing Research.md schema and HOOK/QUOTE callout conventions
- Direct analysis: `.planning/PROJECT.md` — v1.2 milestone goals, existing key decisions log
- Known pattern: LLM attention degradation in long-context generation — documented in multiple long-context benchmarks (RULER, InfiniteBench) showing quality drop in second half of long-form outputs under high input load
- Known pattern: LLM default to "competent but generic" documentary mode without strong behavioral constraints — observed in GPT-4 and Claude creative writing evaluations; overridden by verbatim examples and explicit prohibitions, not by vague style descriptors
- Known pattern: Style profiles as statistics vs. craft rules — failure mode documented in automated readability research showing Flesch-Kincaid and similar metrics do not predict perceived quality or voice distinctiveness

---

*Pitfalls research for: Style Extraction and Script Generation (v1.2 "The Writer") — documentary video production pipeline*
*Researched: 2026-03-14*
