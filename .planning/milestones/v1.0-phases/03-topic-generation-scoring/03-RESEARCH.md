# Phase 3: Topic Generation + Scoring - Research

**Researched:** 2026-03-11
**Domain:** Heuristic topic generation, anchored scoring rubrics, deduplication, CLI integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scoring Rubric Design**
- 1-5 scale for all four dimensions: obscurity, complexity, shock factor, verifiability
- Total score out of 20
- Example-anchored rubric: each level references real topics as calibration points
  - E.g., Obscurity 5 = "Zero mainstream coverage, requires deep research" with a concrete example
  - E.g., Obscurity 1 = "Jack the Ripper, widely covered by 50+ channels"
- No minimum score threshold — all generated topics are shown, ranked by total score
- No content pillar weighting — scores are purely based on the 4 criteria
- Content pillar shown as a tag/label on each topic but doesn't affect scoring

**Topic Generation Source & Method**
- Three sources combined: competitor data (Phase 2 analysis), channel DNA pillars, and live web research
- Web research via tavily-mcp at generation time — Claude searches for obscure cases/events matching content pillars
- Generate 10-15 candidates, present ALL ranked (not filtered to top 5)
- Broad generation, gap-aware: competitor gaps from Phase 2 inform ranking tags but don't constrain generation
- Underserved clusters from Phase 2 topic clustering are tagged on relevant topics but all sources compete equally

**Deduplication Strategy**
- Check generated topics against `context/channel/past_topics.md`
- `past_topics.md` format: simple list with metadata — title, date published, 1-line summary per entry
- Strictness: exact topic only — same subject with different angle is allowed
- Near-duplicates shown with warning tag: "Similar to: [past topic]" rather than silently dropped
- No competitor overlap checking — competitor coverage is already visible in Phase 2 analysis report

**Output Format & Invocation**
- Subcommand: `channel-assistant topics`
- Output to both chat and file
- Chat output: compact cards with scores per topic — title, hook (1 sentence), scores (O:4 C:3 S:5 V:3 = 15/20), estimated runtime, content pillar tag, duplicate warning if applicable
- File output: `context/topics/topic_briefs.md` — full Topic Brief Schema per topic (title, hook, timeline with 3-8 entries, all 4 scores with justification text, estimated runtime, content pillar)
- File overwritten each run (latest snapshot, no history)
- Chat summary line after cards: "N topics generated. Full briefs: context/topics/topic_briefs.md"

### Claude's Discretion
- Exact rubric example topics per level (informed by channel niche)
- Tavily search queries and how many searches per run
- How to structure the generation prompt (single pass vs iterative)
- Internal candidate ranking tiebreakers
- Timeline entry detail level in full briefs

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANLZ-04 | System scores each generated topic on obscurity, complexity, shock factor, and verifiability using anchored rubrics with concrete criteria per score level | Scoring rubric section below — example-anchored 1-5 scale with channel-niche calibration anchors derived from known dark-mysteries topics |
| OUTP-01 | System generates 5 scored topic briefs per run following the Topic Brief Schema (title, hook, timeline, complexity/obscurity/shock scores, estimated runtime) | Note: CONTEXT.md overrides this to 10-15 candidates. Full schema and output format documented below. |
| OUTP-02 | Generated topics are checked against `context/channel/past_topics.md` and duplicates/near-duplicates are rejected | Deduplication is a [DETERMINISTIC] file-read step; near-duplicates get warning tags not silent rejection |
</phase_requirements>

---

## Summary

Phase 3 adds a `topics` subcommand to the existing channel-assistant CLI. The command is fundamentally a [HEURISTIC] operation: Claude reads competitor analysis output, channel DNA, and live web research results, then generates and scores 10-15 topic candidates. The only [DETERMINISTIC] code needed is: reading `past_topics.md` for deduplication, reading `analysis.md` and `channel.md` as input context, writing `context/topics/topic_briefs.md`, and wiring the argparse subcommand.

The Phase 2 competitor analysis (`context/competitors/analysis.md`) is already rich enough to drive topic generation. It contains 7 topic clusters with saturation ratings, outlier video data, and editorial recommendations — all of which become direct inputs to the generation prompt. The underserved clusters (Location Mysteries, Aviation Mysteries, Obscure Cults) are the most actionable generation targets.

