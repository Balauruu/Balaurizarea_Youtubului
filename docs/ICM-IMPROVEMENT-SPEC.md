# ICM-Driven Improvement Spec for Channel-automation V3

*Based on analysis of the Interpreted Context Methodology (ICM/MWP) framework*
*Date: 2026-03-14*

---

## Executive Summary

Your project already implements many ICM principles naturally — filesystem-based context routing, deterministic/heuristic separation, file-based agent handoffs, and zero LLM API wrappers. However, ICM formalizes several patterns you're doing implicitly (or not at all) that would make the pipeline more robust, auditable, and maintainable as you build Agents 1.3, 1.4, and Phase 2.

**High-impact changes:** 5 structural improvements + 4 convention adoptions
**Estimated effort:** 2-3 focused sessions
**Risk:** Low — these are additive, not rewrites

---

## Gap Analysis: ICM vs. Current State

| ICM Concept | Your Current State | Gap |
|---|---|---|
| **Five-Layer Routing** | Implicit — CLAUDE.md + SKILL.md + context/ | No explicit "What to Load" per task; no stage CONTEXT.md contracts |
| **Stage Contracts (Inputs/Process/Outputs)** | Embedded in SKILL.md prose | Not structured; agent must parse narrative text to find what to load |
| **Selective Section Routing** | Agents load entire files | No "read Section X of file Y" optimization |
| **Checkpoints** | Ad-hoc (user intervenes in chat) | Not formalized; no defined pause points |
| **Stage Audits** | None | No quality gates before output is written |
| **Canonical Sources** | Mostly followed | Some duplication (Architecture.md repeats channel.md content) |
| **One-Way Cross-References** | Followed naturally | ✅ No action needed |
| **File-Based Handoffs** | ✅ Already implemented | Working well |
| **Scratch Pad Pattern** | ✅ Already implemented | Working well |
| **Placeholder/Questionnaire** | Not applicable (single-user) | Skip — adds overhead with no benefit for solo use |

---

## Proposed Changes

### 1. Add Stage CONTEXT.md Contracts to Each Skill

**What:** Create a `CONTEXT.md` file in each skill directory that follows the ICM stage contract format: Inputs table, Process steps, Outputs table.

**Why:** Your SKILL.md files currently mix *user documentation* (how to invoke commands) with *agent routing* (what to load, what to produce). When Claude Code invokes a skill, it loads the entire SKILL.md — including CLI examples, setup instructions, and workflow narrative the agent doesn't need. A separate CONTEXT.md gives the agent a **precise contract** in <500 tokens.

**Current problem this solves:** When you build Agent 1.3 (Writer), you'll need to document exactly which files it reads, in what order, and what it produces. Without stage contracts, this context routing gets embedded in SKILL.md prose and becomes hard to audit or change.

**Example for the Researcher skill:**

```markdown
# Researcher — Stage Contract

Research a topic through two-pass web scraping and produce a narrative dossier.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Project | projects/N. [Title]/metadata.md | "Topic Brief" section | Topic scope and angle |
| Channel | context/channel/channel.md | "Core Content Pillars" | Tone and depth calibration |
| Prompt | prompts/survey_evaluation.md | Full file | Source evaluation rubric |
| Prompt | prompts/synthesis.md | Full file | Dossier structure template |

## Process
1. Run `researcher survey "<topic>"` → fetch 10-15 sources → `src_NNN.json`
2. [HEURISTIC] Evaluate sources using survey_evaluation.md → `source_manifest.json`
3. Run `researcher deepen "<topic>"` → fetch deep-dive URLs → `pass2_NNN.json`
4. Run `researcher write "<topic>"` → aggregate → `synthesis_input.md`
5. [HEURISTIC] Synthesize using synthesis.md → `Research.md` + `media_urls.md`

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Research dossier | projects/N. [Title]/research/Research.md | 9-section markdown |
| Media catalog | projects/N. [Title]/research/media_urls.md | Grouped URLs |
| Source manifest | projects/N. [Title]/research/source_manifest.json | JSON with verdicts |
```

**Action:** Create `CONTEXT.md` for:
- `.claude/skills/channel-assistant/CONTEXT.md`
- `.claude/skills/researcher/CONTEXT.md`
- `.claude/skills/visual-style-extractor/CONTEXT.md`
- (And each future skill as you build it)

