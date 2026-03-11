# Phase 4: Project Initialization + Metadata - Research

**Researched:** 2026-03-11
**Domain:** Python filesystem operations, argparse flow extension, heuristic prompt engineering for YouTube metadata
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Topic Selection Flow**
- User selects by number from chat cards (matching the `[N]` format from Phase 3's `format_chat_cards()`)
- One topic per run — user runs again for another topic
- No title edit step — title from the brief is used as-is for the directory name
- Integrated into `topics` flow — after `channel-assistant topics` generates and displays briefs, Claude asks the user to pick a number, then creates the project in the same session
- No separate `select` subcommand — selection is a continuation of the `topics` invocation

**Project Directory Structure**
- Location: `projects/` at the project root (alongside `context/`, `data/`)
- Naming: `projects/N. [Video Title]/` where N is auto-incremented (scan existing dirs, find highest number, add 1; first project = 1)
- Scaffold subdirectories on creation: `research/`, `assets/`, `script/`
- `metadata.md` written into the project directory
- Selected topic is auto-appended to `context/channel/past_topics.md` to close the dedup loop for future runs

**Title Variant Strategy**
- 5 variants per topic
- Pattern-informed: load Phase 2 title patterns from `context/competitors/analysis.md` and generate variants that follow top-performing competitor formulas
- 70 character max enforced on all variants
- One variant marked as recommended with brief reasoning (based on competitor pattern fit and topic strengths)
- Hook types vary across variants (question, statement, revelation, curiosity gap, etc.) — informed by data, not fixed

**Description Format**
- Minimal: hook paragraph only, no chapters/sources/links sections
- No hashtags
- 2-3 sentences: short enough to show before YouTube's "Show more" fold
- Marketing tone: slightly more engaging/clickable than the video's neutral narration — descriptions serve discovery, not narration
- One description per topic (not multiple variants)

### Claude's Discretion
- Exact wording of title variants and description
- How to map Phase 2 title patterns to variant generation
- Which competitor pattern to mark as "recommended" and reasoning
- Order of variants in metadata.md (beyond recommended being labeled)
- How to handle edge cases (e.g., title over 70 chars after pattern application)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OUTP-03 | User selects a topic from chat, and system creates `projects/N. [Video Title]/` with sequential numbering | Directory creation pattern, auto-increment logic documented below |
| OUTP-04 | System generates 3-5 YouTube title variants per selected topic, varying hook type | Heuristic task for Claude; metadata.md prompt format documented below |
| OUTP-05 | System generates 1 YouTube description per selected topic | Heuristic task for Claude; description format constraints locked in CONTEXT.md |
| OUTP-06 | Title variants and description are written to a `metadata.md` file in the project directory | File write pattern established; metadata.md schema documented below |
</phase_requirements>

---

## Summary

Phase 4 is a continuation of the `topics` workflow — after the user picks a number from the displayed chat cards, Claude orchestrates two actions: (1) a [DETERMINISTIC] Python function creates the project directory scaffold and writes metadata.md, and (2) a [HEURISTIC] reasoning pass generates 5 title variants and 1 description before the deterministic write happens.

The entire phase is low-risk technically. All the hard patterns (pathlib, argparse, UTF-8 file writes, `past_topics.md` format) are already established in phases 1-3 and can be directly reused. The only genuinely new code is `init_project()` — a single deterministic function that scans `projects/`, computes the next sequence number, creates the scaffold, and writes the file. The heuristic part (title generation, description writing) is handled by Claude reasoning before calling that function.

**Primary recommendation:** Add one new module `project_init.py` with `init_project()` and a `load_project_inputs()` helper; extend `cmd_topics()` in `cli.py` to print the project initialization context after topic generation completes (Claude then does the heuristic step and calls `init_project()`).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib.Path | stdlib | Directory creation, path construction, file writes | Already used throughout codebase; `mkdir(parents=True, exist_ok=True)` pattern established |
| re | stdlib | Sequential directory number parsing | Already used in `topics.py` for bold-title parsing |
| datetime | stdlib | Timestamp for metadata.md header | Already used in `write_topic_briefs()` |

### No New Dependencies
This phase adds zero new Python packages. Everything needed is in stdlib or already imported.

**Installation:**
```bash
# No new packages required
```

---

## Architecture Patterns

### Recommended Project Structure

New code lives in one new module alongside the existing modules:

```
.claude/skills/channel-assistant/scripts/channel_assistant/
├── cli.py          # extend cmd_topics() to print init context
├── topics.py       # no changes needed
├── project_init.py # NEW: init_project(), load_project_inputs()
└── ...             # existing modules untouched
```

New tests live alongside existing tests:

```
tests/test_channel_assistant/
├── test_topics.py       # existing, no changes
├── test_project_init.py # NEW: covers init_project() and load_project_inputs()
└── ...
```

### Pattern 1: Sequential Project Numbering

**What:** Scan `projects/` for directories matching `N. *` pattern, find the highest N, return N+1. If `projects/` is empty or missing, return 1.

**When to use:** Every time `init_project()` is called.

```python
# Source: derived from existing re usage in topics.py
import re
from pathlib import Path

def _next_project_number(projects_dir: Path) -> int:
    """Return the next sequential project number."""
    if not projects_dir.exists():
        return 1
    pattern = re.compile(r'^(\d+)\.')
    numbers = []
    for d in projects_dir.iterdir():
        if d.is_dir():
            m = pattern.match(d.name)
            if m:
                numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1
```

### Pattern 2: Project Directory Scaffold

**What:** Create `projects/N. [Title]/` plus three subdirectories in one shot. Use `mkdir(parents=True, exist_ok=True)` — established pattern in codebase.

**When to use:** Inside `init_project()` after computing the sequence number.

```python
# Source: established pattern from topics.py write_topic_briefs()
def _create_scaffold(project_dir: Path) -> None:
    for subdir in ("research", "assets", "script"):
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)
```

### Pattern 3: past_topics.md Auto-Append

**What:** Append a new line to `context/channel/past_topics.md` in the canonical format already parsed by `_load_past_topics()`.

**Canonical format:** `- **Title** | YYYY-MM-DD | one-line summary`

**When to use:** After successful `init_project()` call, as a side effect.

```python
# Source: format defined by _load_past_topics() in topics.py
from datetime import datetime, timezone

def _append_past_topic(path: Path, title: str, hook: str) -> None:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"- **{title}** | {date_str} | {hook}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
```

### Pattern 4: metadata.md Schema

**What:** A single markdown file written to `projects/N. [Title]/metadata.md`.

**Schema:**

```markdown
# [Title]

*Created: YYYY-MM-DD*

## Title Variants

| # | Title | Hook Type | Notes |
|---|-------|-----------|-------|
| 1 | [title text] | question | |
| 2 | [title text] | statement | |
| 3 | [title text] | revelation | |
| 4 | [title text] | curiosity gap | |
| 5 | [title text] | [type] | **RECOMMENDED** — [brief reasoning] |

## YouTube Description

[2-3 sentence hook paragraph]

## Topic Brief

[Copy of the selected brief from topic_briefs.md]
```

The "Topic Brief" section copies the full brief for self-contained reference — the project directory is the unit of truth for all downstream phases.

### Pattern 5: Heuristic → Deterministic Handoff

**What:** Claude reasons over competitor title patterns from `context/competitors/analysis.md` to generate variants, then passes the structured result to `init_project()`.

**Flow:**

1. `cmd_topics()` completes, displays chat cards
2. User picks number N
3. Claude reads `context/topics/topic_briefs.md` to load the selected brief
4. Claude reads `context/competitors/analysis.md` Title Patterns section for variant generation guidance
5. Claude generates 5 title variants + 1 description (HEURISTIC)
6. Claude calls `init_project()` with structured data (DETERMINISTIC)
7. `init_project()` creates scaffold, writes metadata.md, appends past_topics.md

### Anti-Patterns to Avoid

- **Embedding title generation logic in Python code:** Title generation is [HEURISTIC] — Claude reasons over patterns, does NOT write Python that calls an LLM. Architecture.md Rule 1.
- **A `select` subcommand:** Locked decision — no new CLI subcommand. Selection is a conversational continuation.
- **Modifying topics.py for project init:** Keep separation clean. `topics.py` is topic-generation-only. New `project_init.py` module handles project creation.
- **Race condition on numbering:** `_next_project_number()` is a point-in-time scan. Acceptable given single-user, non-concurrent usage.
- **Title sanitization for directory name:** The brief title is used as-is. Windows filesystem forbids `< > : " / \ | ? *` in filenames. Must strip or replace forbidden characters if present. Use the brief title verbatim but sanitize for filesystem safety before creating directory.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sequential numbering | Custom counter/database | Directory scan + regex | Zero state to manage; scan is authoritative |
| Directory creation | Custom recursive mkdir | `Path.mkdir(parents=True, exist_ok=True)` | Already the pattern; handles all edge cases |
| past_topics.md format validation | Schema validator | Match `_load_past_topics()` regex pattern | The reader already defines the contract |
| Title character length enforcement | Custom NLP | Simple `len(title) > 70` check | YouTube limit is a byte count, but for ASCII/common chars, len() is sufficient |

---

## Common Pitfalls

### Pitfall 1: Windows Filename Forbidden Characters

**What goes wrong:** If the topic title contains `:`, `?`, `"`, `*`, `/`, `\`, `|`, `<`, or `>`, `Path.mkdir()` raises `OSError` on Windows.

**Why it happens:** Windows NTFS forbids these characters in filenames. Topic titles are generated for YouTube (which allows all of these) so conflicts are possible.

**How to avoid:** Sanitize title before constructing directory path. Replace or strip forbidden chars.

```python
import re
def _sanitize_dir_name(title: str) -> str:
    # Remove characters forbidden on Windows NTFS
    return re.sub(r'[<>:"/\\|?*]', '', title).strip()
```

**Warning signs:** `OSError: [WinError 123]` or similar when calling `mkdir()`.

### Pitfall 2: past_topics.md Format Drift

**What goes wrong:** If the appended line format doesn't match the `\*\*(.+?)\*\*` regex in `_load_past_topics()`, the newly added topic won't be read back on the next `topics` run — defeating the dedup purpose.

**Why it happens:** Easy to forget the exact canonical format when writing the append function.

**How to avoid:** The canonical format is `- **Title** | YYYY-MM-DD | one-line summary`. Test `_load_past_topics()` round-trip: write a line with `_append_past_topic()`, read it back with `_load_past_topics()`, assert the title is present.

### Pitfall 3: projects/ Directory Not Created

**What goes wrong:** On a fresh repo, `projects/` doesn't exist. `_next_project_number()` returns 1 correctly, but `Path("projects/1. Title").mkdir(parents=True)` fails if `projects/` parent doesn't exist — except `parents=True` handles this.

**Why it happens:** Not a real pitfall with `parents=True`, but easy to miss during testing. Use `exist_ok=True` too.

**How to avoid:** Always call `project_dir.mkdir(parents=True, exist_ok=True)`. Already the codebase pattern.

### Pitfall 4: Title Variants Exceed 70 Characters

**What goes wrong:** After applying a competitor title pattern formula (e.g., "The [Subject] That [Did X]"), the resulting title may exceed 70 characters.

**Why it happens:** Pattern application isn't length-aware.

**How to avoid:** Claude enforces 70-char max during HEURISTIC generation step. Additionally, `init_project()` can assert or warn if a variant exceeds 70 chars. The check is `len(variant) > 70`.

### Pitfall 5: topic_briefs.md Not Present When User Selects

**What goes wrong:** User runs `topics` subcommand, Claude generates briefs and displays cards. But if `context/topics/topic_briefs.md` was not written (e.g., Claude omitted the `write_topic_briefs()` call), the project init step has no source data.

**Why it happens:** Phase 3 instruction says Claude must call `write_topic_briefs()` — but if that step is skipped, Phase 4 reads a stale or missing file.

**How to avoid:** `load_project_inputs()` in the new module should raise `FileNotFoundError` if `topic_briefs.md` is missing, with a clear message: "Run 'topics' first to generate topic_briefs.md".

---

## Code Examples

### init_project() — Full Function Signature

```python
# Source: derived from established codebase patterns (topics.py, analyzer.py)
from pathlib import Path
from datetime import datetime, timezone

def init_project(
    root: Path,
    title: str,
    hook: str,
    title_variants: list[dict],  # [{"title": str, "hook_type": str, "recommended": bool, "notes": str}]
    description: str,
    brief_markdown: str,         # raw markdown of the selected brief from topic_briefs.md
) -> Path:
    """Create project directory scaffold and write metadata.md.

    Returns the created project directory path.

    Side effect: appends selected topic to context/channel/past_topics.md.
    """
    projects_dir = root / "projects"
    n = _next_project_number(projects_dir)
    safe_title = _sanitize_dir_name(title)
    project_dir = projects_dir / f"{n}. {safe_title}"

    # Create scaffold
    _create_scaffold(project_dir)

    # Write metadata.md
    metadata_path = project_dir / "metadata.md"
    _write_metadata(metadata_path, title, title_variants, description, brief_markdown)

    # Append to past_topics.md
    past_topics_path = root / "context" / "channel" / "past_topics.md"
    _append_past_topic(past_topics_path, title, hook)

    return project_dir
```

### load_project_inputs() — Loading Selected Brief

```python
# Source: pattern from topics.py load_topic_inputs()
def load_project_inputs(root: Path, topic_number: int) -> dict:
    """Load the selected topic brief and title patterns for project init.

    Returns:
        {
            "brief": dict,          # parsed brief dict for topic_number
            "title_patterns": str,  # Title Patterns section from analysis.md
        }
    """
    briefs_path = root / "context" / "topics" / "topic_briefs.md"
    analysis_path = root / "context" / "competitors" / "analysis.md"

    if not briefs_path.exists():
        raise FileNotFoundError(
            f"Topic briefs not found: {briefs_path}. Run 'topics' first."
        )
    # ... parse brief N from markdown, extract Title Patterns section from analysis.md
```

### metadata.md Write Example

```python
# Source: pattern from write_topic_briefs() in topics.py
def _write_metadata(
    path: Path,
    title: str,
    variants: list[dict],
    description: str,
    brief_markdown: str,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# {title}",
        "",
        f"*Created: {timestamp}*",
        "",
        "## Title Variants",
        "",
        "| # | Title | Hook Type | Notes |",
        "|---|-------|-----------|-------|",
    ]
    for i, v in enumerate(variants, start=1):
        notes = "**RECOMMENDED**" if v.get("recommended") else ""
        if v.get("notes"):
            notes = f"{notes} — {v['notes']}".strip(" — ")
        lines.append(f"| {i} | {v['title']} | {v['hook_type']} | {notes} |")

    lines.extend([
        "",
        "## YouTube Description",
        "",
        description,
        "",
        "## Topic Brief",
        "",
        brief_markdown,
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `open()` + `os.makedirs()` | `pathlib.Path.mkdir(parents=True, exist_ok=True)` | Python 3.5+ | More readable, no import needed for makedirs |
| Hardcoded title caps | YouTube's actual limit: 100 chars title; 70 chars is channel convention | Channel decision | 70 char convention from CONTEXT.md is stricter than platform limit — use channel convention |

**Note on YouTube title length:** YouTube allows up to 100 characters in video titles. The 70-character constraint is a channel editorial decision (from CONTEXT.md), not a YouTube API limit. No API integration needed — this is a soft constraint enforced by Claude during heuristic generation and checked by code after.

---

## Open Questions

1. **Brief parsing from topic_briefs.md**
   - What we know: `write_topic_briefs()` writes numbered markdown sections (`## N. Title`). The selected brief can be extracted by finding `## N.` through `## N+1.` or end of file.
   - What's unclear: Whether to parse to dict or pass raw markdown to `_write_metadata()`. Raw markdown is simpler and avoids a parser.
   - Recommendation: Pass raw markdown section to `metadata.md` "Topic Brief" section — no dict parsing needed.

2. **title_variants dict schema**
   - What we know: 5 variants, one recommended, each with hook_type label.
   - What's unclear: Whether `notes` field is optional or required.
   - Recommendation: Make `notes` optional with empty string default. The recommended variant should always have notes (reasoning for recommendation).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already installed) |
| Config file | `pytest.ini` at project root — `pythonpath = .claude/skills/channel-assistant/scripts` |
| Quick run command | `pytest tests/test_channel_assistant/test_project_init.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OUTP-03 | `init_project()` creates `projects/N. Title/` with correct number | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_creates_numbered_directory -x` | Wave 0 |
| OUTP-03 | Sequential numbering increments past existing projects | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_increments_past_existing -x` | Wave 0 |
| OUTP-03 | Scaffold subdirs (`research/`, `assets/`, `script/`) created | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_scaffold_subdirs -x` | Wave 0 |
| OUTP-03 | Windows forbidden characters stripped from directory name | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_sanitizes_forbidden_chars -x` | Wave 0 |
| OUTP-03 | Topic appended to `past_topics.md` in canonical format | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_appends_past_topic -x` | Wave 0 |
| OUTP-03 | Appended entry round-trips through `_load_past_topics()` | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_past_topic_roundtrip -x` | Wave 0 |
| OUTP-06 | `metadata.md` written to project directory | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_creates_metadata_file -x` | Wave 0 |
| OUTP-06 | All 5 title variants appear in metadata.md | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_variants_written -x` | Wave 0 |
| OUTP-06 | Recommended variant is labeled in metadata.md | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_recommended_labeled -x` | Wave 0 |
| OUTP-06 | Description appears in metadata.md | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestWriteMetadata::test_description_written -x` | Wave 0 |
| OUTP-04 | Title variant length enforcement (≤70 chars) | unit | `pytest tests/test_channel_assistant/test_project_init.py::TestInitProject::test_title_length_check -x` | Wave 0 |
| OUTP-04, OUTP-05 | Heuristic generation (variants + description) | manual-only | N/A — Claude reasoning, not code | manual |

**Manual-only justification:** OUTP-04 and OUTP-05 require Claude to generate natural language content informed by competitor patterns. There is no deterministic output to assert against — quality is validated by human review.

### Sampling Rate

- **Per task commit:** `pytest tests/test_channel_assistant/test_project_init.py -x`
- **Per wave merge:** `pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_channel_assistant/test_project_init.py` — covers all OUTP-03 and OUTP-06 deterministic behaviors listed above
- [ ] `projects/` directory — does not exist yet; `init_project()` must create it via `parents=True`

*(Existing test infrastructure in `pytest.ini` and `tests/test_channel_assistant/` covers all other needs — no new framework setup required)*

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `.claude/skills/channel-assistant/scripts/channel_assistant/topics.py` — `_load_past_topics()` format, `write_topic_briefs()` pattern, `format_chat_cards()` numbering
- Direct code inspection of `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` — `cmd_topics()` entry point, argparse subcommand structure, `_get_project_root()` pattern
- `pytest.ini` at project root — confirmed `pythonpath` and `testpaths` settings
- `tests/test_channel_assistant/test_topics.py` — confirmed test class patterns used in project
- `.planning/phases/04-project-initialization-metadata/04-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- Python stdlib `pathlib` documentation — `Path.mkdir(parents=True, exist_ok=True)` semantics (training knowledge, stable API since Python 3.5)
- Windows NTFS forbidden characters list — `< > : " / \ | ? *` (well-documented OS constraint)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies; all patterns verified in existing codebase
- Architecture: HIGH — `init_project()` design mirrors existing module patterns exactly
- Pitfalls: HIGH — Windows filename issue is OS-documented; format drift is testable; all other pitfalls are derived from actual codebase inspection

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (stdlib patterns; no external dependencies to go stale)
