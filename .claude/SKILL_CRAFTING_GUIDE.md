# Skill Crafting Guide

A living handbook of trusted, tested methods for writing skills that produce reliable, high-quality results. Every principle here has been validated through A/B testing, blind comparison, or production failure analysis — not guesswork.

> **How to use this guide:** Read it before creating or revising a skill. Each section covers a decision you'll face. The principles are general; the examples come from real skills. Add your own findings as you test.

---

## Table of Contents

1. [Core Philosophy](#1-core-philosophy)
2. [Skill Architecture](#2-skill-architecture)
3. [Writing Instructions](#3-writing-instructions)
4. [Code in Skills — When It Helps, When It Hurts](#4-code-in-skills)
5. [Heuristic vs Deterministic Tasks](#5-heuristic-vs-deterministic-tasks)
6. [Quality Gates and Guardrails](#6-quality-gates-and-guardrails)
7. [Evaluation and Scoring Criteria](#7-evaluation-and-scoring-criteria)
8. [Progressive Disclosure](#8-progressive-disclosure)
9. [Testing and Iteration](#9-testing-and-iteration)
10. [Common Failure Modes](#10-common-failure-modes)
11. [Description and Triggering](#11-description-and-triggering)
12. [Environment and Platform](#12-environment-and-platform)
13. [Checklist](#13-checklist)

---

## 1. Core Philosophy

### The skill is a behavioral contract, not a script

A skill doesn't execute — it shapes how the model reasons. The best skills produce consistent, high-quality output by giving the model clear principles and strong examples, not by micromanaging every step.

### Trust the model's reasoning, constrain its judgment

The model is smart. It can evaluate, compare, and decide. Your job is to tell it *what to care about* and *where the boundaries are*, not to write pseudo-code for it to follow.

### Explain the why

The single most impactful thing you can do in a skill is explain **why** a rule exists. "Discard videos under 1,000 views" is a rule. "Discard videos under 1,000 views — channels below this threshold are overwhelmingly AI-generated content farms, which produce slideshow-format videos with no original footage usable in a documentary" is a principle the model can generalize from.

> *"If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag — reframe and explain the reasoning so the model understands why the thing you're asking for is important."*

### Generalize from examples, don't overfit to them

You iterate on a skill using specific test cases, but the skill will be used thousands of times on different inputs. Every rule you add should improve results broadly, not just fix the one case you just tested.

---

## 2. Skill Architecture

### File structure

```
skill-name/
├── SKILL.md           # Required. Main instructions (< 200 lines ideal)
├── prompts/           # Heuristic evaluation criteria, loaded on demand
├── scripts/           # Deterministic tools (Python, bash), executed not read
├── references/        # Domain docs, loaded into context as needed
└── assets/            # Templates, icons, static files used in output
```

### Size targets

| Component | Target | Warning |
|-----------|--------|---------|
| SKILL.md | < 200 lines | > 250 lines: model starts skimming, execution mode kicks in |
| Evaluation prompts | 35-70 lines each | > 100 lines: diminishing returns, becomes a wall of text |
| Total skill (SKILL + prompts) | < 300 lines | > 350: consider splitting into sub-skills or references |

**Tested finding:** A 157-line skill (V3) and a 239-line skill (V5) both produce 94-100% accuracy. A 338-line skill (V4) scores the same in controlled tests but degrades in production because the model shifts behavior when overwhelmed with instructions.

### Keep SKILL.md as the decision tree, not the encyclopedia

SKILL.md should read like a workflow with clear branch points. Detailed evaluation criteria, reference tables, and domain knowledge belong in `prompts/` or `references/`, loaded only when the model reaches that step.

---

## 3. Writing Instructions

### Imperative form, concrete nouns

Write instructions as commands with specific objects. Vague guidance gets vague results.

| ❌ Bad | ✅ Good |
|--------|---------|
| "Process the document appropriately" | "Extract all image URLs from `CrawlResult.media['images']`" |
| "Evaluate the results for quality" | "For each video, answer: does this contain original footage a documentary editor could use?" |
| "Handle edge cases" | "If a YouTube URL returns an error from yt-dlp, the video is dead — drop it from results" |

### Frame evaluation as a role, not a checklist

When the model needs to make judgment calls, frame the task as a role with a clear audience:

> "Write the `description` field as if briefing a video editor: what to look for, approximately where, and why it matters to the documentary."

This produces dramatically better output than "write a description of the video content."

### Ban specific bad outputs by name

If previous runs produced a specific bad pattern, ban it by quoting the exact bad output:

> "The relevance field must never contain 'requires manual review' or 'extracted from source page'. These mean you skipped evaluation."

> "Do not write generic descriptions like 'Long-form content about [topic]' or 'Supporting footage about [topic]'. These are useless to the editor."

This is more effective than positive instructions alone, because it gives the model a concrete pattern to avoid.

### Use tables for classification, prose for reasoning

Tables are excellent for structured decisions (scoring rubrics, source type priority, filter criteria). Prose is better for explaining judgment calls and edge cases. Mix both.

---

## 4. Code in Skills

### ⚠️ The code trap — tested and confirmed

**Finding:** Adding inline code examples to a skill can significantly degrade output quality, even when the code is correct and the instructions are accurate.

**Root cause:** When the model sees code blocks in a skill, it shifts from *reasoning mode* to *execution mode*. Instead of carefully evaluating each item against the skill's criteria, it writes scripts to bulk-process results. This manifests as:
- Identical descriptions across multiple items ("extracted from source page, requires manual review")
- Bulk imports without per-item evaluation
- Skipped heuristic steps to reach the "compile" step faster

**Test data (media-scout skill):**

| Version | Code blocks | Lines | Controlled accuracy | Production quality |
|---------|-------------|-------|--------------------|--------------------|
| V3 | 1 (setup only) | 157 | 94% | Good descriptions, individual evaluation |
| V4 | 8 (inline Python) | 338 | 100% | Lazy bulk imports, generic descriptions |
| V5 | 1 (setup only) | 239 | 100% | Good descriptions, individual evaluation |

V4 and V5 had identical accuracy in controlled tests, but V4 degraded in production while V5 didn't. The only difference: V4 had inline code examples, V5 expressed the same rules as reasoning principles.

### When code belongs in a skill

| Situation | Put code in... | Why |
|-----------|---------------|-----|
| Setup commands (`pip install`, env config) | SKILL.md | One-time, won't trigger execution mode |
| Reusable tools (scraper, validator, converter) | `scripts/` directory | Executed as a black box, not read as instructions |
| Complex data transformations | `scripts/` directory | Deterministic — better as tested code than prose |
| API call patterns, crawl config | `prompts/` as prose | Describe what to do, not how to code it |
| Evaluation/scoring logic | `prompts/` as prose | This is a heuristic task — code kills the reasoning |

### When code hurts

- **Evaluation criteria** — Never express "how to judge quality" as code. The model will execute the code instead of reasoning about quality.
- **Inline Python in workflow steps** — The model treats these as templates to copy-paste, not guidance to reason from. It will run the code even when the situation calls for a different approach.
- **Code that shows iteration patterns** (for loops over results) — Encourages bulk processing instead of individual evaluation.

### The rule of thumb

> If the task requires **judgment**, express it as prose. If the task requires **data transformation**, express it as code in `scripts/`.

---

## 5. Heuristic vs Deterministic Tasks

Before writing any skill section, classify the task:

| Type | Nature | Skill approach |
|------|--------|---------------|
| **[HEURISTIC]** | Requires judgment, evaluation, creative reasoning | Prose instructions, evaluation criteria, role-framing |
| **[DETERMINISTIC]** | Structured data manipulation, file operations, API calls | Code in `scripts/`, clear input/output spec |

**Mark sections explicitly** with `[HEURISTIC]` or `[DETERMINISTIC]` tags. This signals to both the model and human readers what mode of thinking is expected.

### Mixed tasks

Many real tasks are mixed. A web crawl is deterministic (run crawl4ai), but evaluating what images to keep is heuristic. Separate them:

> ❌ "Crawl the page and extract relevant images" (mixed — model will write a script that does both)

> ✅ Step 4: "Crawl source pages via crawl4ai to extract images" (deterministic)
> Step 5: "Evaluate each image individually — is it relevant to the documentary?" (heuristic)

---

## 6. Quality Gates and Guardrails

### Hard filters vs soft evaluation

**Hard filters** are binary rules that don't require judgment. They should be explicit, numbered, and non-negotiable:

> "Discard videos with < 1,000 views (exception: verified survivor personal channels)"

**Soft evaluation** is judgment-based scoring. It should explain the reasoning and give examples of good/bad scores:

> "Score 1 requires ALL of these: the video is primarily about the topic, contains original footage, and comes from a credible producer"

### Budget constraints

When the model tends to over-include, set explicit budgets:

> "Score 1 is rare — reserve it for 3-7 videos maximum per run. If you have 15 Score 1 entries, your threshold is too low."

> "Keep at most 2-3 portraits of any single person — pick the most iconic ones."

These are more effective than qualitative instructions like "be selective" because they give the model a concrete check it can perform.

### Output bans

List specific output patterns that indicate the model skipped its job:

> "Never acceptable as a relevance value: 'requires manual review', 'extracted from source page', 'Image from [domain]'"

> "Never acceptable as a description: 'Long-form content about [topic]', 'Supporting footage about [topic]'"

### Post-hoc validation

Add an audit section that lists checkable conditions the output must satisfy. The model will self-check against these before presenting results:

| Check | Pass Condition |
|-------|---------------|
| No duplicates | No two entries share the same URL |
| No lazy descriptions | Zero entries with banned phrases |
| Budget compliance | Score 1 count ≤ 7 |

---

## 7. Evaluation and Scoring Criteria

### Write scoring rubrics as behavioral descriptions, not just labels

| ❌ Weak rubric | ✅ Strong rubric |
|---------------|-----------------|
| "Score 1: Primary source" | "Score 1: The video is *primarily about the topic* (not just mentioning it), contains *original footage* (not compiled), and comes from a *credible producer* (broadcaster, journalist, survivor)" |
| "Score 3: Supplementary" | "Score 3: Some usable footage but mostly tangential — a 10-minute news clip may have 30 seconds of usable archival footage buried in anchor segments" |

### Include common mis-scoring examples

After the rubric, add "Common mis-scoring to avoid":

> "A biography of the person is NOT a primary source about the events — Score 2 at best"
> "A 100-minute compilation from an unknown channel is NOT a primary source — likely a re-upload"

These negative examples are often more instructive than positive ones.

### Separate discovery from evaluation

In multi-step skills, the model tends to conflate "finding things" with "deciding what's good." Enforce the boundary:

> Step 4: Crawl and collect (deterministic — gather everything)
> Step 5: Deduplicate and filter (heuristic — apply judgment to each item)

If you let the model evaluate during collection, it either includes everything (no filter) or applies judgment inconsistently.

---

## 8. Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — Loaded when skill triggers (< 200 lines ideal)
3. **Bundled resources** — Loaded on demand (prompts, references, scripts)

### When to split content into prompts/references

- **Evaluation criteria** that are topic-specific → `prompts/`
- **Domain knowledge** that doesn't change per run → `references/`
- **The main workflow** → always in SKILL.md

### Reference pointers

When SKILL.md points to a sub-file, be explicit about when and why to read it:

> ✅ "Read `@prompts/youtube_evaluation.md` for scoring criteria and hard filters."

> ❌ "See prompts/youtube_evaluation.md" (no context about when to read it or what's in it)

---

## 9. Testing and Iteration

### The evaluation loop

1. Write a skill draft
2. Create 2-3 realistic test prompts with expected outputs
3. Run the skill on test prompts (with subagents if available)
4. Compare outputs against human reference
5. Identify patterns in failures
6. Revise the skill
7. Re-test on the same prompts + new edge cases
8. Repeat until stable

### Test with human reference data

Create a "golden output" — what you'd want the skill to produce. Then score each version against it. This catches drift that qualitative review misses.

### A/B test structural changes

When you suspect a structural change (like adding code examples) affected quality, test it:
1. Snapshot the current skill version
2. Make the change
3. Run both versions on identical test data using parallel subagents
4. Compare results quantitatively

### Blind comparison

For rigorous evaluation, use blind comparison: give two outputs to an independent evaluator without revealing which skill produced which. This eliminates confirmation bias.

### Watch for overfitting

If you keep tweaking the skill to fix one specific test case, you may be overfitting. After every change, ask: "Would this rule improve results on a *different* topic, or only on this one?"

---

## 10. Common Failure Modes

### The bulk import problem

**Symptom:** The model grabs everything from a source (all images from a Wikipedia page, all videos from a search) and gives them identical or minimal descriptions.

**Cause:** Instructions say "extract images" without specifying that each must be individually evaluated. The model optimizes for completion over curation.

**Fix:** Add a deduplication and relevance gate between collection and output. Explicitly state: "Do not bulk-import. Evaluate each image individually."

### The execution mode shift

**Symptom:** Descriptions become generic, evaluation steps get skipped, the model rushes to compile the final output.

**Cause:** Too many code blocks in the skill. The model shifts from reasoning to executing.

**Fix:** Remove inline code from heuristic sections. Express rules as reasoning principles. Keep code only in `scripts/` or for one-time setup.

### The over-inclusion problem

**Symptom:** Too many results scored as top-tier. Everything is "Score 1" or "High relevance."

**Cause:** Scoring criteria are too vague, or the model doesn't have a budget constraint.

**Fix:** Add budget caps ("max 7 Score 1 entries") and negative examples ("a biography is NOT Score 1").

### The lazy evaluation problem

**Symptom:** Outputs contain "requires manual review" or "Image from [domain]" instead of real descriptions.

**Cause:** The model skipped the evaluation step, treating it as optional.

**Fix:** Explicitly ban lazy output phrases. Add an audit check that catches them.

### The stale dependency problem

**Symptom:** A tool or API that worked during development fails in production (broken URLs, rate limits, encoding errors).

**Cause:** The skill relies on a specific tool behavior that doesn't hold across environments or over time.

**Fix:** Document known failure modes (with workarounds) directly in the skill. Don't assume tools work perfectly.

---

## 11. Description and Triggering

The `description` field in SKILL.md frontmatter is the primary trigger. It determines whether the model invokes the skill.

### Write descriptions slightly "pushy"

The model tends to under-trigger — it won't use skills it could benefit from. Make the description enumerate trigger phrases explicitly:

> ✅ `"Triggers on: 'find media', 'media scout', 'search for images', 'search for footage', 'find visuals for [topic]'"`

### Include both what and when

> ✅ "Media discovery pipeline for documentary video topics. Use this skill when the user wants to find images, photos, documents, or footage for a documentary."

### Test triggering with eval queries

Create 20 test queries (10 should-trigger, 10 should-not-trigger). Focus on edge cases:
- Should-trigger queries that don't use the skill's name
- Should-not-trigger queries that share keywords but need different tools

---

## 12. Environment and Platform

### Document platform-specific fixes

If your skill runs on Windows, macOS, and Linux, document platform differences directly in the skill:

> "On Windows, prefix every Python command with `set PYTHONUTF8=1 && set PYTHONIOENCODING=utf-8`"

Don't assume the model will figure out platform issues on its own. It will try a fix, fail, try another fix, and waste context.

### Pin dependencies

Specify exact versions in setup commands. "pip install crawl4ai" may install a version with breaking changes.

> ✅ `pip install crawl4ai==0.8.0`

### Document known tool limitations

If a dependency has known failure modes, document them upfront:

> "yt-dlp `ytsearch` returns stale video IDs (90% broken in testing). Use crawl4ai for discovery, yt-dlp only for validating known URLs."

This prevents the model from learning the hard way during execution.

---

## 13. Checklist

Use before publishing any skill:

### Structure
- [ ] SKILL.md is under 200 lines
- [ ] Total skill (SKILL + prompts) is under 300 lines
- [ ] Heuristic sections have NO inline code blocks
- [ ] Deterministic tools are in `scripts/`, not inline
- [ ] Evaluation criteria are in `prompts/`, not in SKILL.md body

### Instructions
- [ ] Every rule explains WHY it exists
- [ ] Evaluation tasks are framed as a role with an audience
- [ ] Specific bad output patterns are banned by example
- [ ] Budget constraints exist for scoring/inclusion
- [ ] An audit section lists checkable pass conditions

### Quality
- [ ] Tested with ≥ 2 realistic test prompts
- [ ] Outputs compared against human reference data
- [ ] No code blocks in evaluation/scoring sections
- [ ] Platform-specific workarounds documented
- [ ] Dependencies pinned to exact versions

### Description
- [ ] Includes explicit trigger phrases
- [ ] States both what the skill does and when to use it
- [ ] Slightly "pushy" to combat under-triggering

---

## 14. Using the Skill-Creator Tool

The `/skill-creator` skill is a complete testing and iteration harness. This section covers how to use it effectively, including known blind spots that the tool doesn't catch automatically.

### The core loop

```
1. Define intent → 2. Draft skill → 3. Run test cases → 4. Review in viewer
    ↑                                                           ↓
    └──────────── 5. Improve skill based on feedback ←──────────┘
```

Every iteration follows this cycle. Don't skip the viewer step — human review catches things quantitative evals miss.

### Phase 1: Capture intent

Before the skill-creator writes anything, it will ask four questions:
1. What should this skill do?
2. When should it trigger?
3. What's the expected output format?
4. Should we set up test cases?

**How to get the most out of this phase:**
- Bring a concrete example. "I want a skill that does X" is weaker than "Here's what I did manually last session — turn this into a skill." The skill-creator can extract steps, tools used, and corrections from your conversation history.
- Describe the *output* you want, not just the *process*. "I want a JSON file with scored YouTube leads" is more useful than "I want to search YouTube."
- Mention known failure modes upfront. If yt-dlp search is broken, say so now — don't wait for it to fail during testing.

### Phase 2: Draft the skill

The skill-creator will produce a SKILL.md and possibly supporting files. **Review the draft before testing.** Things to check:

| Check | Why |
|-------|-----|
| Are heuristic sections free of code blocks? | Code in evaluation sections triggers execution mode (see Section 4) |
| Is SKILL.md under 200 lines? | Longer skills cause the model to skim and skip steps |
| Are deterministic tasks separated from judgment tasks? | Mixed steps get sloppy evaluation |
| Does it reference `scripts/` for reusable tools? | If not, the model will regenerate throwaway scripts each run |

### Phase 3: Run test cases

The skill-creator will propose 2-3 test prompts. **Push back on weak test cases:**

- ❌ "Find media for a documentary" (too generic — won't stress-test edge cases)
- ✅ "Find archival images and footage for a documentary about the Duplessis Orphans in Quebec" (specific topic, tests real entity resolution, multiple source types)

**What happens during a run:**
- Two subagents per test case: one **with the skill**, one **without** (baseline)
- Both run in parallel — launched in the same turn
- Results go to `<skill-name>-workspace/iteration-N/eval-ID/{with_skill,without_skill}/outputs/`
- While runs execute, the skill-creator drafts quantitative assertions (grading criteria)

**Tip:** If a test case involves external tools (crawl4ai, yt-dlp), expect longer runtimes. The skill-creator should set appropriate timeouts.

### Phase 4: Review in the viewer

After runs complete, the skill-creator:
1. Grades each run against assertions → `grading.json`
2. Aggregates into benchmark stats → `benchmark.json`
3. Launches an HTML viewer with two tabs: **Outputs** (qualitative) and **Benchmark** (quantitative)

**How to review effectively:**

| Tab | What to look for |
|-----|-----------------|
| **Outputs** | Read the actual outputs, not just the grades. Look for lazy descriptions, bulk imports, skipped steps. Compare with-skill vs without-skill side by side. |
| **Benchmark** | Check pass_rate delta (with vs without skill). If both are similar, the skill isn't helping. Check token usage — a skill that costs 3x more tokens for 5% improvement may not be worth it. |

**Leave feedback in the viewer.** Click through each test case and type comments. Empty feedback = "looks good." The skill-creator reads `feedback.json` to plan improvements.

### Phase 5: Improve and iterate

The skill-creator reads your feedback and revises the skill. This is where most value is created — and where most blind spots hide.

**Known blind spots to watch for:**

#### Blind spot 1: Script regeneration (the media-scout problem)

**What happens:** Every test run independently generates similar Python scripts in scratch (e.g., `crawl_images.py`, `wiki_screenshots.py`). The skill-creator evaluates the *output* quality but doesn't notice that the *process* is wasteful.

**Why it's missed:** The evaluation focuses on final artifacts (did `media_leads.json` come out right?). Scratch scripts are intermediate — they don't appear in the graded outputs.

**How to catch it:** After iteration 1, ask: *"Did the test runs generate any Python scripts? If so, are they similar across runs?"* If yes, bundle them into `scripts/` and make the skill reference them with parameterized input.

**Rule of thumb:** If a skill uses an external tool (crawl4ai, yt-dlp, ffmpeg) and the test runs wrote Python scripts to call it, those scripts should be bundled.

#### Blind spot 2: Assertion quality

**What happens:** Assertions check surface properties ("output file exists", "JSON is valid") but not semantic quality ("descriptions are specific, not generic").

**How to catch it:** Review the assertions the skill-creator proposes. For heuristic output, add assertions like:
- "No description field contains 'requires manual review'"
- "At most N items scored as top tier"
- "Each description is > 20 words" (catches lazy one-liners)

#### Blind spot 3: Baseline comparison gap

**What happens:** The without-skill baseline may perform poorly, making the skill look great by comparison — even if the skill's output is mediocre in absolute terms.

**How to catch it:** Don't just look at the *delta*. Look at the with-skill output on its own. Would you accept this output for a real project?

#### Blind spot 4: Overfitting to test cases

**What happens:** After 3+ iterations on the same 2-3 test prompts, the skill becomes perfectly tuned for those topics but fragile on new ones.

**How to catch it:** After iteration 2, add 1-2 new test cases with different topics or edge cases. If the skill degrades on new cases, recent changes are overfitting.

### Phase 6: Description optimization (optional)

After the skill itself is stable, the skill-creator can optimize the `description` field for better triggering. This uses a separate automated loop:

1. You create 20 eval queries (10 should-trigger, 10 should-not-trigger)
2. The skill-creator runs `scripts/run_loop.py` which iteratively tests and improves the description
3. It uses a train/test split to prevent overfitting
4. Returns the best description found

**Tips for eval queries:**
- Make queries realistic and detailed, not abstract ("Find me archival footage of..." not "Find media")
- Should-not-trigger queries should be near-misses (shares keywords but needs a different skill)
- Don't use trivially obvious negative examples ("write a fibonacci function" is useless as a negative for a media skill)

### Toolkit reference

The skill-creator has bundled scripts you can invoke directly:

| Script | Purpose | When to use |
|--------|---------|-------------|
| `scripts/quick_validate.py` | Validates SKILL.md structure | Before testing — catches missing frontmatter |
| `scripts/aggregate_benchmark.py` | Aggregates run results into stats | After grading — produces benchmark.json |
| `scripts/run_eval.py` | Tests skill triggering on queries | Description optimization phase |
| `scripts/run_loop.py` | Full eval + improve loop for description | Description optimization phase |
| `scripts/improve_description.py` | LLM-based description improvement | Called by run_loop.py |
| `scripts/package_skill.py` | Packages skill into .skill file | When skill is finished |
| `eval-viewer/generate_review.py` | Launches HTML review viewer | After every iteration |

Agent specs in `agents/`:

| Agent | Purpose | Key output |
|-------|---------|------------|
| `grader.md` | Evaluates assertions against outputs | `grading.json` with pass/fail verdicts |
| `comparator.md` | Blind A/B comparison of two outputs | `comparison.json` with winner + rubric scores |
| `analyzer.md` | Post-hoc analysis of why one version won | `analysis.json` with improvement suggestions |

### Checklist for each iteration

Use this before marking an iteration complete:

- [ ] All test runs finished (check for timeouts or crashes)
- [ ] Both with-skill and baseline runs exist
- [ ] Grading ran and produced `grading.json` for each run
- [ ] Benchmark aggregated into `benchmark.json`
- [ ] Viewer launched and reviewed by human
- [ ] **Process audit**: Did runs generate throwaway scripts? → Bundle them
- [ ] **Assertion audit**: Do assertions test semantic quality, not just structure?
- [ ] **Overfitting check**: Would this change help on a different topic?
- [ ] Feedback saved and read by skill-creator

---

## Appendix: Adding to This Guide

When you discover a new principle through testing, add it to the appropriate section with:
1. **The finding** — what you observed
2. **The evidence** — how you tested/confirmed it
3. **The recommendation** — what to do about it

Mark unconfirmed hypotheses with `[UNTESTED]` until validated through A/B testing or production runs.
