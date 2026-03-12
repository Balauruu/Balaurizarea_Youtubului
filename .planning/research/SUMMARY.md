# Project Research Summary

**Project:** Agent 1.2 — The Researcher (Web Research Agent for Documentary Pipeline)
**Domain:** Agentic web research skill integrated into Claude Code documentary production pipeline
**Researched:** 2026-03-12
**Confidence:** HIGH

## Executive Summary

Agent 1.2 is a multi-pass web research agent that converts a topic name (inherited from Agent 1.1's output) into a structured `Research.md` dossier consumed directly by Agent 1.3 (The Writer). The skill must be built as a Claude Code skill following the exact same heuristic/deterministic split pattern established by Agent 1.1: Python handles all I/O deterministically (scraping, file writes, context loading), and Claude handles all reasoning heuristically (source evaluation, synthesis, narrative hooks). The entire pipeline is orchestrated through a CLI with three subcommands — `survey`, `deepen`, `write` — that serve as handoff points between deterministic and heuristic phases.

The recommended approach is a strict two-pass design. Pass 1 scrapes 10-15 broad URLs (Wikipedia, DuckDuckGo results, archive.org) to map the topic landscape and produce a machine-readable JSON source manifest. Claude then evaluates that manifest and selects 5-10 high-value primary source targets. Pass 2 fetches those targets in depth. This separation is the core architectural constraint — collapsing the two passes into one destroys the strategic advantage and is the most common failure mode. The output splits across two files: `Research.md` (curated narrative dossier, max ~2,000 words of scriptwriter-facing content) and `media_urls.md` (URL catalog for downstream agents).

The key risks are well-documented. LLM hallucination of citations is a structural threat — every claim in the dossier must trace back to a URL that was actually fetched and returned HTTP 200, never to something Claude generated from training memory. Anti-bot detection will block the highest-quality news archive sources; the solution is to tier sources by access reliability from the start and log blocked fetches explicitly rather than silently dropping them. crawl4ai browser context contamination after failures must be handled with domain-isolated contexts and minimum-content verification after each fetch. All of these pitfalls must be designed around in Phase 1 — retrofitting source schema, credibility signals, or context hygiene after the agent is producing output is expensive.

---

## Key Findings

### Recommended Stack

The v1.0 stack (Python 3.14, SQLite, yt-dlp, sqlite-utils, tabulate) is unchanged and validated. Agent 1.2 adds only two hard new dependencies: **crawl4ai 0.8.x** for multi-URL async scraping with JS rendering (already specified in Architecture.md; use `arun_many()` with `MemoryAdaptiveDispatcher` for 10-30 concurrent fetches), and **trafilatura 2.0.0** as a boilerplate-stripping fallback when crawl4ai's markdown output is noisy.

Everything else is already installed: `internetarchive 5.8.0` (official archive.org API client — use this instead of scraping archive.org HTML), `beautifulsoup4 4.14.3` (targeted HTML parsing for structured sources), `requests 2.32.5` (MediaWiki API calls for Wikipedia), and `difflib` (stdlib source deduplication for 10-30 sources per run). PyMuPDF for PDF extraction should be added reactively only when government record PDFs are first encountered.

**Core technologies:**
- **crawl4ai 0.8.x**: Multi-URL async scraping — primary scraping engine, already specified in Architecture.md, handles JS-rendered news sites
- **trafilatura 2.0.0**: Boilerplate stripping — F1=0.958 on extraction benchmark, supersedes unmaintained newspaper3k, fallback for noisy crawl4ai output
- **internetarchive 5.8.0**: archive.org API client — already installed, use official client not HTML scraping for archive.org content
- **difflib (stdlib)**: Near-duplicate source detection — adequate for 10-30 source runs, zero install cost
- **requests 2.32.5**: MediaWiki API — already installed, use direct API calls not the `wikipedia` PyPI wrapper (disambiguation bugs, unmaintained)

**Critical install note:** `crawl4ai-setup` must be run after pip install — it runs `playwright install` which installs ~300MB of browser binaries. Set `PYTHONUTF8=1` in the skill's run environment for non-Latin source content. Do NOT install `crawl4ai[torch]` or `crawl4ai[transformer]` extras — those enable LLM-based extraction which violates Architecture.md Rule 1.

### Expected Features

The dossier is not for human browsing — it is structured input for an LLM scriptwriter (Agent 1.3) that needs attributed, narrative-ready facts to produce a 20-50 minute documentary without a human filtering step in between. Every feature decision flows from this consumer requirement.

**Must have (table stakes) — P1, ship with v1:**
- Manual topic input (CLI `topic` arg maps to `projects/N. [Title]/`) — without this, agent cannot run
- Pass 1: Broad survey scrape (Wikipedia, news archives, DuckDuckGo) — baseline topic landscape
- Pass 2: Primary source deep-dive (archive.org, loc.gov, gov archives) — provides script authority; secondary-only dossiers feel thin
- Chronological timeline with source attribution per entry — critical for documentary script structure
- Key figures section: full names, roles, relationships, at least one attributed quote per figure — backbone of narration
- Subject overview (500-word synthesis) — establishing context for the Writer
- Contradictions section — documentary gold; creates narrative tension without resolution
- Unanswered questions section — best documentary endings; ambiguity is a feature
- Source list with structured credibility signals (not scalar scores) — lets Writer calibrate assertion confidence
- Output to `projects/N. [Title]/research/Research.md` — required for pipeline continuity

**Should have (differentiators) — P2, add post-validation:**
- Source chain tracing — traces facts through multiple attribution layers (critical for the channel's "correcting the record" angle)
- Direct quote extraction as separate labeled callout — reference script relies on verbatim historical quotes for scene anchoring
- Narrative hooks identification — 3-5 high-impact story beats explicitly labeled for the Writer
- `media_urls.md` as separate file — keeps Research.md clean for Writer; feeds Agent 1.4 (Visual Director)
- Wikipedia error check — flags where Wikipedia contradicts primary sources; channel differentiator

**Defer (v2+):**
- Scope estimation (minutes-of-material estimate) — defer until enough Research.md outputs exist to calibrate
- Cross-reference with past topics — low risk without it; add when backlog grows large enough that overlap is a real concern

### Architecture Approach

The skill follows the context-loader CLI pattern established by Agent 1.1: Python CLI subcommands run deterministic I/O logic, print structured context to stdout, and Claude performs heuristic reasoning. All scraped page content goes to `.claude/scratch/researcher/` as individual files — never concatenated into Claude's context. Claude receives a summary table (source, URL, file path, word count) and reads specific files on demand. The Pass 1 output is a machine-readable JSON source manifest (not prose) that Claude uses to select deep-dive targets; Pass 2 reads that manifest file. Claude synthesizes a structured JSON dossier, then calls `cmd_write` which formats and saves — Python handles all file I/O, Claude handles all content decisions.

**Major components:**
1. `cli.py` — Entry point with `survey`, `deepen`, `write` subcommands; context-loader pattern; inherits `_get_project_root()` from Agent 1.1
2. `fetcher.py` — crawl4ai wrapper with per-domain browser context isolation, minimum-content verification (>200 chars), retry, file output to `.claude/scratch/researcher/`
3. `url_builder.py` — Generates 8-12 initial search URLs from topic string; Pass 1 default sources only; Pass 2 targets selected by Claude heuristically
4. `writer.py` — Formats and writes `Research.md` and `media_urls.md` from validated dossier JSON; enforces schema completeness
5. `prompts/survey_evaluation.md` — HEURISTIC prompt: source quality evaluation, gap identification, deep-dive target selection
6. `prompts/synthesis.md` — HEURISTIC prompt: full dossier synthesis from all scraped content into structured JSON

### Critical Pitfalls

1. **LLM hallucination of citations** — GPT-4o fabricates 56% of citations; 100+ hallucinated refs made it into NeurIPS 2025 accepted papers. Every source entry in Research.md must include `url` (actually fetched), `fetched_at` (timestamp), and `relevant_excerpt` (direct quote, not paraphrase). Never ask Claude to generate citation text — only cite URLs that crawl4ai returned HTTP 200.

2. **crawl4ai browser context contamination** — After a failed fetch, subsequent requests in the same context return silent empty results (GitHub issue #501). Use a fresh browser context per source domain. Verify `result.markdown` length > 200 chars after every fetch; reset context on short results. Always use `async with AsyncWebCrawler() as crawler:` pattern.

3. **Anti-bot access failures** — crawl4ai's success rate is 72% on anti-bot protected sites. Major publishers (NYT, WaPo, Gannett) actively block AI crawlers as of 2026. Tier sources by access reliability: Tier 1 (Wikipedia, archive.org pre-2025, `.gov` domains, HathiTrust) — reliable; Tier 2 (regional news, older archives) — attempt but expect failures; Tier 3 (major newspapers, PACER) — do not attempt. Log all blocked fetches as `access_blocked` explicitly.

4. **Two-pass design collapse into one expensive unfocused pass** — The survey pass expands when promising sources are immediately deep-dived. Enforce hard constraints in code: Pass 1 maximum 2 URLs per source type, output is JSON source manifest only (no draft Research.md content). Pass 2 operates exclusively on that manifest, maximum 15 fetches.

5. **Scalar credibility scores create false confidence** — Domain-level scoring (`.gov` = reliable) is as reliable as a coin flip for obscure topics. Use structured signals: `source_type` (primary/secondary/tertiary), `corroborated_by` (list of corroborating sources), `access_quality` (full_text/excerpt_only/blocked), and `single_source` flag. No scalar numbers.

6. **Research.md overloads scriptwriter context** — An 8,000-word comprehensive dossier consumes the Writer agent's context before script work begins, producing listicle output rather than narrative. Research.md scriptwriter-facing version: maximum 2,000 words. Full source detail goes to `ResearchArchive.md` or remains in `.claude/scratch/`.

---

## Implications for Roadmap

Based on combined research, all 6 critical pitfalls map to Phase 1 design decisions — there are no safe shortcuts to defer to later phases. The build order follows strict component dependencies.

### Phase 1: Foundation — crawl4ai Integration Layer

**Rationale:** `fetcher.py` is the dependency for everything downstream. A fragile scraper produces a fragile research agent regardless of prompt quality. This phase must be built and tested before any research logic is written. Browser context contamination and anti-bot failures are impossible to patch retroactively.
**Delivers:** Working `fetcher.py` with domain-isolated browser contexts, minimum-content verification, retry logic, and file output to `.claude/scratch/researcher/`. Working `url_builder.py` with source tier configuration.
**Addresses features:** Pass 1 broad survey (infrastructure), Pass 2 primary source dive (infrastructure)
**Avoids:** Pitfall 2 (browser context contamination), Pitfall 3 (anti-bot access failures)

### Phase 2: Survey CLI + SKILL.md Skeleton

**Rationale:** Establishes the CLI pattern and enables first end-to-end test of Pass 1. SKILL.md can be written before prompts — instructions reference prompts as TBD. This phase is fast because it directly reuses the Agent 1.1 context-loader pattern.
**Delivers:** `cmd_survey` subcommand — fetches initial sources, writes to scratch, prints summary table to stdout. Skeleton SKILL.md.
**Uses:** `fetcher.py` + `url_builder.py` from Phase 1; `_get_project_root()` pattern from Agent 1.1 `cli.py`
**Implements:** Context-loader CLI pattern (Architecture Pattern 1)

### Phase 3: Pass 1 Heuristic — Survey Evaluation Prompt

**Rationale:** Pass 1 only delivers value if Claude can evaluate source quality and produce a machine-readable JSON source manifest for deep-dive targeting. This is the critical phase where the intermediate artifact schema is defined — must happen before Pass 2 infrastructure so the contract between passes is locked.
**Delivers:** `prompts/survey_evaluation.md` — instructs Claude to evaluate scraped sources, identify coverage gaps, score relevance, and output a JSON source manifest. Full Pass 1 flow works end-to-end.
**Avoids:** Pitfall 4 (two-pass collapse — manifest is machine-readable JSON, enforced by prompt design)
**Critical design gate:** Intermediate artifact is JSON source manifest, never prose. This boundary is enforced in the prompt.

### Phase 4: Deep-Dive CLI

**Rationale:** Needs Phase 1 infrastructure and Phase 3's defined intermediate artifact schema. `cmd_deepen` reads the JSON source manifest written by Claude in Phase 3 and fetches targeted primary source URLs.
**Delivers:** `cmd_deepen` subcommand — reads `deep_targets.txt`, fetches primary sources, writes `pass2_src_N.md` files to scratch, prints summary table.
**Implements:** Two-pass research architecture (Architecture Pattern 3)

### Phase 5: Synthesis Prompt

**Rationale:** Pass 2 content is only useful once a synthesis prompt produces a schema-compliant structured JSON dossier. This phase also finalizes the Research.md content structure and credibility signal design — both must be designed here because retrofitting them after the agent is producing output is expensive.
**Delivers:** `prompts/synthesis.md` — instructs Claude to synthesize all pass1 + pass2 content into structured JSON matching the Research.md schema, with structured credibility signals, contradiction pairs, unanswered questions, and narrative hooks.
**Avoids:** Pitfall 1 (hallucinated citations — prompt enforces URL provenance), Pitfall 5 (scalar credibility scores replaced with structured signals), Pitfall 6 (2,000-word curated output budget enforced in prompt)

### Phase 6: Output Layer — writer.py + cmd_write

**Rationale:** Final persistence layer. Formats Claude's structured JSON dossier into `Research.md` and `media_urls.md`. Schema validation here catches incomplete dossiers before they reach the Writer agent.
**Delivers:** `writer.py` with schema compliance checking + `cmd_write` subcommand. Writes `Research.md` (curated, max 2,000 words) and `media_urls.md` (separated URL catalog). Unit tests for schema enforcement.
**Addresses features:** Media inventory as separate file (keeps Research.md clean for Writer; feeds Agent 1.4 eventually)
**Avoids:** Pitfall 6 (context window overload — word budget enforced by writer.py)

### Phase 7: SKILL.md Finalization + Integration Test

**Rationale:** After all components work individually, SKILL.md needs complete operating instructions. Integration test with a real topic validates the full pipeline end-to-end in one Claude Code session.
**Delivers:** Complete SKILL.md. Integration test passing with a project title containing spaces (Windows path handling validation).
**Critical verification:** Spot-check 3 URLs from Research.md (source provenance), verify Pass 1 produced JSON manifest not prose, verify no fetch content held in conversation context.

### Phase Ordering Rationale

- Phases 1-2 come first because all subsequent phases depend on working scraping infrastructure and the established CLI pattern
- Phase 3 must precede Phase 4 because it defines the intermediate artifact schema that Phase 4 reads — the contract between passes must be defined before the second pass is built
- Phase 5 must precede Phase 6 because `writer.py` formats the dossier schema that the synthesis prompt defines
- Phase 7 is polish — integration test and SKILL.md finalization after all components are individually proven
- The pitfalls research is emphatic: all 6 critical pitfalls have "Phase 1" as their prevention phase — schema design, credibility signals, source tiering, and browser context handling cannot be deferred

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (crawl4ai Integration):** crawl4ai's Windows-specific behavior and `PYTHONUTF8=1` requirement may need hands-on testing; API field names differ between versions (`result.markdown` vs `result.markdown_v2.raw_markdown`) — run `crawl4ai-doctor` and verify field names on install before writing `fetcher.py`
- **Phase 3 (Survey Evaluation Prompt):** Source tier list for the channel's specific niche (dark history, cults, true crime) needs validation in practice; DuckDuckGo HTML scraping behavior via crawl4ai may require iteration

Phases with standard patterns (skip research-phase):
- **Phase 2 (Survey CLI):** Direct reuse of Agent 1.1's context-loader pattern — well-documented, low risk
- **Phase 6 (writer.py):** Straightforward JSON-to-Markdown formatting with schema validation — standard Python file I/O
- **Phase 7 (Integration Test):** Standard testing protocol

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | crawl4ai, trafilatura, internetarchive all verified on PyPI with current versions; Python 3.14 compatibility confirmed; Windows-specific PYTHONUTF8 requirement documented from official sources |
| Features | HIGH | Downstream consumer (Agent 1.3 Writer) is fully defined; output schema specified in Architecture.md; reference script analyzed for scriptwriter requirements; feature set derived from concrete pipeline constraints |
| Architecture | HIGH | Pattern derived from direct codebase inspection of Agent 1.1 (channel-assistant/cli.py); build order follows strict dependency chain; all integration points verified against existing project structure |
| Pitfalls | HIGH | crawl4ai issues verified via GitHub issue tracker; citation hallucination rates from NeurIPS 2025 audit and GPT-4o study; anti-bot blocking from Nieman Lab and Techdirt reports (2026); credibility scoring research from PMC |

**Overall confidence:** HIGH

### Gaps to Address

- **PyMuPDF on Windows (MEDIUM confidence):** PDF extraction speed benchmarks verified, but whether government PDFs in the channel's niche are text-based or scanned images is unknown. Add PyMuPDF reactively on first PDF encounter; flag scanned PDFs as requiring OCR (currently out of scope).
- **DuckDuckGo HTML scraping stability:** Recommended over direct Google search (better bot detection tolerance), but this is community experience, not a documented crawl4ai guarantee. Validate in Phase 1 testing before committing to it as the default search path.
- **Pass 1 source manifest schema:** The exact JSON structure for the intermediate artifact between passes needs to be explicitly defined before Phase 3 prompt writing. This is a design decision, not a research gap, but it must be resolved before Phase 3.
- **crawl4ai API field stability:** Research documents that field names changed between minor versions. Pin crawl4ai version in requirements.txt on install and test output field names explicitly — do not assume stability across minor updates.

---

## Sources

### Primary (HIGH confidence)
- Existing codebase: `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` — Agent 1.1 pattern reference (direct inspection)
- Existing codebase: `.claude/skills/channel-assistant/SKILL.md` — context-loader pattern reference (direct inspection)
- `Architecture.md` — binding project constraints, Research Dossier Schema, heuristic/deterministic rules
- [Crawl4AI Documentation v0.8.x](https://docs.crawl4ai.com/) — features, installation, `arun_many()`, MemoryAdaptiveDispatcher
- [Crawl4AI PyPI](https://pypi.org/project/Crawl4AI/) — v0.8.0 January 16, 2026 confirmed
- [Trafilatura PyPI](https://pypi.org/project/trafilatura/) — v2.0.0 December 3, 2024 confirmed
- [Trafilatura Evaluation](https://trafilatura.readthedocs.io/en/latest/evaluation.html) — F1=0.958 benchmark
- [internetarchive PyPI](https://pypi.org/project/internetarchive/) — v5.8.0 February 18, 2026 confirmed
- [Crawl4AI GitHub Issue #501](https://github.com/unclecode/crawl4ai/issues/501) — browser context contamination after failures
- [GPTZero NeurIPS 2025 audit](https://gptzero.me/news/neurips/) — 100+ hallucinated citations in accepted papers

### Secondary (MEDIUM confidence)
- [Morphllm AI Web Scraping 2026](https://www.morphllm.com/ai-web-scraping) — 72% crawl4ai success rate on anti-bot sites
- [Nieman Journalism Lab 2026](https://www.niemanlab.org/2026/01/news-publishers-limit-internet-archive-access-due-to-ai-scraping-concerns/) — publisher AI blocking actions
- [StudyFinds: GPT-4o citation fabrication](https://studyfinds.org/chatgpts-hallucination-problem-fabricated-references/) — 56% fabricated citations study
- [PMC: source credibility domain-level scoring](https://revistas.unir.net/index.php/ijimai/article/download/856/915) — domain scoring as unreliable as coin flip
- [PyMuPDF Features Comparison](https://pymupdf.readthedocs.io/en/latest/about.html) — speed benchmarks vs pdfminer (official docs, partially self-reported)
- [MediaWiki API:Query](https://www.mediawiki.org/wiki/API:Query) — Wikipedia API endpoint reference

### Tertiary (informational)
- `context/script references/Mexico's Most Disturbing Cult.md` — reference script analysis for scriptwriter requirements
- [ScrapingHub Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark) — trafilatura vs newspaper3k comparison

---
*Research completed: 2026-03-12*
*Ready for roadmap: yes*
