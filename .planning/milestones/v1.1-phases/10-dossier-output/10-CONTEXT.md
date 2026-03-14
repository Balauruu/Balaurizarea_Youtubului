# Phase 10: Dossier Output - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI `cmd_write` subcommand that aggregates all scraped source files into a single synthesis input, then Claude's synthesis prompt produces a Writer-ready Research.md dossier and a separate media_urls.md. This is the final phase of the v1.1 Researcher milestone — the complete deliverable for Agent 1.3 (The Writer).

</domain>

<decisions>
## Implementation Decisions

### Synthesis workflow
- **Aggregator approach**: writer.py reads all src_*.json + pass2_*.json, merges into a single `synthesis_input.md` (url, domain, tier, content per source), writes to `.claude/scratch/researcher/`
- cmd_write prints "Synthesis input ready" and the output path — Claude then reads synthesis_input.md + the synthesis prompt and produces both final files
- **Claude writes markdown directly** — no intermediate JSON-to-markdown conversion step. The synthesis prompt instructs Claude to produce Research.md and media_urls.md as final markdown
- **Claude writes files directly** to `projects/N. [Title]/research/` using its file tools. cmd_write only handles aggregation. SKILL.md workflow tells Claude where to write
- **Word cap enforced by prompt** — synthesis_input.md includes ALL source content (20-50k words). The synthesis prompt instructs Claude to distill to ~2,000 words of curated scriptwriter-facing content. No code-level truncation

### Dossier section ordering (narrative-first)
- Section order: Subject Overview (~500 words) → Timeline → Key Figures → Narrative Hooks → Direct Quotes → Contradictions → Unanswered Questions → Correcting the Record → Source Credibility
- Writer reads top-to-bottom and gets the story arc before the analytical/sourcing sections

### Narrative hooks
- Labeled callout blocks in a dedicated section: `**HOOK: [Title]**` followed by 1-2 sentences explaining the story beat and why it's high-impact
- 3-5 hooks total — Writer scans and decides which to use as chapter anchors

### Direct quotes
- Blockquote callouts with attribution: `**QUOTE: [Label]**` followed by markdown blockquote, speaker name, role, and source URL/reference
- Writer can drop these directly into the script as narration beats

### Source credibility
- Compact table at the end of Research.md with columns: Source, Type (gov/academic/journalism/wiki/primary), Corroborated By, Access Quality (full/partial/paywall)
- Structured signals per DOSS-04 — no scalar scores

### Timeline
- 5-15 chronological entries, each with date, event description (1-2 sentences), and source attribution
- Enough for the Writer to build the narrative arc without overwhelming detail

### Key figures
- Name-role-relevance blocks: each figure gets name, role/title, relevance (1-2 sentences), and cross-reference to their quote in Direct Quotes section if applicable
- 3-8 figures depending on topic complexity

### Media URL extraction
- **Visual media only**: images, video clips, document scans (photos, archival footage, newspaper clippings, Wikimedia Commons, archive.org media). Exclude PDFs, academic papers, text-only web pages
- **Claude extracts during synthesis** — the synthesis prompt instructs Claude to identify and catalog media URLs while reading sources. Both Research.md and media_urls.md produced in one synthesis pass
- **Organized by asset type** matching Architecture's categories: Archival Footage, Archival Photos, Documents, B-Roll. Each entry has URL, description, and source domain

### Writer handoff
- Research.md stays **factual with narrative signals** — no 'recommended angle', no chapter suggestions, no tone guidance
- HOOK labels, QUOTE callouts, contradictions, unanswered questions, and correcting-the-record sections serve as implicit editorial signals
- Writer agent decides narrative structure, chapter breaks, and which hooks to use

### Claude's Discretion
- Exact synthesis prompt wording and structure
- How to handle sources with no useful content (empty/failed fetches)
- Correcting-the-record section format
- Unanswered questions section format
- Whether to include a brief metadata header (topic, date, source count)

</decisions>

<specifics>
## Specific Ideas

- Research.md should feel like a briefing document — dense but scannable
- The narrative hooks format was inspired by investigative journalism "nut graf" conventions — each hook is a story beat the Writer can anchor a chapter around
- media_urls.md groups match the Architecture.md asset folder structure (archival_footage/, archival_photos/, documents/, broll/) so Agent 2.1 can consume them directly

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli.py:cmd_survey()` and `cli.py:cmd_deepen()` — Pattern for output dir resolution, file I/O, summary table printing
- `url_builder.py:resolve_output_dir()` — Resolves `projects/N. [Title]/research/` or standalone scratch dir
- `url_builder.py:_get_project_root()` — Project root detection
- `_print_summary_table()` — Could be reused or adapted for write command summary
- `_strip_wiki_noise()` — Already applied during fetch; content in source files is pre-cleaned

### Established Patterns
- Context-loader CLI: code outputs structured data, Claude does all reasoning
- JSON per-source files with content field (src_*.json, pass2_*.json)
- source_manifest.json as lightweight index with evaluation annotations
- asyncio.run() not needed for cmd_write (no async crawl4ai calls)
- SKILL.md documents the full workflow including heuristic steps

### Integration Points
- **Input**: src_*.json + pass2_*.json files in output dir (written by cmd_survey and cmd_deepen)
- **Input**: source_manifest.json for metadata (topic, URLs, domains, tiers, evaluation notes)
- **Output**: synthesis_input.md to `.claude/scratch/researcher/` (aggregated source content)
- **Output**: Research.md and media_urls.md to `projects/N. [Title]/research/` (written by Claude, not code)
- **Prompt**: synthesis.md prompt file in `.claude/skills/researcher/prompts/` (new, instructs Claude's synthesis)
- **SKILL.md**: needs update with cmd_write step and full end-to-end workflow documentation

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-dossier-output*
*Context gathered: 2026-03-14*
