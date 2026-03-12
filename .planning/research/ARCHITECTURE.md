# Architecture Research

**Domain:** Agent 1.2 — Web Research Agent integrated into Claude Code skill pipeline
**Researched:** 2026-03-12
**Confidence:** HIGH (codebase direct inspection + established pattern reuse)

---

## Standard Architecture

### System Overview

```
                      CLAUDE CODE (Orchestrator)
                                |
                reads researcher/SKILL.md for instructions
                                |
         +----------------------+----------------------+
         |                                             |
   [Pass 1: Survey]                          [Pass 2: Deep Dive]
   DETERMINISTIC phase                       HEURISTIC + DETERMINISTIC
         |                                             |
   +-----+-----+                             +---------+---------+
   | scraper.py|                             | scraper.py (reuse)|
   | batch URLs|                             | targeted URLs     |
   | -> files  |                             | -> files          |
   +-----+-----+                             +---------+---------+
         |                                             |
         v                                             v
   .claude/scratch/                          .claude/scratch/
   pass1_raw_*.md                            pass2_raw_*.md
         |                                             |
         v                                             v
   [HEURISTIC: Claude evaluates]             [HEURISTIC: Claude synthesizes]
   source quality, coverage gaps,            chronology, contradictions,
   selects deep dive targets                 narrative hooks, unanswered Qs
         |                                             |
         +------------------+--------------------------+
                            |
                            v
              projects/N. Title/research/
              Research.md  (scriptwriter input)
              media_urls.md (separated URL catalog)
```

### Component Responsibilities

| Component | Type | Responsibility | Lives In |
|-----------|------|---------------|----------|
| `cli.py` (new skill) | DETERMINISTIC | CLI entry point, argument parsing, path resolution | `researcher/scripts/researcher/cli.py` |
| `fetcher.py` | DETERMINISTIC | crawl4ai wrapper with error handling, retry, output to file | `researcher/scripts/researcher/fetcher.py` |
| `url_builder.py` | DETERMINISTIC | Generate search URLs and source URLs from topic + config | `researcher/scripts/researcher/url_builder.py` |
| `pass1 context loader` | DETERMINISTIC | Print topic context + source list to stdout for Claude | `cli.py cmd_survey` |
| `pass2 context loader` | DETERMINISTIC | Print scraped content summary + gap list to stdout | `cli.py cmd_deepen` |
| `writer.py` | DETERMINISTIC | Write Research.md and media_urls.md with correct schema | `researcher/scripts/researcher/writer.py` |
| Survey prompt | HEURISTIC | Claude evaluates sources, identifies gaps, picks deep targets | `researcher/prompts/survey_evaluation.md` |
| Synthesis prompt | HEURISTIC | Claude synthesizes full research dossier from scraped content | `researcher/prompts/synthesis.md` |

---

## How Heuristic/Deterministic Split Applies

This is the critical architectural decision. The existing pattern from Agent 1.1 is the authoritative template:

### Deterministic (Python code):
- Fetching URLs via crawl4ai (I/O, no judgment)
- Generating search query URLs from a topic string (string manipulation)
- Writing Research.md to the project directory (file I/O)
- Printing structured context to stdout for Claude to read (context-loader pattern)
- Extracting and cataloging raw media URLs found in scraped pages

### Heuristic (Claude reasoning):
- Deciding which scraped sources are high quality vs. unreliable
- Identifying what's still missing after Pass 1 and which gaps matter
- Selecting the 5-10 best URLs for deep dive in Pass 2
- Synthesizing contradictions across multiple sources
- Extracting narrative hooks and unanswered questions
- Writing the final Research.md content (Claude writes, `writer.py` saves)

**Key rule inherited from Architecture.md:** Python never calls an LLM API. Claude reads outputs from Python scripts and reasons over them natively.

---

## Recommended Project Structure