**Token impact:** ~200-400 tokens per contract vs. 1500-3000 tokens for full SKILL.md. Agent loads CONTEXT.md for routing, SKILL.md only when user needs help.

---

### 2. Add "What to Load" Section to Project CLAUDE.md

**What:** Add a task-routing table to CLAUDE.md that maps each task type to the minimal set of files the agent should load.

**Why:** ICM's Layer 1 routing principle. Currently, your CLAUDE.md lists context files but doesn't say *which task needs which files*. When Claude starts a new conversation, it loads everything referenced in CLAUDE.md — including competitor analysis when you're just doing research, or visual style guides when you're just doing topic ideation.

**Proposed addition to CLAUDE.md:**

```markdown
## What to Load

| Task | Load These | Skip These | Why Skip |
|------|-----------|------------|----------|
| Topic ideation | channel.md, past_topics.md, competitors/analysis.md, channel-assistant/CONTEXT.md | visual-references/, script-references/ | Not relevant to topic selection |
| Research | channel.md, researcher/CONTEXT.md, projects/N/metadata.md | competitors/, visual-references/ | Research is topic-focused, not channel-strategy |
| Script writing | channel.md, writting_style_guide.md, script-references/, projects/N/research/Research.md | competitors/, visual-references/ (unless doing visual inserts) | Writer needs voice + research, not strategy |
| Visual planning | visual-references/*/VISUAL_STYLE_GUIDE.md, projects/N/script.txt | competitors/, channel.md | Director needs visual vocabulary + script |
| Style extraction | visual-style-extractor/CONTEXT.md, target video URL | Everything else | Self-contained pipeline |
```

**Token savings:** Prevents loading 3000-5000 tokens of irrelevant context per task. More importantly, prevents attention dilution — Claude reasons better with focused context.

---

### 3. Formalize Checkpoints in Skill Workflows

**What:** Add a `## Checkpoints` section to each skill's CONTEXT.md that defines where the agent pauses for human steering.

**Why:** Your pipeline already has natural pause points (user selects topic from briefs, user confirms source evaluation), but they're implicit — embedded in SKILL.md workflow prose. ICM's checkpoint pattern makes these **explicit contracts**: after step X, present Y, human decides Z.

**Current checkpoints (implicit):**

| Skill | Implicit Pause | What Happens |
|-------|----------------|--------------|
| Channel Assistant | After topic briefs generated | User picks topic from chat |
| Channel Assistant | After title variants generated | User picks title |
| Researcher | After survey evaluation | User can redirect source selection |
| Researcher | After dossier synthesis | User reviews before next phase |

**Proposed formalization (add to CONTEXT.md):**

```markdown
## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 6 (topic briefs) | 5 scored topic cards | Which topic to pursue |
| Step 9 (title variants) | 3-5 title options + description | Final title for project init |
```

**Why this matters for future agents:** Agent 1.3 (Writer) will need checkpoints for outline approval before full script generation. Agent 1.4 (Visual Orchestrator) will need checkpoints for shot list review. Define these now so the pattern is established.

---

### 4. Add Stage Audits (Quality Gates)

**What:** Define pass/fail quality checks that run *after* an agent's process steps but *before* output is finalized.

**Why:** ICM's Pattern 12. Currently, your pipeline has no quality gates — output goes directly to disk. For topic ideation this is fine (low-stakes, user reviews immediately). But for Research.md and future script output, a quality audit catches issues before they propagate downstream.

**Proposed audits:**

**Researcher audit (after synthesis, before writing Research.md):**
```markdown
## Audit
| Check | Pass Condition |
|-------|---------------|
| Source diversity | At least 3 distinct source domains cited |
| Timeline populated | Timeline section has ≥5 dated entries |
| Contradictions addressed | Section 7 is non-empty OR explicitly states "no contradictions found" |
| Media inventory | At least 5 media URLs cataloged |
| No fabrication | Every claim in Subject Overview traces to a source in Sections 4-5 |
```

**Writer audit (future — after script generation):**
```markdown
## Audit
| Check | Pass Condition |
|-------|---------------|
| Chapter count | 4-7 chapters (per channel.md targets) |
| Word count | 3,000-7,000 words (per channel.md output targets) |
| Source grounding | Every major claim traceable to Research.md |
| Voice consistency | No first-person, no editorializing, neutral tone throughout |
| Hook quality | First 100 words create immediate tension or mystery |
```

**Implementation:** These are prompt instructions, not code. Add them to the CONTEXT.md contract. Claude self-audits before writing output. No code needed.

