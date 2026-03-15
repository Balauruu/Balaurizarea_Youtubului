# Architecture Research

**Domain:** Documentary pipeline — Visual Orchestrator (Agent 1.4) skill integration (v1.3)
**Researched:** 2026-03-15
**Confidence:** HIGH (direct codebase inspection of all existing skills and actual shotlist.json artifact)

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Claude Code (Orchestrator)                         │
│          Dispatches skills, performs all [HEURISTIC] reasoning        │
├──────────────┬──────────────┬──────────────┬────────────────────────-┤
│  Agent 1.1   │  Agent 1.2   │  Agent 1.3   │  Agent 1.4              │
│  channel-    │  researcher  │  writer      │  visual-                │
│  assistant   │              │              │  orchestrator           │
│  (existing)  │  (existing)  │  (existing)  │  (NEW)                  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────────┬──────────────┘
       |              |              |                  |
       v              v              v                  v
┌──────────────────────────────────────────────────────────────────────┐
│                      Filesystem (shared state)                        │
├─────────────────┬──────────────────┬─────────────────────────────────┤
│ context/        │ projects/N.Title/ │ context/visual-references/      │
│ channel/        │   metadata.md     │   [Video Name]/                 │
│ channel.md      │   research/       │   VISUAL_STYLE_GUIDE.md         │
│ STYLE_PROFILE.md│     Research.md   │   (from visual-style-extractor) │
│                 │   Script.md       │                                 │
│                 │   shotlist.json   │                                 │
│                 │   (NEW)           │                                 │
└─────────────────┴──────────────────┴─────────────────────────────────┘
                                                |
                              ┌─────────────────┘
                              | (Phase 2)
                              v
┌──────────────────────────────────────────────────────────────────────┐
│                      Asset Pipeline                                   │
├──────────────┬──────────────┬──────────────┬────────────────────────-┤
│  Agent 2.1   │  Agent 2.2   │  Agent 2.3   │  Agent 2.4              │
│  Media       │  Vector Gen  │  Animation   │  Asset Manager          │
│  Acquisition │  (ComfyUI)   │  (Remotion)  │                         │
└──────────────┴──────────────┴──────────────┴─────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Classification | Status |
|-----------|----------------|----------------|--------|
| `channel-assistant` | Competitor intel, topic briefs, project init | DETERMINISTIC + HEURISTIC | Existing — no changes |
| `researcher` | Two-pass web research → Research.md | DETERMINISTIC + HEURISTIC | Existing — no changes |
| `style-extraction` | One-time: reference scripts → STYLE_PROFILE.md | HEURISTIC only | Existing — no changes |
| `writer` | Research.md + STYLE_PROFILE.md → Script.md | HEURISTIC + minimal CLI | Existing — no changes |
| `visual-style-extractor` | Reference video → VISUAL_STYLE_GUIDE.md | DETERMINISTIC + HEURISTIC | Existing — no changes |
| `visual-orchestrator` | Script.md + VISUAL_STYLE_GUIDE.md → shotlist.json | HEURISTIC only | NEW |

---

## Recommended Project Structure

```
.claude/skills/
├── channel-assistant/           # Existing - no changes
├── researcher/                  # Existing - no changes
├── style-extraction/            # Existing - no changes
├── writer/                      # Existing - no changes
├── visual-style-extractor/      # Existing - no changes
└── visual-orchestrator/         # NEW skill (zero Python code)
    ├── SKILL.md                 # Human-facing: how to invoke, prerequisites, output path
    ├── CONTEXT.md               # Stage contract: inputs, process steps, checkpoint, outputs
    └── prompts/
        └── generation.md        # All shot-list generation instructions Claude follows
```

### Structure Rationale

- **No scripts/ directory:** Zero Python code. This is a pure [HEURISTIC] skill identical in shape to `style-extraction`. Claude reads two input files and produces one output file. No CLI is needed.
- **Single prompt file named generation.md:** Matches the writer skill's convention (`prompts/generation.md`). Contains the complete shot-list generation instructions.
- **CONTEXT.md as stage contract:** Mirrors the pattern in every existing skill. Orchestrator routing in CLAUDE.md references CONTEXT.md, not SKILL.md.

---

## Architectural Patterns

### Pattern 1: Pure Heuristic Skill (style-extraction — the direct template)

**What:** A skill with zero Python code. SKILL.md describes the step-by-step invocation workflow, including any conditional logic. CONTEXT.md is the stage contract for orchestrator routing. A single prompt file in `prompts/` contains all generation instructions Claude follows at reasoning time. No CLI, no pip install, no PYTHONPATH.

