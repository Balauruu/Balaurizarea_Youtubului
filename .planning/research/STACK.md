# Stack Research

**Domain:** Style Extraction and Script Generation (Agent 1.3 — The Writer)
**Researched:** 2026-03-14
**Confidence:** HIGH

> **Scope:** This document covers stack additions for v1.2 only. The validated v1.0/v1.1 stack (Python, SQLite stdlib, yt-dlp, crawl4ai, trafilatura, requests, difflib, beautifulsoup4, internetarchive) is unchanged. Do not re-evaluate those decisions.
>
> **Architecture reminder:** Architecture.md Rule 2 — classify before building. Style extraction is [HEURISTIC]: Claude reasons over the reference script and produces STYLE_PROFILE.md. Script generation is [HEURISTIC]: Claude reads Research.md + STYLE_PROFILE.md and writes the narration. The only [DETERMINISTIC] work is the CLI that assembles and prints context files for Claude to consume.

---

## What v1.2 Needs That v1.1 Does Not Have

Two deliverables, both primarily prompt-driven:

1. **Style extraction** — a one-time operation that reads `context/script-references/*.md` and produces a `STYLE_PROFILE.md` capturing sentence rhythm, vocabulary register, chapter structure, and pacing. Claude does the reasoning; a small deterministic layer quantifies surface metrics (sentence lengths, word counts, punctuation density) to anchor the prompt.

2. **Script generation** — an agent that reads Research.md + STYLE_PROFILE.md + channel DNA and produces numbered chapters with pure narration. This is 100% [HEURISTIC]. No deterministic code beyond a CLI context-loader.

The reference scripts are plain `.md` files (YouTube auto-transcription text, as seen in `context/script-references/Mexico's Most Disturbing Cult.md`). They are already clean prose — no HTML, no PDF, no scraped content. This means the extraction problem is straightforward text processing, not NLP pipeline complexity.

---

## Recommended Stack Additions

### Core: Style Metric Extraction

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `re` (stdlib) | stdlib | Sentence splitting, pattern detection | The reference scripts are transcribed speech — no consistent punctuation. Sentences must be split on `.`, `?`, `!` with basic heuristics (abbreviation handling). `re.split()` covers this with a 10-line pattern. No third-party tokenizer needed for this input format. |
| `collections` (stdlib) | stdlib | Word frequency, vocabulary analysis | `Counter` computes type-token ratio, top-N word frequencies, and chapter word counts. Zero install. Already used idiomatically in the channel-assistant codebase. |
| `statistics` (stdlib) | stdlib | Sentence length distribution | `statistics.mean()`, `statistics.median()`, `statistics.stdev()` compute the sentence length stats (mean words/sentence, standard deviation). These numbers go into STYLE_PROFILE.md as anchors for Claude's generation prompt. |

**Why NOT textstat (0.7.8):** textstat computes Flesch-Kincaid, Gunning Fog, and other readability scores that measure how hard text is to read for a general audience. These metrics are not useful for style replication. The channel's writing style goal is not "readable" in the academic sense — it is "neutral, cinematic, deadpan." Readability indices do not capture sentence rhythm, vocabulary register, or narrative pacing. textstat adds a dependency that solves the wrong problem.

**Why NOT spaCy (3.8.11, 11MB model):** spaCy provides POS tagging, dependency parsing, NER, and lemmatization. These would be useful if the style profile needed to classify noun phrases, passive voice frequency, or syntactic complexity. For this use case — transcribed speech from a documentary narrator — the style signal lives in sentence length distribution, clause-level punctuation rhythm, and chapter structure. These are all computable with `re` and `collections`. spaCy adds a 50MB install (core + model), a `python -m spacy download en_core_web_sm` step, and an `import spacy; nlp = spacy.load()` startup overhead for metrics that `str.split()` and `re` can compute directly. The v1.0 Key Decisions established "stdlib-only where possible" — this is a direct application. The Agent 1.2 STACK.md explicitly ruled out spaCy for the same reason.

**Why NOT NLTK:** NLTK is older than spaCy, heavier (3.7GB+ corpus downloads), and designed for academic text analysis. Same conclusion as spaCy: wrong tool for this input type.

