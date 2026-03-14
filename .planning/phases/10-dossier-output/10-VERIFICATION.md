---
phase: 10-dossier-output
verified: 2026-03-14T00:00:00Z
status: passed
score: 13/13 must-haves verified
---

# Phase 10: Dossier Output Verification Report

**Phase Goal:** Aggregate scraped sources into synthesis_input.md, provide a synthesis prompt, and produce a structured Research.md dossier plus media_urls.md — completing the researcher skill's write pass.
**Verified:** 2026-03-14
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | cmd_write aggregates all src_*.json and pass2_*.json into synthesis_input.md | VERIFIED | `writer.py:load_source_files` globs both patterns; `cmd_write` in `cli.py:534` calls it; `synthesis_input.md` present in project research dir |
| 2 | synthesis_input.md includes source URL, domain, tier, word count, and full content per source | VERIFIED | `build_synthesis_input` in `writer.py:128-146` writes these fields per source section |
| 3 | Failed/empty sources listed as skipped at the top, not silently dropped | VERIFIED | `writer.py:99-107` emits "## Skipped/failed sources" section for non-ok or empty sources |
| 4 | cmd_write works when no pass2_*.json files exist (Pass 1 only) | VERIFIED | `test_load_source_files_no_pass2` passes; function returns `(pass1, [])` without error |
| 5 | synthesis_input.md includes the output directory path | VERIFIED | `writer.py:96` emits `**Output directory:** {output_dir}`; test `test_build_synthesis_input_includes_output_dir` passes |
| 6 | synthesis prompt defines all 9 Research.md sections in correct narrative-first order | VERIFIED | `synthesis.md` defines Sections 1-9 in order: Subject Overview, Timeline, Key Figures, Narrative Hooks, Direct Quotes, Contradictions, Unanswered Questions, Correcting the Record, Source Credibility |
| 7 | Synthesis prompt enforces ~2,000 word cap on body text | VERIFIED | `synthesis.md:194-216` has explicit cap rules with counts/excludes list; "2,000" appears 3 times |
| 8 | Synthesis prompt defines exact HOOK and QUOTE callout formats | VERIFIED | `synthesis.md:87-119` defines both formats with examples; 3 HOOK: and 4 QUOTE: occurrences in prompt |
| 9 | Synthesis prompt defines source credibility table with structured signals (no scalar scores) | VERIFIED | `synthesis.md:171-188` defines table with Type/Corroborated By/Access Quality columns; explicitly forbids scalar scores |
| 10 | Synthesis prompt instructs media URL extraction grouped by asset type | VERIFIED | `synthesis.md:233-253` defines Archival Footage/Archival Photos/Documents/B-Roll grouping |
| 11 | SKILL.md documents complete end-to-end workflow including cmd_write and synthesis step | VERIFIED | SKILL.md:132-159 has "Workflow (Pass 3 — Write Dossier)" with cmd_write step and Claude synthesis step; no "planned" markers remain |
| 12 | cmd_write produces synthesis_input.md from real project source files | VERIFIED | `projects/1. The Duplessis Orphans.../research/synthesis_input.md` exists; sourced from 13 src_*.json + 2 pass2_*.json |
| 13 | Research.md and media_urls.md exist with correct schema in projects/N. [Title]/research/ | VERIFIED | Both files present; Research.md has all 9 sections with HOOK:/QUOTE: callouts; media_urls.md grouped by Archival Footage/Archival Photos/Documents/B-Roll |

**Score:** 13/13 truths verified