---

### 5. Restructure Project Directories to Follow ICM Stage Handoffs

**What:** Reorganize per-video project directories to use numbered stage folders, making the pipeline stage that produced each artifact explicit.

**Why:** Currently, `projects/N. [Title]/research/` holds all research outputs. As you add Writer (script), Director (shot list), and Phase 2 (assets), you'll need to distinguish what came from which stage. ICM's numbered-folder convention makes handoffs visible and auditable.

**Current:**
```
projects/1. The Duplessis Orphans/
├── metadata.md
└── research/
    ├── Research.md
    ├── media_urls.md
    └── source_manifest.json
```

**Proposed:**
```
projects/1. The Duplessis Orphans/
├── metadata.md                          # Created by Agent 1.1
├── 01-research/                         # Agent 1.2 outputs
│   ├── Research.md
│   ├── media_urls.md
│   └── source_manifest.json
├── 02-script/                           # Agent 1.3 outputs (future)
│   └── script.md
├── 03-shotlist/                         # Agent 1.4 outputs (future)
│   └── shotlist.json
└── 04-assets/                           # Phase 2 outputs (future)
    ├── manifest.json
    ├── archival_footage/
    ├── archival_photos/
    └── ...
```

**Benefit:** Each numbered folder is an ICM "stage output" folder. Agent N+1 reads from folder N. If you re-run Agent 1.2, you blow away `01-research/` without touching `02-script/`. The directory structure *documents* the pipeline.

**Trade-off:** This is the most disruptive change — it touches `project_init.py` and the researcher's output paths. Could also keep current structure and only adopt numbered folders for new agents. Your call.

---

### 6. Adopt "Docs Over Outputs" Convention

**What:** Establish a rule that agents reference `context/` files (docs) as authoritative, never previous project outputs as templates.

**Why:** ICM Pattern 14. As you produce more videos, there's a risk that Agent 1.2 starts referencing `projects/1. Duplessis/research/Research.md` as a template for future research. This causes quality degradation — early outputs become frozen patterns, and improvements to prompts don't propagate.

**Rule:** Prompt files (`prompts/synthesis.md`) and context files (`context/channel/channel.md`) are authoritative. Previous project outputs in `projects/*/` are artifacts, not models.

**Action:** Add to CLAUDE.md under a new `## Conventions` section:

```markdown
## Conventions

### Docs Over Outputs
Reference docs (prompts/, context/) are authoritative. Previous project outputs
(projects/*/research/) are artifacts, NOT templates. Agents never read other
projects' outputs to learn patterns — they read prompt files.
```

---

### 7. Add Token Budget Awareness to SKILL.md Files

**What:** Add a brief note to each SKILL.md estimating the token cost of the context it loads, so you can make informed decisions about what to load.

**Why:** ICM's token management principle. "Every token of irrelevant context is a token of diluted attention." You don't need exact counts — rough estimates help you notice when a skill is loading too much.

**Example addition to Researcher SKILL.md:**

```markdown
## Context Budget
| File | ~Tokens | When Needed |
|------|---------|-------------|
| CONTEXT.md | ~300 | Always (routing) |
| prompts/survey_evaluation.md | ~800 | Pass 1 evaluation |
| prompts/synthesis.md | ~600 | Pass 3 synthesis |
| context/channel/channel.md | ~1200 | Tone calibration |
| metadata.md (per project) | ~400 | Topic scoping |
| **Total per run** | **~3300** | |
```

---

### 8. Create a Top-Level CONTEXT.md for Task Routing

**What:** Add a `CONTEXT.md` at project root that serves as ICM Layer 1 — a routing table mapping task types to skill invocations and their required context.

**Why:** Your CLAUDE.md currently mixes *instructions to Claude* (coding style, git conventions, platform notes) with *project routing* (which skills exist, where context lives). ICM separates these: CLAUDE.md = "rules for how to behave", CONTEXT.md = "where to go for each task type."

**Proposed `CONTEXT.md`:**

