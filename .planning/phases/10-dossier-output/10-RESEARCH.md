# Phase 10: Dossier Output - Research

**Researched:** 2026-03-14
**Domain:** Python CLI aggregation + synthesis prompt engineering
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Synthesis workflow:**
- writer.py reads all src_*.json + pass2_*.json, merges into a single `synthesis_input.md` (url, domain, tier, content per source), writes to `.claude/scratch/researcher/`
- cmd_write prints "Synthesis input ready" and the output path — Claude then reads synthesis_input.md + the synthesis prompt and produces both final files
- Claude writes markdown directly — no intermediate JSON-to-markdown conversion step. The synthesis prompt instructs Claude to produce Research.md and media_urls.md as final markdown
- Claude writes files directly to `projects/N. [Title]/research/` using its file tools. cmd_write only handles aggregation. SKILL.md workflow tells Claude where to write
- Word cap enforced by prompt — synthesis_input.md includes ALL source content (20-50k words). The synthesis prompt instructs Claude to distill to ~2,000 words of curated scriptwriter-facing content. No code-level truncation

**Dossier section ordering (narrative-first):**
- Section order: Subject Overview (~500 words) → Timeline → Key Figures → Narrative Hooks → Direct Quotes → Contradictions → Unanswered Questions → Correcting the Record → Source Credibility

**Narrative hooks:**
- Labeled callout blocks in a dedicated section: `**HOOK: [Title]**` followed by 1-2 sentences explaining the story beat and why it's high-impact
- 3-5 hooks total — Writer scans and decides which to use as chapter anchors

**Direct quotes:**
- Blockquote callouts with attribution: `**QUOTE: [Label]**` followed by markdown blockquote, speaker name, role, and source URL/reference
- Writer can drop these directly into the script as narration beats

**Source credibility:**
- Compact table at the end of Research.md with columns: Source, Type (gov/academic/journalism/wiki/primary), Corroborated By, Access Quality (full/partial/paywall)
- Structured signals per DOSS-04 — no scalar scores

**Timeline:**
- 5-15 chronological entries, each with date, event description (1-2 sentences), and source attribution
- Enough for the Writer to build the narrative arc without overwhelming detail

**Key figures:**
- Name-role-relevance blocks: each figure gets name, role/title, relevance (1-2 sentences), and cross-reference to their quote in Direct Quotes section if applicable
- 3-8 figures depending on topic complexity

**Media URL extraction:**
- Visual media only: images, video clips, document scans (photos, archival footage, newspaper clippings, Wikimedia Commons, archive.org media). Exclude PDFs, academic papers, text-only web pages
- Claude extracts during synthesis — the synthesis prompt instructs Claude to identify and catalog media URLs while reading sources. Both Research.md and media_urls.md produced in one synthesis pass
- Organized by asset type matching Architecture's categories: Archival Footage, Archival Photos, Documents, B-Roll. Each entry has URL, description, and source domain

**Writer handoff:**
- Research.md stays factual with narrative signals — no 'recommended angle', no chapter suggestions, no tone guidance
- HOOK labels, QUOTE callouts, contradictions, unanswered questions, and correcting-the-record sections serve as implicit editorial signals
- Writer agent decides narrative structure, chapter breaks, and which hooks to use