**When to use:** When the task is classification, narrative reasoning, or structured creative output — where LLM judgment produces better output than deterministic code.

**Trade-offs:** Invocation is Claude reading SKILL.md and following the steps using Read/Write/Glob tools directly. No external tool output. Harder to unit-test. Well-suited to generation tasks with a known schema.

**Existing examples:**
```
.claude/skills/style-extraction/
    SKILL.md          -- step-by-step invocation (8 steps with conditional logic)
    CONTEXT.md        -- inputs table, process steps, checkpoints, outputs table
    prompts/
        extraction.md -- reconstruction and extraction pass instructions

.claude/skills/writer/
    SKILL.md          -- CLI command + 3-step workflow
    CONTEXT.md        -- inputs, process, checkpoints, outputs
    prompts/
        generation.md -- all script-writing instructions
```

Visual Orchestrator follows style-extraction's zero-code pattern (not writer's CLI pattern), because the only file resolution needed is a Glob or Bash ls — no multi-file aggregation warrants a context-loader.

### Pattern 2: Single-Pass Generation

**What:** Claude reads all inputs, then generates the output in one reasoning pass. No intermediate evaluation gate, no separate synthesis step.

**When to use:** When the task has a linear structure — iterate input sequentially, emit output per item. No branching evaluation or merge step required.

**Why it applies here:** Shot generation proceeds chapter-by-chapter, beat-by-beat. Each narrative beat maps to a building block via the VISUAL_STYLE_GUIDE decision tree. There is no evaluation step between reading the script and emitting shots — the decision tree is the evaluation logic, applied inline.

**Contrast with two-pass skills:** researcher (broad survey → evaluate → deep-dive) and visual-style-extractor (extract patterns → synthesize building blocks) both have genuine evaluation gates. Visual Orchestrator does not.

### Pattern 3: Schema-Locked JSON Output

**What:** The generation prompt defines the exact JSON schema. Claude outputs conforming JSON. Downstream consumers rely on field names being stable.

**When to use:** When output is consumed by code (Agent 2.1 will read shotlist.json programmatically). Markdown is appropriate for human-read outputs; JSON is appropriate for machine-read outputs.

**Trade-offs:** Schema changes require updating both the prompt and downstream consumers. More rigid than markdown. But rigidity is the point — it is a contract.

---

## Data Flow

### Invocation Flow

```
User triggers visual-orchestrator skill
    |
Claude reads SKILL.md
    |
Claude resolves project directory (Glob on projects/)
Claude identifies which VISUAL_STYLE_GUIDE to use
    |
Claude reads Script.md                Claude reads VISUAL_STYLE_GUIDE.md
(narration + chapter structure)       (building blocks + decision tree)
    |______________________________________|
                    |
          Claude reads prompts/generation.md
                    |
          Claude generates shotlist.json
          (sequential pass through chapters)
                    |
          Claude writes shotlist.json
          to projects/N. [Title]/shotlist.json
```

### Shot Generation Logic (within the single pass)

```
For each chapter in Script.md:
    |
    Parse ## N. Chapter Title heading
    chapter_title = verbatim heading text
    chapter = integer N (0 for prologue — content before ## 1.)
    |
    For each narrative beat in chapter prose:
        |
        Apply VISUAL_STYLE_GUIDE Type Selection Decision Tree:
            |
            IF verbatim quote (quote card)     --> text_overlay, text_content populated
            IF date/time reference             --> text_overlay, Date Card, text_content populated
            IF single impact sentence          --> text_overlay, Keyword Stinger, text_content populated
            IF introduces a named person       --> archival_photo (portrait) or vector
            IF introduces a location           --> map + archival_video or archival_photo
            IF references an official document --> archival_photo (document scan)
            IF builds narrative tension        --> archival_video (b-roll)
            IF statistics / funding amounts    --> animation (concept diagram)
        |
        Emit shot entry:
            id: "S001" ... sequential across all chapters, never reset
            chapter: integer (0 for prologue)
            chapter_title: verbatim heading
            narrative_context: concise paraphrase of what narrator says
            visual_need: free-text visual description (intentionally loose)
            building_block: name from VISUAL_STYLE_GUIDE (must match exactly)
            shotlist_type: enum value (see schema below)
            building_block_variant: variant name from guide, or null
            text_content: verbatim text for text_overlay shots, null for media shots
            suggested_sources: array of domain hints, [] for text_overlay
```

