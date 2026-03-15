# Stack Research

**Domain:** Visual Orchestrator — Zero-Code Shot List Generation from Documentary Scripts (Agent 1.4)
**Researched:** 2026-03-15
**Confidence:** HIGH

> **Scope:** This document covers stack additions for v1.3 only. The validated stack from v1.0–v1.2 (Python stdlib, SQLite, yt-dlp, crawl4ai, trafilatura, requests, BeautifulSoup4, scenedetect, imagededup, Pillow, numpy) is unchanged. Do not re-evaluate those decisions.
>
> **Architecture reminder:** Architecture.md Rule 2 applies directly. The Visual Orchestrator is classified [HEURISTIC]. Claude reads Script.md and VISUAL_STYLE_GUIDE.md and reasons about visual needs for each narrative beat. The only [DETERMINISTIC] work is a thin CLI that assembles context files for Claude to consume and validates the resulting shotlist.json against its schema.

---

## What v1.3 Needs That v1.2 Does Not Have

One deliverable, entirely prompt-driven:

**Shot list generation** — an agent that reads a finished Script.md and maps each narrative beat to a visual need. Output is `shotlist.json` at `projects/N. [Title]/shotlist.json`. Claude does all reasoning; no NLP, no vector similarity, no third-party tools.

The script is already clean prose in a known format: chapter headers (`## N. Title`), continuous narration paragraphs, no bullet points, no stage directions. The parsing problem is purely structural — identify chapter boundaries and segment prose into shootable units. This is a `str.split()` problem, not a parsing framework problem.

---

## Recommended Stack Additions

### Total new dependencies: 0

All required capability is present in the existing stack.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `re` (stdlib) | stdlib | Chapter boundary detection, paragraph segmentation | Script format is fixed: `## N. Title` headers on their own line. `re.split()` on `^\#\# \d+\.` cleanly separates chapters. Already used in v1.2 style extractor. |
| `json` (stdlib) | stdlib | Write and validate shotlist.json | JSON serialization for the shot list output. Already project standard throughout all agents. |
| `pathlib` (stdlib) | stdlib | File discovery — resolve project directory, locate Script.md and VISUAL_STYLE_GUIDE.md | Already the project standard per CLAUDE.md. Identical to writer CLI pattern. |
| `argparse` (stdlib) | stdlib | CLI argument parsing | Same pattern as `python -m writer load "[topic]"`. Accept topic name, resolve project directory, print assembled context. |

No new install step. No new compatibility surface. Zero deviation from the project's established "stdlib-only for thin deterministic layers" rule.

---

## Prompt Engineering Patterns for Heuristic Shot List Generation

The skill is prompt-driven. These patterns apply directly to building the generation prompt at `.claude/skills/visual-orchestrator/prompts/generation.md`.

### Pattern 1: Narrative Beat Segmentation (not paragraph-based)

**What it is:** Instruct Claude to segment narration by *visual transition moments*, not by paragraph boundaries. A paragraph that covers three distinct visual ideas should produce three shot entries. A long paragraph with one sustained visual idea produces one shot entry.

**Why it works for this domain:** Documentary narration frequently sustains a single visual for multiple sentences before cutting. Paragraph-per-shot produces over-segmentation. Transition-moment-per-shot matches how editors actually cut.

**Prompt instruction pattern:**
```
Identify each moment where the visual subject changes: a new person is introduced,
the location shifts, an event is described that requires different imagery,
or the temporal context changes (e.g., "thirty years later").
Each change is a shot boundary. Do not split shots at paragraph boundaries
unless a visual transition coincides.
```

### Pattern 2: Narrative Context Verbatim Extraction

**What it is:** The `narrative_context` field in each shot entry captures the *actual narration text* driving that shot — a direct quote from Script.md, not a paraphrase. Claude copies the relevant passage as-is.

**Why it works:** The downstream Media Acquisition agent (2.1) reads only `shotlist.json`, not the script. If `narrative_context` is paraphrased, the acquisition agent loses the specific language that anchors search queries ("the 1942 law allowing unclaimed bodies to be sold to medical schools for $10 each" is a more useful search signal than "information about deaths in institutions"). Verbatim extraction preserves the signal.

