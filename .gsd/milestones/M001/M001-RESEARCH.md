# Project Research Summary

**Project:** Channel Automation v1.2 — "The Writer"
**Domain:** Prompt-driven style extraction and automated script generation for documentary video pipeline
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

This milestone adds two skills to a working agentic pipeline (v1.1 ships Channel Assistant + Researcher): Skill 1.3 (Style Extraction) and Agent 1.3 (The Writer). Both are almost entirely [HEURISTIC] operations — Claude Code does the reasoning natively, and the only deterministic code required is a thin context-loader CLI that aggregates files and prints them to stdout. The recommended approach is to resist the pull toward NLP libraries, LLM SDKs, and complex templating in favor of prompt files and stdlib-only Python. Zero new pip dependencies are required.

The core insight from combined research: this is a prompt engineering problem, not a software engineering problem. STYLE_PROFILE.md is the key artifact — it must contain craft-oriented behavioral rules with verbatim examples from the reference script, not statistical summaries. The Writer's quality ceiling is determined by how precisely the synthesis prompt names the channel's deadpan-neutral voice patterns and how explicitly it instructs use of Research.md's HOOK/QUOTE callouts as narrative anchors. The build order is sequential and non-negotiable: style extraction must be validated before meaningful writer testing can begin.

The primary risk is misclassification — defaulting to deterministic code for tasks that are inherently heuristic. The Architecture.md HEURISTIC/DETERMINISTIC rule is the explicit guard against this. A secondary risk is context saturation: loading too many files into the Writer's generation context degrades output quality in the later chapters of the script. The research identifies a hard budget of 8,000 words of total context at generation time. Both risks are avoidable by strictly applying the classification rule before touching a keyboard.

---

## Key Findings

### Recommended Stack

The v1.0/v1.1 stack is unchanged and requires no re-evaluation. For v1.2 specifically, zero new third-party dependencies are needed. All deterministic work uses Python stdlib: `re` for sentence splitting, `collections.Counter` for word frequency, `statistics` for length distribution, `pathlib` for file operations, and `argparse` for the CLI. This is the correct outcome for a primarily heuristic milestone — the deterministic layer is intentionally thin by design.

**Core technologies:**
- `re` (stdlib): Sentence splitting and pattern detection for style metric computation — no third-party tokenizer needed for transcribed speech input
- `collections` (stdlib): Word frequency and vocabulary analysis via Counter — already idiomatic in the channel-assistant codebase
- `statistics` (stdlib): Sentence length distribution (mean, median, stdev) — anchors quantitative surface metrics in STYLE_PROFILE.md
- `pathlib` (stdlib): File discovery and project path resolution — already the project standard per CLAUDE.md
- `argparse` (stdlib): CLI argument parsing — same pattern as researcher and channel-assistant CLIs

