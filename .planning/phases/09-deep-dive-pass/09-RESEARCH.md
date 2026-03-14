# Phase 9: Deep-Dive Pass (Pass 2) - Research

**Researched:** 2026-03-14
**Domain:** Python CLI extension — reading an annotated JSON manifest, fetching targeted URLs, writing pass2_NNN.json files, updating source_manifest.json, budget guard logic
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**URL source selection:**
- Fetch deep_dive_urls ONLY from sources with verdict "recommended" — skip verdicts are ignored
- Deduplicate URLs across sources — if the same URL appears in multiple sources' deep_dive_urls, fetch once
- Apply same Tier 3 filtering to deep_dive_urls — skip social media domains even if extracted by evaluation
- If no deep_dive_urls exist in the manifest (or none after filtering), print "No deep-dive URLs found in manifest — skip Pass 2 or re-evaluate sources" and exit cleanly

**Output file format:**
- JSON format, same schema as Pass 1 (index, url, domain, tier, word_count, fetch_status, error, content)
- Separate `pass2_` prefix numbering: pass2_001.json, pass2_002.json, etc.
- Update existing source_manifest.json with Pass 2 entries under a `pass2_sources` key — single manifest file for Phase 10

**Post-fetch behavior:**
- No evaluation step after fetching — raw storage only
- Print summary table in same format as Pass 1 (#, Domain, Tier, Words, Status)
- After completion, SKILL.md instructs Claude to print "Both passes complete. Run cmd_write to generate Research.md." — clean handoff to Phase 10

**Budget & dedup guard:**
- Hard cap: total source files across both passes ≤ 15
- cmd_deepen counts existing src_*.json files in output dir; Pass 2 budget = 15 - Pass 1 count
- Skip URLs already fetched in Pass 1 (match against URLs in existing src_*.json files)
- When deep_dive_urls exceed remaining budget, process in source order (manifest order) — higher-ranked Pass 1 sources' URLs get priority
- URLs beyond budget are logged as skipped with reason

### Claude's Discretion

- Noise stripping approach for primary source content (reuse _strip_wiki_noise or extend for .gov/.archive pages)
- Exact error messages and logging format
- Whether to reuse _print_summary_table from cmd_survey or create a shared utility

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RSRCH-03 | Pass 2 reads the source manifest and fetches 5-10 targeted primary sources (archive.org, .gov, academic) | Manifest read pattern, URL collection logic, pass2_NNN.json schema, budget guard all documented below |
</phase_requirements>

---

## Summary

Phase 9 adds a single new CLI subcommand `deepen` to the existing researcher skill. The command is structurally identical to `cmd_survey` from Phase 8 — read a manifest, iterate URLs, call `fetch_with_retry`, write JSON files, print a summary table, update the manifest — but its input is the annotated `source_manifest.json` rather than a fresh topic string, and its output files carry the `pass2_` prefix.

All Phase 7-8 infrastructure is reused without modification: `fetcher.py`, `tiers.py`, `_get_tier_from_url`, `_strip_wiki_noise`, `_print_summary_table`, and `resolve_output_dir` all work as-is. The only new logic is: (1) reading `deep_dive_urls` from recommended sources in the manifest, (2) deduplicating and budget-guarding the URL list, (3) writing `pass2_NNN.json` files, and (4) appending a `pass2_sources` key to the manifest.

The command is pure [DETERMINISTIC] — no LLM calls, no evaluation. Claude's role is to confirm after the summary table is printed: "Both passes complete. Run cmd_write to generate Research.md."

**Primary recommendation:** Implement `cmd_deepen(topic: str) -> None` in `cli.py` following the `cmd_survey` pattern exactly. Reuse `_print_summary_table` as-is (same columns). Keep all budget and dedup logic inside `cmd_deepen` — no new modules needed.

---

## Standard Stack

### Core (no new dependencies — everything already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `json` | stdlib | Read source_manifest.json, write pass2_NNN.json | Already used throughout cli.py |
| Python stdlib `pathlib` | stdlib | File paths for pass2_NNN.json and manifest | Already used throughout cli.py |
| Python stdlib `urllib.parse` | stdlib | Domain extraction from deep_dive_urls | Already used in cli.py via `urlparse` |
| `fetcher.fetch_with_retry` | project | Fetch with tier-aware retry | Already validated in Phases 7-8 |
| `tiers.classify_domain` | project | Tier classification for deep_dive_urls | Already used in _get_tier_from_url |
| `url_builder.resolve_output_dir` | project | Find correct output dir (project or scratch) | Already used in cmd_survey |

**Installation:**
```bash
# No new installs required — all dependencies from Phases 7-8 cover Phase 9
```

---

## Architecture Patterns

### What Changes in Phase 9

Only `cli.py` and `SKILL.md` are modified. No new modules, no new files in `scripts/researcher/`.

```
.claude/skills/researcher/
├── scripts/researcher/
│   ├── tiers.py          # NO CHANGE
│   ├── url_builder.py    # NO CHANGE
│   ├── fetcher.py        # NO CHANGE
│   ├── cli.py            # MODIFY: add cmd_deepen, register 'deepen' subcommand
│   └── __main__.py       # NO CHANGE
└── prompts/
    └── survey_evaluation.md   # NO CHANGE

SKILL.md                       # MODIFY: add Pass 2 workflow step and handoff instruction
```

### Pattern 1: Reading deep_dive_urls from Annotated Manifest

**What:** Open `source_manifest.json`, iterate sources where `verdict == "recommended"`, collect all `deep_dive_urls` entries, deduplicate.
**When to use:** At the start of `cmd_deepen`, before any fetch calls.

```python
# In cmd_deepen — read manifest and collect URLs
import json
from pathlib import Path

def _collect_deep_dive_urls(manifest_path: Path) -> list[str]:
    """Read deep_dive_urls from recommended sources in annotated manifest.

    Returns deduplicated list preserving manifest source order.
    Social/Tier 3 URLs filtered out. Already-fetched URLs excluded by caller.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    urls: list[str] = []

    for source in manifest.get("sources", []):
        if source.get("verdict") != "recommended":
            continue
        for url in source.get("deep_dive_urls", []):
            if url in seen:
                continue
            seen.add(url)
            # Tier 3 filter
            from researcher.tiers import classify_domain
            if classify_domain(url) == 3:
                continue
            urls.append(url)

    return urls
```

### Pattern 2: Budget Guard — Counting Pass 1 Files

**What:** Count existing `src_*.json` files in output_dir to determine remaining Pass 2 budget.
**When to use:** Before building the fetch list for Pass 2.

```python
# Count Pass 1 sources to determine budget
pass1_count = len(list(output_dir.glob("src_*.json")))
pass2_budget = 15 - pass1_count  # hard cap: total ≤ 15

if pass2_budget <= 0:
    print("Budget exhausted — Pass 1 already reached 15 source files.")
    return
```

### Pattern 3: URL Dedup Against Pass 1 Fetched URLs

**What:** Read all existing `src_*.json` files to collect already-fetched URLs. Skip deep_dive_urls that match.
**When to use:** After collecting deep_dive_urls, before trimming to budget.

```python
# Collect already-fetched URLs from Pass 1
fetched_urls: set[str] = set()
for src_file in output_dir.glob("src_*.json"):
    try:
        data = json.loads(src_file.read_text(encoding="utf-8"))
        if url := data.get("url"):
            fetched_urls.add(url)
    except (json.JSONDecodeError, OSError):
        continue

# Filter out already-fetched URLs from deep_dive list
deep_dive_urls = [u for u in deep_dive_urls if u not in fetched_urls]
```

### Pattern 4: pass2_NNN.json File Writing

**What:** Write fetched content to `pass2_NNN.json` using the same schema as `src_NNN.json`. Index starts at 1, independent of Pass 1 numbering.
**When to use:** Inside the fetch loop in `cmd_deepen`.

```python
# Write pass2 source file — same schema as src_NNN.json
filename = f"pass2_{idx:03d}.json"
src_data = {
    "index": idx,
    "url": url,
    "domain": domain,
    "tier": _get_tier_from_url(url),
    "word_count": word_count,
    "fetch_status": status,
    "error": result["error"],
    "content": content,
}
(output_dir / filename).write_text(
    json.dumps(src_data, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

### Pattern 5: Updating source_manifest.json with pass2_sources

**What:** After all Pass 2 fetches, read the existing manifest, add a `pass2_sources` key, write back in-place.
**When to use:** At the end of `cmd_deepen`, after the summary table is printed.

```python
# Append pass2_sources to existing manifest (preserve all Pass 1 data)
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["pass2_sources"] = pass2_sources_list  # lightweight entries (no content)
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

**pass2_sources entry schema** (same lightweight format as Pass 1 `sources` entries, no content field):
```json
{
    "index": 1,
    "filename": "pass2_001.json",
    "url": "https://vault.fbi.gov/jonestown",
    "domain": "vault.fbi.gov",
    "tier": 1,
    "word_count": 3200,
    "fetch_status": "ok"
}
```

### Pattern 6: Clean Exit When No URLs Found

**What:** Check after URL collection — if list is empty after filtering, print message and return.
**When to use:** After `_collect_deep_dive_urls` and before budget guard.

```python
if not deep_dive_urls:
    print("No deep-dive URLs found in manifest — skip Pass 2 or re-evaluate sources")
    return
```

### Pattern 7: Logging Skipped URLs (Beyond Budget)

**What:** URLs beyond the budget should be logged, not silently dropped.
**When to use:** After truncating deep_dive_urls to budget.

```python
skipped_urls = deep_dive_urls[pass2_budget:]
deep_dive_urls = deep_dive_urls[:pass2_budget]

for url in skipped_urls:
    print(f"  [budget] Skipping {url} — budget exhausted ({15} total cap)")
```

### Full cmd_deepen Skeleton

```python
def cmd_deepen(topic: str) -> None:
    """Run a deep-dive pass for a topic (Pass 2).

    Steps:
      a. Resolve output directory.
      b. Read source_manifest.json — collect deep_dive_urls from recommended sources.
      c. Deduplicate URLs, filter Tier 3, skip already-fetched.
      d. Apply budget guard (15 - Pass 1 count).
      e. Exit cleanly if no URLs remain.
      f. Fetch each URL, write pass2_NNN.json.
      g. Print summary table.
      h. Update source_manifest.json with pass2_sources key.
      i. Print manifest path.

    Args:
        topic: Topic string (same as used for cmd_survey).
    """
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)
    manifest_path = output_dir / "source_manifest.json"

    if not manifest_path.exists():
        print(f"Error: source_manifest.json not found in {output_dir}", file=sys.stderr)
        print("Run 'survey' first to generate the manifest.", file=sys.stderr)
        sys.exit(1)

    # Collect and filter deep_dive_urls
    deep_dive_urls = _collect_deep_dive_urls(manifest_path)

    # Dedup against already-fetched Pass 1 URLs
    fetched_urls = _get_fetched_urls(output_dir)
    deep_dive_urls = [u for u in deep_dive_urls if u not in fetched_urls]

    # Budget guard
    pass1_count = len(list(output_dir.glob("src_*.json")))
    pass2_budget = 15 - pass1_count
    if pass2_budget <= 0:
        print("Budget exhausted — total source cap (15) already reached by Pass 1.")
        return

    # Clean exit if nothing to fetch
    if not deep_dive_urls:
        print("No deep-dive URLs found in manifest — skip Pass 2 or re-evaluate sources")
        return

    # Log budget-skipped URLs
    if len(deep_dive_urls) > pass2_budget:
        for url in deep_dive_urls[pass2_budget:]:
            print(f"  [budget] Skipping {url} — budget exhausted ({15} total cap)")
        deep_dive_urls = deep_dive_urls[:pass2_budget]

    # Fetch loop
    pass2_sources = []
    for idx, url in enumerate(deep_dive_urls, start=1):
        print(f"  [{idx}/{len(deep_dive_urls)}] Fetching {url} ...", end=" ", flush=True)
        result = fetch_with_retry(url)
        status = result["fetch_status"]
        content = _strip_wiki_noise(result["content"] or "")
        word_count = len(content.split()) if content else 0
        domain = urlparse(url).hostname or ""
        domain = domain.removeprefix("www.")

        if status == "ok":
            print(f"ok ({word_count} words)")
        elif status == "skipped_tier3":
            print("skipped (tier 3)")
        else:
            print(f"failed — {result['error']}")

        filename = f"pass2_{idx:03d}.json"
        src_data = {
            "index": idx, "url": url, "domain": domain,
            "tier": _get_tier_from_url(url), "word_count": word_count,
            "fetch_status": status, "error": result["error"], "content": content,
        }
        (output_dir / filename).write_text(
            json.dumps(src_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        pass2_sources.append({
            "index": idx, "filename": filename, "url": url, "domain": domain,
            "tier": src_data["tier"], "word_count": word_count, "fetch_status": status,
        })

    _print_summary_table(pass2_sources)

    # Update manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["pass2_sources"] = pass2_sources
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Manifest updated: {manifest_path}")
```

### Anti-Patterns to Avoid

- **Clearing pass1 src_*.json before Pass 2:** Pass 2 must NOT clean the output dir — that's cmd_survey's job. cmd_deepen only writes new `pass2_NNN.json` files.
- **Evaluating Pass 2 content in Python:** No LLM calls in cmd_deepen. Phase 10 handles synthesis. cmd_deepen is fetch-and-store only.
- **Re-fetching Pass 1 URLs:** Always check fetched URLs from existing src_*.json files — same URL in deep_dive_urls that was already fetched in Pass 1 must be skipped.
- **Calling LLM API from cmd_deepen:** Same constraint as cmd_survey — all [HEURISTIC] work is Claude reading files after the command runs.
- **Importing crawl4ai at module level:** Keep deferred import pattern (already established in fetcher.py and cli.py) so unit tests can run without crawl4ai installed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fetch with retry | Custom HTTP loop | `fetch_with_retry` from fetcher.py | Handles tier logic, content validation, min-length check |
| Tier classification | Inline domain check | `_get_tier_from_url` / `classify_domain` | Single source of truth, already tested |
| Noise stripping | New stripping function | `_strip_wiki_noise` | Already handles 50% guard; works on all markdown, not just Wikipedia |
| Summary table | New formatter | `_print_summary_table` | Same columns, reusable as-is |
| Output dir resolution | Path construction | `resolve_output_dir` | Handles project mode vs standalone mode transparently |

**Key insight:** Phase 9 is almost entirely composition of existing Phase 7-8 building blocks. The only genuinely new logic is the URL collection from the manifest and the budget guard.

---

## Common Pitfalls

### Pitfall 1: Cleaning Output Dir at Start of cmd_deepen

**What goes wrong:** If `cmd_deepen` follows `cmd_survey`'s pattern of deleting `src_*.json` before running, it destroys the Pass 1 files that Phase 10 needs.
**Why it happens:** Copy-paste from `cmd_survey` skeleton which does clean the dir.
**How to avoid:** `cmd_deepen` must NOT glob-delete any files. It only creates new `pass2_NNN.json` files.
**Warning signs:** After `cmd_deepen`, output dir contains only `pass2_*.json` and no `src_*.json`.

### Pitfall 2: Budget Count Uses Wrong Glob

**What goes wrong:** Budget guard counts `pass2_*.json` instead of `src_*.json` (or vice versa), producing wrong remaining budget.
**Why it happens:** Confusion about which files represent Pass 1 vs Pass 2.
**How to avoid:** Pass 1 count = `len(list(output_dir.glob("src_*.json")))`. Pass 2 files use `pass2_` prefix. These are distinct and non-overlapping.

### Pitfall 3: No manifest_path.exists() Check

**What goes wrong:** `cmd_deepen` crashes with `FileNotFoundError` when called before `cmd_survey`.
**Why it happens:** No guard against missing manifest.
**How to avoid:** Check `manifest_path.exists()` at the top of `cmd_deepen`. Print a clear error and `sys.exit(1)` if missing.

### Pitfall 4: Verdict Field May Be Missing (Unannotated Manifest)

**What goes wrong:** If the user calls `cmd_deepen` without running the [HEURISTIC] evaluation step first, `verdict` fields will be absent from all source entries. Every source passes the `verdict == "recommended"` filter vacuously (or fails it, depending on None check).
**Why it happens:** The evaluation step is [HEURISTIC] (Claude manual step), not enforced by code.
**How to avoid:** In `_collect_deep_dive_urls`, treat a missing `verdict` key the same as `"skip"` — only collect from sources with explicit `"recommended"`. If the resulting URL list is empty, the clean-exit message "No deep-dive URLs found" naturally tells the user to evaluate first.

### Pitfall 5: pass2_sources Key Conflicts with Existing Re-run

**What goes wrong:** If `cmd_deepen` is run twice, the second run overwrites `pass2_sources` in the manifest — but the old `pass2_NNN.json` files from the first run remain on disk. The manifest and disk state diverge.
**Why it happens:** No cleanup of old pass2 files before re-run.
**How to avoid:** At the start of `cmd_deepen`, delete existing `pass2_*.json` files (parallel to how cmd_survey deletes `src_*.json`). This is safe because pass2 files are always regeneratable from the manifest.

### Pitfall 6: _strip_wiki_noise Called on .gov or archive.org Pages

**What goes wrong:** Some `.gov` or `archive.org` pages use "References" as a real content heading rather than a bibliography marker. Strip guard fires correctly (50% check), but edge cases may strip valuable content.
**Why it happens:** `_strip_wiki_noise` is heading-name-based, not domain-aware.
**How to avoid:** The 50% pitfall guard already handles this — if stripping removes more than half the content, original markdown is returned unchanged. No additional logic needed.

---

## Code Examples

### Verified Pattern: _collect_deep_dive_urls

```python
# Source: project convention — follows cmd_survey patterns
def _collect_deep_dive_urls(manifest_path: Path) -> list[str]:
    """Collect deep_dive_urls from recommended sources in annotated manifest.

    Returns deduplicated list in manifest source order.
    Filters Tier 3 domains.
    """
    from researcher.tiers import classify_domain  # noqa: PLC0415
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    urls: list[str] = []
    for source in manifest.get("sources", []):
        if source.get("verdict") != "recommended":
            continue
        for url in source.get("deep_dive_urls", []):
            if url in seen:
                continue
            seen.add(url)
            if classify_domain(url) == 3:
                continue
            urls.append(url)
    return urls
```

### Verified Pattern: _get_fetched_urls (dedup against Pass 1)

```python
# Source: project convention
def _get_fetched_urls(output_dir: Path) -> set[str]:
    """Return set of URLs already fetched in Pass 1 (from src_*.json files)."""
    fetched: set[str] = set()
    for src_file in output_dir.glob("src_*.json"):
        try:
            data = json.loads(src_file.read_text(encoding="utf-8"))
            if url := data.get("url"):
                fetched.add(url)
        except (json.JSONDecodeError, OSError):
            continue
    return fetched
```

### Verified Pattern: Clean Old pass2_*.json Files on Re-run

```python
# At start of cmd_deepen, before any reads (parallel to cmd_survey's cleanup)
for old_file in output_dir.glob("pass2_*.json"):
    old_file.unlink()
```

### Verified Pattern: Register deepen Subcommand in main()

```python
# In main() in cli.py — add after survey subcommand registration
deepen_parser = subparsers.add_parser(
    "deepen",
    help="Pass 2: fetch targeted primary sources from evaluated manifest",
)
deepen_parser.add_argument(
    "topic",
    help="Topic string (same as used for survey)",
)

# In dispatch block:
elif args.command == "deepen":
    try:
        cmd_deepen(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

### Verified Pattern: SKILL.md Pass 2 Workflow Section

```markdown
## Workflow (Pass 2 — Deep Dive)

### Step 1 — Confirm evaluation is complete

Ensure source_manifest.json has verdict/deep_dive_urls fields on all sources.
If not, run the survey_evaluation prompt first (see Pass 1 workflow Step 2).

### Step 2 — Run deepen command

PYTHONPATH=.claude/skills/researcher/scripts python -m researcher deepen "Your Topic Here"

The command reads deep_dive_urls from recommended sources, applies Tier 3 filter and
dedup, applies budget guard (15 total cap), fetches each URL, writes pass2_NNN.json,
prints summary table, and updates source_manifest.json with pass2_sources key.

### Step 3 — Handoff to Phase 10

After cmd_deepen completes, say:
"Both passes complete. Run cmd_write to generate Research.md."
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-pass scraping (broad only) | Two-pass: broad survey + targeted deep dives | Phase 9 | Primary sources fetched explicitly, not incidentally |
| source_manifest.json has only `sources` key | source_manifest.json gains `pass2_sources` key | Phase 9 | Single manifest file covers full research corpus for Phase 10 |
| src_NNN.json files only | src_NNN.json + pass2_NNN.json in same output dir | Phase 9 | Both pass types distinguishable by filename prefix |

**Deprecated/outdated after Phase 9:**
- None — Phase 9 is additive only.

---

## Open Questions

1. **_strip_wiki_noise reuse on non-Wikipedia primary sources**
   - What we know: The function strips by heading name; the 50% guard prevents over-stripping. It's been applied to all Pass 1 sources successfully.
   - What's unclear: Whether .gov and archive.org pages produce markdown with heading structures that trigger false positives. This is Claude's discretion per CONTEXT.md.
   - Recommendation: Reuse `_strip_wiki_noise` unchanged. The 50% guard is the right safety valve. If archive.org content is getting stripped incorrectly during implementation testing, add a domain allowlist to skip stripping for known primary source domains.

2. **Whether to extract _collect_deep_dive_urls as module-level helper or keep inline in cmd_deepen**
   - What we know: cmd_survey keeps all its helpers inline or as module-level functions in cli.py. CONTEXT.md says this is Claude's discretion.
   - Recommendation: Extract as module-level private function (prefixed `_`) in cli.py for testability. Tests will need to mock manifest content.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` or `pyproject.toml` (check project root) |
| Quick run command | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"` |
| Full suite command | `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RSRCH-03 | cmd_deepen reads deep_dive_urls from "recommended" sources only | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | cmd_deepen writes pass2_NNN.json with correct schema | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | cmd_deepen updates source_manifest.json with pass2_sources key | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Budget guard: total files across both passes ≤ 15 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Dedup: URL in src_*.json not re-fetched in pass2 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Dedup: same URL in multiple deep_dive_urls fetched once | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Clean exit when no deep_dive_urls in manifest | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Tier 3 URLs in deep_dive_urls are skipped | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Old pass2_*.json files cleaned on re-run | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | "skip" verdict sources excluded from deep_dive_url collection | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |
| RSRCH-03 | Summary table printed in same format as Pass 1 | unit | `pytest tests/test_researcher/test_cli.py -k deepen -x --tb=short` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short -m "not integration"`
- **Per wave merge:** `PYTHONPATH=.claude/skills/researcher/scripts pytest tests/test_researcher/ -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_researcher/test_cli.py` — add all `test_cmd_deepen_*` tests (new test functions in existing file)
- [ ] No new test files needed — all deepen tests fit in test_cli.py

**Existing test infrastructure:**
- `tests/test_researcher/test_cli.py` exists and has the `_install_crawl4ai_mock()` pattern — new `cmd_deepen` tests follow the same mocking approach
- `tests/test_researcher/test_fetcher.py`, `test_tiers.py`, `test_url_builder.py` — no changes needed
- Integration test file exists but no changes needed for Phase 9

---

## Sources

### Primary (HIGH confidence)

- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\.claude\skills\researcher\scripts\researcher\cli.py` — actual `cmd_survey` implementation read directly; all patterns are adaptations of verified code
- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\.claude\skills\researcher\scripts\researcher\tiers.py` — tier constants and `classify_domain` read directly
- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\.claude\skills\researcher\scripts\researcher\url_builder.py` — `resolve_output_dir` read directly
- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\.planning\phases\09-deep-dive-pass\09-CONTEXT.md` — all locked decisions read directly
- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\.planning\REQUIREMENTS.md` — RSRCH-03 definition read directly
- `D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3\tests\test_researcher\test_cli.py` — existing test patterns read directly for Wave 0 test structure

### Secondary (MEDIUM confidence)

- Phase 8 RESEARCH.md — manifest schema, `_print_summary_table` columns, `_strip_wiki_noise` 50% guard behavior all cross-referenced

### Tertiary (LOW confidence)

- None — all findings verified against actual source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are existing project dependencies, verified by reading actual source files
- Architecture: HIGH — cmd_deepen is a composition of verified Phase 7-8 patterns; no novel patterns introduced
- Pitfalls: HIGH — sourced from reading actual implementation code and understanding what cmd_survey does that cmd_deepen must NOT do
- Test map: HIGH — existing test_cli.py patterns read directly; new tests are analogous to existing Phase 8 tests

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (no external dependencies; all libraries are pinned Phase 7-8 versions)