**Prompt instruction pattern:**
```
narrative_context: Copy the exact narration text that plays during this shot.
Trim to the relevant span — not the full paragraph. Preserve original wording.
```

### Pattern 3: Visual Need as a Search Query

**What it is:** The `visual_need` field is written as if it were a search query submitted to an image archive — specific subject, era, geography, and mood. No production language ("slow zoom", "cut to"), no editorial tone ("haunting", "unsettling").

**Why it works:** The Media Acquisition agent (2.1) will build search queries from `visual_need`. Vague descriptions ("something dark and historical") generate bad results. Specific, factual descriptions ("Quebec psychiatric hospital interior 1950s black and white photograph") generate useful ones. Writing the field as a search query forces the right level of specificity.

**Prompt instruction pattern:**
```
visual_need: Describe the visual in searchable terms — subject, era, geography, medium
(photograph vs. footage vs. map). Write it as an image archive search query.
No production instructions, no mood adjectives.
```

### Pattern 4: suggested_types Anchored to VISUAL_STYLE_GUIDE.md

**What it is:** The `suggested_types` array is populated from the fixed vocabulary defined in VISUAL_STYLE_GUIDE.md — not invented per shot. The generation prompt loads the guide's type taxonomy and instructs Claude to select from it.

**Why it works:** The asset pipeline downstream expects consistent type identifiers. If the orchestrator invents types (`"period_engraving"`, `"courtroom_sketch"`), the acquisition agent cannot map them to its source domains. The VISUAL_STYLE_GUIDE.md already defines the type taxonomy (`archival_video`, `archival_photo`, `broll`, `map_animation`, `document_scan`, etc.) from actual reference video analysis. Claude selects from this closed vocabulary.

**Prompt instruction pattern:**
```
suggested_types: Select 1–3 types from the type vocabulary in the Visual Style Guide.
Do not invent new types. If no type fits, use the closest match and add a note
to visual_need explaining the gap.
```

### Pattern 5: Chapter-First Grouping

**What it is:** Shot entries are grouped under their chapter before being serialized to JSON. The `chapter` field uses the exact chapter title from Script.md (e.g., `"1. The Arithmetic of Abandonment"`), not a normalized slug.

**Why it works:** Human editors reviewing the shot list need to navigate by chapter, matching the script. Using the exact chapter title preserves traceability to Script.md without requiring a separate mapping table. The Asset Manager (2.4) can group the final asset manifest the same way.

---

## JSON Schema Design for shotlist.json

### Confirmed Schema (from Architecture.md)

```json
{
  "shots": [
    {
      "id": "S001",
      "chapter": "1. The Arithmetic of Abandonment",
      "narrative_context": "exact narration text excerpt from Script.md",
      "visual_need": "Quebec orphanage exterior 1940s black and white photograph",
      "suggested_types": ["archival_photo", "archival_video"]
    }
  ]
}
```

### Schema Design Rationale

**What the schema intentionally excludes — and why:**

| Excluded Field | Why Excluded | What Handles It Instead |
|----------------|--------------|-------------------------|
| `duration` | Editor's domain (DaVinci Resolve), not the orchestrator's. Duration depends on final narration pacing, music, and cut rhythm. | Human editor |
| `priority` | Asset acquisition priorities are determined by gap analysis in Agent 2.1, not pre-assigned. Pre-assigning creates false precision. | Agent 2.1 gap analysis |
| `effects` / `transitions` | Post-production decisions that depend on what assets are actually acquired. The orchestrator works from script, not final cut. | Human editor / future Remotion agent |
| `search_query` | `visual_need` already functions as the search query. A separate field creates duplication and drift risk. | `visual_need` field |
| `confidence` | Shot confidence scoring adds complexity without observable benefit at this stage. Every shot is Claude's best reading of the script. | Human review step |
| `asset_id` | Asset IDs are assigned by the Asset Manager (2.4), not the orchestrator. Orchestrator works before assets exist. | Agent 2.4 |

**What makes the schema robust without bloat:**