The anchored scoring rubric is the most design-sensitive component. Each dimension must be calibrated to the dark mysteries niche — not generic content scoring — so that a 4/5 on obscurity means something specific to this channel's audience and competitive landscape. Rubric anchors should reference real recognizable topics from the niche (Jack the Ripper = Obscurity 1; Mesa Verde Cannibal Clan = Obscurity 5) so Claude can apply scores consistently across runs.

**Primary recommendation:** Implement `cmd_topics()` in `cli.py` as a thin [DETERMINISTIC] wrapper that loads input files, injects them into a structured generation prompt, and writes the output file. Claude performs all [HEURISTIC] reasoning (generation, scoring, dedup judgment) during that command execution.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (pathlib, argparse, json) | 3.14+ | File I/O, CLI subcommand, JSON parsing | Already in use across Phases 1-2; zero new dependencies |
| tavily-mcp | MCP tool | Live web research for obscure topic discovery | Already in CLAUDE.md skill list; enables real-time research without LLM API wrappers |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| difflib (stdlib) | 3.14+ | Fuzzy string matching for near-duplicate detection against past_topics.md | Use `difflib.SequenceMatcher` for title similarity scoring |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| difflib fuzzy match | embedding-based semantic similarity | Overkill for a flat topic list; difflib is zero-dependency and sufficient for exact/near-exact title matching |
| File overwrite on each run | Append with timestamps | CONTEXT.md locks overwrite; history tracking is deferred |

**Installation:**
```bash
# No new dependencies — stdlib only
```

---

## Architecture Patterns

### Recommended Project Structure (additions to existing)

```
.claude/skills/channel-assistant/scripts/channel_assistant/
├── cli.py               # ADD: cmd_topics() + 'topics' subparser
├── topics.py            # NEW: load_inputs(), check_duplicates(), write_briefs()
├── models.py            # EXTEND: TopicBrief dataclass or TypedDict
├── analyzer.py          # UNCHANGED
├── database.py          # UNCHANGED
context/
└── topics/
    └── topic_briefs.md  # NEW: written by cmd_topics()
```

### Pattern 1: [DETERMINISTIC] / [HEURISTIC] Split

**What:** Deterministic Python handles file I/O and output writing. Claude's heuristic reasoning handles generation, scoring, and editorial judgment. This is the established project pattern from Phase 2.

**When to use:** Any task requiring LLM judgment (generation, scoring, editorial taste) is [HEURISTIC]. Any task requiring structured data manipulation is [DETERMINISTIC].

**Example (Phase 2 precedent):**
```python
# From cli.py cmd_analyze() — deterministic code writes placeholder, Claude fills it
report_lines.extend([
    "## Topic Clusters",
    "",
    "<!-- HEURISTIC: To be completed by Claude reasoning over video_data_for_analysis.md -->",
])
```

**For Phase 3 — the cmd_topics() pattern:**
```python
# [DETERMINISTIC] in topics.py
def load_topic_inputs(root: Path) -> dict:
    """Load all input context for topic generation."""
    return {
        "analysis": (root / "context" / "competitors" / "analysis.md").read_text(encoding="utf-8"),
        "channel_dna": (root / "context" / "channel" / "channel.md").read_text(encoding="utf-8"),
        "past_topics": _load_past_topics(root / "context" / "channel" / "past_topics.md"),
    }

def _load_past_topics(path: Path) -> list[str]:
    """Read past_topics.md and return list of topic titles."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    # Extract title lines (format: "- **Title** | date | summary")
    titles = []
    for line in lines:
        line = line.strip()
        if line.startswith("- **") or line.startswith("**"):
            # Extract text between ** markers
            import re
            match = re.search(r'\*\*(.+?)\*\*', line)
            if match:
                titles.append(match.group(1))
    return titles

def check_duplicates(candidate_title: str, past_titles: list[str], threshold: float = 0.85) -> str | None:
    """Return matching past title if near-duplicate detected, else None."""
    import difflib
    for past in past_titles:
        ratio = difflib.SequenceMatcher(None, candidate_title.lower(), past.lower()).ratio()
        if ratio >= threshold:
            return past
    return None

def write_topic_briefs(briefs: list[dict], output_path: Path) -> None:
    """Write full topic briefs to file. Overwrites each run."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Topic Briefs",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]
    for i, brief in enumerate(briefs, 1):
        lines.extend(_format_brief(i, brief))
    output_path.write_text("\n".join(lines), encoding="utf-8")
```

