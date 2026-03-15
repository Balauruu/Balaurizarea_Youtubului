# S06: End-to-End Integration — Research

**Date:** 2026-03-15

## Summary

S06 is a verification and integration slice — no new features, just proving the 5 skills chain correctly on the Duplessis Orphans project. The pipeline is: Visual Orchestrator (generate shotlist.json from Script.md) → Media Acquisition (download assets, produce manifest.json) → Graphics Generator (fill gaps with code-gen/ComfyUI) → Animation (render map clips via Remotion) → Asset Manager (number, pool, finalize).

The current state has a critical gap: the existing `shotlist.json` in the Duplessis project is a **1-shot minimal stub** (created during S02 CLI testing), not a real shotlist. The real Script.md is 123 lines across 9+ chapters — the orchestrator needs to generate a proper 60-100 shot shotlist before anything downstream can be meaningfully tested. Additionally, `pytest.ini` is missing the visual-orchestrator pythonpath, causing 20 tests to fail on collection.

The integration test should be structured as a verification of each skill's CLI in sequence on real project data, not mocked. Some stages (ComfyUI, live API downloads) may need to be optional/skipped based on environment, but the pipeline's file contracts (shotlist.json → manifest.json → numbered assets) must be proven end-to-end.

## Recommendation

**Approach: Sequential live pipeline execution + contract verification tests.**

1. **Fix pytest.ini** — Add visual-orchestrator scripts to pythonpath (prerequisite, blocks 20 tests).
2. **Generate real shotlist.json** — Run visual-orchestrator on Duplessis Script.md (this is [HEURISTIC] — Claude generates, then validate subcommand verifies). The stub must be replaced with a real 60-100 shot shotlist.
3. **Run media acquisition** — Create search_plan.json (Claude plans queries from shotlist + media_urls.md), run acquire, verify manifest.json schema validity and gap identification. Some sources may need API keys (Pexels, Pixabay, Smithsonian) — use sources that don't need keys first (archive.org, Wikimedia, direct_url, YouTube CC).
4. **Run graphics generator** — Generate code-gen assets for animation-type shots. ComfyUI optional (--code-gen-only if server not running).
5. **Run animation** — Render map shots if any exist in the shotlist. Remotion node_modules already installed.
6. **Run asset manager** — Organize, number, pool, finalize. Verify manifest validity.
7. **Write integration test** — Pytest test that validates the final state: shotlist schema valid, manifest schema valid, numbered assets exist, gaps are terminal.

The integration test should be **post-hoc validation** of pipeline outputs (check files exist, schemas valid, numbering correct) — NOT a test that re-runs the pipeline (too slow, requires APIs).

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Shotlist validation | `visual_orchestrator.schema.validate_shotlist()` | Already proven by 10 tests |
| Manifest validation | `media_acquisition.schema.validate_manifest()` | Already proven by 29 tests |
| Project dir resolution | `resolve_project_dir()` in every skill | Consistent substring matching |

## Existing Code and Patterns

- `tests/test_researcher/test_integration.py` — Integration test pattern: uses `pytest.mark.integration` marker, checks for real dependencies, skips if unavailable. Follow this pattern for environment-dependent tests.
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — `validate_shotlist()` returns `list[str]` errors. Use for post-pipeline shotlist validation.
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — `validate_manifest()` returns `list[str]` errors. Use for manifest validation at every stage.
- `.claude/skills/media-acquisition/scripts/media_acquisition/acquire.py` — `load_search_plan()` validates search_plan.json entries (required fields: source, query, media_type, shot_ids, dest_folder, limit).
- `.claude/skills/asset-manager/scripts/asset_manager/cli.py` — `cmd_organize()` already validates manifest pre and post — just invoke it.
- `pytest.ini` — All skill pythonpaths listed here EXCEPT visual-orchestrator (bug to fix).

## Constraints

- **[HEURISTIC] stages can't be automated in tests** — shotlist generation and search plan creation require Claude reasoning. The integration test validates outputs, not the generation process.
- **API keys required for 3 sources** — Pexels (`PEXELS_API_KEY`), Pixabay (`PIXABAY_API_KEY`), Smithsonian (`SMITHSONIAN_API_KEY`). Other sources (archive.org, Wikimedia, direct_url, YouTube CC) work without keys.
- **ComfyUI optional** — Server may not be running. `--code-gen-only` flag exists for this case.
- **Remotion first render** — Downloads Chrome Headless Shell (~108MB) on first run. May be slow.
- **Windows paths** — All skills use `_ensure_utf8_stdout()` for Unicode handling. Already handled.
- **Cross-skill import** — Asset manager imports `validate_manifest` from `media_acquisition.schema`. PYTHONPATH must include both skill script dirs (already in pytest.ini).
- **Stub shotlist must be replaced** — The current 1-shot stub was for CLI testing. Visual orchestrator must generate a real one.

## Common Pitfalls

- **Running acquire without search_plan.json** — The acquire command reads a search_plan.json that Claude must author first. It's not auto-generated from the shotlist.
- **Expecting map shots in every shotlist** — The Duplessis Orphans topic may or may not produce map-type shots depending on the visual orchestrator's judgment. Animation skill exits 0 with "No map shots" message if none exist — this is valid.
- **Test isolation** — Integration tests that read real project files must not modify them destructively. Validate in-place, don't clean up the pipeline outputs (they're the proof).
- **pytest.ini pythonpath gap** — visual-orchestrator/scripts is missing. Must be added or 20 tests remain broken.
- **Shotlist ID sequencing** — Schema validator enforces sequential IDs (S001, S002, ...) with no gaps. Regeneration must produce a clean sequence.

## Open Risks

- **Live API rate limiting** — archive.org and Wikimedia may rate-limit during bulk acquisition. Per-source rate limiting exists but untested with real APIs.
- **Search result quality** — Media acquisition depends on Claude authoring good search queries in search_plan.json. Poor queries → poor assets → more gaps.
- **Shotlist quality** — Visual orchestrator's generated shotlist drives the entire pipeline. If it produces poor building block assignments or unreasonable shot counts, downstream skills will underperform.
- **Remotion render time** — Each map shot takes ~10-30s to render. Multiple map shots could make the pipeline slow.
- **ComfyUI model availability** — Z-image-turbo checkpoint must be loaded in ComfyUI. If not available, creative blocks will fail (mitigated by --code-gen-only).

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Pillow | — | none needed (stdlib-level usage) |
| Remotion | — | none found (custom scaffold already built) |
| ComfyUI | — | none found (custom REST client already built) |

No external skills needed — all integration is between skills already built in S01-S05.

## Sources

- S01-S05 summary files provided key integration contracts and forward intelligence
- Codebase exploration of all 5 skill CLIs confirmed function signatures and expected inputs/outputs
- pytest.ini inspection revealed missing visual-orchestrator pythonpath (20 broken tests)
- Duplessis Orphans project inspection confirmed stub shotlist.json (1 shot) vs real Script.md (123 lines, 9+ chapters)
