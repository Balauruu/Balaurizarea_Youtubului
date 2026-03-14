# Architecture Research

**Domain:** Documentary pipeline — style extraction and script generation (v1.2)
**Researched:** 2026-03-14
**Confidence:** HIGH (direct codebase inspection of all existing skills)

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Claude Code (Orchestrator)                         │
│          Dispatches skills, performs all [HEURISTIC] reasoning        │
├──────────────┬──────────────┬──────────────┬────────────────────────-┤
│  Agent 1.1   │  Agent 1.2   │  Skill 1.3   │     Agent 1.3           │
│  channel-    │  researcher  │  style-      │     writer              │
│  assistant   │              │  extraction  │     (NEW)               │
│  (existing)  │  (existing)  │  (NEW)       │                         │
└──────┬───────┴──────┬───────┴──────┬───────┴──────────┬──────────────┘
       |              |              |                  |
       v              v              v                  v
┌──────────────────────────────────────────────────────────────────────┐
│                      Filesystem (shared state)                        │
├─────────────────┬──────────────────┬────────────────────────---------┤
│ context/        │ projects/N.Title/ │ context/script-references/      │
│ channel/        │ research/         │ (reference scripts - read-only) │
│ channel.md      │   Research.md     │                                 │
│ STYLE_PROFILE.md│ script/           │                                 │
│ (NEW)           │   Script.md (NEW) │                                 │
└─────────────────┴──────────────────┴─────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Classification | Status |
|-----------|----------------|----------------|--------|
| `channel-assistant` | Competitor intel, topic briefs, project init | DETERMINISTIC + HEURISTIC | Existing - no changes |
| `researcher` | Two-pass web research → Research.md | DETERMINISTIC + HEURISTIC | Existing - no changes |
| `style-extraction` skill | One-time: read reference scripts, produce STYLE_PROFILE.md | HEURISTIC only | NEW |
| `writer` skill | Per-video: Research.md + STYLE_PROFILE.md → Script.md | HEURISTIC + minimal DETERMINISTIC | NEW |

---

## Recommended Project Structure

```
.claude/skills/
├── channel-assistant/           # Existing - no changes
├── researcher/                  # Existing - no changes
├── style-extraction/            # NEW skill (one-time, no Python code)
│   ├── SKILL.md                 # Workflow instructions for Claude
│   └── prompts/
│       └── extract.md           # Style extraction prompt and output schema
└── writer/                      # NEW skill (per-video)
    ├── SKILL.md                 # Workflow instructions for Claude
    ├── scripts/
    │   └── writer/
    │       ├── __init__.py
    │       ├── __main__.py
    │       └── cli.py           # Single 'load' subcommand
    └── prompts/
        └── write_script.md      # Script generation rules and output schema

context/
├── channel/
│   ├── channel.md               # Existing - Channel DNA
│   ├── past_topics.md           # Existing
│   └── STYLE_PROFILE.md         # NEW - written once by style-extraction
└── script-references/
    └── Mexico's Most Disturbing Cult.md  # Existing reference script

projects/
└── N. [Video Title]/
    ├── metadata.md              # Existing - from channel-assistant
    ├── research/
    │   ├── Research.md          # Existing - from researcher
    │   └── media_urls.md        # Existing - from researcher
    └── script/                  # Existing scaffold dir - writer fills it
        └── Script.md            # NEW output
```

### Structure Rationale

- **style-extraction/ has no scripts/ directory:** It is a pure [HEURISTIC] operation. Claude reads reference scripts and writes STYLE_PROFILE.md directly using the Write tool. The only implementation artifacts are SKILL.md and the extract.md prompt.
- **writer/ has a thin scripts/ directory:** One CLI subcommand (`load`) aggregates context files and prints to stdout for Claude to reason over — identical to the `researcher write` pattern where code prepares input and Claude produces output.
- **STYLE_PROFILE.md lives in context/channel/:** It is channel-level context, not project-specific. Written once, reused across every video. Parallel to channel.md and past_topics.md.
- **Script.md goes into projects/N. Title/script/:** The `script/` directory is already created by `channel-assistant`'s `project_init.py` scaffold. Writer fills it without creating directories.