### Pattern 2: Compact Chat Card Format

**What:** `cmd_topics()` prints scannable cards to stdout, one per topic, before writing the full file. User reads chat, picks a topic, then Phase 4 reads the file.

**Example card format:**
```
[1] The Matamoros Cult Murders — Mexico's cartel-linked occult killings that inspired a wave of Satanic panic
    O:5 C:4 S:5 V:4 = 18/20 | ~35 min | Cults & Psychological Control
    [UNDERSERVED CLUSTER: True Crime & Cults]

[2] The Disappearance of Flight 980's Black Box — ...
    O:4 C:3 S:4 V:5 = 16/20 | ~28 min | Unsolved Disappearances
    [WARNING: Similar to "The Mysterious Black Box Of Flight 980"]
```

### Pattern 3: Input Context Injection

**What:** The `topics` command loads all three input sources into memory and passes them as context when Claude performs the [HEURISTIC] generation. This is not an automated pipeline — `cmd_topics()` prints the structured inputs to stdout for Claude to reason over, then Claude writes the results.

**When to use:** Whenever Claude needs context to perform reasoning over project files.

**Clarification on execution model:** The `topics` subcommand is invoked by Claude in the terminal. Claude reads the printed output (competitor analysis summary + past topics list), then generates and scores topics based on that data plus tavily-mcp web research. The Python code does not call an LLM — it prepares and displays context, then Claude (running the shell command) produces the output.

**Revised execution flow:**
```
cmd_topics() called
  → load_topic_inputs() — reads analysis.md, channel.md, past_topics.md
  → print structured summary to stdout (for Claude to read)
  → Claude (the agent running this command) performs [HEURISTIC]:
      - Searches tavily-mcp for 3-5 obscure topic candidates
      - Generates 10-15 topic briefs
      - Scores each on 4 dimensions using anchored rubric
      - Checks candidates against past_topics list
      - Ranks by total score
  → Claude calls write_topic_briefs() with completed brief dicts
  → cmd_topics() prints chat cards to stdout
  → Prints summary line
```

**Alternative simpler model:** `cmd_topics()` just loads files, prints context to stdout, and Claude generates topics interactively — then Claude calls a separate `write` subcommand or directly writes `topic_briefs.md`. This avoids the awkward "Python calls Claude" problem entirely.

**Recommendation:** Use the simpler model. `cmd_topics` is a context-loading and output-writing helper; Claude does the actual generation in the conversation. See Anti-Patterns section.

### Anti-Patterns to Avoid

- **LLM API wrappers inside Python:** Architecture.md Rule 1. `topics.py` must not import anthropic, openai, or any LLM SDK. All reasoning happens natively in Claude Code.
- **Blocking on web research in Python:** tavily-mcp calls are Claude's tool calls during the heuristic phase, not subprocess calls from Python.
- **Over-engineering the CLI:** The `topics` subcommand does not need to orchestrate the generation itself. It loads context, optionally prints a structured summary, and provides a `write` helper for saving output. Claude is the orchestrator.
- **Storing history:** File is overwritten each run. No append logic, no timestamps on filenames.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Web research for obscure topics | Custom crawl4ai scraper per-run | tavily-mcp tool calls by Claude | tavily indexes the web; crawl4ai requires known URLs — topic discovery needs search |
| Fuzzy string matching | Custom edit-distance implementation | `difflib.SequenceMatcher` (stdlib) | Already handles case-insensitive ratio comparison; zero dependency |
| Markdown file writing | Jinja2 or template engine | Plain f-strings in Python | File has simple structure; template engine is overkill |
| Scoring logic | Algorithmic scoring from metadata | Claude reasoning over anchored rubric | Obscurity, shock factor, and complexity require editorial judgment, not keyword counting |

**Key insight:** The scoring rubric cannot be automated. Any attempt to compute obscurity from view counts or shock factor from topic keywords will produce wrong results. The rubric anchors exist precisely to calibrate Claude's judgment to the niche — they are prompt engineering, not code.

---

## Common Pitfalls