- `id` uses zero-padded sequential integers (`S001`, `S002`) — sortable, collision-free, short
- `chapter` uses the exact Script.md heading — preserves traceability without a mapping table
- `narrative_context` is verbatim — preserves search signal for downstream agents
- `visual_need` is human-readable and machine-queryable — serves both review and acquisition
- `suggested_types` is a closed vocabulary array — prevents type taxonomy drift

### Schema Validation (Deterministic Layer)

The CLI should validate the output JSON before writing it. Using only stdlib `json` + manual key checks — no jsonschema library needed. The validation is:

```python
required_keys = {"id", "chapter", "narrative_context", "visual_need", "suggested_types"}
valid_types = {"archival_video", "archival_photo", "broll", "map_animation",
               "document_scan", "text_overlay", "talking_head"}

for shot in data["shots"]:
    assert required_keys.issubset(shot.keys()), f"Missing keys in {shot['id']}"
    assert isinstance(shot["suggested_types"], list), f"suggested_types must be list"
    assert all(t in valid_types for t in shot["suggested_types"]), f"Unknown type in {shot['id']}"
```

No `jsonschema` (0.7MB install) needed. Five lines of stdlib assertions catch schema drift.

---

## Documentary Shot List Conventions Applied to This Domain

These conventions from professional documentary production inform the prompt design.

### What documentary editors actually need on a shot list

Based on professional documentary production workflows (HIGH confidence — conventions are stable and well-documented across industry sources):

1. **Narrative anchor** — what the narrator is saying. The visual editor must know the narration to choose matching footage duration. `narrative_context` serves this.

2. **Visual subject** — what appears on screen, not how it's edited. A shot list specifies the subject (`Quebec orphanage, 1940s`), not the cut (`medium shot, slow zoom`). Editorial choices happen in the edit suite.

3. **Media type** — archival footage vs. photograph vs. map vs. animation. Different types require different sourcing workflows (archive.org vs. Wikipedia Commons vs. generated). `suggested_types` serves this.

4. **Sequence position** — which chapter and roughly which narrative moment. `chapter` + `id` (sequential) serve this.