### Claude's Discretion
- Exact synthesis prompt wording and structure
- How to handle sources with no useful content (empty/failed fetches)
- Correcting-the-record section format
- Unanswered questions section format
- Whether to include a brief metadata header (topic, date, source count)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOSS-01 | Research.md with subject overview (~500 words), chronological timeline, and key figures | Synthesis prompt design section + section ordering pattern |
| DOSS-02 | Research.md includes contradictions section identifying conflicting accounts | Contradictions section format + survey_evaluation.md already flags these |
| DOSS-03 | Research.md includes unanswered questions that create narrative tension | Unanswered Questions section format |
| DOSS-04 | Research.md uses structured credibility signals (source_type, corroborated_by, access_quality) — no scalar scores | Source credibility table pattern |
| DOSS-05 | Research.md capped at ~2,000 words of curated scriptwriter-facing content | Word cap enforced by synthesis prompt, not code |
| DOSS-06 | Agent extracts direct quotes as labeled callouts for scene anchoring | QUOTE callout format locked in decisions |
| DOSS-07 | Agent identifies 3-5 narrative hooks (high-impact story beats) explicitly labeled for the Writer | HOOK callout format locked in decisions |
| DOSS-08 | Agent flags where mainstream coverage contradicts primary sources (correcting-the-record opportunities) | Correcting the Record section — format at Claude's discretion |
| DOSS-09 | Agent writes Research.md to `projects/N. [Title]/research/` | Claude writes file directly; resolve_output_dir already provides path |
| MEDIA-01 | Agent produces a separate `media_urls.md` cataloging media URLs found during research | Produced in same synthesis pass as Research.md |
| MEDIA-02 | media_urls.md includes URL, description, and source type — kept separate from Research.md | Organized by asset type (Archival Footage, Archival Photos, Documents, B-Roll) |
</phase_requirements>

---

## Summary

Phase 10 is the final phase of the v1.1 Researcher milestone. It adds a single `write` subcommand to the existing researcher CLI. The command aggregates all scraped source files (src_*.json and pass2_*.json) into a single flat synthesis_input.md, then signals Claude to perform the [HEURISTIC] synthesis step. Claude reads the aggregated content plus a synthesis prompt and writes both final output files directly using its file tools.

The architecture follows the same [DETERMINISTIC] data-aggregation + [HEURISTIC] Claude reasoning split used in cmd_survey and cmd_deepen. Code does the mechanical work of reading and formatting source files. Claude does all editorial judgment. No LLM API calls in code — consistent with Architecture.md Rule 1 throughout the project.

The synthesis prompt is the most critical artifact in this phase. It must constrain Claude to a strict section order, enforce the 2,000-word cap, define the HOOK and QUOTE callout formats precisely, and guide media URL extraction in parallel with text synthesis.

**Primary recommendation:** Build writer.py as a thin aggregator (no business logic beyond reading and serializing source files), invest most design effort in synthesis.md prompt precision, and update SKILL.md to document the complete end-to-end workflow.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (json, pathlib, sys) | 3.14+ | File reading and formatting | Already used throughout the skill |
| No new dependencies | — | cmd_write is sync-only, no crawl4ai needed | Architecture is context-loader only |

### No New Dependencies Required

cmd_write reads from disk and writes to disk. It calls no external services and requires no async. The same stdlib already used in the skill is sufficient. This is the simplest command in the entire researcher skill.

**Installation:**
```bash
# No new packages. All dependencies already installed.
```

---

## Architecture Patterns

### Recommended Project Structure

The phase adds three artifacts to the existing skill:

```
.claude/skills/researcher/
├── scripts/researcher/
│   └── writer.py            # NEW — aggregation function for cmd_write
│   └── cli.py               # MODIFIED — add write subcommand + import writer
├── prompts/
│   └── survey_evaluation.md # existing
│   └── synthesis.md         # NEW — synthesis prompt for Claude
└── SKILL.md                 # MODIFIED — add write workflow section
```

Output artifacts (written by Claude after synthesis):

```
projects/N. [Title]/research/
├── src_001.json ... src_NNN.json    # existing (Pass 1)
├── pass2_001.json ... pass2_NNN.json # existing (Pass 2)
├── source_manifest.json             # existing
├── synthesis_input.md               # NEW — written by cmd_write
├── Research.md                      # NEW — written by Claude
└── media_urls.md                    # NEW — written by Claude
```

### Pattern 1: Context-Loader Command (established pattern)

**What:** A CLI subcommand that loads data from disk, formats it for Claude to reason over, then prints a path and instruction line. Claude handles all editorial judgment.

**When to use:** Any step requiring synthesis, evaluation, or narrative judgment — not mechanical transformation.

