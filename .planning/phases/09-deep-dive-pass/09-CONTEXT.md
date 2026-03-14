# Phase 9: Deep-Dive Pass (Pass 2) - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI `cmd_deepen` subcommand that reads Claude's annotated source manifest and fetches targeted primary sources (deep_dive_urls extracted during Pass 1 evaluation), completing the two-pass research architecture. No evaluation or synthesis happens here — content is stored raw for Phase 10.

</domain>

<decisions>
## Implementation Decisions

### URL source selection
- Fetch deep_dive_urls ONLY from sources with verdict "recommended" — skip verdicts are ignored
- Deduplicate URLs across sources — if the same URL appears in multiple sources' deep_dive_urls, fetch once
- Apply same Tier 3 filtering to deep_dive_urls — skip social media domains even if extracted by evaluation
- If no deep_dive_urls exist in the manifest (or none after filtering), print "No deep-dive URLs found in manifest — skip Pass 2 or re-evaluate sources" and exit cleanly

### Output file format
- JSON format, same schema as Pass 1 (index, url, domain, tier, word_count, fetch_status, error, content)
- Separate `pass2_` prefix numbering: pass2_001.json, pass2_002.json, etc.
- Update existing source_manifest.json with Pass 2 entries under a `pass2_sources` key — single manifest file for Phase 10

### Post-fetch behavior
- No evaluation step after fetching — raw storage only
- Print summary table in same format as Pass 1 (#, Domain, Tier, Words, Status)
- After completion, SKILL.md instructs Claude to print "Both passes complete. Run cmd_write to generate Research.md." — clean handoff to Phase 10

### Budget & dedup guard
- Hard cap: total source files across both passes ≤ 15
- cmd_deepen counts existing src_*.json files in output dir; Pass 2 budget = 15 - Pass 1 count
- Skip URLs already fetched in Pass 1 (match against URLs in existing src_*.json files)
- When deep_dive_urls exceed remaining budget, process in source order (manifest order) — higher-ranked Pass 1 sources' URLs get priority
- URLs beyond budget are logged as skipped with reason

### Claude's Discretion
- Noise stripping approach for primary source content (reuse _strip_wiki_noise or extend for .gov/.archive pages)
- Exact error messages and logging format
- Whether to reuse _print_summary_table from cmd_survey or create a shared utility

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The design follows Pass 1 patterns closely.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli.py:cmd_survey()` — Pattern for fetch loop, file writing, summary table, manifest update. cmd_deepen follows the same structure.
- `cli.py:_print_summary_table()` — Reusable for Pass 2 summary output (same columns)
- `cli.py:_strip_wiki_noise()` — Content cleaning, may need extension for non-Wikipedia primary sources
- `cli.py:_get_tier_from_url()` — Tier lookup, reusable as-is
- `fetcher.py:fetch_with_retry()` — crawl4ai wrapper, no changes needed
- `tiers.py:classify_domain()` — Tier 3 filtering for deep_dive_urls
- `url_builder.py:resolve_output_dir()` — Output directory resolution, reusable

### Established Patterns
- Context-loader CLI: code fetches and stores, Claude does reasoning (no evaluation step in Phase 9)
- JSON per-source files with lightweight manifest index
- Scratch pad convention: `.claude/scratch/researcher/` for standalone mode
- asyncio.run() for async crawl4ai calls within sync CLI commands

### Integration Points
- `source_manifest.json` — cmd_deepen reads `sources[].deep_dive_urls` and `sources[].verdict` from Pass 1 evaluation; writes `pass2_sources` key back
- `pass2_*.json` files — Phase 10 synthesis reads these alongside src_*.json for the full research corpus
- SKILL.md workflow — needs update to add Pass 2 step (cmd_deepen) and handoff instruction to Phase 10

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-deep-dive-pass*
*Context gathered: 2026-03-14*