### Supporting: Context-Loader CLI

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pathlib` (stdlib) | stdlib | File discovery and reading | Glob `context/script-references/*.md` and `projects/N. [Title]/Research.md`. Already the project standard for all file operations per CLAUDE.md. |
| `argparse` (stdlib) | stdlib | CLI argument parsing | The writer skill needs a CLI that accepts `--project-dir` and `--mode` (extract-style | generate-script). Same pattern as researcher's `cli.py`. |

No new third-party dependencies for the context-loader. It reads files and prints structured context — identical to the pattern in `researcher/cli.py` and `channel-assistant/cli.py`.

---

## Installation

```bash
# No new pip installs required for v1.2.
# All needed libraries are Python stdlib:
#   re, collections, statistics, pathlib, argparse, json, datetime

# Confirm Python version (should be 3.10+ for match/case syntax if used)
python --version
```

**Total new hard dependencies: 0.** This is the correct outcome for a primarily [HEURISTIC] milestone. The deterministic layer is thin by design.

---

## What the Deterministic Layer Actually Does

The style extractor script (`writer/style_extractor.py`) has one job: compute quantifiable surface metrics from a reference script and write a JSON snapshot that Claude's synthesis prompt can reference. Claude does all the qualitative interpretation.

**Metrics to compute (all via stdlib):**

| Metric | How Computed | Why It Matters |
|--------|--------------|----------------|
| Mean sentence word count | `re.split()` + `statistics.mean()` | Deadpan narration runs long sentences; knowing the mean anchors Claude |
| Sentence length std deviation | `statistics.stdev()` | Low stdev = uniform cadence; high stdev = varied rhythm |
| Chapter count and avg chapter word count | Split on `^\d+\.` chapter headers | Establishes act structure expectations |
| Type-Token Ratio | `len(set(words)) / len(words)` | Measures vocabulary richness — low TTR = repetitive, high = varied |
| Top-50 most frequent words | `Counter(words).most_common(50)` | Reveals vocabulary register (formal vs. colloquial) |
| Punctuation density | count `,` `;` `:` per 100 words | Reveals clause-level rhythm and pause frequency |
| Sentence-opening patterns | first word of each sentence | Shows whether narrator favors subject-first or transition-phrase openings |

This JSON snapshot feeds into a synthesis prompt file (`prompts/style_synthesis.md`) that Claude reads to write STYLE_PROFILE.md. STYLE_PROFILE.md is the writer-facing output — a plain markdown file Claude loads when generating the script.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| stdlib `re` + `statistics` | textstat 0.7.8 | Use textstat if you need Flesch-Kincaid or academic readability scores for a different feature (e.g., comparing script complexity to competitors). Not needed here. |
| stdlib `re` + `statistics` | spaCy 3.8.11 + en_core_web_sm | Use spaCy if a future milestone needs POS-based analysis (passive voice frequency, noun chunk density, syntactic complexity) for style comparison. The install cost becomes worthwhile at that point. |
| stdlib `re` + `statistics` | NLTK | Use NLTK only if you need corpus-level frequency analysis against a reference corpus (e.g., comparing channel vocabulary against Brown corpus). Not a current requirement. |
| Prompt-driven script generation (Claude native) | Fine-tuned model | A fine-tuned model would produce more stylistically consistent output but requires GPU infrastructure, training data curation, and ongoing maintenance. Claude Code with STYLE_PROFILE.md context is the correct approach for this pipeline's scale and architecture constraints. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| textstat | Computes readability indices (Flesch, Gunning Fog) — wrong signal for style replication. Adds dependency for metrics that do not appear in STYLE_PROFILE.md. | `statistics` stdlib for sentence length distribution |
| spaCy + en_core_web_sm | POS tagging and NER are unnecessary for surface style metrics on transcribed speech. 50MB install for zero functional gain at this milestone. | `re` + `collections` stdlib |
| NLTK | Older, heavier, requires corpus downloads. No capability advantage over stdlib for this use case. | `re` + `collections` stdlib |
| LangChain / LlamaIndex | Architecture.md Rule 1: zero LLM API wrappers. These do not add value when Claude Code is the orchestrator. | Claude Code native orchestration |
| Any LLM embedding library (sentence-transformers, openai embeddings) | Style similarity is computed by Claude reading STYLE_PROFILE.md — not by embedding comparison. Adds PyTorch to the dependency graph for no reason. | Claude reasoning over STYLE_PROFILE.md |
| Jinja2 or other templating engines | The script output is pure narration text, not HTML or structured templates. Claude generates the narration directly; a template engine adds indirection without value. | Claude generates narration directly into a text file |

---

## Stack Patterns

**Style extraction (one-time, per reference script added):**
- CLI accepts path to reference script directory
- Python reads all `.md` files, computes surface metrics via stdlib
- Writes `style_metrics.json` to `.claude/scratch/` (transient)
- Claude reads the JSON snapshot + reference script excerpts → synthesizes STYLE_PROFILE.md
- STYLE_PROFILE.md written to `context/channel/` for persistent use

**Script generation (per video, after research dossier is complete):**
- CLI loads: `projects/N. [Title]/Research.md` + `context/channel/STYLE_PROFILE.md` + `context/channel/channel.md`
- Prints assembled context to stdout
- Claude reads context, generates script as numbered chapters with pure narration
- Output written to `projects/N. [Title]/Script.md`

Both patterns follow the established context-loader CLI pattern from v1.0/v1.1. No new architectural concepts.

---

## Version Compatibility

| Package | Version | Python 3.10+ Status | Notes |
|---------|---------|---------------------|-------|
| re | stdlib | Always available | No compatibility concerns |
| collections | stdlib | Always available | No compatibility concerns |
| statistics | stdlib | Always available (3.4+) | No compatibility concerns |
| pathlib | stdlib | Always available (3.4+) | Already project standard |
| argparse | stdlib | Always available | Already used in researcher and channel-assistant CLIs |

No new compatibility risks. Zero external dependencies means zero version conflict surface.

---

## Sources

- [textstat PyPI](https://pypi.org/project/textstat/) — Version 0.7.8 (July 22, 2025) confirmed; readability metrics assessed — HIGH confidence
- [spaCy PyPI](https://pypi.org/project/spacy/) — Version 3.8.11 (November 17, 2025) confirmed; en_core_web_sm at 11MB — HIGH confidence
- [spaCy Models Documentation](https://spacy.io/models/en) — en_core_web_sm components (tok2vec, tagger, parser, senter, ner, lemmatizer) — HIGH confidence
- [Programming Historian: Introduction to Stylometry with Python](https://programminghistorian.org/en/lessons/introduction-to-stylometry-with-python) — Type-Token Ratio, sentence length, punctuation density as standard stylometric features — MEDIUM confidence (academic source, validated against multiple stylometry papers)
- [TextDescriptives / textstat GitHub](https://github.com/textstat/textstat) — Confirmed readability metrics scope; does not include sentence rhythm or vocabulary register features — HIGH confidence
- Python stdlib documentation: `re`, `collections.Counter`, `statistics` — no external verification needed

---
*Stack research for: v1.2 Style Extraction and Script Generation (documentary video pipeline)*
*Researched: 2026-03-14*
