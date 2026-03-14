# Phase 12: Writer Agent - Research

**Researched:** 2026-03-15
**Domain:** Python CLI skill + generation prompt design for documentary script writing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Arc Construction**
- Writer derives chapter structure from Research.md content — timeline, hooks, key figures, and narrative tension points determine natural chapter breaks
- No predefined arc template required; Universal Voice Rules from STYLE_PROFILE.md apply to all topics regardless of arc shape
- Soft guardrail: 4-7 chapters per script (matches channel.md target of 4-7 acts)
- Per-chapter word count is not enforced — natural flow determines chapter length
- Open Ending Template from STYLE_PROFILE.md is applied when the topic qualifies (contested resolution, permanently incomplete record, moral weight in not-knowing)

**HOOK/QUOTE Consumption**
- Writer selects a best subset of HOOKs from Research.md — the dossier is a buffet, not a checklist. Typically 2-4 hooks per script
- The strongest HOOK becomes the video's opening, following STYLE_PROFILE's 4-part hook formula: quote → compressed overview → optional misinformation flag → "This is the true story of…" closing formula. This formula is always followed.
- Remaining selected HOOKs anchor chapter entry points — they're the reason a new chapter begins
- QUOTEs appear verbatim as direct speech with inline attribution. The narrator introduces the speaker, the quote speaks, the narrator resumes. Example: 'As Nestor would later say: "When you are a bastard, it's like being born into a garbage can."'

**Script Output Format**
- Script.md starts directly with Chapter 1 — no header, no metadata, no table of contents
- Each chapter is an H2 heading: `## N. Evocative Title` followed by continuous prose paragraphs
- No bullet points, sub-sections, stage directions, visual cues, or production notes within chapters
- Chapter titles use evocative register (what the chapter feels like) not descriptive (what happens in it) — per STYLE_PROFILE chapter naming rules
- Output location: `projects/N. [Title]/Script.md`

**Writer Invocation Workflow**
- CLI subcommand: `python -m writer load "<topic>"` — resolves project directory, aggregates Research.md + STYLE_PROFILE.md + channel.md, prints to stdout
- Context package is fixed — all three files always included, no flags needed. Stays within 8,000-word budget.
- One-shot generation with no review gate — Claude generates full script and writes Script.md directly. Human reviews via git diff after the fact.
- Single generation prompt file (e.g., `prompts/generation.md`) contains all writer instructions. The prompt IS the agent's brain.
- No revision capability in Phase 12 — chapter-level iteration deferred to REFINE-01 (future requirement)

### Claude's Discretion
- Exact arc shape per topic (chronological, thematic, or hybrid) — derived from research content
- Which HOOKs and QUOTEs to select from the dossier
- Chapter count within the 4-7 range
- How to distribute word count across chapters
- Whether to apply the Truth-Seeking Coda (only when widespread misinformation exists about the subject)

### Deferred Ideas (OUT OF SCOPE)
- REFINE-01: Iterate on specific chapters without regenerating the full script — future milestone
- REFINE-02: Adjust script length to hit target runtime (word count → minutes estimate) — future milestone
- REFINE-03: Multi-reference blending when multiple scripts exist in `context/script-references/` — future milestone
- Automated style drift detection between generated scripts and STYLE_PROFILE.md — future quality gate
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRIPT-01 | Writer generates numbered chapter-based narration from a project's Research.md | CLI `load` command aggregates Research.md and prints to stdout; Claude writes chapters via generation prompt |
| SCRIPT-02 | Writer anchors all claims to Research.md sources — no hallucinated facts | Generation prompt instructs Claude to only state claims present in the dossier; source sections and contradictions sections in Research.md provide the ground-truth boundary |
| SCRIPT-03 | Writer maintains channel voice consistency using STYLE_PROFILE.md + channel.md | Both files included in fixed context package printed by CLI; generation prompt references the 5 Universal Voice Rules by name |
| SCRIPT-04 | Writer consumes HOOK and QUOTE callouts from Research.md for narrative impact | Research.md Section 4 (HOOKs) and Section 5 (QUOTEs) are formatted with explicit labels; generation prompt instructs on selection and placement rules |
| SCRIPT-05 | Writer supports open endings for unsolved mystery topics | Generation prompt includes Open Ending Template trigger condition and three-part structure; Duplessis topic qualifies |
| SCRIPT-06 | Writer outputs pure narration text (no visual cues, no production notes, no host commentary) | Format locked in decisions: no bullets, sub-sections, stage directions, or production notes; Rule 3 (No Host Commentary) enforced via generation prompt |
| SCRIPT-07 | Writer outputs Script.md into the project directory (`projects/N. [Title]/`) | CLI resolves project directory using same `resolve_output_dir` pattern as researcher; writes Script.md to resolved path |
</phase_requirements>