```markdown
# Channel-automation V3 — Context Router

Documentary video generation pipeline. Claude Code is the orchestrator.

## Task Routing

| Task | Skill | Entry Point |
|------|-------|-------------|
| Find/add competitors | channel-assistant | `cmd_add`, `cmd_scrape`, `cmd_analyze` |
| Generate topic ideas | channel-assistant | `cmd_topics` + Claude heuristic |
| Initialize video project | channel-assistant | `cmd_init_project` |
| Research a topic | researcher | `cmd_survey` → evaluate → `cmd_deepen` → `cmd_write` |
| Extract visual style | visual-style-extractor | 6-stage pipeline |
| Write script | (not yet implemented) | — |
| Create shot list | (not yet implemented) | — |

## What to Load

| Task | Required Context | Skip |
|------|-----------------|------|
| Topic ideation | channel.md, past_topics.md, analysis.md | visual-references/, script-references/ |
| Research | channel.md, metadata.md | competitors/, visual-references/ |
| Style extraction | Target video only | Everything else |

## Project Directory

Each video lives at `projects/N. [Video Title]/`. See Architecture.md for full schema.
```

**Benefit:** New conversations start with a 400-token routing table instead of parsing a 2000-token CLAUDE.md to figure out what to invoke. Claude can also use this to suggest next steps ("Research is done — the next task in the routing table is script writing").

---

### 9. Adopt "Specs Are Contracts" for Future Agent Design

**What:** When designing Agents 1.3 (Writer) and 1.4 (Director), define their output specs as *contracts* — WHAT and WHEN, not HOW.

**Why:** ICM Pattern 10. Your Architecture.md already does this well for the shot list schema (narrative need, not asset type). Extend this principle explicitly: the Writer's script spec defines chapter structure and word count range, but not sentence construction. The Director's shot list defines visual needs, but not camera angles or editing decisions.

**Anti-pattern to avoid:**
```markdown
# BAD — too prescriptive
## Process
1. Open with a rhetorical question
2. Use 3 sentences of context-setting
3. Transition with "But beneath the surface..."
```

**Correct pattern:**
```markdown
# GOOD — contract format
## Process
1. Read Research.md for factual foundation
2. [HEURISTIC] Structure into 4-7 chapters following channel voice
3. Audit against quality checks
4. Write to 02-script/script.md

## Audit
| Check | Pass Condition |
|-------|---------------|
| Hook | First 100 words create tension |
| Voice | Third-person, neutral, no editorializing |
| Sources | Every major claim traceable to Research.md |
```

---

## Changes NOT Recommended

These ICM patterns don't fit your project:

| ICM Pattern | Why Skip |
|---|---|
| **Questionnaire/Placeholders** | Single-user project — channel DNA is already written. Placeholders add overhead with no reuse benefit. |
| **Workspace-level CLAUDE.md separation** | You already have one CLAUDE.md. ICM uses workspace CLAUDE.md for multi-workspace repos; you have one pipeline. |
| **`setup` / `status` trigger keywords** | Your GSD system (`/gsd:progress`) already handles status. No need for a second status mechanism. |
| **Shared constants file** | Not a code-producing pipeline (no Remotion yet). Add this when you build Agent 2.3. |
| **Design system as code recipes** | Same — relevant only when you have visual generation agents. |

---

## Implementation Priority

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| **P0** | 1. Stage CONTEXT.md contracts | 1 hour | High — establishes pattern for all future agents |
| **P0** | 6. Docs Over Outputs convention | 5 min | High — prevents quality degradation as you produce more videos |
| **P1** | 2. "What to Load" in CLAUDE.md | 15 min | Medium — reduces context dilution |
| **P1** | 8. Top-level CONTEXT.md router | 20 min | Medium — cleaner task routing |
| **P1** | 3. Formalize checkpoints | 15 min | Medium — critical for Writer/Director agents |
| **P2** | 4. Stage audits | 30 min | Medium — quality gates for research and future script output |
| **P2** | 9. Contract-style specs for future agents | Design-time | Medium — prevents over-prescriptive agent design |
| **P3** | 7. Token budget notes | 15 min | Low — nice-to-have for optimization |
| **P3** | 5. Numbered project stage folders | 1 hour | Low — cosmetic unless you need stage isolation |

---

## Summary

Your project is architecturally aligned with ICM already. The main gaps are:

1. **Routing is implicit** — agents parse SKILL.md prose instead of reading structured CONTEXT.md contracts
2. **Quality gates are absent** — no audits before output is finalized
3. **Checkpoints are informal** — human steering points aren't documented as contracts
4. **Context loading is unscoped** — no "What to Load" tables to prevent attention dilution

The P0 and P1 changes (CONTEXT.md contracts, routing table, checkpoints, docs-over-outputs) can be done in a single session and will pay off immediately as you build the next agents.