---

## Architectural Patterns

### Pattern 1: CLI Prints, Claude Reasons (established convention)

All existing skills follow the same contract: Python CLI does [DETERMINISTIC] work (file I/O, aggregation, path resolution), prints structured data to stdout, and Claude performs [HEURISTIC] reasoning natively in-context.

**What:** The `load` subcommand reads three files — Research.md, STYLE_PROFILE.md, channel.md — concatenates them with clear section headers, and prints to stdout. Claude receives this in its context window and generates the script.

**Reference implementation (from researcher SKILL.md):**
```
researcher write "Topic"  ->  aggregates sources, prints synthesis_input.md path
Claude reads file          ->  reads synthesis.md prompt
Claude writes              ->  Research.md + media_urls.md
```

**Writer equivalent:**
```
writer load "Topic"   ->  prints Research.md + STYLE_PROFILE.md + channel.md to stdout
Claude reads          ->  reads write_script.md prompt
Claude writes         ->  projects/N. Title/script/Script.md
```

### Pattern 2: Prompt File Encodes Output Schema and Rules

Both existing skills put all generation instructions in `.claude/skills/[name]/prompts/` files. SKILL.md references them by path. Code never embeds generation logic.

**What:** The write_script.md prompt defines chapter structure, narration rules, word count targets, anti-patterns, and output format. The extract.md prompt defines what STYLE_PROFILE.md sections to produce and how to read reference scripts.

**Trade-offs:** Prompts are cheap to iterate without touching Python code. They also make the reasoning contract explicit, inspectable, and versionable via git.

### Pattern 3: One-Time vs Per-Run Operations

Style extraction is a setup operation: run once when setting up the channel, re-run only when new reference scripts are added. Writer runs once per video.

**What:** style-extraction has no CLI entry point. Its SKILL.md describes a single workflow: read all files in `context/script-references/`, apply the extract.md prompt, write `context/channel/STYLE_PROFILE.md`. No loop, no incremental state.

**When to update STYLE_PROFILE.md:** Only when a new high-performing video is added to `context/script-references/` and the style profile needs to reflect it.

---

## Data Flow

### Style Extraction Flow (one-time, channel setup)

```
context/script-references/
    [one or more reference script files]
         |
         | (Claude reads directly via Read tool)
         v
[HEURISTIC] apply prompts/extract.md
         |
         v
context/channel/STYLE_PROFILE.md
    (committed to repo, shared across all future videos)
```

### Script Generation Flow (per video)

```
projects/N. Title/research/Research.md   -+
context/channel/STYLE_PROFILE.md          +-> writer load "Topic"
context/channel/channel.md               -+        |
                                                    | (printed to stdout)
                                                    v
                                        [HEURISTIC] write_script.md prompt
                                                    |
                                                    v
                                    projects/N. Title/script/Script.md
```

### Full v1.2 Pipeline (all phases combined)

```
channel-assistant -> projects/N. Title/ (metadata.md + directory scaffold)
                                    |
researcher        -> projects/N. Title/research/Research.md
                                    |
style-extraction  -> context/channel/STYLE_PROFILE.md (one-time, already done)
                                    |
                    writer load "Topic" (merges all context)
                                    |
                    [HEURISTIC] generate script
                                    |
                    projects/N. Title/script/Script.md
```

### Key Data Flows