---

## Summary

Phase 12 builds a single-subcommand CLI skill (`writer`) following the exact pattern established by the `researcher` skill. The Python code's only job is deterministic: find the project directory, read three fixed files (Research.md + STYLE_PROFILE.md + channel.md), concatenate them into a context package, and print to stdout. Claude then reads that output and writes the script — all reasoning is heuristic and happens outside Python.

The generation prompt (`prompts/generation.md`) is the cognitive core of this phase. It must specify the hook formula, chapter naming register, HOOK/QUOTE selection and placement rules, Open Ending Template trigger, output format, and all 5 Universal Voice Rules from STYLE_PROFILE.md. Getting this prompt right is the bulk of the implementation work. The Python code is approximately 60-80 lines.

The validation target is the Duplessis Orphans project (`projects/1. The Duplessis Orphans Quebec's Stolen Children/research/Research.md`), which already exists with 6 HOOKs and 5 QUOTEs in properly labeled sections. This topic qualifies for the Open Ending Template (Church never apologized, waiver required, unanswered questions about bodies and experiments, no exhumation outcome on record).

**Primary recommendation:** Write the generation prompt first; the CLI is a mechanical translation of the researcher CLI pattern and follows in minutes.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.14+ | argparse, pathlib, sys | Project rule: stdlib only for CLI tools |
| argparse | stdlib | Subcommand parsing | Matches researcher and channel-assistant pattern exactly |
| pathlib.Path | stdlib | File resolution and I/O | Project coding standard — never string concatenation |

### Supporting

None. No third-party dependencies. The researcher skill uses crawl4ai for fetching; the writer skill reads local files only.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Printing context to stdout | Writing to a temp file | stdout matches researcher pattern exactly; keeps the CLI contract uniform across all skills |
| Fixed 3-file context package | Flags for optional files | Complexity with no benefit — all three files are always needed for meaningful generation |

**Installation:**

```bash
# No dependencies to install — stdlib only
```

---

## Architecture Patterns

### Recommended Project Structure

```
.claude/skills/writer/
├── SKILL.md                    # Invocation docs + workflow
├── CONTEXT.md                  # Stage contract (inputs, process, output)
├── prompts/
│   └── generation.md           # The writer's brain — all generation instructions
└── scripts/
    └── writer/
        ├── __init__.py
        ├── __main__.py         # Entry point for python -m writer
        └── cli.py              # load subcommand — thin context aggregator
```

Output target (already exists, no changes needed):

```
projects/
└── 1. The Duplessis Orphans Quebec's Stolen Children/
    ├── research/
    │   └── Research.md         # Input — already populated
    └── Script.md               # Output — written by Claude after load
```

### Pattern 1: CLI Context Aggregator (load subcommand)

**What:** Resolves project directory, reads 3 fixed files, prints a labeled markdown package to stdout.

**When to use:** Every time the writer skill is invoked. No conditions — same behavior always.

**Example:**