**Example from cmd_topics (existing pattern):**
```python
# Source: cli.py:cmd_topics
def cmd_topics(args: argparse.Namespace, root: Path) -> None:
    # ... load data from disk ...
    print(f"Prompt file: {prompt_path}")
    print()
    print(
        "Context loaded. Use the generation prompt to generate exactly 5 topic briefs. "
        "..."
    )
```

cmd_write follows the same pattern: aggregate to file, print path, instruct Claude.

### Pattern 2: Source File Aggregation

**What:** Read all src_*.json and pass2_*.json files in sorted order. For each, extract url, domain, tier, fetch_status, and content. Skip failed/empty fetches with a note. Write as a flat markdown document to synthesis_input.md.

**Aggregation format for synthesis_input.md:**
```markdown
# Synthesis Input
**Topic:** {topic}
**Generated:** {timestamp}
**Sources:** {N} total ({pass1} Pass 1, {pass2} Pass 2)

---

## Source 1 — src_001.json
**URL:** https://en.wikipedia.org/wiki/...
**Domain:** en.wikipedia.org
**Tier:** 1
**Words:** 4523

{full content here}

---

## Source 2 — src_002.json
...
```

Skipped/failed sources are listed as a brief note at the top (not repeated inline):
```markdown
**Skipped/failed (no content):** src_005.json (fetch failed), src_009.json (skipped_tier3)
```

### Pattern 3: Synthesis Prompt Design

**What:** A prompt file that instructs Claude precisely how to synthesize source content into Research.md and media_urls.md.

**Critical constraints to encode in the prompt:**
1. Read synthesis_input.md in full before writing anything
2. Produce Research.md first (complete), then media_urls.md
3. Strict section order: Subject Overview → Timeline → Key Figures → Narrative Hooks → Direct Quotes → Contradictions → Unanswered Questions → Correcting the Record → Source Credibility
4. Word cap: Research.md body text ~2,000 words. Source Credibility table and callout labels do not count toward cap.
5. HOOK format: `**HOOK: [Title]**` on its own line, then 1-2 sentences. 3-5 hooks total.
6. QUOTE format: `**QUOTE: [Label]**` on its own line, then markdown blockquote (> ...), then attribution line: — Name, Role, [source URL]
7. Source Credibility table columns: Source (domain), Type, Corroborated By, Access Quality
8. Media extraction: while reading sources, identify visual media URLs only. Output to media_urls.md grouped by Archival Footage / Archival Photos / Documents / B-Roll
9. Write files to projects/N. [Title]/research/ using file tools. Use the path from synthesis_input.md header or the output directory printed by cmd_write.

### Pattern 4: writer.py Module Structure

```python
# writer.py
import json
from datetime import datetime, timezone
from pathlib import Path


def load_source_files(output_dir: Path) -> tuple[list[dict], list[dict]]:
    """Return (pass1_sources, pass2_sources) loaded from src_*.json and pass2_*.json."""
    ...


def build_synthesis_input(topic: str, pass1: list[dict], pass2: list[dict]) -> str:
    """Format source content into the flat synthesis_input.md string."""
    ...


def write_synthesis_input(output_dir: Path, content: str) -> Path:
    """Write synthesis_input.md to output_dir and return path."""
    ...
```

cmd_write in cli.py:
```python
def cmd_write(topic: str) -> None:
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)

    pass1, pass2 = load_source_files(output_dir)
    content = build_synthesis_input(topic, pass1, pass2)
    synthesis_path = write_synthesis_input(output_dir, content)

    print(f"Synthesis input ready: {synthesis_path}")
    print(f"Sources: {len(pass1)} Pass 1, {len(pass2)} Pass 2")
    print()
    prompt_path = _get_project_root() / ".claude" / "skills" / "researcher" / "prompts" / "synthesis.md"
    print(f"Synthesis prompt: {prompt_path}")
    print()
    print(
        "Aggregation complete. Read synthesis_input.md and the synthesis prompt, "
        "then produce Research.md and media_urls.md in the research/ directory."
    )
```