```
.claude/skills/researcher/
├── SKILL.md                          # Claude's operating instructions
├── scripts/
│   └── researcher/
│       ├── __init__.py
│       ├── cli.py                    # Entry point: survey / deepen / write subcommands
│       ├── fetcher.py                # crawl4ai wrapper (async, error handling, file output)
│       ├── url_builder.py            # Generate search + source URLs from topic
│       └── writer.py                 # Write Research.md and media_urls.md
├── prompts/
│   ├── survey_evaluation.md          # Pass 1 HEURISTIC: evaluate sources, pick deep targets
│   └── synthesis.md                  # Pass 2 HEURISTIC: synthesize dossier from content
└── tests/
    ├── test_fetcher.py
    ├── test_url_builder.py
    └── test_writer.py

projects/N. Title/                    # Created by Agent 1.1 — researcher writes into it
├── metadata.md                       # Input: topic brief, hook, scoring (Agent 1.1 output)
└── research/                         # Created by Agent 1.1 scaffold — researcher fills
    ├── Research.md                   # PRIMARY OUTPUT: full dossier for scriptwriter
    └── media_urls.md                 # SECONDARY OUTPUT: separated URL catalog
```

### What Agent 1.1 Already Creates

`project_init.py` calls `_create_scaffold()` which makes `research/`, `assets/`, and `script/` subdirectories. The researcher writes directly into the pre-existing `research/` folder — no directory creation logic needed in the new skill.

---

## Architectural Patterns

### Pattern 1: Context-Loader CLI (inherited from Agent 1.1)

**What:** CLI subcommand runs Python deterministic logic, then prints structured markdown to stdout. Claude reads stdout and performs HEURISTIC reasoning.

**When to use:** Every handoff point between deterministic and heuristic phases. This is the established project convention.

**Agent 1.1 reference implementation:** `cmd_topics()` in `cli.py` — loads files, prints structured context, ends with an instruction line for Claude.

**Researcher adaptation:**
```
cmd_survey(topic):
    1. [DETERMINISTIC] Build search query URLs from topic
    2. [DETERMINISTIC] Fetch URLs via crawl4ai, write to .claude/scratch/pass1_raw_*.md
    3. [DETERMINISTIC] Print: topic, scraped file paths, source count
    4. Claude reads survey_evaluation.md prompt, evaluates sources, picks deep targets
    5. Claude calls cmd_deepen with selected URL list

cmd_deepen(urls_file):
    1. [DETERMINISTIC] Read URL list from file
    2. [DETERMINISTIC] Fetch each URL via crawl4ai, write to .claude/scratch/pass2_raw_*.md
    3. [DETERMINISTIC] Print: file list, byte counts, any fetch failures
    4. Claude reads synthesis.md prompt, synthesizes full dossier
    5. Claude calls cmd_write with structured dossier data

cmd_write(project_dir, dossier_json):
    1. [DETERMINISTIC] Parse structured dossier
    2. [DETERMINISTIC] Write Research.md using schema template
    3. [DETERMINISTIC] Write media_urls.md
    4. Print: file paths, section counts, word count
```

### Pattern 2: Scratch Pad for Large Raw Content

**What:** Scraped page content goes to `.claude/scratch/` as individual files, never into Claude's context directly. Claude receives file paths and reads targeted sections.

**When to use:** Whenever individual scraped pages exceed ~1,500 tokens (almost always — web pages are large).

**Why:** Matches the project's established context hygiene convention from CLAUDE.md. Raw Wikipedia article bodies, news articles, and archive pages are too large to embed in conversation.

**Implementation:** Each crawl4ai fetch writes to `.claude/scratch/researcher/pass1_src_{N}.md`. Pass 1 produces N files. Claude receives a summary table (source, URL, file path, word count) and reads specific files on demand.

### Pattern 3: Two-Pass Research with Gap Analysis

**What:** Pass 1 is deliberately broad — search results and overview pages. After Claude evaluates coverage, Pass 2 targets specific primary sources that fill identified gaps.

**When to use:** Any research task where quality differs by source and the researcher cannot know upfront which sources will be authoritative.

**Trade-offs:**
- Adds one Claude interaction between passes (costs one turn but dramatically improves output quality)
- Prevents wasting crawl4ai calls on low-value sources
- Maps cleanly to HEURISTIC (gap analysis) / DETERMINISTIC (fetching) separation

**Pass 1 default sources (built by `url_builder.py`):**
- Wikipedia search results
- Archive.org search
- Google News search (via DuckDuckGo — avoids bot detection)
- 2-3 targeted academic/primary source domains from source_config.json

**Pass 2 targets (selected by Claude after Pass 1 evaluation):**
- Primary sources identified in Pass 1 (court records, official reports, named archives)
- Individual Wikipedia article (full text, not search results)
- Specific news investigations identified in Pass 1
- Academic papers or documented sources cited in overview pages