```python
# Source: researcher/cli.py pattern — adapted for writer
def cmd_load(topic: str) -> None:
    """Aggregate Research.md + STYLE_PROFILE.md + channel.md and print to stdout."""
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    research_path = project_dir / "research" / "Research.md"
    style_path = root / "context" / "channel" / "STYLE_PROFILE.md"
    channel_path = root / "context" / "channel" / "channel.md"
    prompt_path = root / ".claude" / "skills" / "writer" / "prompts" / "generation.md"

    for path, label in [
        (research_path, "Research Dossier"),
        (style_path, "Style Profile"),
        (channel_path, "Channel DNA"),
    ]:
        if not path.exists():
            print(f"Error: {label} not found at {path}", file=sys.stderr)
            sys.exit(1)

    parts = []
    for path, label in [
        (research_path, "Research Dossier"),
        (style_path, "Style Profile"),
        (channel_path, "Channel DNA"),
    ]:
        parts.append(f"# {label}\n\n{path.read_text(encoding='utf-8')}")

    print("\n\n---\n\n".join(parts))
    print(f"\nGeneration prompt: {prompt_path}")
    print("\nContext loaded. Read the generation prompt, then produce Script.md.")
```

### Pattern 2: Project Directory Resolution

**What:** Resolves topic string to `projects/N. [Title]/` using fuzzy match on directory names.

**When to use:** `cmd_load` always calls this. Same logic as `resolve_output_dir` in researcher's `url_builder.py`.

**Example:**

```python
# Source: adapted from researcher/url_builder.py pattern
def resolve_project_dir(root: Path, topic: str) -> Path:
    """Resolve topic string to projects/N. [Title]/ directory.

    Matches by substring of the directory name (case-insensitive).
    Falls back to creating path in .claude/scratch/ if no project found.
    """
    projects_dir = root / "projects"
    if projects_dir.exists():
        topic_lower = topic.lower()
        for candidate in sorted(projects_dir.iterdir()):
            if candidate.is_dir() and topic_lower in candidate.name.lower():
                return candidate
    # Fallback: scratch directory for topics without a project
    scratch_dir = root / ".claude" / "scratch" / "writer" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir
```

### Pattern 3: Generation Prompt Structure

**What:** `prompts/generation.md` contains all instructions Claude uses to write the script. It is read by Claude after the CLI prints context — it is not read by Python code.

**When to use:** Every script generation session. Claude reads it as a reference after loading context.

**Mandatory sections in generation.md:**

1. **Role statement** — "You are the writer for a dark mysteries documentary channel…"
2. **Input contract** — what the context package contains (Research.md sections, STYLE_PROFILE.md sections, channel.md)
3. **Hook construction** — 4-part formula (opening quote → compressed overview → optional misinformation flag → closing formula)
4. **HOOK/QUOTE selection rules** — subset selection logic, typical 2-4 HOOKs, strongest HOOK opens the video
5. **Chapter structure rules** — derive from research content, 4-7 chapters, H2 format `## N. Evocative Title`
6. **Voice rules reference** — enumerate all 5 Universal Voice Rules from STYLE_PROFILE.md with their names
7. **Output format constraints** — pure narration only, no stage directions, no visual cues, no host commentary, no metadata header
8. **Open Ending Template trigger** — when to apply it, three-part structure
9. **Output instruction** — write Script.md to `projects/N. [Title]/Script.md`

### Pattern 4: __main__.py Entry Point

**What:** Minimal dispatch file, identical to researcher pattern.

