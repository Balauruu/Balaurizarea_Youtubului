# Phase 6: Tech Debt Cleanup + OUTP-02 Wiring - Research

**Researched:** 2026-03-11
**Domain:** Python module wiring, pytest test assertions, documentation accuracy
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OUTP-02 | Generated topics are checked against `context/channel/past_topics.md` and duplicates/near-duplicates are rejected | `check_duplicates()` already exists in `topics.py` and has 7 passing tests — only needs to be called from `cmd_topics()` in `cli.py` with the loaded `past_topics` list |
</phase_requirements>

---

## Summary

Phase 6 is a focused cleanup phase with exactly three deliverables, all of which are small, contained changes to already-written code. No new modules need to be created. No new dependencies are required. The work is: (1) wire one existing function call into one existing function, (2) update one test assertion to reflect the current behavior of the production code, and (3) update one line of documentation.

The audit identified that `check_duplicates()` in `topics.py` is exported and tested (7 tests, all green) but is never imported or called by `cli.py`. The function signature is `check_duplicates(candidate_title: str, past_titles: list[str], threshold: float = 0.85) -> str | None`. The `cmd_topics()` function in `cli.py` already loads `past_topics` via `load_topic_inputs()` and already prints it to stdout. The wiring change is a single `from .topics import check_duplicates` addition to the import block and a loop that calls the function inside `cmd_topics()` before printing.

The scraper test regression (`test_raises_scrape_error_after_retries_exhausted`) is caused by scraper.py having an uncommitted `--flat-playlist` fallback path that calls `_run_ytdlp()` a second time when the first call raises `ScrapeError`. With all 6 mock calls returning `returncode=1`, the full path is: `_run_ytdlp(cmd_full)` exhausts 3 attempts, raises `ScrapeError` internally (caught by `scrape_channel`), then `_run_ytdlp(cmd_flat)` exhausts 3 more attempts, raises `ScrapeError` that propagates out. Total: 6 calls. The test expects 3. The fix is to update the test assertion from `== 3` to `== 6`, not to revert the production code (the fallback path is correct and desirable behavior).

**Primary recommendation:** Wire `check_duplicates()` into `cmd_topics()` as a post-heuristic filter note printed to stdout; update the test assertion to `== 6`; update SKILL.md entry point docs. All three changes fit in one plan, one wave.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `difflib.SequenceMatcher` | stdlib | Near-duplicate title comparison | Already used in `check_duplicates()` — zero new deps |
| `pytest` | 9.0.2 | Test runner | Already configured via `pytest.ini` |

### No new dependencies required

All tools needed for this phase are already installed and in use.

---

## Architecture Patterns

### Pattern 1: Context-Loader with Programmatic Safety Net

**What:** `cmd_topics()` is a [DETERMINISTIC] context loader. It loads data, formats it, and prints to stdout. Claude then does [HEURISTIC] topic generation. OUTP-02 requires a programmatic dedup check as a **safety net** — not a replacement for Claude's heuristic judgment, but a hard-coded backstop that catches exact/near-exact matches.

**Correct wiring location:** Inside `cmd_topics()`, after Claude is instructed to generate topics, add a printed instruction block that:
1. Imports `check_duplicates` from `.topics`
2. Is called in a loop over the printed past_topics list
3. Prints warnings for any candidate titles that hit the threshold

**Practical approach per the audit evidence:** The programmatic check cannot intercept Claude's output mid-stream. The correct pattern is to call `check_duplicates()` when `write_topic_briefs()` is called — that function receives the final `briefs: list[dict]` including the `duplicate_of` field. The `duplicate_of` field is already rendered in the output file if non-None. What is missing is that `check_duplicates()` is never called to *populate* `duplicate_of`.

Since topic generation is heuristic (Claude generates the briefs), `check_duplicates()` should be called at the one point where deterministic code touches the final briefs. Looking at the flow:

```
cmd_topics() prints context → Claude generates briefs → Claude calls write_topic_briefs(briefs, path)
```

Claude already calls `write_topic_briefs()`. The instruction text printed by `cmd_topics()` must tell Claude to call `check_duplicates()` on each brief title against `past_topics` and populate `duplicate_of` before calling `write_topic_briefs()`. This is the correct wiring: Claude receives the instruction, calls the function, and the brief carries the result deterministically.