1. **Research.md is the primary writer input:** The writer consumes only Research.md from the research directory. Raw source files (src_*.json, synthesis_input.md) are not needed — Research.md already distills them into a scriptwriter-optimized dossier.
2. **STYLE_PROFILE.md is shared, stable state:** Treat it like channel.md — stable channel-level context that does not change per video.
3. **Project path resolution:** writer's `load` command uses the same directory-matching logic as researcher — walk `projects/` and match on topic string. This pattern is established and must be reused, not reimplemented differently.
4. **script/ directory already exists:** `channel-assistant`'s `project_init.py` creates the `script/` subdirectory in the project scaffold. Writer writes directly into it with no directory creation logic required.

---

## New vs. Modified Components

### New (does not exist yet)

| Component | Location | What It Is |
|-----------|----------|------------|
| `style-extraction/SKILL.md` | `.claude/skills/style-extraction/` | Workflow instructions — no Python code |
| `style-extraction/prompts/extract.md` | `.claude/skills/style-extraction/prompts/` | Style extraction prompt + STYLE_PROFILE.md schema |
| `context/channel/STYLE_PROFILE.md` | `context/channel/` | Output of style-extraction — committed to repo |
| `writer/SKILL.md` | `.claude/skills/writer/` | Workflow instructions |
| `writer/scripts/writer/cli.py` | `.claude/skills/writer/scripts/writer/` | `load` subcommand — context aggregation only |
| `writer/prompts/write_script.md` | `.claude/skills/writer/prompts/` | Script generation rules + output schema |
| `projects/N. Title/script/Script.md` | `projects/N. Title/script/` | Per-video output |

### Existing — No Changes Needed

| Component | Reason |
|-----------|--------|
| `channel-assistant` | Upstream — already creates project scaffold including `script/` dir |
| `researcher` | Upstream — already writes Research.md in correct location |
| `projects/N. Title/research/Research.md` | Writer reads this as-is |
| `context/channel/channel.md` | Writer reads this as-is |
| `context/script-references/` | Style-extraction reads this as-is |
| `project_init.py` scaffold | Already creates `script/` subdirectory |

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| researcher → writer | File: `projects/N. Title/research/Research.md` | Writer reads directly, no modification needed |
| style-extraction → writer | File: `context/channel/STYLE_PROFILE.md` | One-time write, per-run read |
| channel-assistant → writer | Directory structure: `projects/N. Title/script/` already exists | Writer does not need to create directories |
| writer → editor (DaVinci Resolve) | File: `projects/N. Title/script/Script.md` | Terminal output — no downstream agent in v1.2 |

### External Services

None. Both new skills operate entirely on filesystem content already in the repo. No web scraping, no API calls, no new dependencies.

---

## Build Order

Sequence is determined by validation dependencies — you cannot test the writer without STYLE_PROFILE.md:

### Step 1: style-extraction skill (SKILL.md + extract.md prompt)

No Python code to write. The entire implementation is two files. Run it immediately against `context/script-references/Mexico's Most Disturbing Cult.md` to produce STYLE_PROFILE.md. Validate the output before proceeding. This is the prerequisite for meaningful writer testing.

**Deliverable:** `context/channel/STYLE_PROFILE.md` committed to repo.

### Step 2: writer prompts/write_script.md

Write the script generation prompt before the CLI, because the prompt structure determines what context the CLI needs to load. The prompt defines: chapter structure, word count targets, narration voice rules, section schema, anti-patterns.

**Deliverable:** Reviewable prompt that can be evaluated against STYLE_PROFILE.md for coherence before any code is written.

### Step 3: writer scripts/writer/cli.py (load subcommand)

Simple file aggregation: resolve project directory from topic string, read Research.md, read STYLE_PROFILE.md, read channel.md, print concatenated output to stdout with clear section headers. Write tests for path resolution logic.

**Deliverable:** `writer load "Topic"` prints assembled context to stdout.

### Step 4: writer SKILL.md

Write complete workflow instructions after both the prompt and CLI are validated. SKILL.md references both: it tells Claude to run `writer load`, then read write_script.md, then produce Script.md.

**Deliverable:** Complete skill with testable end-to-end workflow.

### Step 5: End-to-end validation