```python
"""Entry point for `python -m writer <subcommand>`."""
import sys

def main() -> None:
    try:
        from writer import cli
        cli.main()
    except ImportError:
        print("writer: no subcommand specified", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Anti-Patterns to Avoid

- **LLM calls in Python code:** The architecture explicitly prohibits LLM API wrappers. All reasoning is Claude's native reasoning in the same session. Never add an API call to cli.py.
- **Flags for optional context files:** The context package is fixed. Adding `--no-style-profile` or similar flags violates the design decision and adds complexity for no benefit.
- **Writing Script.md from Python:** Claude writes Script.md using the Write tool. cli.py only prints context. If Python wrote the file, it would require an LLM API call.
- **Printing raw file paths instead of content:** The stdout output must include the actual file content (for Claude to reason over), not just paths. Paths are a common shortcut that breaks the workflow.
- **Topic matching that raises on no-match:** Should fall back to scratch directory, matching researcher's pattern. Raising an error on first invocation with a new topic is a bad UX.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Project directory lookup | Custom registry or DB query | Substring match on `projects/` directory names | Already works for the one existing project; no registry needed at this scale |
| Style enforcement | Python string analysis or NLP checks | Generation prompt rules + human git-diff review | Project explicitly out-of-scoped automated quality scoring |
| Context file reading | Custom markdown parser | Plain `Path.read_text()` | Files are already valid markdown; no parsing needed |
| Output validation | Word count gates, sentence analyzers | Human review via git diff | Explicitly out of scope in REQUIREMENTS.md |

**Key insight:** The simpler the Python, the more reliable the tool. Every line of Python that tries to do reasoning is a line that should be in the prompt instead.

---

## Common Pitfalls

### Pitfall 1: Context Package Exceeds 8,000-Word Budget

**What goes wrong:** STYLE_PROFILE.md + channel.md + Research.md concatenated exceeds the soft budget, causing the generation session to hit context limits or degrade.

**Why it happens:** STYLE_PROFILE.md is approximately 370 lines with many verbatim examples. Research.md is ~2,000 words. channel.md is ~68 lines. Total is roughly 3,500-4,000 words combined — well within the 8,000-word budget based on current file sizes. But if Research.md grows (deeper dossiers) or STYLE_PROFILE.md is expanded, this could become an issue.

**How to avoid:** No truncation needed for Phase 12. The current files fit comfortably. Document the budget as a constraint in SKILL.md for future maintainers. The decision is already locked: no flags, all three files always included.

**Warning signs:** CLI stdout exceeds ~60,000 characters (~8,000 words).

---

### Pitfall 2: Topic String Doesn't Match Directory Name

**What goes wrong:** `python -m writer load "Duplessis Orphans"` fails to find `projects/1. The Duplessis Orphans Quebec's Stolen Children/` because the substring match misses.

**Why it happens:** Project directories include a number prefix and may use different words than the user types. The researcher skill has the same issue and uses a loose substring match.

**How to avoid:** Case-insensitive substring match. Test with the actual topic string "Duplessis Orphans" against the actual directory name. Fall back gracefully to scratch directory rather than erroring.

**Warning signs:** CLI exits with "project not found" error on first use.

---

### Pitfall 3: Generation Prompt Is Too Permissive on Output Format

**What goes wrong:** Claude adds a header block (title, date, topic), a table of contents, or section labels before Chapter 1. The locked decision is: Script.md starts directly with Chapter 1, no header, no metadata.

**Why it happens:** Claude's default behavior when writing a document is to add metadata and structure. Without explicit prohibition in the prompt, it adds these.

**How to avoid:** Generation prompt must explicitly state: "Begin the script immediately with the first chapter heading. Do not add a title, date, topic header, table of contents, or any document-level metadata."

**Warning signs:** First line of Script.md is not `## 1. [Chapter Title]`.

---

### Pitfall 4: HOOK vs QUOTE Confusion in Generation Prompt

**What goes wrong:** Claude treats all Research.md Section 4 (HOOKs) and Section 5 (QUOTEs) as equivalent, placing quotes mid-paragraph or using HOOKs as verbatim narration.

**Why it happens:** HOOKs are narrative hooks (story angles, factual revelations) — they inform the chapter structure. QUOTEs are verbatim spoken words — they appear as direct speech with attribution. The distinction must be explicit in the prompt.

**How to avoid:** Generation prompt must define: HOOKs = structural anchors that determine where chapters begin and what drives them; QUOTEs = verbatim text, always attributed, always introduced by narrator, always set apart from narration prose.