### Pitfall 1: Rubric Drift Between Runs
**What goes wrong:** Without concrete anchors, Claude scores the same topic differently on different runs. A "5" in one session becomes a "3" in the next.
**Why it happens:** Scoring dimensions (obscurity, shock factor) are abstract. Without calibration examples, the LLM uses its own shifting reference frame.
**How to avoid:** Embed 2-3 concrete topic examples per score level per dimension in the generation prompt. Examples must be real dark-mysteries topics the channel would recognize (e.g., "Jack the Ripper = Obscurity 1; Heaven's Gate = Obscurity 2; Jonestown = Obscurity 3; the Matamoros cult = Obscurity 4; the Dena'ina cannibal case = Obscurity 5").
**Warning signs:** High variance in scores across runs for the same topic type.

### Pitfall 2: past_topics.md Empty at Launch
**What goes wrong:** `past_topics.md` currently has 0 lines (confirmed: file exists but is 1 line, empty). Deduplication code that expects a specific format will return no past topics, silently skipping the check.
**Why it happens:** Channel is new; no videos published yet. The file format is not yet established.
**How to avoid:** `_load_past_topics()` must gracefully return `[]` when file is empty or missing. Add test for empty file case. Define the `past_topics.md` format explicitly so when the user adds entries, the parser works correctly.
**Warning signs:** No duplicate warnings even when same topic is generated twice.

### Pitfall 3: "Topics Subcommand Calls Claude" Architecture Confusion
**What goes wrong:** Developer tries to make `cmd_topics()` call an LLM API to generate topics, violating Architecture Rule 1. Or: developer expects Python to "run" the heuristic phase autonomously.
**Why it happens:** The command feels like it should be self-contained. But Claude IS the runtime — the command is invoked by Claude Code, which then performs the heuristic work.
**How to avoid:** Keep `cmd_topics()` as a context-display + output-write helper. Claude runs the command, reads its output, does web research via tavily-mcp, generates topics in the conversation, and then writes them to file (either directly or via a `write_briefs` helper function the planner can call).
**Warning signs:** Any import of anthropic, openai, requests-to-LLM-endpoints, or subprocess calls to model APIs in topics.py.

### Pitfall 4: Topic Brief Schema Drift
**What goes wrong:** The file output for `topic_briefs.md` uses a different field structure than what Phase 4 expects to read.
**Why it happens:** Phase 3 defines the schema; Phase 4 depends on it. If the file format is informal/undocumented, Phase 4 will need reverse-engineering.
**How to avoid:** Define the exact markdown structure for one topic brief as a canonical example in `topics.py`. Phase 4 can then parse it deterministically.
**Warning signs:** Phase 4 planner can't identify fields in topic_briefs.md without reading the whole file.

### Pitfall 5: Windows Path Issues with `context/topics/`
**What goes wrong:** `Path.mkdir(parents=True, exist_ok=True)` works correctly, but hardcoded string paths with backslashes fail.
**Why it happens:** Windows 11 platform; Git Bash mixes path conventions.
**How to avoid:** Always use `pathlib.Path` for path construction (already the project convention). Never concatenate strings for paths.

---

## Code Examples

### Topic Brief Schema (canonical format for topic_briefs.md)

```markdown
## [1] The Matamoros Cult Murders

**Pillar:** Cults & Psychological Control
**Score:** O:5 C:4 S:5 V:4 = 18/20
**Estimated runtime:** ~35 min
**Hook:** A Mexican drug cartel's occult enforcer kidnapped and ritually murdered a US student, triggering a cross-border manhunt for a cult that believed human sacrifice granted supernatural protection.

**Timeline:**
- 1986: Adolfo de Jesús Constanzo begins blending Palo Mayombe with narco violence in Mexico City
- 1988: Constanzo moves to Matamoros, gains control of a cartel faction
- March 1989: University of Texas student Mark Kilroy disappears after crossing the border for spring break
- April 1989: Mexican police raid Rancho Santa Elena; discover 15 ritual murder victims including Kilroy
- May 1989: Constanzo killed by his own followers in a Mexico City standoff after a 47-hour siege
- 1990: Surviving cult members convicted; case inspires Satanic panic legislation in Texas

**Scoring Justification:**
- **Obscurity (5/5):** Zero mainstream English-language documentary treatment. Constanzo known only in true crime niche; the broader cult structure and cartel integration is unknown to general audience.
- **Complexity (4/5):** Multi-layered: religious syncretism, cartel politics, cross-border jurisdiction, multiple victims and perpetrators. Stops short of 5 because the core narrative is linear.
- **Shock Factor (5/5):** Ritual murders, human sacrifice confirmed by forensics, US college student victim. Highest shock ceiling in our content pillars.
- **Verifiability (4/5):** Court records, FBI case files, multiple journalist accounts (Dianne Dugger's reporting). One point deducted: key supernatural belief system relies on perpetrators' self-reporting.
```