Run the full v1.2 pipeline against the existing Duplessis Orphans project, which already has a completed Research.md. This is the integration test — produce the first real Script.md and evaluate it against the channel's quality standards.

---

## Anti-Patterns

### Anti-Pattern 1: Embedding Style Rules Directly in write_script.md

**What people do:** Hardcode narration style instructions (sentence length, vocabulary register, pacing ratios) directly in write_script.md instead of referencing STYLE_PROFILE.md.

**Why it's wrong:** Hardcoded rules drift away from actual reference scripts as the channel evolves. Updating them requires editing the prompt. STYLE_PROFILE.md is generated from actual reference scripts, so it stays grounded.

**Do this instead:** write_script.md instructs Claude to apply STYLE_PROFILE.md. All specific style rules live in STYLE_PROFILE.md, updated by re-running style-extraction when the reference library changes.

### Anti-Pattern 2: Passing Raw Research Sources to the Writer

**What people do:** Give the writer access to synthesis_input.md or src_*.json files for "richer context."

**Why it's wrong:** Research.md already distills 40,000+ words of scraped source material into ~2,000 words of curated, scriptwriter-optimized content including narrative hooks, timeline, contradictions, and key figures. Raw sources add noise and bloat without improving script quality.

**Do this instead:** Writer reads only Research.md. If the dossier lacks something, fix the researcher's synthesis.md prompt — that is where the curation decision belongs.

### Anti-Pattern 3: Regenerating STYLE_PROFILE.md Per Video

**What people do:** Run style-extraction at the start of every video production to "stay fresh."

**Why it's wrong:** STYLE_PROFILE.md represents stable channel DNA — patterns extracted from reference scripts. Regenerating it per-run adds latency, introduces noise from per-run variation, and undermines the purpose of having a stable style guide.

**Do this instead:** Run style-extraction once. Commit STYLE_PROFILE.md. Update reactively when a new high-performing video is added to `context/script-references/`.

### Anti-Pattern 4: Adding LLM API Calls to the Writer CLI

**What people do:** Add script generation logic to cli.py using an LLM SDK, following the naive "code for generation" pattern.

**Why it's wrong:** Architecture.md Rule 1 prohibits LLM API wrappers. Claude Code is the runtime. Script generation is entirely [HEURISTIC] — it requires no deterministic code beyond context loading.

**Do this instead:** cli.py does one thing: aggregate and print context. Claude does all script generation natively using the write_script.md prompt.

### Anti-Pattern 5: Having style-extraction Write to the Project Directory

**What people do:** Put STYLE_PROFILE.md in `projects/N. Title/` alongside Research.md, treating it as a per-video artifact.

**Why it's wrong:** Writing style is a channel-level property, not a per-video property. Putting it in the project directory requires re-extraction for every new video, and breaks the separation between channel context and project context that the existing architecture maintains.

**Do this instead:** STYLE_PROFILE.md lives in `context/channel/`, same tier as channel.md. It is channel context, not project context.

---

## Sources

- Direct inspection: `.claude/skills/researcher/SKILL.md` and `cli.py` (HIGH confidence)
- Direct inspection: `.claude/skills/channel-assistant/SKILL.md` and `project_init.py` (HIGH confidence)
- Direct inspection: `.claude/skills/researcher/prompts/synthesis.md` — output schema reference (HIGH confidence)
- Direct inspection: `projects/1. The Duplessis Orphans.../research/Research.md` — confirmed existing dossier format (HIGH confidence)
- Direct inspection: `context/script-references/Mexico's Most Disturbing Cult.md` — confirmed reference script format (HIGH confidence)
- `Architecture.md` — CRITICAL ARCHITECTURE RULES (binding project constraints) (HIGH confidence)
- `.planning/PROJECT.md` — v1.2 milestone requirements and key decisions table (HIGH confidence)

---
*Architecture research for: style extraction and script generation — Channel Automation Pipeline v1.2*
*Researched: 2026-03-14*