### Anti-Patterns to Avoid

- **Code-level markdown generation:** Don't build Research.md structure in Python. The synthesis prompt drives all section content and ordering. Python's job is aggregation only.
- **Truncating content in code:** CONTEXT.md is explicit — no code-level truncation. All content passes through to synthesis_input.md. The synthesis prompt enforces the 2,000-word output cap.
- **Async in cmd_write:** cmd_write needs no crawl4ai calls. Don't use asyncio.run() here — it's purely sync file I/O.
- **Separate passes for Research.md and media_urls.md:** Both come from one synthesis pass. The prompt instructs Claude to extract media URLs while reading sources, then write both files.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Source file discovery | Custom glob patterns | `output_dir.glob("src_*.json")` and `output_dir.glob("pass2_*.json")` | Already the pattern throughout cli.py |
| Output dir resolution | New path logic | `resolve_output_dir(root, topic)` from url_builder.py | Already handles project vs. standalone mode |
| Markdown generation for Research.md | Python markdown builder | Synthesis prompt + Claude's file tools | Architecture Rule 1 — no code wrapping LLM output |
| Media URL classification | regex/ML classifier | Synthesis prompt instructs Claude | Claude reads source context and categorizes accurately |

---

## Common Pitfalls

### Pitfall 1: synthesis_input.md Written to Wrong Location

**What goes wrong:** synthesis_input.md is a large scratch file (20-50k words). It should go to `.claude/scratch/researcher/` for standalone runs, but to `projects/N. [Title]/research/` for project runs. Using the wrong path breaks the handoff.

**Why it happens:** resolve_output_dir already returns the correct path based on project detection. The mistake is writing synthesis_input.md to a hardcoded scratch path instead of using output_dir.

**How to avoid:** Write synthesis_input.md directly to output_dir (same directory as src_*.json). This keeps all research artifacts co-located and lets Claude find them by the single output directory path printed by cmd_write.

**Warning signs:** Claude reads the wrong synthesis_input.md (from a previous topic run in scratch).

### Pitfall 2: Empty/Failed Sources Silently Omitted

**What goes wrong:** Sources with fetch_status != "ok" have empty content fields. If silently skipped, Claude doesn't know those URLs were attempted and failed — can't flag gaps.

**How to avoid:** Include failed sources in synthesis_input.md as a brief skipped/failed list at the top (not full entries). Enough for Claude to note gaps.

### Pitfall 3: No Pass 2 Files — cmd_write Still Works

**What goes wrong:** If the user ran cmd_write without running cmd_deepen first, there are no pass2_*.json files. This is valid — cmd_write should aggregate Pass 1 only and note the absence.

**How to avoid:** `output_dir.glob("pass2_*.json")` returns an empty list — not an error. writer.py handles empty pass2 list gracefully. The summary line says "0 Pass 2" sources.

### Pitfall 4: SKILL.md Incomplete — Workflow Not Documented

**What goes wrong:** SKILL.md currently shows cmd_write as "planned" with no workflow steps. If SKILL.md isn't updated to show the complete end-to-end workflow including cmd_write, Claude won't know to invoke it or what to do after it runs.

**How to avoid:** SKILL.md update is a required deliverable of this phase (per CONTEXT.md). Must document Step 3: Run write command, Step 4: Claude reads synthesis_input.md + synthesis.md prompt, Step 5: Claude writes Research.md + media_urls.md.

### Pitfall 5: Synthesis Prompt Missing Output Path Guidance

**What goes wrong:** Claude synthesizes correctly but writes files to the wrong directory (e.g., cwd instead of research/).

**How to avoid:** synthesis_input.md header must include the output directory path explicitly. The synthesis prompt must instruct Claude to write to that directory. Both synthesis_input.md (aggregated input) and Research.md/media_urls.md (Claude output) go to the same output_dir.

---

## Code Examples

Verified patterns from existing codebase:

### Reading All Source Files (from cli.py established pattern)

```python
# Pattern from cmd_deepen (cli.py)
for old_file in output_dir.glob("pass2_*.json"):
    old_file.unlink()

# For writer.py — read in sorted order
pass1_files = sorted(output_dir.glob("src_*.json"))
pass2_files = sorted(output_dir.glob("pass2_*.json"))

for src_file in pass1_files:
    data = json.loads(src_file.read_text(encoding="utf-8"))
```

### resolve_output_dir (from url_builder.py — no change needed)

```python
# url_builder.py:resolve_output_dir — already handles both cases
output_dir = resolve_output_dir(root, topic)
# Returns: projects/N. Title/research/  (if project found)
# Returns: .claude/scratch/researcher/  (standalone)
```

### Adding write subcommand to cli.py main()

```python
# Pattern mirrors survey/deepen in existing main()
write_parser = subparsers.add_parser(
    "write",
    help="Aggregate sources and prepare synthesis input for Research.md",
)
write_parser.add_argument(
    "topic",
    help="Topic string (same as used for survey/deepen)",
)

# In dispatch block:
elif args.command == "write":
    try:
        cmd_write(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

### synthesis_input.md Format (output of cmd_write)

```markdown
# Synthesis Input
**Topic:** Jonestown Massacre
**Generated:** 2026-03-14T10:00:00Z
**Sources:** 12 total (8 Pass 1, 4 Pass 2)
**Output directory:** /path/to/projects/1. Jonestown/research/

**Skipped/failed (no content):** src_005.json (failed — connection timeout), src_009.json (skipped — tier 3)

---

## Source 1 — src_001.json
**URL:** https://en.wikipedia.org/wiki/Jonestown
**Domain:** en.wikipedia.org
**Tier:** 1
**Words:** 4523
**Evaluation:** recommended — FBI vault docs referenced

{full content}

---
```

### synthesis.md Prompt Structure

```markdown
# Synthesis Prompt — Research Dossier

## Task

Read synthesis_input.md in full. Then produce two files:
1. Research.md — scriptwriter-ready research dossier (~2,000 words body text)
2. media_urls.md — catalog of visual media URLs found in sources

Write both files to the output directory shown in synthesis_input.md header.

## Research.md — Required Sections (in order)

### Subject Overview
~500 words. Dense factual summary. No editorial framing.

### Timeline
5-15 entries. Each: `- **[Date]** — [Event description, 1-2 sentences]. *Source: [domain]*`

### Key Figures
3-8 figures. Format per figure:
**[Name]** — [Role/Title]
[Relevance in 1-2 sentences. Cross-ref: see QUOTE: [Label] if a quote exists.]