### Pattern 4: Structured Dossier Input to writer.py

**What:** Claude synthesizes findings into a structured Python dict (or JSON), then calls `cmd_write` with that data. `writer.py` formats it into Research.md.

**Why:** This maintains the HEURISTIC/DETERMINISTIC boundary. Claude reasons; Python formats and saves. Claude does not write file I/O directly (fragile in agent workflows). Python does not make content decisions.

**Schema passed by Claude to writer.py:**
```python
{
    "subject_overview": str,       # 500-word summary
    "timeline": [                  # chronological events
        {"date": str, "event": str, "source": str}
    ],
    "key_figures": [               # people involved
        {"name": str, "role": str, "quotes": [str]}
    ],
    "primary_sources": [
        {"title": str, "type": str, "url": str, "reliability": int}
    ],
    "secondary_sources": [
        {"title": str, "outlet": str, "url": str, "reliability": int}
    ],
    "contradictions": [str],       # conflicting accounts
    "unanswered_questions": [str], # narrative tension gaps
    "narrative_hooks": [str],      # high-impact story beats for scriptwriter
    "media_urls": [                # separated, goes to media_urls.md
        {"description": str, "url": str, "type": str}
    ]
}
```

---

## Data Flow

### Full Research Flow

```
User provides topic name (e.g., "The Matamoros Cult Murders")
    |
    v
SKILL.md instructs Claude to locate project dir
    |
    +---> Read projects/N. Title/metadata.md (Agent 1.1 output)
    |     Extract: topic title, hook, complexity score, estimated runtime
    |
    v
cmd_survey "[topic title]"
    |
    +---> [DETERMINISTIC] url_builder.py generates 8-12 initial URLs
    |
    +---> [DETERMINISTIC] fetcher.py crawls each URL
    |     Writes: .claude/scratch/researcher/pass1_src_0.md
    |             .claude/scratch/researcher/pass1_src_1.md
    |             ... (one file per source)
    |
    +---> Prints summary table to stdout:
    |     source | url | file_path | word_count | status
    |
    v
[HEURISTIC] Claude reads survey_evaluation.md prompt
    Evaluates: source quality, coverage gaps, primary source leads
    Outputs: ranked list of 5-10 deep dive target URLs
    |
    v
cmd_deepen --urls-file .claude/scratch/researcher/deep_targets.txt
    |
    +---> [DETERMINISTIC] fetcher.py crawls each deep target URL
    |     Writes: .claude/scratch/researcher/pass2_src_0.md
    |             .claude/scratch/researcher/pass2_src_1.md
    |
    +---> Prints summary table to stdout
    |
    v
[HEURISTIC] Claude reads synthesis.md prompt
    Synthesizes: all pass1 + pass2 content into structured dossier
    Produces: structured JSON matching Research.md schema
    |
    v
cmd_write --project-dir "projects/N. Title" --dossier dossier.json
    |
    +---> [DETERMINISTIC] writer.py formats and writes:
    |     projects/N. Title/research/Research.md
    |     projects/N. Title/research/media_urls.md
    |
    +---> Prints: confirmation + word count + section count
    |
    v
Downstream: Agent 1.3 (Writer) reads Research.md
```

### Key Data Flows

1. **Agent 1.1 → Agent 1.2:** Via filesystem. `projects/N. Title/metadata.md` is the handoff document. Researcher reads it to get topic brief, hook, and estimated complexity.

2. **Pass 1 → Pass 2 (within Agent 1.2):** Via `.claude/scratch/researcher/deep_targets.txt`. Claude writes target URLs after survey evaluation; `cmd_deepen` reads the file. File-based, not in-memory — matches project conventions.

3. **Agent 1.2 → Agent 1.3:** Via filesystem. `projects/N. Title/research/Research.md` is the output artifact. Writer agent reads this directly.

4. **Media URL separation:** `media_urls.md` is written separately from `Research.md` to keep the dossier clean for scriptwriting. Agent 1.4 (Visual Director) will consume media URLs when building the shot list.

---

## New vs. Modified Components

### New (does not exist yet)