**What to add to `cmd_topics()` output:**
```python
# After printing the past topics list, add:
print(
    "DEDUP CHECK (required): Before calling write_topic_briefs(), "
    "call check_duplicates(title, past_topics, threshold=0.85) for each brief "
    "and populate brief['duplicate_of'] with the return value. "
    "Import: from channel_assistant.topics import check_duplicates, load_topic_inputs"
)
```

And update the existing "Context loaded." instruction line to explicitly reference this step.

### Pattern 2: Test Assertion Update (not revert)

**What:** The scraper.py `--flat-playlist` fallback was added as an uncommitted working-tree change. The audit explicitly says "Runtime behavior is correct (more resilient)." The scraper.py file is already modified (`M` in git status). The fix is to commit scraper.py as-is and update the test assertion.

**Exact change in test:**
```python
# Line 189 of test_scraper.py — BEFORE:
assert mock_run.call_count == 3  # 1 initial + 2 retries

# AFTER:
assert mock_run.call_count == 6  # 3 full-scrape attempts + 3 flat-playlist fallback attempts
```

**Why 6:** `_run_ytdlp()` has `max_attempts = 3`. When all 3 fail, it raises `ScrapeError`. `scrape_channel()` catches that and calls `_run_ytdlp()` again with the flat-playlist command, which also exhausts all 3 attempts. `mock_run.return_value` always returns `returncode=1`, so both paths exhaust fully: 3 + 3 = 6.

The `test_retry_on_failure` test (which uses `side_effect` not `return_value`) is unaffected — it already passes because it only enters the first `_run_ytdlp()` call and succeeds on attempt 3.

### Pattern 3: SKILL.md Entry Point Fix

**What:** SKILL.md currently documents the entry point as:
```bash
python .claude/skills/channel-assistant/scripts/channel_assistant/cli.py <subcommand>
```

The audit states the correct entry point is:
```bash
python -m channel_assistant.cli <subcommand>
```

This matters because `python -m` respects the package `__init__.py` and relative imports. Direct script invocation with `python path/to/cli.py` can fail with relative import errors unless the working directory is configured correctly.

**Scope of change:** Update the `## Entry Point` section and all example command blocks in SKILL.md to use `python -m channel_assistant.cli`. Also update the subcommand examples in the `## Subcommands` section (lines 22, 29, 48, 53).

**The `analyze`, `topics`, `trends` subcommands** added in Phases 2-5 are not documented in SKILL.md at all. Phase 6 should add them.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Near-duplicate title detection | Custom similarity algorithm | `check_duplicates()` in topics.py | Already built, already tested (7 tests) |
| Test count verification | Complex mock inspection | Update `assert mock_run.call_count == 3` to `== 6` | The behavior is already correct in production |

**Key insight:** All three deliverables are edits to existing files. Zero new code architecture is required.

---

## Common Pitfalls

### Pitfall 1: Wiring `check_duplicates()` in the wrong place

**What goes wrong:** Adding the import and call inside `cmd_topics()` at the context-loading stage, before Claude generates anything, means the function has no candidate titles to check against.

**Why it happens:** The function signature suggests it should be called during generation. But generation is heuristic — Claude does it.

**How to avoid:** The wiring point is in the *instruction text printed by `cmd_topics()`*. Claude must be explicitly told to call `check_duplicates()` on each generated brief title and populate `duplicate_of`. The function is then called by Claude as part of its deterministic step before `write_topic_briefs()`.

**Warning signs:** If `duplicate_of` is always `None` in topic_briefs.md, the wiring is missing.

### Pitfall 2: Reverting scraper.py to fix the test

**What goes wrong:** `git checkout` or manual removal of the `--flat-playlist` fallback to make the test pass.

**Why it happens:** The easiest path to `call_count == 3` is to remove the second `_run_ytdlp()` call.

**How to avoid:** The audit explicitly says the runtime behavior is correct. Fix the test, not the code. Update the assertion comment to explain why it's 6.

### Pitfall 3: Only fixing SKILL.md entry point, not the subcommand examples

**What goes wrong:** Updating the `## Entry Point` section but leaving the old `python ...cli.py scrape` examples throughout `## Subcommands`.

**How to avoid:** Update all 4+ example commands in the subcommand sections, not just the entry point block.

### Pitfall 4: Missing `analyze`, `topics`, `trends` subcommands in SKILL.md

**What goes wrong:** SKILL.md currently documents only: `add`, `scrape`, `status`. Three phases of subcommands were added afterward. Readers of SKILL.md cannot discover `analyze`, `topics`, or `trends`.