### Key Data Flows

1. **Script.md chapter parsing:** Content before `## 1.` is chapter 0 (the hook formula — opening quote, compressed overview, closing formula). Each `## N.` heading opens a new chapter. Chapter integer is N; chapter_title is the verbatim heading text after the number.

2. **VISUAL_STYLE_GUIDE → building_block selection:** The guide's "Type Selection Decision Tree" section is the authoritative mapping from narrative triggers to building block names. `building_block` values in shotlist.json must match guide building block names exactly, because Agent 2.1 will look them up.

3. **shotlist.json → Agent 2.1:** Agent 2.1 reads shotlist.json exclusively — it does not read Script.md. The `narrative_context`, `visual_need`, `building_block`, and `suggested_sources` fields are the acquisition signals. Shots with `shotlist_type: "text_overlay"` are editor-managed — Agent 2.1 skips them.

---

## Shotlist Schema (Canonical)

Architecture.md defines the baseline schema (id, chapter, narrative_context, visual_need, suggested_types). The actual first shotlist generated (Duplessis Orphans, 2026-03-15) extends it with fields that proved necessary during generation. This extended schema is the one the Visual Orchestrator skill must produce:

```json
{
  "project": "The Duplessis Orphans Quebec's Stolen Children",
  "guide_source": "Lemmino Consumed by the Climb",
  "generated": "2026-03-15T01:18:00Z",
  "shots": [
    {
      "id": "S001",
      "chapter": 0,
      "chapter_title": "Prologue",
      "narrative_context": "Opening survivor quote — being born into a garbage can.",
      "visual_need": "Quote card with survivor testimony against dark background",
      "building_block": "Quote Card",
      "shotlist_type": "text_overlay",
      "building_block_variant": null,
      "text_content": "\"When you are a bastard...\"",
      "suggested_sources": []
    },
    {
      "id": "S002",
      "chapter": 0,
      "chapter_title": "Prologue",
      "narrative_context": "Narrator introduces the scheme — orphans falsely certified as mentally deficient.",
      "visual_need": "Dark archival footage of Quebec institutional building exterior, 1940s-1950s",
      "building_block": "Archival Footage",
      "shotlist_type": "archival_video",
      "building_block_variant": "Institutional/Urban",
      "text_content": null,
      "suggested_sources": ["archive.org", "nfb.ca"]
    }
  ]
}
```

**Top-level fields:**

| Field | Type | Description |
|-------|------|-------------|
| `project` | string | Project name (from directory name) |
| `guide_source` | string | Which VISUAL_STYLE_GUIDE was used (video title) |
| `generated` | ISO 8601 string | Generation timestamp |
| `shots` | array | Ordered shot entries |

**Per-shot fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Sequential: S001, S002, ... never reset across chapters |
| `chapter` | integer | Yes | 0 for prologue/hook, 1+ for numbered chapters |
| `chapter_title` | string | Yes | Verbatim chapter heading from Script.md |
| `narrative_context` | string | Yes | What narrator is saying — concise paraphrase |
| `visual_need` | string | Yes | Free-text visual description (intentionally loose) |
| `building_block` | string | Yes | Named building block from VISUAL_STYLE_GUIDE (exact match) |
| `shotlist_type` | enum | Yes | `archival_video`, `archival_photo`, `text_overlay`, `map`, `animation`, `vector` |
| `building_block_variant` | string or null | Yes | Variant name from guide, or null |
| `text_content` | string or null | Yes | Verbatim text for text_overlay shots; null for all media shots |
| `suggested_sources` | array | Yes | Domain hints from Architecture.md tier list; `[]` for text_overlay |

**shotlist_type values and Agent 2.1 behavior:**

| shotlist_type | Agent 2.1 action |
|---------------|-----------------|
| `archival_video` | Acquire from Tier 1/2 domains, yt-dlp for CC footage |
| `archival_photo` | Acquire from Tier 1/2 image domains, Wikipedia screenshots |
| `map` | Flag for Agent 2.3 (animation) — Agent 2.1 skips |
| `animation` | Flag for Agent 2.3 — Agent 2.1 skips |
| `vector` | Flag for Agent 2.2 (ComfyUI) — Agent 2.1 skips |
| `text_overlay` | Editor-managed — Agent 2.1 skips entirely |

---

## SKILL.md Structure Recommendation

Pattern: style-extraction (zero CLI, numbered steps, prerequisites table, output section).