What shot lists for documentary post-production do NOT contain:
- Camera angles or movements (editor decides)
- On-screen duration (pacing decided in edit)
- Transitions between shots (editor decides)
- Music or audio cues (separate music supervision workflow)
- Color grade instructions (colorist's domain)

The Architecture.md schema already reflects these conventions correctly. The prompt design should reinforce them by explicitly excluding production language from `visual_need`.

### Shot density heuristics for 20–50 minute documentaries

For this channel's format (20–50 minute documentaries, 3,000–7,000 word scripts):

- Typical documentary cut rate: 1 shot every 4–12 seconds of screen time
- 20 minutes at 8 seconds average = ~150 shots; 50 minutes = ~375 shots
- 5,000-word narration at 130 words/minute ≈ 38 minutes of screen time ≈ 285 shots

In practice, the orchestrator does not aim for a target shot count. It identifies visual transition moments in the script. A 7-chapter, 5,000-word script will naturally produce 40–80 distinct visual needs — fewer than total shots, because the acquisition agent maps each visual need to potentially several asset files, and the editor may hold a single asset for multiple sentences.

The prompt should target **one shot entry per visual transition** in the narration, not one per sentence or one per paragraph.

---

## Installation

```bash
# No new pip installs required for v1.3.
# All required libraries are Python stdlib:
#   re, json, pathlib, argparse, sys

# Confirm no dependency additions are needed
python -c "import re, json, pathlib, argparse; print('All stdlib modules available')"
```

**Total new hard dependencies: 0.** Correct outcome for a [HEURISTIC] milestone. The deterministic layer is a thin context-loader and schema validator.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Verbatim `narrative_context` (copied from script) | Paraphrased summary | Use paraphrase only if the downstream agent cannot handle long text fields. Agent 2.1 benefits from full verbatim text for search query construction — no reason to paraphrase. |
| Closed `suggested_types` vocabulary from VISUAL_STYLE_GUIDE.md | Open-ended free-text types | Use open types only if the VISUAL_STYLE_GUIDE.md type taxonomy is abandoned. The closed vocabulary prevents type drift across the pipeline. |
| Manual `json` key validation (stdlib) | `jsonschema` library | Use jsonschema if schema complexity grows (nested objects, pattern validation, optional fields with defaults). At 5 flat required keys, stdlib assertions are proportionate. |
| Chapter header as `chapter` field value | Numeric chapter index | Use numeric index if chapter titles change frequently during script revision. Titles give human editors direct traceability to the script without a lookup table — prefer until there's evidence of instability. |
| Single-pass generation (read script, output JSON) | Two-pass (identify beats, then assign types) | Use two-pass if the generation prompt produces inconsistent type assignments. The VISUAL_STYLE_GUIDE.md type taxonomy is small enough (5–8 types) that single-pass assignment is reliable. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `jsonschema` library | Five required flat keys do not justify a 0.7MB install. Stdlib assertions catch schema violations with less code. | `assert` + manual key checks in CLI |
| spaCy / NLTK sentence tokenization | Script sentences are editorial prose, not raw text. The format is clean. `re.split()` on `\n\n` for paragraphs and on chapter headers is sufficient. | `re.split()` stdlib |
| Any LLM API wrapper | Architecture.md Rule 1. The skill runs as Claude Code natively. | Claude Code native orchestration |
| `shot_duration` or `priority` fields | Both require information the orchestrator does not have (final assets, edit pacing). Adding them now creates false precision and placeholder-filling behavior. | Omit; downstream agents determine these |
| Sentence-level segmentation | One shot per sentence produces 500+ entries for a 5,000-word script — too granular for an acquisition agent to work with and not how documentary editors think about shot lists. | One shot per visual transition in narration |
| Shot confidence scores | Adds a numeric field that encodes Claude's uncertainty, which is already expressed through the `visual_need` text. Numeric confidence scores invite downstream agents to make threshold decisions that belong to human review. | Human review of shotlist.json |
| Automated script parsing before Claude reads it | Pre-parsing chapters via Python before handing to Claude adds code for no gain. Claude reads chapter structure directly from the raw Script.md format. | Load raw Script.md, let Claude segment |

---

## Stack Patterns

**Shot list generation (per video, after Script.md is complete):**

1. CLI loads: `projects/N. [Title]/Script.md` + `context/visual-references/*/VISUAL_STYLE_GUIDE.md`
2. Prints assembled context to stdout with labeled sections
3. Claude reads generation prompt at `.claude/skills/visual-orchestrator/prompts/generation.md`
4. Claude identifies visual transition moments in each chapter
5. Claude generates `shotlist.json` entries using verbatim narrative context and closed type vocabulary
6. CLI validates JSON schema before writing to `projects/N. [Title]/shotlist.json`

This follows the identical context-loader CLI pattern established in v1.0–v1.2. No new architectural concepts.

---

## Version Compatibility

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| `re` | stdlib | Always available | No compatibility concerns |
| `json` | stdlib | Always available | No compatibility concerns |
| `pathlib` | stdlib | 3.4+ | Already project standard |
| `argparse` | stdlib | Always available | Already used in all existing CLI entry points |

No new compatibility risks. Zero external dependencies means zero version conflict surface.

---

## Sources

- Architecture.md (`Agent 1.4: Visual Orchestrator` section) — Shot entry schema and field definitions — HIGH confidence (canonical project spec)
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — Type taxonomy (`archival_video`, `archival_photo`, `broll`, etc.) confirmed from actual v4 output — HIGH confidence
- `projects/1. The Duplessis Orphans.../Script V1.md` — Actual script structure: chapter headers (`## N. Title`), prose paragraphs, no stage directions — HIGH confidence (primary artifact)
- `.claude/skills/writer/CONTEXT.md` — Confirms Script.md format: starts with `## 1. [Chapter Title]`, pure prose, no production notes — HIGH confidence
- `.claude/skills/writer/prompts/generation.md` — Confirms no visual cues in script output; visual Orchestrator owns those — HIGH confidence
- Architecture.md (Phase 2 Asset Pipeline section) — Confirms Agent 2.1 reads only `shotlist.json`, not Script.md — HIGH confidence (informs what signal shotlist.json must preserve)

---
*Stack research for: v1.3 Visual Orchestrator — Shot List Generation (documentary video pipeline)*
*Researched: 2026-03-15*