---

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `.claude/skills/researcher/scripts/researcher/writer.py` | VERIFIED | 166 lines; exports `load_source_files`, `build_synthesis_input`, `write_synthesis_input`; no stubs |
| `tests/test_researcher/test_writer.py` | VERIFIED | 222 lines (well above 60-line min); 10 tests; all pass |
| `.claude/skills/researcher/prompts/synthesis.md` | VERIFIED | 285 lines (well above 60-line min); contains "HOOK:"; all 9 sections defined |
| `.claude/skills/researcher/SKILL.md` | VERIFIED | Contains "cmd_write" (9+ matches); references `synthesis.md`; no "planned" markers |
| `projects/*/research/Research.md` | VERIFIED | Present at `projects/1. The Duplessis Orphans.../research/Research.md`; contains "HOOK:" callouts |
| `projects/*/research/media_urls.md` | VERIFIED | Present at same directory; contains "Archival" groupings |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli.py` | `writer.py` | `from researcher.writer import` | WIRED | `cli.py:27` imports all 3 writer functions; `cmd_write` at line 534 calls all 3 |
| `writer.py` | `url_builder.py` via `cli.py` | `resolve_output_dir` used in `cmd_write` | WIRED | `writer.py` does not import `url_builder` directly — `resolve_output_dir` is called in `cli.py:cmd_write` which passes the resolved `output_dir` to writer functions. This is correct separation of concerns: writer is stateless, cli handles path resolution. Plan 01 key_link is fulfilled through the calling context |
| `synthesis.md` | `projects/*/research/Research.md` | Claude reads prompt and produces dossier | WIRED | `Research.md` exists with all 9 sections; "Research.md" appears in synthesis prompt instructions |
| `SKILL.md` | `synthesis.md` | Workflow references prompt path | WIRED | `SKILL.md:151` references `@.claude/skills/researcher/prompts/synthesis.md`; `cli.py:cmd_write` also prints the prompt path |
| `cli.py` | `projects/*/research/synthesis_input.md` | cmd_write writes aggregated content | WIRED | `synthesis_input.md` found in research dir; `write_synthesis_input` in cli's cmd_write confirmed |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| DOSS-01 | 10-02, 10-03 | Research.md with subject overview, timeline, key figures | SATISFIED | Research.md Sections 1-3 present with ~500-word overview, 15-entry timeline, 6 figures |
| DOSS-02 | 10-02, 10-03 | Research.md includes contradictions section | SATISFIED | Research.md Section 6 has 3 contradiction entries naming conflicting sources |
| DOSS-03 | 10-02, 10-03 | Research.md includes unanswered questions | SATISFIED | Research.md Section 7 has 6 numbered open questions |
| DOSS-04 | 10-02, 10-03 | Structured credibility signals, no scalar scores | SATISFIED | Source Credibility table uses Type/Corroborated By/Access Quality; synthesis.md explicitly forbids scalar scores |
| DOSS-05 | 10-02, 10-03 | Research.md capped at ~2,000 words | SATISFIED | synthesis.md enforces cap; Research.md body text is within target range |
| DOSS-06 | 10-02, 10-03 | Direct quotes as labeled callouts | SATISFIED | Research.md Section 5 has 5 QUOTE: labeled callouts with blockquote format and attribution |
| DOSS-07 | 10-02, 10-03 | 3-5 narrative hooks explicitly labeled | SATISFIED | Research.md Section 4 has exactly 5 HOOK: labeled entries |
| DOSS-08 | 10-02, 10-03 | Correcting-the-record section flagging mainstream vs primary divergences | SATISFIED | Research.md Section 8 has 3 mainstream/primary divergence entries |
| DOSS-09 | 10-01, 10-03 | Research.md written to `projects/N. [Title]/research/` | SATISFIED | File exists at `projects/1. The Duplessis Orphans.../research/Research.md` |
| MEDIA-01 | 10-02, 10-03 | Separate media_urls.md cataloging media URLs | SATISFIED | `media_urls.md` exists as a separate file in the research directory |
| MEDIA-02 | 10-02, 10-03 | media_urls.md includes URL, description, source type | SATISFIED | Each entry has `**URL:**`, `**Description:**`, `**Source:**` fields |

All 11 requirement IDs accounted for. No orphaned requirements detected.

---

### Anti-Patterns Found

None. No TODO/FIXME/PLACEHOLDER comments, no empty return stubs, no silent exception swallowing in core logic detected in `writer.py`, `cli.py` (cmd_write section), `synthesis.md`, or `SKILL.md`.

Note: `writer.py:37,44` has bare `except Exception` with a `pass` for JSON parse failures in `load_source_files`. This is intentional (malformed files are skipped gracefully) and documented in the docstring as "Files that fail to parse are silently skipped." This is a policy decision, not a stub. Severity: Info only.

---

### Human Verification Required

One item was already human-verified during Plan 03 execution:

**Research.md and media_urls.md content quality** — Human reviewed both files during Plan 03 Task 2 (blocking checkpoint) and approved. The approval is recorded in `10-03-SUMMARY.md`: "Human approved Research.md and media_urls.md output quality — milestone v1.1 confirmed production-ready."

No additional human verification required.

---

### Test Suite Results

- `tests/test_researcher/test_writer.py`: **10/10 passed** (verified by running `python -m pytest`)
- Full researcher suite (excluding integration): **64/64 passed**
- CLI `--help` lists `write` subcommand confirmed: `{survey, deepen, write}`

---

### Summary

Phase 10 fully achieves its goal. The write pass of the researcher skill is complete:

1. `writer.py` provides deterministic aggregation — reads all scraped source JSON files, formats them into `synthesis_input.md` with a skipped/failed section, and writes the file to the project output directory.
2. `cmd_write` in `cli.py` wires the aggregation into the CLI, following established patterns from `cmd_survey` and `cmd_deepen`.
3. `synthesis.md` is a complete 285-line synthesis prompt encoding all 9 Research.md sections, callout formats, word cap rules, and media extraction grouping.
4. `SKILL.md` documents the full 3-pass workflow with no incomplete markers.
5. End-to-end integration was run on a real project (The Duplessis Orphans) producing Research.md and media_urls.md that were human-approved.

All 11 requirements (DOSS-01 through DOSS-09, MEDIA-01, MEDIA-02) are satisfied. The Researcher skill (v1.1) milestone is complete and production-ready.

---

_Verified: 2026-03-14_
_Verifier: Claude (gsd-verifier)_