### Deduplication Check

```python
# Source: project pattern — stdlib difflib
import difflib

def check_duplicates(candidate_title: str, past_titles: list[str], threshold: float = 0.85) -> str | None:
    """Return matching past title if near-duplicate detected, else None.

    Uses SequenceMatcher ratio. 0.85 threshold catches plurals, minor
    wording differences, and subtitle variations while allowing different
    angles on the same subject (threshold deliberately high per CONTEXT.md).
    """
    candidate_normalized = candidate_title.lower().strip()
    for past in past_titles:
        ratio = difflib.SequenceMatcher(
            None,
            candidate_normalized,
            past.lower().strip()
        ).ratio()
        if ratio >= threshold:
            return past
    return None
```

### Adding topics subparser to cli.py

```python
# In main() alongside existing subparsers
topics_parser = subparsers.add_parser(
    "topics", help="Generate scored topic briefs using competitor analysis + web research"
)
# No required args — runs against default file locations

# In the dispatch block
elif args.command == "topics":
    cmd_topics(args, root)
```

### Anchored Scoring Rubric (for generation prompt)

The rubric must be embedded in the [HEURISTIC] prompt that Claude uses during topic generation. Recommended anchor topics per dimension:

**Obscurity**
| Score | Meaning | Anchor Example |
|-------|---------|----------------|
| 1 | Covered by 50+ channels, mainstream awareness | Jack the Ripper, Zodiac Killer |
| 2 | Covered by 10-20 channels, true crime literate audience knows it | Heaven's Gate, Jonestown |
| 3 | Covered by 2-5 niche channels, requires active interest | Matamoros cult (pre-viral), the Delphi murders |
| 4 | Covered by 1 channel or none in English; known only to researchers | The Mesa Verde ritual site controversies |
| 5 | Zero English documentary treatment; requires original research | Obscure regional cults, non-English historical crimes with no translation |

**Complexity**
| Score | Meaning | Anchor Example |
|-------|---------|----------------|
| 1 | Single actor, single event, clear motive | Standard robbery-homicide case |
| 2 | One layer of context needed to understand | Single perpetrator cult with simple belief system |
| 3 | Multiple actors, institutional failure, or contested facts | Jonestown (requires understanding cold war context) |
| 4 | Multiple actors + institutional cover-up + contested narrative | COINTELPRO church bombing cases |
| 5 | Requires understanding of 3+ intersecting systems (legal, cultural, political, religious) | Iran-Contra with cult dimensions |

**Shock Factor**
| Score | Meaning | Anchor Example |
|-------|---------|----------------|
| 1 | Disturbing but common crime type | Embezzlement, standard fraud |
| 2 | Violent but without unusual elements | Gang-related homicide |
| 3 | Unusual method or target; produces genuine unease | Organ trafficking, ritual threats |
| 4 | Viscerally disturbing detail that reframes the story | Human sacrifice confirmed by forensics |
| 5 | Detail that produces involuntary physical reaction in a calm adult | Mass graves of children; sustained ritual torture |

**Verifiability**
| Score | Meaning | Anchor Example |
|-------|---------|----------------|
| 1 | Entirely speculative; no primary sources | Urban legend, unverified forum posts |
| 2 | Some news reports, no official records | Local news coverage only |
| 3 | Multiple credible journalist accounts or academic papers | Investigative journalism with named sources |
| 4 | Court records, official investigations, or FBI files | Documented criminal cases |
| 5 | Primary-source video/audio, confessions on record, government documents released | Waco recordings, Jonestown death tape |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Topic selection by gut feel / YouTube browsing | Structured competitor analysis feeding anchored rubric | Phase 2 completion | Scoring is now calibrated to competitor gap data |
| Single source for topic ideas | Three sources: competitor gaps + channel pillars + live web research | Phase 3 design | Reduces blind spots; tavily finds obscure cases no competitor has covered |

**No deprecated patterns** in this phase — it is a net-new addition.

---

## Open Questions