**How to avoid:** Add sections for `analyze`, `topics`, and `trends` to SKILL.md matching the existing documentation pattern.

---

## Code Examples

### OUTP-02 wiring — instruction text addition in `cmd_topics()`

```python
# Source: cli.py cmd_topics() — append to existing instruction line
print(
    "Context loaded. Use the generation prompt to generate 10-15 topic briefs. "
    "REQUIRED dedup step: call check_duplicates(title, past_topics, threshold=0.85) "
    "for each brief title and set brief['duplicate_of'] = result before calling "
    "write_topic_briefs(). Import: from channel_assistant.topics import check_duplicates"
)
```

Also add `check_duplicates` to the import in `cli.py`:
```python
from .topics import load_topic_inputs, check_duplicates
```

### Test fix — exact line change

```python
# tests/test_channel_assistant/test_scraper.py line 189
# BEFORE:
assert mock_run.call_count == 3  # 1 initial + 2 retries

# AFTER:
assert mock_run.call_count == 6  # 3 attempts (full) + 3 attempts (flat-playlist fallback)
```

### SKILL.md entry point — corrected form

```bash
# All subcommand examples change from:
python .claude/skills/channel-assistant/scripts/channel_assistant/cli.py <subcommand>

# To:
python -m channel_assistant.cli <subcommand>
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (project root) |
| Quick run command | `python -m pytest tests/test_channel_assistant/test_scraper.py -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OUTP-02 | `check_duplicates()` called in topics generation path | integration | `python -m pytest tests/test_channel_assistant/test_topics.py -v` | Yes |
| OUTP-02 (regression) | `test_raises_scrape_error_after_retries_exhausted` passes | unit | `python -m pytest tests/test_channel_assistant/test_scraper.py::TestScrapeChannel::test_raises_scrape_error_after_retries_exhausted -v` | Yes |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_channel_assistant/test_scraper.py tests/test_channel_assistant/test_topics.py -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green (175/175) before `/gsd:verify-work`

### Wave 0 Gaps

None — existing test infrastructure covers all phase requirements. The scraper test already exists; it needs its assertion updated, not a new test written.

---

## Open Questions

1. **Should `check_duplicates()` wiring add a new test to `test_topics.py`?**
   - What we know: `check_duplicates()` has 7 unit tests. The *integration* of it being called during topic generation is currently untested.
   - What's unclear: Whether a new integration test for `cmd_topics()` instruction text is worth the effort given this is a documentation/wiring change.
   - Recommendation: No new test required for the wiring — the instruction text is not code that can be unit tested. The `duplicate_of` field in briefs is already tested in `test_topics.py` via `write_topic_briefs()` tests.

2. **Should SKILL.md add full `analyze`, `topics`, `trends` documentation?**
   - What we know: These subcommands are undocumented in SKILL.md.
   - What's unclear: How detailed the new sections need to be.
   - Recommendation: Add a brief section per subcommand matching the existing pattern (purpose, command, output format). This is the appropriate scope for a gap-closure phase.

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `.claude/skills/channel-assistant/scripts/channel_assistant/scraper.py` — full `--flat-playlist` fallback path visible
- Direct code inspection: `.claude/skills/channel-assistant/scripts/channel_assistant/topics.py` — `check_duplicates()` signature and logic verified
- Direct code inspection: `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` — `cmd_topics()` import block verified (missing `check_duplicates`)
- Direct test run: `test_raises_scrape_error_after_retries_exhausted` — confirmed `call_count == 6` vs expected `3`
- Audit file: `.planning/v1.0-MILESTONE-AUDIT.md` — all three gaps documented with evidence

### Secondary (MEDIUM confidence)

- `pytest.ini` presence confirmed — `python -m pytest` is the correct runner invocation
- `python -m channel_assistant.cli` correctness inferred from package structure (`__init__.py` present in `channel_assistant/`) — relative imports require module execution mode

---

## Metadata

**Confidence breakdown:**
- OUTP-02 wiring location: HIGH — code trace is definitive, correct insertion point identified
- Scraper test fix: HIGH — live test run confirms `call_count == 6`, code explains exactly why
- SKILL.md corrections: HIGH — audit evidence is explicit, correct form is verifiable

**Research date:** 2026-03-11
**Valid until:** Stable (no external dependencies — pure internal code changes)