| Component | Location | What It Is |
|-----------|----------|------------|
| `researcher/SKILL.md` | `.claude/skills/researcher/` | Operating instructions for Claude |
| `researcher/cli.py` | `scripts/researcher/` | Entry point with `survey`, `deepen`, `write` subcommands |
| `researcher/fetcher.py` | `scripts/researcher/` | crawl4ai wrapper with file output, retry, error handling |
| `researcher/url_builder.py` | `scripts/researcher/` | Generate search + source URLs from topic string |
| `researcher/writer.py` | `scripts/researcher/` | Write Research.md and media_urls.md from dossier dict |
| `prompts/survey_evaluation.md` | `researcher/prompts/` | HEURISTIC prompt: source evaluation + gap analysis |
| `prompts/synthesis.md` | `researcher/prompts/` | HEURISTIC prompt: dossier synthesis from scraped content |
| `tests/test_fetcher.py` | `researcher/tests/` | Unit tests for fetcher (mock crawl4ai calls) |
| `tests/test_url_builder.py` | `researcher/tests/` | Unit tests for URL generation |
| `tests/test_writer.py` | `researcher/tests/` | Unit tests for file output formatting |

### Modified (exists, no changes needed)

| Component | Reason No Change Needed |
|-----------|------------------------|
| `crawl4ai-scraper/scripts/scraper.py` | Researcher uses this for ad-hoc single-URL scraping; `fetcher.py` handles batch with file output separately |
| `channel-assistant/project_init.py` | Already creates `research/` subdirectory in scaffold — no modification needed |
| `projects/N. Title/metadata.md` | Already contains topic brief — researcher reads it as input |

### Reused Without Modification

| Component | How Researcher Uses It |
|-----------|----------------------|
| `crawl4ai-scraper/SKILL.md` | Not invoked directly — `fetcher.py` imports crawl4ai directly following the same async pattern |
| `_get_project_root()` pattern from cli.py | Copy into researcher's cli.py (walk up to CLAUDE.md) |
| `.claude/scratch/` convention | Researcher writes pass1/pass2 raw files here, same as Agent 1.1 |

---

## Integration Points

### Upstream: Agent 1.1 Output

| Artifact | Location | What Researcher Reads |
|----------|----------|----------------------|
| `metadata.md` | `projects/N. Title/metadata.md` | Topic title, hook sentence, complexity/shock scores, estimated runtime |
| Directory scaffold | `projects/N. Title/research/` | Pre-created by `project_init.py` — researcher writes output here |

The researcher SKILL.md should instruct Claude to locate the project directory by listing `projects/` and finding the most recently created one (or by taking the project number as an argument).

### Downstream: Agent 1.3 Writer Input

| Artifact | Location | What Writer Reads |
|----------|----------|------------------|
| `Research.md` | `projects/N. Title/research/Research.md` | Full structured dossier |
| `media_urls.md` | `projects/N. Title/research/media_urls.md` | Optional reference |

The Writer agent does not need any changes — it will read Research.md as context, same filesystem handoff pattern.

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| crawl4ai | Python import in `fetcher.py`, async `AsyncWebCrawler` | Already in environment |
| Web search | DuckDuckGo HTML search (no API key) via crawl4ai | Avoids bot detection better than Google direct |
| Wikipedia | Direct article URL scraping via crawl4ai | Full article text available, no API needed |
| Archive.org | Direct search URL via crawl4ai | Public domain, crawler-friendly |

---

## Build Order

Dependencies determine build order. Tests unlock confidence for each stage.

```
Phase 1: fetcher.py + url_builder.py + tests
    Why first: All subsequent phases depend on working scraping and URL generation.
    Deliverable: Can scrape a URL list and write files to .claude/scratch/
    Test: Mock crawl4ai responses, verify file output and error handling.
    |
    v
Phase 2: cli.py (cmd_survey subcommand) + SKILL.md skeleton
    Why: Establishes the CLI pattern and enables the first end-to-end test of Pass 1.
    Deliverable: `python -m researcher.cli survey "Topic"` fetches and files sources.
    Note: SKILL.md can be written before prompts — instructions can reference prompts as TBD.
    |
    v
Phase 3: survey_evaluation.md prompt
    Why: Pass 1 is only useful if Claude can evaluate and select deep dive targets.
    Deliverable: Full Pass 1 flow works end-to-end (survey → gap analysis → target list).
    Note: This is a HEURISTIC component — no Python code, just a well-structured prompt file.
    |
    v
Phase 4: cli.py (cmd_deepen subcommand)
    Why: Needs Phase 1 infrastructure (fetcher) and Phase 3 (knows what to fetch).
    Deliverable: `python -m researcher.cli deepen --urls-file targets.txt` works.
    |
    v
Phase 5: synthesis.md prompt
    Why: Pass 2 content is only useful once a synthesis prompt exists.
    Deliverable: Full two-pass flow works — raw content → structured dossier in conversation.
    |
    v
Phase 6: writer.py + cli.py (cmd_write subcommand) + tests
    Why: Final step — persists Claude's synthesis to Research.md on disk.
    Deliverable: `python -m researcher.cli write --project-dir "..." --dossier dossier.json` writes both files.
    Test: Verify schema compliance, section completeness, media URL separation.
    |
    v
Phase 7: SKILL.md finalization + integration test
    Why: After all components work individually, SKILL.md needs complete instructions.
    Deliverable: Full pipeline from "topic name" → Research.md in one Claude Code session.
```