1. **Exact tavily-mcp query strategy**
   - What we know: tavily-mcp is available as a Claude tool call; it returns web search results
   - What's unclear: How many searches per run? What query formulations work best for obscure historical crimes? Does tavily return academic/archival sources or primarily news?
   - Recommendation: Plan for 3-5 targeted searches per run. One query per content pillar cluster marked "Underserved" in Phase 2 analysis. Example queries: "obscure cult murders [region] [decade] documentary", "unsolved disappearance [profession] [country] investigation". Claude's discretion per CONTEXT.md.

2. **past_topics.md format enforcement**
   - What we know: File currently has 1 line (empty). Format is described in CONTEXT.md as "title, date published, 1-line summary per entry"
   - What's unclear: Exact markdown syntax — is it a table, a list, or front matter?
   - Recommendation: Define a canonical line format in topics.py as a comment or docstring: `- **Title** | YYYY-MM-DD | one-line summary`. Parser extracts `**...**` content. The format is simple enough that the user can manually add entries without tooling.

3. **Tiebreaker for equal total scores**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - Recommendation: Tiebreak priority order: (1) shock_factor desc — highest emotional impact first; (2) obscurity desc — rarer topics preferred; (3) verifiability desc — more documented is more production-safe. Document this in the generation prompt.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | `pytest.ini` (root) — `pythonpath = .claude/skills/channel-assistant/scripts` |
| Quick run command | `pytest tests/test_channel_assistant/test_topics.py -x` |
| Full suite command | `pytest tests/test_channel_assistant/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANLZ-04 | Scoring rubric produces 1-5 scores across all 4 dimensions | unit | `pytest tests/test_channel_assistant/test_topics.py::TestScoringRubric -x` | ❌ Wave 0 |
| OUTP-01 | `write_topic_briefs()` writes valid markdown with all schema fields | unit | `pytest tests/test_channel_assistant/test_topics.py::TestWriteTopicBriefs -x` | ❌ Wave 0 |
| OUTP-02 | `check_duplicates()` returns match for near-identical titles, None for distinct | unit | `pytest tests/test_channel_assistant/test_topics.py::TestDeduplication -x` | ❌ Wave 0 |
| OUTP-02 | `_load_past_topics()` returns empty list for missing/empty file | unit | `pytest tests/test_channel_assistant/test_topics.py::TestLoadPastTopics -x` | ❌ Wave 0 |
| OUTP-01 | `context/topics/` directory created if absent | unit | `pytest tests/test_channel_assistant/test_topics.py::TestWriteTopicBriefs::test_creates_directory -x` | ❌ Wave 0 |

**Note:** Topic generation itself (the [HEURISTIC] portion — Claude generating and scoring topics) is not automatically testable. Tests cover the [DETERMINISTIC] wrapper functions only.

### Sampling Rate
- **Per task commit:** `pytest tests/test_channel_assistant/test_topics.py -x`
- **Per wave merge:** `pytest tests/test_channel_assistant/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_channel_assistant/test_topics.py` — covers ANLZ-04, OUTP-01, OUTP-02
- [ ] `.claude/skills/channel-assistant/scripts/channel_assistant/topics.py` — new module (not a test file, but must exist before tests can import it)

---

## Sources

### Primary (HIGH confidence)
- Project codebase — `cli.py`, `analyzer.py`, `models.py`, `conftest.py` read directly
- `context/competitors/analysis.md` — Phase 2 output confirming available input data
- `03-CONTEXT.md` — locked user decisions driving all architectural choices
- `REQUIREMENTS.md` — phase requirement IDs and descriptions
- `pytest.ini` — confirmed test framework and pythonpath configuration

### Secondary (MEDIUM confidence)
- Python docs — `difflib.SequenceMatcher` for fuzzy matching (standard library, well-documented)
- Architecture.md — HEURISTIC/DETERMINISTIC classification rules and zero-LLM-wrapper constraint

### Tertiary (LOW confidence)
- tavily-mcp behavior at generation time — confirmed available per CLAUDE.md skills list, but exact query behavior and result quality for obscure historical topics unverified without live test

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all additions are stdlib; no new dependencies needed
- Architecture: HIGH — follows established Phase 2 HEURISTIC/DETERMINISTIC split exactly
- Scoring rubric design: HIGH — locked by CONTEXT.md; anchor examples are Claude's discretion and have been drafted
- Deduplication: HIGH — stdlib difflib, simple implementation
- Tavily integration: MEDIUM — tool is available, query strategy is Claude's discretion

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (stable domain — no fast-moving dependencies)