```markdown
---
name: visual-orchestrator
description: Parse Script.md into shotlist.json with per-shot visual needs.
  Use this skill when the user wants to create a shot list, map visual needs
  from a script, generate shotlist.json, or says "create shot list for [topic]",
  "map visuals for [topic]", "orchestrate visuals", "director pass".
  Requires Script.md and a VISUAL_STYLE_GUIDE.md.
---

# Visual Orchestrator

Script.md + VISUAL_STYLE_GUIDE.md → shotlist.json. Pure [HEURISTIC] — zero Python.

## Workflow

### Step 1: Identify project and style guide

- **Project:** Resolve from `projects/` by sequential number or title substring.
- **Style guide:** List `context/visual-references/*/VISUAL_STYLE_GUIDE.md`.
  If one guide exists, use it. If multiple exist, ask the user which to apply.

### Step 2: Read inputs

- `projects/N. [Title]/Script.md`
- `context/visual-references/[Video Name]/VISUAL_STYLE_GUIDE.md`
- `prompts/generation.md` (generation instructions — read before generating)

### Step 3: Generate and write shotlist.json

Follow the instructions in `prompts/generation.md`. Write to
`projects/N. [Title]/shotlist.json`.

## Prerequisites

- `projects/N. [Title]/Script.md` — from the writer skill
- `context/visual-references/[Video Name]/VISUAL_STYLE_GUIDE.md` — from visual-style-extractor

## Output

`projects/N. [Title]/shotlist.json` — shot list with per-shot visual needs.
```

## CONTEXT.md Structure Recommendation

Pattern: writer/CONTEXT.md exactly (inputs table, numbered process steps, checkpoint section, outputs table, deferred section).

```markdown
# Visual Orchestrator — Stage Contract

**Phase:** 13 — Visual Orchestrator
**Skill:** visual-orchestrator
**Type:** [HEURISTIC] — Claude does all reasoning; zero Python code

## Inputs

| File | Source | Required |
|------|--------|----------|
| `projects/N. [Title]/Script.md` | writer skill | Yes |
| `context/visual-references/[Video]/VISUAL_STYLE_GUIDE.md` | visual-style-extractor | Yes |
| `prompts/generation.md` | skill-internal | Yes |

## Process

1. Resolve project directory and identify which VISUAL_STYLE_GUIDE to use.
2. Read Script.md + VISUAL_STYLE_GUIDE.md. Read prompts/generation.md.
3. Generate shotlist.json in a single pass through the script chapters.
4. Write shotlist.json to the project directory.

## Checkpoints

Human review after generation via `git diff`. No automated gate.

## Outputs

| File | Location | Description |
|------|----------|-------------|
| `shotlist.json` | `projects/N. [Title]/shotlist.json` | Per-shot visual needs, JSON |

## Deferred

- Shot duration and timing — editor's domain (DaVinci Resolve)
- Priority ranking across shots — Agent 2.1 acquires all; gaps feed Agent 2.2/2.3
- Automatic guide selection when multiple guides exist
```

---

## Prompt Architecture: generation.md

### Structure

The prompt is a single file with these sections, in order:

1. **Role and task statement** — what the Visual Orchestrator produces and why
2. **Input structure** — how to parse Script.md (chapter detection, hook/prologue handling)
3. **Shot granularity rules** — how many shots per paragraph/beat
4. **Schema definition** — exact field names, types, and allowed enum values
5. **Building block application** — how to use the VISUAL_STYLE_GUIDE Type Selection Decision Tree
6. **Per-type rules** — text_overlay handling, suggested_sources policy, null vs empty array
7. **ID sequencing** — S001 sequential across the entire script, never reset per chapter
8. **Output format** — write as JSON to the path in SKILL.md using the Write tool

### Shot Granularity (must be specified in the prompt)

The Duplessis shotlist demonstrates the density pattern to document:

| Narrative trigger | Shot count | Rationale |
|------------------|------------|-----------|
| Single impact sentence ("Someone did the math.") | 1 — Keyword Stinger | The sentence IS the shot |
| Verbatim quote | 1 — Quote Card, text_content populated | Always a single card |
| Date reference | 1 — Date Card | Single establishing card |
| Paragraph introducing a named person | 1-2 (portrait + contextual b-roll) | Person + environment |
| Paragraph introducing a location | 1-2 (map + archival footage/photo) | Geography + atmosphere |
| Dense factual paragraph (statistics, policy mechanics) | 2-4 | Each data point may warrant a shot |
| Chapter transition headings | 0 — chapter headings are not shots | Structural only |
| Long atmospheric paragraph | 1-2 — lean toward b-roll | Avoid over-shotting description |

### Text Overlay Handling (must be explicit in the prompt)

Three building blocks produce text_overlay shots that are editor-managed. Agent 2.1 skips them. The prompt must instruct:

- Set `shotlist_type: "text_overlay"` for: Quote Card, Date Card, Keyword Stinger
- Populate `text_content` with the verbatim text to display on screen
- Set `suggested_sources: []` — no acquisition needed
- `building_block_variant` is null for Date Cards, optional for Quote Cards (e.g., "Survivor Testimony")

### Building Block Vocabulary

The prompt must state: building_block names must be copied exactly from the VISUAL_STYLE_GUIDE. Do not invent names. If no building block fits, use the closest match and note the gap in narrative_context.

---

## Integration Points

### Upstream: Writer Skill

| Integration | Detail |
|-------------|--------|
| Input file | `projects/N. [Title]/Script.md` |
| Format | Begins with hook prose (chapter 0), then `## 1. [Chapter Title]` headings |
| Chapter parse | Split on `## N.` headings; content before `## 1.` is chapter 0 |
| Dependency | Script.md must be complete and approved before orchestrator runs |
| No changes needed | Writer outputs to the correct path; orchestrator reads it as-is |

### Upstream: Visual Style Extractor

| Integration | Detail |
|-------------|--------|
| Input file | `context/visual-references/[Video Name]/VISUAL_STYLE_GUIDE.md` |
| Which guide | Human specifies at invocation; SKILL.md step 1 handles disambiguation |
| Key sections | "Type Selection Decision Tree" — primary mapping; building block names/variants |
| Coupling | building_block values in shotlist.json must match guide names exactly |
| guide_source field | Records which guide was used, enabling re-runs after guide updates |

### Downstream: Agent 2.1 (Media Acquisition)

| Integration | Detail |
|-------------|--------|
| Output file | `projects/N. [Title]/shotlist.json` |
| Consumer reads | `visual_need`, `building_block`, `shotlist_type`, `suggested_sources` |
| Consumer skips | All `text_overlay` shotlist_type entries |
| Contract | shotlist.json is Agent 2.1's sole input — it does not read Script.md |
| Shot IDs | manifest.json uses S001/S002/... to map acquired assets back to shots |

### CLAUDE.md Changes Needed

After the skill is built, update CLAUDE.md in two places:

1. **Task Routing table:** Add row `| Create shot list | visual-orchestrator | CONTEXT.md |`
2. **"What to Load" table:** Add row for visual planning: `projects/N/Script.md`, `context/visual-references/*/VISUAL_STYLE_GUIDE.md`

---

## New vs. Modified Components

### New (does not exist yet)

| Component | Location | What It Is |
|-----------|----------|------------|
| `visual-orchestrator/SKILL.md` | `.claude/skills/visual-orchestrator/` | Invocation workflow — zero Python |
| `visual-orchestrator/CONTEXT.md` | `.claude/skills/visual-orchestrator/` | Stage contract for orchestrator routing |
| `visual-orchestrator/prompts/generation.md` | `.claude/skills/visual-orchestrator/prompts/` | All shot-list generation instructions |
| `shotlist.json` | `projects/N. [Title]/shotlist.json` | Per-video output artifact |

### Existing — No Changes Needed

| Component | Reason |
|-----------|--------|
| `writer` skill | Upstream — already outputs Script.md in correct location |
| `visual-style-extractor` skill | Upstream — already outputs VISUAL_STYLE_GUIDE.md in correct location |
| `channel-assistant` project scaffold | Project directory already created; shotlist.json written directly into it |
| `Architecture.md` shotlist schema | Already defines the baseline; the extended schema is additive |

### Existing — Minor Update Needed

| Component | Change |
|-----------|--------|
| `CLAUDE.md` Task Routing table | Add visual-orchestrator row |
| `CLAUDE.md` "What to Load" table | Add visual planning row |

---

## Build Order

All three skill files are independent — no code imports, no test suite. Build in this order based on validation dependency:

### Step 1: CONTEXT.md

Defines the contract. Other files reference it. Write it first to lock inputs, outputs, and process steps before authoring the prompt.

### Step 2: prompts/generation.md

This is where the reasoning complexity lives. Write it second, with CONTEXT.md's inputs as the anchor. Validate against the Duplessis Script V1.md manually before proceeding — does the prompt produce the expected shot density and building block distribution?

### Step 3: SKILL.md

Write after the prompt is validated. SKILL.md references the prompt file path and guides Claude through the invocation sequence. It is the human-facing entry point.

All three files can be drafted and validated in a single session against the existing Duplessis project artifacts (Script V1.md and the existing shotlist.json as a quality baseline).

---

## Anti-Patterns

### Anti-Pattern 1: Adding a Python CLI

**What people do:** Follow the writer skill's pattern and add `scripts/visual_orchestrator/cli.py` for project directory resolution.

**Why it's wrong:** The visual orchestrator reads two files from known paths. Glob/Bash ls is sufficient for project directory resolution. A CLI adds a scripts/ directory, PYTHONPATH invocation, and untested Python code for zero benefit. style-extraction proves a zero-code approach handles more complex workflows (8 steps with conditional logic).

**Do this instead:** Follow style-extraction. Document project resolution in SKILL.md step 1 as a Glob or Bash operation Claude performs directly.

### Anti-Pattern 2: Two-Pass Shot Generation

**What people do:** Design a "parse" pass (extract narrative beats) then an "assign" pass (match beats to building blocks), following the visual-style-extractor's two-pass architecture.

**Why it's wrong:** Shot generation is linear, not merge-and-synthesize. The beats and building blocks emerge simultaneously as Claude reads the script. Two passes double context usage with no quality improvement — there is no evaluation gate between them.

**Do this instead:** Single pass, linear read, emit shots as narrative beats are encountered.

### Anti-Pattern 3: Embedding the VISUAL_STYLE_GUIDE as Static Prompt Text

**What people do:** Copy-paste the current VISUAL_STYLE_GUIDE building blocks into generation.md as hardcoded content.

**Why it's wrong:** The guide changes when new reference videos are extracted. Embedding makes the prompt stale. It also bloats the generation.md unnecessarily and creates a maintenance hazard.

**Do this instead:** The generation.md instructs Claude to apply the guide it already read in step 2 of SKILL.md. The guide is runtime context, not prompt content.

### Anti-Pattern 4: Enriching the Schema Beyond Agent 2.1's Needs

**What people do:** Add `duration`, `priority`, `mood`, `effects`, `transition`, `color_grade` fields to the shotlist "for the editor."

**Why it's wrong:** Architecture.md is explicit — "No duration, priority, effects, transitions, or post-production instructions — those are the editor's domain." Agent 2.1 uses only visual_need, building_block, and suggested_sources. Extra fields add generation overhead with no consumer.

**Do this instead:** Lock the schema to the canonical fields documented in this file. The only editor-serving exception is `text_content`, which provides the verbatim text for text_overlay shots the editor must place.

### Anti-Pattern 5: Using suggested_types Instead of suggested_sources

**What people do:** Follow the Architecture.md baseline schema which uses `suggested_types` (e.g., `["archival_video", "archival_photo"]`) in the baseline example.

**Why it's wrong:** The actual generated shotlist.json uses `suggested_sources` (domain names like `["archive.org", "wikimedia_commons"]`) and `shotlist_type` separately. `suggested_sources` tells Agent 2.1 where to look; `shotlist_type` tells it what kind of asset to acquire. These serve distinct purposes and must not be conflated.

**Do this instead:** Use `shotlist_type` for the asset type enum; use `suggested_sources` for domain hints. Set `suggested_sources: []` when no domain is more likely than another (e.g., text_overlay shots, or generic b-roll).

---

## Sources

- Direct inspection: `.claude/skills/style-extraction/SKILL.md`, `CONTEXT.md`, `prompts/extraction.md` (HIGH confidence)
- Direct inspection: `.claude/skills/writer/SKILL.md`, `CONTEXT.md`, `prompts/generation.md` (HIGH confidence)
- Direct inspection: `.claude/skills/visual-style-extractor/prompts/synthesis_prompt.txt` — two-pass reference (HIGH confidence)
- Direct inspection: `Architecture.md` — Agent 1.4 spec, Phase 2 schema, asset categories, CRITICAL ARCHITECTURE RULES (HIGH confidence)
- Direct inspection: `projects/1. The Duplessis Orphans.../shotlist.json` — actual generated schema with 60+ shots (HIGH confidence)
- Direct inspection: `projects/1. The Duplessis Orphans.../Script V1.md` — actual Script.md format (HIGH confidence)
- `.planning/PROJECT.md` — v1.3 milestone requirements (HIGH confidence)

---
*Architecture research for: Visual Orchestrator (Agent 1.4) — pure heuristic skill integration into Channel Automation Pipeline v1.3*
*Researched: 2026-03-15*
