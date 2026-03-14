# Researcher Skill

**Purpose:** Agent 1.2 — The Researcher. Executes web scraping to build factual foundations for documentary videos.

**Status:** All modules implemented. v1.1 complete.

---

## Invocation

```bash
# Run a subcommand
PYTHONPATH=.claude/skills/researcher/scripts python -m researcher <subcommand>

# Subcommands:
#   survey  — Pass 1: bulk topic scraping
#   deepen  — Pass 2: targeted deep dives
#   write   — Aggregate sources into synthesis_input.md
```

---

## Setup (first run only)

```bash
pip install crawl4ai==0.8.0
python -m playwright install chromium   # installs ~300MB Playwright browser binaries — run once
pip install ddgs   # DuckDuckGo search library (duckduckgo-search renamed to ddgs)
```

Environment variable for non-Latin source content:
```bash
export PYTHONUTF8=1
```

---

## Modules

### Phase 7 (implemented)

| Module | Purpose | Exports |
|--------|---------|---------|
| `tiers.py` | Source tier constants and domain classification | `TIER_1_DOMAINS`, `TIER_2_DOMAINS`, `TIER_3_DOMAINS`, `TIER_RETRY_MAP`, `classify_domain` |
| `fetcher.py` | crawl4ai wrapper with domain isolation, retry, content validation | `fetch_url`, `fetch_with_retry` |

### Phase 7 Plan 2 (implemented)

| Module | Purpose | Exports |
|--------|---------|---------|
| `url_builder.py` | Project directory resolution and URL construction | `find_project_dir`, `resolve_output_dir`, `make_ddg_url`, `build_survey_urls` |
| `cli.py` | CLI entry point with `survey` subcommand | `main`, `cmd_survey` |

### Phase 9 (implemented)

| Module | Purpose | Status |
|--------|---------|--------|
| `deepen` command | Pass 2: targeted deep dives on recommended sources | Implemented |

### Phase 10 (implemented)

| Module | Purpose | Exports |
|--------|---------|---------|
| `writer.py` | Source file aggregation into synthesis_input.md | `load_source_files`, `build_synthesis_input`, `write_synthesis_input` |

---

## Tier System

| Tier | Behavior | Retries | Examples |
|------|----------|---------|---------|
| 1 | Authoritative — fetch with full retry | 3 | archive.org, loc.gov, en.wikipedia.org |
| 2 | General / unknown — attempt once | 1 | bbc.com, reuters.com, reddit.com, old.reddit.com, unknown domains |
| 3 | Social / do-not-fetch — skip entirely | 0 | facebook.com, x.com, instagram.com, tiktok.com, pinterest.com |

Unknown domains default to Tier 2.

---

## Workflow (Pass 1 — Survey)

### Step 1 — Run survey command

PYTHONPATH=.claude/skills/researcher/scripts python -m researcher survey "Your Topic Here"