### Narrative Hooks
3-5 hooks. Format:
**HOOK: [Title]**
[1-2 sentences: what the story beat is and why it's high-impact.]

### Direct Quotes
All significant quotes. Format per quote:
**QUOTE: [Label]**
> [Exact quote]
— [Speaker name], [Role], [source URL or domain]

### Contradictions
[Conflicting accounts. Name both sources and the disputed fact. 1-3 sentences per conflict.]

### Unanswered Questions
[Gaps that create narrative tension. Short list, 1 sentence each.]

### Correcting the Record
[Where mainstream coverage diverges from primary sources. Flag specifically.]

### Source Credibility

| Source | Type | Corroborated By | Access Quality |
|--------|------|-----------------|----------------|
| [domain] | [gov/academic/journalism/wiki/primary] | [other domain(s)] | [full/partial/paywall] |

## media_urls.md — Required Format

Group by asset type. Skip PDFs, academic papers, text-only pages.

### Archival Footage
- **URL:** [url]
  **Description:** [1 sentence]
  **Source:** [domain]

### Archival Photos
[same format]

### Documents
[same format]

### B-Roll
[same format]

## Word Cap

Research.md body text must be ~2,000 words total. The Source Credibility table,
HOOK labels, QUOTE labels, and section headings do not count toward the cap.
Distill — do not summarize everything; select the highest-value content.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All research in conversation context | Scratch files + context-loader pattern | Phase 8 | No context pollution — 20-50k words of source material stays on disk |
| LLM API wrapper for synthesis | Claude's native file tools + synthesis prompt | Architecture rule (from start) | No extra dependencies, no API cost, uses Claude Code's built-in capabilities |

---

## Open Questions

1. **synthesis_input.md size with 15 sources at 4,000+ words each**
   - What we know: 15 sources × avg 3,000 words = ~45,000 words. This is the intended design per CONTEXT.md.
   - What's unclear: Whether Claude Code's context window can handle 45,000-word synthesis_input.md reliably in all cases.
   - Recommendation: Proceed as designed. The synthesis prompt can instruct Claude to skim source summaries and read selectively when sources are redundant. Flag in SKILL.md that very large topics may require manual pruning of synthesis_input.md before synthesis.

2. **Metadata header in Research.md**
   - What we know: Whether to include a brief metadata header (topic, date, source count) is at Claude's discretion per CONTEXT.md.
   - What's unclear: Whether the Writer agent benefits from seeing source count or whether it adds noise.
   - Recommendation: Include a minimal header (topic + date only). Source count belongs in synthesis_input.md, not the final dossier.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (tests run from project root) |
| Quick run command | `pytest tests/test_researcher/ -x --tb=short -k "writer"` |
| Full suite command | `pytest tests/test_researcher/ -x --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DOSS-01 through DOSS-09 | Research.md content structure | manual/heuristic | N/A — Claude synthesis, not code | N/A |
| MEDIA-01, MEDIA-02 | media_urls.md structure | manual/heuristic | N/A — Claude synthesis, not code | N/A |
| (structural) | writer.py loads src_*.json + pass2_*.json | unit | `pytest tests/test_researcher/ -x --tb=short -k "writer"` | ❌ Wave 0 |
| (structural) | build_synthesis_input formats correctly | unit | `pytest tests/test_researcher/ -x --tb=short -k "writer"` | ❌ Wave 0 |
| (structural) | cmd_write dispatches and prints correct output | unit | `pytest tests/test_researcher/ -x --tb=short -k "write"` | ❌ Wave 0 |
| (structural) | cmd_write handles no pass2 files gracefully | unit | `pytest tests/test_researcher/ -x --tb=short -k "write"` | ❌ Wave 0 |

Note: DOSS-01 through MEDIA-02 requirements are satisfied by the synthesis prompt + Claude's synthesis step, not by deterministic code. Tests cover the deterministic aggregation layer only.

### Sampling Rate

- **Per task commit:** `pytest tests/test_researcher/ -x --tb=short -k "writer or write"`
- **Per wave merge:** `pytest tests/test_researcher/ -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_researcher/test_writer.py` — unit tests for writer.py (load_source_files, build_synthesis_input, write_synthesis_input) and cmd_write (smoke test, no-pass2 graceful handling)

*(No new framework needed — existing pytest infrastructure covers all tests)*

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — cli.py, url_builder.py, fetcher.py (direct read) — patterns for cmd_write
- `.planning/phases/10-dossier-output/10-CONTEXT.md` — locked design decisions
- `.claude/skills/researcher/SKILL.md` — existing module inventory and patterns

### Secondary (MEDIUM confidence)

- channel-assistant/cli.py cmd_topics/cmd_analyze — context-loader command pattern (verified by reading)
- `.claude/skills/researcher/prompts/survey_evaluation.md` — prompt structure precedent

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; pure stdlib file I/O already in use
- Architecture: HIGH — direct extension of established patterns in cli.py + url_builder.py
- Synthesis prompt design: MEDIUM — prompt content is at Claude's discretion; structure is locked but exact wording needs iteration
- Pitfalls: HIGH — derived from direct code reading and established decisions

**Research date:** 2026-03-14
**Valid until:** Phase remains stable; synthesis prompt may need tuning after first real use