**Minimum viable:** Phases 1-3 deliver a working Pass 1 survey. Phases 4-5 complete the two-pass design. Phase 6 persists the output. Phase 7 is polish.

---

## Anti-Patterns

### Anti-Pattern 1: Reading All Scraped Content into Context

**What people do:** Fetch 10 web pages, concatenate them all, pass the full text to Claude in one prompt.

**Why it's wrong:** 10 web pages = 50,000-200,000 tokens. Blows context window. Claude loses coherence on earlier sources by the time it reads later ones.

**Do this instead:** Write each page to `.claude/scratch/researcher/pass1_src_N.md`. Give Claude a summary table (URL, file path, word count). Let Claude read specific files on demand using the Read tool.

### Anti-Pattern 2: Single-Pass Research

**What people do:** Fetch the first 10 search results and synthesize immediately.

**Why it's wrong:** Search results for obscure documentary topics are dominated by secondary sources (Wikipedia, listicle sites). Primary sources (court documents, archived news investigations, academic papers) appear buried or not at all in search results.

**Do this instead:** Two passes. Pass 1 identifies what primary sources exist and where. Pass 2 fetches those primary sources directly.

### Anti-Pattern 3: Hardcoding Source Domains

**What people do:** Build a fixed list of domains to scrape for every topic (e.g., always scrape archive.org, always scrape Wikipedia).

**Why it's wrong:** Some topics have rich Wikipedia coverage; others have almost none. Some topics are in government archives; others are in newspaper morgues. Hardcoded domains miss topic-specific primary sources.

**Do this instead:** `url_builder.py` generates a starting list of search queries and 2-3 default domains. Pass 1 evaluation (HEURISTIC) identifies the topic-specific sources worth deep diving. Pass 2 targets those dynamically.

### Anti-Pattern 4: Writing Research.md Directly from Claude Without a Writer Module

**What people do:** Have Claude write the Research.md content directly using a Write tool call with a huge markdown string.

**Why it's wrong:** Fragile — any Claude error or interruption loses all unsaved synthesis. Schema enforcement is impossible. Media URL separation cannot be verified.

**Do this instead:** Claude produces a structured JSON dossier (validates schema), then calls `cmd_write` which formats and saves. Python handles all I/O; Claude handles all reasoning.

### Anti-Pattern 5: Mixing Research.md and Media URLs

**What people do:** Include image URLs, video links, and archive media links inline in Research.md.

**Why it's wrong:** Pollutes the scriptwriting context with 50+ media URLs. The Writer agent doesn't need URLs — it needs narrative content. The Visual Director (Agent 1.4) needs URLs but reads a separate file anyway.

**Do this instead:** `writer.py` always writes two files: `Research.md` (clean narrative dossier) and `media_urls.md` (URL catalog with descriptions and types). Downstream agents consume whichever file they need.

---

## Sources

- Existing codebase: `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` (HIGH confidence — direct inspection)
- Existing codebase: `.claude/skills/channel-assistant/SKILL.md` (HIGH confidence — pattern reference)
- Existing codebase: `.claude/skills/crawl4ai-scraper/scripts/scraper.py` (HIGH confidence — tool reference)
- Architecture rules: `Architecture.md` (HIGH confidence — binding project constraints)
- Project requirements: `.planning/PROJECT.md` v1.1 milestone spec (HIGH confidence)
- Project conventions: `CLAUDE.md` scratch pad rules (HIGH confidence)

---
*Architecture research for: Agent 1.2 Web Research integration into Claude Code skill pipeline*
*Researched: 2026-03-12*