**Warning signs:** A HOOK appears verbatim as narration text, or a QUOTE appears without attribution or merged into a paragraph.

---

### Pitfall 5: Cult-Arc Overfitting on Non-Cult Topic

**What goes wrong:** The generation prompt references STYLE_PROFILE.md Template A (Cult / Group Radicalization Arc) and Claude applies it to the Duplessis Orphans — a case of institutional corruption — forcing the narrative into cult-arc chapter structure.

**Why it happens:** Template A is the only documented template in STYLE_PROFILE.md. The profile already warns against this with "Do not apply a cult arc to an unrelated topic" and the notice that topics not matching labeled arc types should create their own arc structure. But the generation prompt must reinforce this.

**How to avoid:** Generation prompt must explicitly state: "The Duplessis Orphans is an institutional corruption topic — Template A (Cult / Group Radicalization Arc) does not apply. Derive the chapter structure from the Research.md timeline, key figures, and narrative tension points."

**Warning signs:** Chapter titles mirror the Template A act progression (Setting → Initial Control → Radicalization Peak → Rupture → Aftermath).

---

## Code Examples

Verified patterns from existing project code:

### Full CLI Structure (researcher pattern to replicate)

```python
# Source: .claude/skills/researcher/scripts/researcher/cli.py
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="writer",
        description="Writer skill — documentary script generation",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="Load context for script generation")
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

### Project Root Detection (from researcher url_builder.py pattern)

```python
# Source: .claude/skills/researcher/scripts/researcher/url_builder.py pattern
def _get_project_root() -> Path:
    """Walk up from cwd until we find CLAUDE.md (project root marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    return current
```

### File Read Pattern (from researcher writer.py)

```python
# Source: .claude/skills/researcher/scripts/researcher/writer.py
content = path.read_text(encoding="utf-8")
```

### Test Pattern (from tests/test_researcher/test_writer.py)

```python
# Source: tests/test_researcher/test_writer.py
def test_cmd_load_smoke(tmp_path: Path, capsys) -> None:
    """cmd_load prints all three context files and generation prompt path."""
    from writer.cli import cmd_load

    with patch("writer.cli._get_project_root", return_value=tmp_path), \
         patch("writer.cli.resolve_project_dir", return_value=tmp_path):
        # Setup fake files
        (tmp_path / "research").mkdir()
        (tmp_path / "research" / "Research.md").write_text("# Research", encoding="utf-8")
        # ... etc
        cmd_load("test topic")

    captured = capsys.readouterr()
    assert "Research Dossier" in captured.out
    assert "Style Profile" in captured.out
    assert "Channel DNA" in captured.out
    assert "generation.md" in captured.out
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM calls in Python skill code | No LLM calls — Claude is the runtime | v1.0 architecture decision | All skills are pure data-loaders; reasoning is native Claude |
| Template-driven arc structure | Research-content-driven arc derivation | Phase 12 design decision | Writer creates original arc per topic rather than mapping to templates |
| Full script in one prompt with all instructions embedded | Prompt file separate from CLI | Phase 12 design decision | Prompt can be edited without touching Python code |

**Deprecated/outdated:**
- `context/channel/writting_style_guide.md`: Absorbed into STYLE_PROFILE.md during Phase 11. Deleted. Do not reference it.
- `style-extraction/` skill: Phase 11 complete — STYLE_PROFILE.md is the output, not a process to run again.

---

## Open Questions

1. **`_get_project_root()` duplication**
   - What we know: Both researcher and writer need this same function. It currently lives in `researcher/url_builder.py`.
   - What's unclear: Whether to copy it into `writer/cli.py` directly or share it somehow.
   - Recommendation: Copy it into `writer/cli.py`. Do not create a shared utility — the project rule is "three similar lines of code is better than a premature abstraction." One copy per skill is the pattern already in use.

2. **Script.md write instruction placement**
   - What we know: Claude writes Script.md using the Write tool, but the generation prompt must tell Claude the exact output path.
   - What's unclear: Whether the CLI should print the resolved output path explicitly so Claude doesn't have to compute it.
   - Recommendation: Print the resolved output path at the end of stdout. Pattern: `Output: projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md`. Claude then uses that exact path with the Write tool.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already installed — see existing tests/) |
| Config file | none — runs with `pytest -x --tb=short` from project root |
| Quick run command | `PYTHONPATH=.claude/skills/writer/scripts pytest tests/test_writer/ -x --tb=short` |
| Full suite command | `pytest -x --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRIPT-01 | `cmd_load` prints Research.md content to stdout | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_research -x` | Wave 0 |
| SCRIPT-02 | No Python code enforces claim anchoring — prompt-level only | manual | Human review of Script.md against Research.md | manual-only |
| SCRIPT-03 | `cmd_load` prints STYLE_PROFILE.md content to stdout | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_style_profile -x` | Wave 0 |
| SCRIPT-04 | Research.md Section 4 (HOOKs) visible in printed context | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_hooks -x` | Wave 0 |
| SCRIPT-05 | Open Ending Template — prompt-level only | manual | Human review of Script.md ending | manual-only |
| SCRIPT-06 | Pure narration format — prompt-level only | manual | Human review for absence of stage directions | manual-only |
| SCRIPT-07 | `cmd_load` prints resolved output path | unit | `pytest tests/test_writer/test_cli.py::test_cmd_load_prints_output_path -x` | Wave 0 |

Note: SCRIPT-02, SCRIPT-05, SCRIPT-06 are manual-only because they test the quality of Claude's heuristic output, not Python code behavior. The project explicitly out-of-scoped automated quality scoring for scripts.

### Sampling Rate

- **Per task commit:** `PYTHONPATH=.claude/skills/writer/scripts pytest tests/test_writer/ -x --tb=short`
- **Per wave merge:** `pytest -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_writer/__init__.py` — package marker
- [ ] `tests/test_writer/test_cli.py` — covers SCRIPT-01, SCRIPT-03, SCRIPT-04, SCRIPT-07
- [ ] No framework install needed — pytest already present

---

## Sources

### Primary (HIGH confidence)

- Direct file reads: `.claude/skills/researcher/scripts/researcher/cli.py` — CLI pattern, project root detection, argparse subcommand structure
- Direct file reads: `.claude/skills/researcher/scripts/researcher/writer.py` — file aggregation and stdout printing pattern
- Direct file reads: `context/channel/STYLE_PROFILE.md` — 5 Universal Voice Rules, arc templates, Open Ending Template, Hook Patterns, Chapter Naming Register
- Direct file reads: `context/channel/channel.md` — output targets (3,000-7,000 words, 4-7 chapters)
- Direct file reads: `projects/1. The Duplessis Orphans .../research/Research.md` — validation target structure (6 HOOKs, 5 QUOTEs, 9 sections)
- Direct file reads: `tests/test_researcher/test_writer.py` — test patterns (tmp_path, capsys, unittest.mock.patch)
- Direct file reads: `.planning/phases/12-writer-agent/12-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — SCRIPT-01 through SCRIPT-07 definitions and out-of-scope table
- `.planning/STATE.md` — accumulated decisions from v1.2 planning

### Tertiary (LOW confidence)

None — all findings are from direct project file inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed from existing skills, project uses stdlib only, no new dependencies
- Architecture: HIGH — confirmed from researcher skill code, exact pattern to replicate is readable
- Pitfalls: HIGH — derived from locked decisions and existing STYLE_PROFILE.md warnings about cult-arc overfitting
- Generation prompt design: MEDIUM — no existing writer prompt to reference; must be created from scratch using STYLE_PROFILE.md content as the source of truth

**Research date:** 2026-03-15
**Valid until:** 2026-06-15 (stable — no external dependencies, all context is local project files)