The command fetches Wikipedia and up to 12 DDG result pages. Each page is saved as
src_NNN.json in the output directory. A source_manifest.json index is written.
A summary table (#, Domain, Tier, Words, Status) is printed to stdout.

### Step 2 — Auto-evaluate sources [HEURISTIC]

After cmd_survey prints its summary table, Claude reads the survey_evaluation.md prompt:

@.claude/skills/researcher/prompts/survey_evaluation.md

Claude then reads every src_NNN.json file listed in source_manifest.json and evaluates
each source per the rubric. The manifest is annotated in-place with:
- evaluation_notes (what was found, why useful or not)
- deep_dive_urls (primary source URLs extracted from source content)
- verdict ("recommended" or "skip")

Claude then prints a verdict summary table and asks: "Proceed to Pass 2 (cmd_deepen)?"

### Step 3 — Confirm

Review the verdict summary. Confirm to proceed to Phase 9 (cmd_deepen), or adjust
deep_dive_urls manually before continuing.

---

## Workflow (Pass 2 — Deep Dive)

### Step 1 — Confirm evaluation is complete

Verify that source_manifest.json has `verdict` and `deep_dive_urls` populated on all
sources. If any source is missing these fields, re-run the evaluation step (Step 2 of
Pass 1 Workflow) before proceeding.

### Step 2 — Run deepen command

```bash
PYTHONPATH=.claude/skills/researcher/scripts python -m researcher deepen "Your Topic Here"
```

The command reads source_manifest.json, collects deep_dive_urls from "recommended"
sources only, filters Tier 3 URLs and already-fetched URLs, then fetches up to
(15 - pass1_count) URLs. Each is saved as pass2_NNN.json in the output directory.
A summary table is printed and source_manifest.json is updated with a pass2_sources key.

### Step 3 — Handoff

After cmd_deepen completes, both passes are done. Proceed to Pass 3 (Write Dossier) below.

---

## Workflow (Pass 3 — Write Dossier)

### Step 1 — Run write command

```bash
PYTHONPATH=.claude/skills/researcher/scripts python -m researcher write "Your Topic Here"
```

The command reads all src_*.json and pass2_*.json files, aggregates them into synthesis_input.md
(full content, no truncation), and prints the file path and synthesis prompt path.

### Step 2 — Claude synthesizes dossier [HEURISTIC]

After cmd_write prints its summary, Claude reads:
- The synthesis_input.md file (path printed by cmd_write as "Synthesis input: ...")
- The synthesis prompt: @.claude/skills/researcher/prompts/synthesis.md

Claude produces two files:
- **Research.md** (~2,000 words, narrative-first dossier with all 9 sections)
- **media_urls.md** (visual media catalog grouped by asset type)

Both files are written to the output directory shown in the synthesis_input.md header.
Claude writes these files directly using its file tools — no code step involved.

### Step 3 — Review

Read Research.md. Verify all 9 sections are present and content is factual.
Word count should be approximately 2,000 words of body text.
Check media_urls.md for valid URLs grouped correctly by asset type.

---

## Output Schema (Phase 8+)

**Per-source file:** `src_001.json`, `src_002.json`, ...
```json
{
    "index": 1,
    "url": "https://en.wikipedia.org/wiki/Jonestown",
    "domain": "en.wikipedia.org",
    "tier": 1,
    "word_count": 4523,
    "fetch_status": "ok",
    "error": "",
    "content": "..."
}
```

**Source manifest (lightweight index, annotated after evaluation):** `source_manifest.json`
```json
{
    "topic": "Jonestown Massacre",
    "run_timestamp": "2026-03-12T10:00:00Z",
    "sources": [
        {
            "index": 1,
            "filename": "src_001.json",
            "url": "https://en.wikipedia.org/wiki/Jonestown",
            "domain": "en.wikipedia.org",
            "tier": 1,
            "word_count": 4523,
            "fetch_status": "ok",
            "evaluation_notes": "Strong overview — FBI vault and archive.org docs referenced.",
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
            "verdict": "recommended"
        }
    ]
}
```

Note: `evaluation_notes`, `deep_dive_urls`, and `verdict` are added by the [HEURISTIC] evaluation
step (Step 2 of the Workflow). They are not written by cmd_survey itself.

**Synthesis input file:** `synthesis_input.md` (written to `.claude/scratch/researcher/` by cmd_write)

Header fields:
```
**Topic:** [topic name]
**Output directory:** [path to projects/N. Title/research/]
**Sources included:** [N]
**Skipped / failed sources:** [N] (if any)
```

Per-source sections:
```markdown
---
## Source N: [domain]
**URL:** [url]
**Tier:** [1/2]
**Pass:** [1/2]

[full content field from src_NNN.json or pass2_NNN.json]
```

---

## Key Decisions

- **Fresh AsyncWebCrawler per fetch call** — no session_id reuse across domains (domain isolation)
- **Minimum content length:** 200 chars — fetches below threshold trigger retry (anti-bot detection)
- **Tier 3 domains:** Skipped before any fetch attempt, logged as `skipped_tier3`
- **DuckDuckGo:** Use `html.duckduckgo.com/html/?q=...` (static endpoint); fall back to `ddgs` library if blocked
- **Do NOT install** `crawl4ai[torch]` or `crawl4ai[transformer]` — violates Architecture.md Rule 1
- **crawl4ai 0.8.0 markdown API:** `result.markdown` is `StringCompatibleMarkdown` (str subclass). Access content via `result.markdown.raw_markdown` (str, full markdown) or use directly as string. Both are equivalent.
- **lxml version:** crawl4ai 0.8.0 requires `lxml~=5.3` but works with `lxml>=6.0` despite pip warning.
- **duckduckgo-search renamed:** Package renamed to `ddgs`. Use `pip install ddgs` and `from ddgs import DDGS`.
- **resolve_output_dir:** Returns `projects/N. Title/research/` if project found, else `.claude/scratch/researcher/` (standalone mode). Creates dir automatically.
- **Integration test isolation:** Run `pytest tests/test_researcher/test_integration.py` separately — test_fetcher.py installs a module-level crawl4ai mock that interferes if tests run together without the `_clear_crawl4ai_mock()` guard.
- **synthesis_input.md includes ALL source content (no code-level truncation).** Word cap is enforced by the synthesis prompt — Claude distills 20–50k words to ~2,000 words of curated dossier content.