**Explicitly rejected:** textstat (wrong signal — readability indices do not capture voice patterns), spaCy (50MB install for POS tagging that adds nothing on transcribed speech input), NLTK (heavy corpus downloads, no advantage over stdlib for this use case), LangChain/LlamaIndex (violates Architecture.md Rule 1 — zero LLM API wrappers), any LLM embedding library (style similarity is Claude's job, not cosine distance).

### Expected Features

The Writer milestone delivers two features. Style extraction is a one-time channel setup operation; script generation is a per-video production step. Both feed directly into the downstream Visual Orchestrator (Agent 1.4, future milestone), so the script output format must be stable.

**Must have (table stakes):**
- Style extraction prompt that produces STYLE_PROFILE.md with craft-oriented behavioral rules and verbatim examples — not statistics or readability scores
- STYLE_PROFILE.md stored in `context/channel/` as stable channel-level context (parallel to channel.md, not inside any project directory)
- Writer SKILL.md: numbered chapter structure, pure narration output, no stage directions or embedded production notes
- Factual anchoring: every claim in the script traceable to Research.md — Writer does not generate facts from training memory
- HOOK/QUOTE integration: Writer prompt explicitly instructs use of Research.md callouts as chapter entry points and narration anchors
- Script word count in target range: 3,000–7,000 words (20–50 min runtime per channel.md output targets)
- Channel tone enforcement: calm, journalistic, deadpan — achieved by loading STYLE_PROFILE.md + channel.md as generation context

**Should have (differentiators):**
- Transition phrase library extracted verbatim from reference script — prevents generic connective language ("furthermore", "notably") that breaks the deadpan register
- Pacing profile: slow historical build for first third, escalation to horror — qualitative instruction, not a hard word-count ratio
- Open-ending template derived from reference — prevents LLMs from artificially resolving ambiguity in unsolved cases (explicit style rule in writting_style_guide.md)
- Chapter title generation in the reference register: evocative short titles ("Strangers in the Jungle") rather than generic labels ("Background", "Chapter 1")
- Source authority woven into narration naturally ("court records from 1962 show...") without disrupting pacing
- STYLE_PROFILE.md distinguished into "Universal Voice Rules" vs. "Narrative Arc Templates by story type" — avoids cult-topic arc template overfitting to non-cult topics

**Defer (v2+):**
- Chapter outline approval checkpoint before full script generation — add reactively only if full scripts frequently need structural revision
- Multiple script variants for A/B testing — doubles review work, no feedback loop exists yet
- Style drift detection across generated scripts — needs more than one reference to establish a meaningful baseline
- TTS/voiceover generation — out of scope per Architecture.md; audio is handled in DaVinci Resolve

### Architecture Approach

Both new skills extend the established "CLI prints, Claude reasons" pattern used by all existing skills. The style-extraction skill has no Python code at all — two files only (SKILL.md + extract.md prompt). The writer skill adds a thin `cli.py` with a single `load` subcommand that aggregates Research.md + STYLE_PROFILE.md + channel.md and prints to stdout. Claude performs all generation natively from that context. No new architectural concepts are introduced — both skills are direct applications of patterns already proven in researcher and channel-assistant.

**Major components:**
1. `style-extraction/SKILL.md` + `prompts/extract.md` — One-time channel setup: reads reference scripts, writes STYLE_PROFILE.md. Pure heuristic, zero Python code written
2. `context/channel/STYLE_PROFILE.md` — Stable channel-level artifact: written once by style-extraction, read by every Writer invocation. Lives at the same tier as channel.md
3. `writer/scripts/writer/cli.py` — Thin context aggregator: resolves project path from topic string, reads three files, prints to stdout. Single `load` subcommand, identical pattern to researcher's CLI
4. `writer/prompts/write_script.md` — Script generation rules: chapter structure defined by narrative logic (not word count), voice constraints with verbatim examples, explicit Research.md reading instructions, output format specification
5. `projects/N. Title/script/Script.md` — Per-video terminal output: first-class production artifact (not scratch), feeds Agent 1.4 in the next milestone

**Build sequence (non-negotiable order):** style-extraction SKILL.md and extract.md prompt → validate STYLE_PROFILE.md output → writer prompts/write_script.md → writer cli.py → writer SKILL.md → end-to-end validation against Duplessis Orphans Research.md.

### Critical Pitfalls

1. **Style extraction implemented as NLP code instead of a prompt** — Any Python file created for style extraction is a classification error. STYLE_PROFILE.md must contain behavioral rules with examples ("sentences fragment mid-thought at revelation moments to force a beat") not statistics ("average sentence length: 14.2 words"). If the profile describes what the text IS rather than how it WORKS, discard and re-run with a corrected prompt.

2. **Script loses channel voice within the first chapter** — LLMs default to "competent documentary narrator" when given research + vague style instructions. Break the default with: verbatim reference script excerpts labeled with what they demonstrate, explicit prohibitions (no rhetorical questions, no "imagine if you will", no emotional signposting like "shockingly"), and the channel's specific deadpan device named and demonstrated. Validate the prompt against the Duplessis Orphans Research.md before considering the prompt finished.

3. **Research.md HOOK/QUOTE callouts ignored in script output** — Agent 1.2 embeds explicit narrative signal callouts in the dossier specifically for the Writer. The Writer's synthesis prompt must contain reading instructions: "The HOOK is the story's entry point — build the introduction around it, not buried in chapter 2." "QUOTE callouts anchor the chapter they appear in — they are not summary material." The handoff is a structured reading instruction, not a file path.

4. **Context saturation degrades second-half chapter quality** — Hard budget: 8,000 words of total input context at generation time. Curated package: Research.md + STYLE_PROFILE.md (relevant sections only) + reference script excerpt (intro + one chapter, not the full script) + channel.md executive summary (first 200 words). Do not load ResearchArchive.md, raw source files, or past_topics.md at generation time.

5. **LLM API wrapper introduced for quality evaluation or any other step** — Any `import anthropic` or `import openai` in writer skill scripts is an Architecture.md Rule 1 violation. Script quality evaluation is [HEURISTIC] — Claude reads the output and evaluates natively in the same session. No code evaluates script quality.

---

## Implications for Roadmap

Based on combined research, two phases cover the entire milestone. Both are tightly coupled by validation dependencies — Phase 1 must complete and produce a validated STYLE_PROFILE.md before Phase 2 has any meaningful tests to run.

### Phase 1: Style Extraction Skill

**Rationale:** STYLE_PROFILE.md is a prerequisite for meaningful Writer testing. Without it, writer output cannot be evaluated against the channel's voice — you have no anchor. This phase has zero code to write (pure heuristic), so it completes quickly and unblocks Phase 2 immediately. The sooner STYLE_PROFILE.md is committed to the repo, the sooner all downstream work has stable channel DNA to reference.

**Delivers:** `context/channel/STYLE_PROFILE.md` committed to the repository as stable channel-level context. Also delivers `.claude/skills/style-extraction/SKILL.md` and `prompts/extract.md`.

**Addresses (features):** STYLE_PROFILE.md with craft-oriented behavioral rules, transition phrase library, pacing profile, open-ending template, "Universal Voice Rules" vs. "Narrative Arc Templates" distinction (mitigates single-reference overfitting to cult topic type).

**Avoids:** Pitfall 1 (style extraction as NLP code — classify as HEURISTIC before any file is created), Pitfall 3 (single-reference profile forcing cult arc onto non-cult topics — design the profile format to accommodate multiple arc templates from the start), Pitfall 7 (STYLE_PROFILE.md drifting via in-place edits — set the versioning and regeneration policy before the first profile is written).

### Phase 2: Writer Agent

**Rationale:** Depends directly on Phase 1 output. The write_script.md prompt is written before the CLI because the prompt structure determines what context the CLI needs to load and print. Validated against the existing Duplessis Orphans Research.md as an integration test — this project has a completed dossier, so no new research work is required to run the first real end-to-end script generation.

**Delivers:** `writer/SKILL.md`, `writer/prompts/write_script.md`, `writer/scripts/writer/cli.py`, and `projects/1. The Duplessis Orphans.../script/Script.md` as the integration test output.

**Uses (stack):** stdlib only — `pathlib`, `argparse`. No new installs required.

**Implements (architecture):** "CLI prints, Claude reasons" pattern (established convention from researcher and channel-assistant). Project path resolution via directory matching — reuse researcher's pattern exactly, do not reimplement. Context aggregation: Research.md + STYLE_PROFILE.md + channel.md printed to stdout with clear section headers.

**Avoids:** Pitfall 2 (script loses channel voice — use verbatim examples and explicit prohibitions in write_script.md), Pitfall 4 (Research.md hooks lost in handoff — explicit reading instructions in synthesis prompt, not in a comment or readme), Pitfall 5 (LLM API wrapper for evaluation — evaluation is heuristic, no code), Pitfall 6 (formatting constraints override narrative logic — chapter breaks defined by narrative beats, not word count thresholds), Pitfall 8 (context saturation — enforce 8,000-word context budget before writing the generation prompt).

### Phase Ordering Rationale

- Style extraction must precede script generation because the Writer has no validated voice anchor without STYLE_PROFILE.md. Running Phase 2 before Phase 1 produces untestable output with no quality baseline.
- Within Phase 2, write_script.md must precede cli.py because the prompt defines the required context package, which determines what the CLI loads. Writing the CLI first produces a loader that may not serve the actual generation needs.
- SKILL.md for the writer is written last — after both prompt and CLI are validated — because SKILL.md references both and must accurately describe a tested, working workflow.
- End-to-end validation against the Duplessis Orphans project is the terminal step, not an optional check. It is the only meaningful integration test because it exercises the full pipeline on a real topic with a completed Research.md dossier.

### Research Flags

Phases with standard patterns (no deeper research needed during planning):
- **Phase 1 (Style Extraction):** No code, pure prompt design. Classification is HEURISTIC per Architecture.md Rule 2. No unknowns to research — the only variable is STYLE_PROFILE.md output quality, which is validated empirically by running the extraction and reviewing the result.
- **Phase 2 (Writer Agent):** CLI follows the researcher's established pattern exactly. The prompt engineering variables are fully documented by pitfalls research (8 specific failure modes with prevention strategies). No deeper technical research needed.

No phases require `/gsd:research-phase` during planning. Both phases are well-defined by direct codebase inspection and Architecture.md constraints. The only open question is whether the single reference script produces a STYLE_PROFILE.md that generalizes adequately to non-cult topic types — this is validated in Phase 1, not researched in advance.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies — all stdlib. No version conflicts possible. Confirmed by direct codebase analysis of existing channel-assistant and researcher skills, both stdlib-only. |
| Features | HIGH | Derived from direct analysis of existing reference script, channel.md, writting_style_guide.md, Architecture.md spec, and the live Duplessis Orphans Research.md. Feature boundaries driven by the HEURISTIC/DETERMINISTIC rule, which is explicit and binding. No speculation involved. |
| Architecture | HIGH | Based on direct inspection of all existing skills. Both new skills extend established patterns without introducing new concepts. Build order is determined by validation dependencies, not preference. |
| Pitfalls | HIGH | Pitfalls derived from Architecture.md Rules 1 and 2 (binding constraints), direct analysis of the degraded reference script format, and documented LLM behavior patterns in long-context generation (RULER, InfiniteBench benchmarks). Prevention strategies map to specific, actionable prompt engineering decisions. |

**Overall confidence:** HIGH

### Gaps to Address

- **Single reference script limits STYLE_PROFILE.md coverage:** STYLE_PROFILE.md will be derived from one reference (`Mexico's Most Disturbing Cult.md`), which is a cult/group narrative — not all topic types on the channel. Mitigate by explicitly labeling profile sections as "universal voice rules" vs. "cult arc template (one reference only)." Add a second reference when a clean transcript becomes available for a non-cult topic (institutional corruption, disappearance, or dark web topic).
- **Auto-caption format degrades quantitative style metrics:** The reference script is a YouTube auto-caption export with no punctuation and arbitrary line breaks. Sentence boundary detection and length distribution will have lower signal quality than a properly punctuated transcript. The extraction prompt must work qualitatively — inferring rhythm from line groupings and narrative structure from chapter headers — rather than quantitatively. This is acknowledged and handled in the prompt design approach; it is not a blocker.
- **Script quality validation is manual at launch:** There is no automated way to verify a generated script matches the channel's voice. The validation step is human review of the Duplessis Orphans script against the reference. This is by design (heuristic task), but it means iteration speed depends on reviewer availability. Add a pacing audit heuristic (post-generation word count per chapter review) as a secondary check in v1.x after the first scripts are validated.

---

## Sources

### Primary (HIGH confidence)

- `.claude/skills/researcher/SKILL.md` and `cli.py` — established "CLI prints, Claude reasons" pattern that writer replicates directly
- `.claude/skills/channel-assistant/SKILL.md` and `project_init.py` — confirmed that scaffold already creates `script/` subdirectory; writer needs no directory creation logic
- `Architecture.md` — CRITICAL ARCHITECTURE RULES (binding project constraints): Rule 1 (zero LLM API wrappers), Rule 2 (HEURISTIC vs. DETERMINISTIC classification)
- `context/script-references/Mexico's Most Disturbing Cult.md` — confirmed reference script format (auto-caption, degraded), chapter structure, voice patterns, transition phrases
- `context/channel/channel.md` — channel DNA, tone rules, audience profile, output targets (3,000–7,000 words, 20–50 min)
- `context/channel/writting_style_guide.md` — six style rules: narration-only, chapters, pacing, sources, silence, open endings
- `projects/1. The Duplessis Orphans.../research/Research.md` — confirmed live dossier format, HOOK/QUOTE callout structure, word count
- `.planning/PROJECT.md` — v1.2 milestone definition, key decisions log

### Secondary (MEDIUM confidence)

- Programming Historian: Introduction to Stylometry with Python — validated TTR, sentence length, punctuation density as standard stylometric features for style analysis
- LLM long-context behavior (RULER, InfiniteBench benchmarks) — quality degradation in second half of long-form outputs under high input load; informed the 8,000-word context budget recommendation

### Tertiary (LOW confidence)

- LLM default to "competent but generic" documentary narrator mode — observed behavior pattern documented in multiple creative writing evaluation contexts; overridden by verbatim examples and explicit prohibitions rather than by abstract style descriptions

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*

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

# Stack Research

**Domain:** Style Extraction and Script Generation (Agent 1.3 — The Writer)
**Researched:** 2026-03-14
**Confidence:** HIGH

> **Scope:** This document covers stack additions for v1.2 only. The validated v1.0/v1.1 stack (Python, SQLite stdlib, yt-dlp, crawl4ai, trafilatura, requests, difflib, beautifulsoup4, internetarchive) is unchanged. Do not re-evaluate those decisions.
>
> **Architecture reminder:** Architecture.md Rule 2 — classify before building. Style extraction is [HEURISTIC]: Claude reasons over the reference script and produces STYLE_PROFILE.md. Script generation is [HEURISTIC]: Claude reads Research.md + STYLE_PROFILE.md and writes the narration. The only [DETERMINISTIC] work is the CLI that assembles and prints context files for Claude to consume.

---

## What v1.2 Needs That v1.1 Does Not Have

Two deliverables, both primarily prompt-driven:

1. **Style extraction** — a one-time operation that reads `context/script-references/*.md` and produces a `STYLE_PROFILE.md` capturing sentence rhythm, vocabulary register, chapter structure, and pacing. Claude does the reasoning; a small deterministic layer quantifies surface metrics (sentence lengths, word counts, punctuation density) to anchor the prompt.

2. **Script generation** — an agent that reads Research.md + STYLE_PROFILE.md + channel DNA and produces numbered chapters with pure narration. This is 100% [HEURISTIC]. No deterministic code beyond a CLI context-loader.

The reference scripts are plain `.md` files (YouTube auto-transcription text, as seen in `context/script-references/Mexico's Most Disturbing Cult.md`). They are already clean prose — no HTML, no PDF, no scraped content. This means the extraction problem is straightforward text processing, not NLP pipeline complexity.

---

## Recommended Stack Additions

### Core: Style Metric Extraction

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `re` (stdlib) | stdlib | Sentence splitting, pattern detection | The reference scripts are transcribed speech — no consistent punctuation. Sentences must be split on `.`, `?`, `!` with basic heuristics (abbreviation handling). `re.split()` covers this with a 10-line pattern. No third-party tokenizer needed for this input format. |
| `collections` (stdlib) | stdlib | Word frequency, vocabulary analysis | `Counter` computes type-token ratio, top-N word frequencies, and chapter word counts. Zero install. Already used idiomatically in the channel-assistant codebase. |
| `statistics` (stdlib) | stdlib | Sentence length distribution | `statistics.mean()`, `statistics.median()`, `statistics.stdev()` compute the sentence length stats (mean words/sentence, standard deviation). These numbers go into STYLE_PROFILE.md as anchors for Claude's generation prompt. |

**Why NOT textstat (0.7.8):** textstat computes Flesch-Kincaid, Gunning Fog, and other readability scores that measure how hard text is to read for a general audience. These metrics are not useful for style replication. The channel's writing style goal is not "readable" in the academic sense — it is "neutral, cinematic, deadpan." Readability indices do not capture sentence rhythm, vocabulary register, or narrative pacing. textstat adds a dependency that solves the wrong problem.

**Why NOT spaCy (3.8.11, 11MB model):** spaCy provides POS tagging, dependency parsing, NER, and lemmatization. These would be useful if the style profile needed to classify noun phrases, passive voice frequency, or syntactic complexity. For this use case — transcribed speech from a documentary narrator — the style signal lives in sentence length distribution, clause-level punctuation rhythm, and chapter structure. These are all computable with `re` and `collections`. spaCy adds a 50MB install (core + model), a `python -m spacy download en_core_web_sm` step, and an `import spacy; nlp = spacy.load()` startup overhead for metrics that `str.split()` and `re` can compute directly. The v1.0 Key Decisions established "stdlib-only where possible" — this is a direct application. The Agent 1.2 STACK.md explicitly ruled out spaCy for the same reason.

**Why NOT NLTK:** NLTK is older than spaCy, heavier (3.7GB+ corpus downloads), and designed for academic text analysis. Same conclusion as spaCy: wrong tool for this input type.

### Supporting: Context-Loader CLI

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pathlib` (stdlib) | stdlib | File discovery and reading | Glob `context/script-references/*.md` and `projects/N. [Title]/Research.md`. Already the project standard for all file operations per CLAUDE.md. |
| `argparse` (stdlib) | stdlib | CLI argument parsing | The writer skill needs a CLI that accepts `--project-dir` and `--mode` (extract-style | generate-script). Same pattern as researcher's `cli.py`. |

No new third-party dependencies for the context-loader. It reads files and prints structured context — identical to the pattern in `researcher/cli.py` and `channel-assistant/cli.py`.

---

## Installation

```bash
# No new pip installs required for v1.2.
# All needed libraries are Python stdlib:
#   re, collections, statistics, pathlib, argparse, json, datetime

# Confirm Python version (should be 3.10+ for match/case syntax if used)
python --version
```

**Total new hard dependencies: 0.** This is the correct outcome for a primarily [HEURISTIC] milestone. The deterministic layer is thin by design.

---

## What the Deterministic Layer Actually Does

The style extractor script (`writer/style_extractor.py`) has one job: compute quantifiable surface metrics from a reference script and write a JSON snapshot that Claude's synthesis prompt can reference. Claude does all the qualitative interpretation.

**Metrics to compute (all via stdlib):**

| Metric | How Computed | Why It Matters |
|--------|--------------|----------------|
| Mean sentence word count | `re.split()` + `statistics.mean()` | Deadpan narration runs long sentences; knowing the mean anchors Claude |
| Sentence length std deviation | `statistics.stdev()` | Low stdev = uniform cadence; high stdev = varied rhythm |
| Chapter count and avg chapter word count | Split on `^\d+\.` chapter headers | Establishes act structure expectations |
| Type-Token Ratio | `len(set(words)) / len(words)` | Measures vocabulary richness — low TTR = repetitive, high = varied |
| Top-50 most frequent words | `Counter(words).most_common(50)` | Reveals vocabulary register (formal vs. colloquial) |
| Punctuation density | count `,` `;` `:` per 100 words | Reveals clause-level rhythm and pause frequency |
| Sentence-opening patterns | first word of each sentence | Shows whether narrator favors subject-first or transition-phrase openings |

This JSON snapshot feeds into a synthesis prompt file (`prompts/style_synthesis.md`) that Claude reads to write STYLE_PROFILE.md. STYLE_PROFILE.md is the writer-facing output — a plain markdown file Claude loads when generating the script.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| stdlib `re` + `statistics` | textstat 0.7.8 | Use textstat if you need Flesch-Kincaid or academic readability scores for a different feature (e.g., comparing script complexity to competitors). Not needed here. |
| stdlib `re` + `statistics` | spaCy 3.8.11 + en_core_web_sm | Use spaCy if a future milestone needs POS-based analysis (passive voice frequency, noun chunk density, syntactic complexity) for style comparison. The install cost becomes worthwhile at that point. |
| stdlib `re` + `statistics` | NLTK | Use NLTK only if you need corpus-level frequency analysis against a reference corpus (e.g., comparing channel vocabulary against Brown corpus). Not a current requirement. |
| Prompt-driven script generation (Claude native) | Fine-tuned model | A fine-tuned model would produce more stylistically consistent output but requires GPU infrastructure, training data curation, and ongoing maintenance. Claude Code with STYLE_PROFILE.md context is the correct approach for this pipeline's scale and architecture constraints. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| textstat | Computes readability indices (Flesch, Gunning Fog) — wrong signal for style replication. Adds dependency for metrics that do not appear in STYLE_PROFILE.md. | `statistics` stdlib for sentence length distribution |
| spaCy + en_core_web_sm | POS tagging and NER are unnecessary for surface style metrics on transcribed speech. 50MB install for zero functional gain at this milestone. | `re` + `collections` stdlib |
| NLTK | Older, heavier, requires corpus downloads. No capability advantage over stdlib for this use case. | `re` + `collections` stdlib |
| LangChain / LlamaIndex | Architecture.md Rule 1: zero LLM API wrappers. These do not add value when Claude Code is the orchestrator. | Claude Code native orchestration |
| Any LLM embedding library (sentence-transformers, openai embeddings) | Style similarity is computed by Claude reading STYLE_PROFILE.md — not by embedding comparison. Adds PyTorch to the dependency graph for no reason. | Claude reasoning over STYLE_PROFILE.md |
| Jinja2 or other templating engines | The script output is pure narration text, not HTML or structured templates. Claude generates the narration directly; a template engine adds indirection without value. | Claude generates narration directly into a text file |

---

## Stack Patterns

**Style extraction (one-time, per reference script added):**
- CLI accepts path to reference script directory
- Python reads all `.md` files, computes surface metrics via stdlib
- Writes `style_metrics.json` to `.claude/scratch/` (transient)
- Claude reads the JSON snapshot + reference script excerpts → synthesizes STYLE_PROFILE.md
- STYLE_PROFILE.md written to `context/channel/` for persistent use

**Script generation (per video, after research dossier is complete):**
- CLI loads: `projects/N. [Title]/Research.md` + `context/channel/STYLE_PROFILE.md` + `context/channel/channel.md`
- Prints assembled context to stdout
- Claude reads context, generates script as numbered chapters with pure narration
- Output written to `projects/N. [Title]/Script.md`

Both patterns follow the established context-loader CLI pattern from v1.0/v1.1. No new architectural concepts.

---

## Version Compatibility

| Package | Version | Python 3.10+ Status | Notes |
|---------|---------|---------------------|-------|
| re | stdlib | Always available | No compatibility concerns |
| collections | stdlib | Always available | No compatibility concerns |
| statistics | stdlib | Always available (3.4+) | No compatibility concerns |
| pathlib | stdlib | Always available (3.4+) | Already project standard |
| argparse | stdlib | Always available | Already used in researcher and channel-assistant CLIs |

No new compatibility risks. Zero external dependencies means zero version conflict surface.

---

## Sources

- [textstat PyPI](https://pypi.org/project/textstat/) — Version 0.7.8 (July 22, 2025) confirmed; readability metrics assessed — HIGH confidence
- [spaCy PyPI](https://pypi.org/project/spacy/) — Version 3.8.11 (November 17, 2025) confirmed; en_core_web_sm at 11MB — HIGH confidence
- [spaCy Models Documentation](https://spacy.io/models/en) — en_core_web_sm components (tok2vec, tagger, parser, senter, ner, lemmatizer) — HIGH confidence
- [Programming Historian: Introduction to Stylometry with Python](https://programminghistorian.org/en/lessons/introduction-to-stylometry-with-python) — Type-Token Ratio, sentence length, punctuation density as standard stylometric features — MEDIUM confidence (academic source, validated against multiple stylometry papers)
- [TextDescriptives / textstat GitHub](https://github.com/textstat/textstat) — Confirmed readability metrics scope; does not include sentence rhythm or vocabulary register features — HIGH confidence
- Python stdlib documentation: `re`, `collections.Counter`, `statistics` — no external verification needed

---
*Stack research for: v1.2 Style Extraction and Script Generation (documentary video pipeline)*
*Researched: 2026-03-14*

# Feature Research

**Domain:** Style extraction and automated script generation for documentary narrative content
**Researched:** 2026-03-14
**Confidence:** HIGH (domain derived from existing reference scripts, channel DNA, and Architecture.md spec — not speculation)

---

## Context: What Already Exists

This milestone adds two features to a working pipeline (v1.1 shipped):

- Agent 1.1 (Channel Assistant) — topic briefs, competitor intel, project init
- Agent 1.2 (The Researcher) — two-pass web research → `Research.md` dossier with HOOK/QUOTE callouts
- `context/script-references/Mexico's Most Disturbing Cult.md` — one reference script (auto-captioned transcript, fragmented format)
- `context/channel/channel.md` — channel DNA (tone, voice, audience, output targets)
- `context/channel/writting_style_guide.md` — six style rules (narration-only, chapters, pacing, sources)

The two new features:

- **Skill 1.3: Style Extraction** — one-time heuristic that reads reference scripts, writes `STYLE_PROFILE.md`
- **Agent 1.3: The Writer** — per-video agent that reads `Research.md` + `STYLE_PROFILE.md` + channel DNA → numbered chapter script

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the pipeline must have or the output is unusable / requires heavy manual correction.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Chapter structure with numbered acts | Reference script shows chapters 1–N with evocative titles; channel DNA mandates numbered acts | LOW | Style extraction must identify chapter boundaries in reference; Writer must output same format |
| Pure narration output — no stage directions, no host commentary | Style rule #2: "Script is narration only." Producer cannot hand this to a voiceover artist if production notes are embedded | LOW | Enforced via prompt output format spec; the existing SKILL.md pattern handles this |
| Factual fidelity anchored to Research.md | Style rule #4: "Every claim must be sourced. Speculation labeled as such." Hallucinated facts undermine the channel's authority positioning | MEDIUM | Writer prompt must anchor to dossier content; Research.md already provides per-claim attribution |
| Channel tone: calm, journalistic, deadpan | Channel DNA defines this as the core voice. Deviation breaks brand consistency across every video | MEDIUM | Achieved via STYLE_PROFILE.md + channel.md loaded as context in Writer prompt |
| Script word count in target range | 3,000–7,000 words, 20–50 min runtime (channel.md output targets). Too short = thin content; too long = padding | MEDIUM | Writer prompt must state target; may need a review pass if first draft is significantly short or long |
| STYLE_PROFILE.md captures actionable patterns | "Calm tone" is not actionable. Must capture sentence rhythm, transition phrases, pacing structure, vocabulary register | MEDIUM | Reference script is a YouTube auto-caption transcript (no punctuation, arbitrary line breaks). Extraction prompt must work with this degraded format — see Implementation Notes |
| STYLE_PROFILE.md as standalone readable artifact | Writer loads it as context on every video; it must be human-readable for manual review and editing | LOW | Plain markdown; stored in `context/` — not embedded in code |

### Differentiators (Competitive Advantage)

Features that make this pipeline produce better scripts than a generic "write a documentary script about X" prompt.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Hook and quote integration from Research.md | Research.md already contains `HOOK:` and `QUOTE:` callouts placed by Agent 1.2 specifically for the Writer. Consuming these directly = narrative tension for free | LOW | Writer prompt must explicitly instruct: use HOOK/QUOTE callouts as chapter openers and narration anchors. High ROI, zero extra work |
| Transition phrase library extracted from reference | Reference script uses specific connective phrases ("this proved to be", "in the spring of", "it was upon this track that"). Capturing these preserves voice consistency; generic transitions ("furthermore", "notably") break the deadpan register | LOW | Simple verbatim extraction during style analysis. High signal, low effort |
| Pacing profile: exposition vs. tension escalation | Reference script spends 2–3 chapters in slow historical setup before escalating to horror. Encoding this pattern as a qualitative instruction ("build slowly for the first third, then escalate") prevents flat pacing in generated scripts | MEDIUM | Word count per chapter in reference gives a rough baseline; qualitative instruction in STYLE_PROFILE.md is more durable than a hard ratio |
| Open-ending pattern explicitly encoded | Style rule #6: if a mystery is unsolved, present evidence and leave the weight with the audience. Without explicit instruction, LLMs tend to artificially resolve ambiguity | LOW | STYLE_PROFILE.md includes an open-ending template derived from reference; prompt constraint reinforces it |
| Chapter title generation in reference register | Reference uses evocative short titles ("Strangers in the Jungle", "Initial Control"). These titles carry narrative weight. Writer generates titles in same register, not generic "Background" or "Chapter 1" | LOW | Example titles from reference provide direct model for Writer |
| Source authority woven into narration | Dossier provides per-claim attribution. Weaving these into narration naturally ("court records from 1962 show...") elevates perceived credibility without disrupting pacing | MEDIUM | Prompt instruction + example from reference of how factual authority is conveyed (stated with conviction, not always explicitly cited) |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multiple script variants (A/B versions) | Seems useful for optimization | Doubles review work; pipeline converges on one topic per video; no feedback loop exists yet to evaluate which variant performs better | One authoritative script per run; manual iteration if revision is needed |
| Inline production notes in script text | Directors want visual cues alongside narration | Breaks the "pure narration" rule (style rule #2); confuses voiceover source with direction; Agent 1.4 (Visual Orchestrator) reads the finished script and generates the shotlist — that is where visual cues live | Clean narration only; Agent 1.4 handles visual interpretation |
| Style extraction re-run every video | "Fresher style" sounds like quality | Style extraction is explicitly one-time per Architecture.md Skill 1.3 spec; re-running on the same reference adds cost with no benefit | Re-run only when new reference scripts are added to `context/script-references/` |
| Automated fact-checking pass after writing | Catching hallucinations sounds essential | The dossier-anchored approach already mitigates hallucination risk; a fact-checking pass requires another scraping/LLM pass, adds latency, and the checking LLM faces the same hallucination risk as the writing LLM | Anchor Writer to Research.md; human review catches errors that matter for publication |
| Auto-generated chapter outline for Writer approval before full script | Adds a review checkpoint | Adds a round-trip that may not be needed; the Writer derives structure from the material using STYLE_PROFILE.md guidance; impose this only if full scripts frequently need structural revision | Ship full scripts first; add outline approval step reactively if structural issues emerge |
| TTS / voice-over generation | Natural next step after script | Out of scope per Architecture.md; no TTS tool in stack; audio is handled in DaVinci Resolve by the editor | Stop at script text; TTS is a Phase 3+ concern |
| Style extraction from multiple reference scripts averaged | More data sounds better | The existing reference is already an auto-caption transcript (degraded format); averaging multiple degraded transcripts produces more noise, not better signal | Use one clean style profile; add more references only when clean transcripts are available |
| LLM API wrapper for Writer reasoning | Seems like the "right" way to call Claude programmatically | Architecture.md Rule 1: zero LLM API wrappers. All reasoning handled natively by Claude Code runtime | SKILL.md pattern — Claude Code is the runtime; no SDK code written |

---

## Feature Dependencies

```
[context/script-references/*.md]
    └──required by──> [Style Extraction (Skill 1.3)]  [HEURISTIC — one-time]
                          └──produces──> [context/STYLE_PROFILE.md]
                                             └──required by──> [The Writer (Agent 1.3)]

[projects/N. Title/research/Research.md]   (output of Agent 1.2)
    └──required by──> [The Writer (Agent 1.3)]

[context/channel/channel.md]
    └──required by──> [The Writer (Agent 1.3)]
    └──required by──> [Style Extraction (Skill 1.3)]   (tone validation context)

[context/channel/writting_style_guide.md]
    └──required by──> [The Writer (Agent 1.3)]

[The Writer (Agent 1.3)]
    └──produces──> [projects/N. Title/script.md]
                       └──feeds──> [Agent 1.4: Visual Orchestrator]  (future milestone)
```

### Dependency Notes

- **Style Extraction requires reference scripts:** One reference exists (`Mexico's Most Disturbing Cult.md`). Sufficient to produce an initial STYLE_PROFILE.md. The auto-caption format is degraded — see Implementation Notes.
- **Writer requires STYLE_PROFILE.md:** Without it, Writer falls back to generic documentary voice, losing the channel's deadpan-neutral register. Hard dependency.
- **Writer requires Research.md:** Script cannot be generated without a completed research dossier. Sequential dependency — research must complete before writing begins.
- **STYLE_PROFILE.md is a reusable artifact:** Lives in `context/`, shared across all future videos. Not regenerated per video.
- **Agent 1.4 is downstream:** The Writer's script is consumed by the Visual Orchestrator (not yet built). The script output format must be stable for that future handoff.

---

## MVP Definition

### Launch With (v1.2)

Minimum needed to produce a usable script from a research dossier.

- [ ] **Style extraction prompt** — reads reference script(s), outputs `STYLE_PROFILE.md` with: sentence rhythm description, chapter structure pattern, transition phrases (verbatim list), pacing notes (build rate), tone markers, open-ending instruction. [HEURISTIC — no code needed]
- [ ] **STYLE_PROFILE.md stored in `context/`** — loaded by Writer on every run; human-readable for manual adjustment
- [ ] **Writer SKILL.md** — defines the four context files to load, output format (numbered chapters, word count target, file path), and the generation prompt
- [ ] **Script format spec** — chapter numbers and evocative titles, pure narration, no production notes, 3,000–7,000 word target
- [ ] **HOOK/QUOTE integration instruction** — Writer prompt explicitly instructs use of Research.md callouts as narrative anchors

### Add After Validation (v1.x)

Add once a first script has been reviewed and gaps identified.

- [ ] **Pacing audit heuristic** — after Writer produces script, a secondary review step checks word count per chapter and flags disproportionate chapters. Trigger: first scripts show consistently unbalanced acts.
- [ ] **Transition phrase enforcement** — if early scripts drift from channel voice, promote the transition phrase list from STYLE_PROFILE.md to a hard constraint section in the Writer prompt
- [ ] **Second reference script** — when a clean (non-auto-captioned) transcript is available, re-run style extraction and expand STYLE_PROFILE.md with merged patterns
- [ ] **Writer CLI pre-check** — thin Python script that verifies `Research.md` exists before invoking Writer, prints clear error if missing. [DETERMINISTIC — low priority, prevents confusing failures]

### Future Consideration (v2+)

Defer until core is validated.

- [ ] **Chapter outline approval checkpoint** — generate outline first, get user approval, then write full narration. Add only if full scripts frequently need structural revision.
- [ ] **Style drift detection** — compare script output against STYLE_PROFILE.md metrics. Needs multiple reference scripts to establish meaningful baselines.
- [ ] **Script versioning** — keep draft history in `projects/N. Title/drafts/`. Worthwhile once multiple videos shipped and iteration patterns emerge.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Style extraction prompt → STYLE_PROFILE.md | HIGH | LOW (pure heuristic) | P1 |
| Writer SKILL.md: chapter structure + pure narration | HIGH | LOW (prompt + format spec) | P1 |
| Writer: factual anchoring to Research.md | HIGH | MEDIUM (prompt engineering) | P1 |
| Writer: HOOK/QUOTE integration from dossier | HIGH | LOW (prompt instruction) | P1 |
| Writer: channel tone via STYLE_PROFILE.md | HIGH | LOW (context loading) | P1 |
| Writer: chapter title generation | MEDIUM | LOW | P1 |
| STYLE_PROFILE.md: transition phrase library | MEDIUM | LOW | P2 |
| STYLE_PROFILE.md: pacing notes | MEDIUM | MEDIUM | P2 |
| STYLE_PROFILE.md: open-ending template | MEDIUM | LOW | P2 |
| Pacing audit heuristic (post-generation) | LOW | MEDIUM | P3 |
| Chapter outline approval checkpoint | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Implementation Notes

### Reference Script Format Problem

The only existing reference script (`Mexico's Most Disturbing Cult.md`) is a YouTube auto-caption transcript. It has:
- No sentence-ending punctuation
- Arbitrary line breaks mid-sentence
- `[Music]` / `[Applause]` markers interspersed
- Chapter headers embedded mid-file (`1. Strangers in the Jungle`, `2. Initial Control`)

**Consequence for style extraction:** Cannot use punctuation-based sentence boundary detection or quantitative rhythm analysis. The extraction prompt must instead:
1. Identify chapter boundaries from numbered headers
2. Read line groupings to infer sentence rhythm qualitatively
3. Extract transition phrases and connective language verbatim
4. Characterize pacing as qualitative instruction ("slow historical build for chapters 1–2, escalate in chapters 3–4") not a numeric ratio

This is a prompt engineering constraint, not a blocker. The extraction is still achievable from this format. A clean transcript (properly punctuated) would yield higher-confidence style patterns.

### STYLE_PROFILE.md Scope

The profile should contain only what the Writer can act on. Avoid abstract descriptions. Include:
- 5–8 example transition phrases extracted verbatim from the reference script
- Chapter structure pattern: how many chapters, approximate distribution of content across acts
- Pacing instruction: when to build slowly, when to escalate, when to let a fact land without commentary
- Vocabulary register: word classes to favor (precise historical nouns, active past-tense verbs) and avoid (rhetorical questions, superlatives, first-person)
- Open-ending template: how the reference script ends unresolved cases, with example
- What the voice does NOT do: no "smash that subscribe button", no "join us as we explore", no "shockingly", no rhetorical questions to the audience

### Writer Skill Architecture

Per Architecture.md Rule 2, the Writer is [HEURISTIC] — Claude Code does the reasoning. The skill is a SKILL.md that:
1. Instructs Claude to load the four context files (STYLE_PROFILE.md, Research.md, channel.md, writting_style_guide.md)
2. Defines the output format (numbered chapters with titles, word count target, file path)
3. Provides the generation prompt

No Python code needed for the core writing step. A thin CLI pre-check (deterministic) can be added later to verify Research.md exists before invoking, but that is not MVP.

---

## Sources

- `context/script-references/Mexico's Most Disturbing Cult.md` — analyzed directly: chapter format, voice patterns, transition phrases, pacing, open-ending treatment
- `context/channel/channel.md` — channel DNA, tone rules, audience profile, output targets
- `context/channel/writting_style_guide.md` — six style rules (narration-only, chapters, pacing, sources, silence, open endings)
- `Architecture.md` — Skill 1.3 and Agent 1.3 spec, HEURISTIC/DETERMINISTIC classification rule, zero-LLM-wrapper rule
- `.planning/PROJECT.md` — v1.2 milestone definition, existing features, constraints
- `.claude/skills/researcher/SKILL.md` — Research.md dossier format (Writer's primary input); confirmed HOOK/QUOTE callout structure
- `projects/1. The Duplessis Orphans.../research/Research.md` — live example of dossier output, confirmed section structure and callout pattern

---
*Feature research for: Skill 1.3 (Style Extraction) and Agent 1.3 (The Writer)*
*Researched: 2026-03-14*

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