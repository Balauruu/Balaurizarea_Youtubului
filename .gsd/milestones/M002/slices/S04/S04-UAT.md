# S04: Remotion Animation Skill — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven for contract tests, live-runtime for CLI smoke tests)
- Why this mode is sufficient: Remotion rendering is proven via T01 smoke test; subprocess orchestration is contract-tested with mocks. Real end-to-end rendering with map-bearing shotlists deferred to S06.

## Preconditions

- Python 3.11+ with pytest installed
- Node.js 18+ with npm installed
- Working directory: `Channel-automation V3/`
- `pytest.ini` includes `.claude/skills/animation/scripts` in pythonpath
- Duplessis Orphans project exists at `projects/1. The Duplessis Orphans/`
- Remotion npm dependencies installed: `cd .claude/skills/animation/remotion && npm install`

## Smoke Test

Run `pytest tests/test_animation/ -v` — all 22 tests pass in <1s.

## Test Cases

### 1. CLI load command shows map shots section

1. Run: `PYTHONPATH=.claude/skills/animation/scripts python -m animation load "Duplessis Orphans"`
2. **Expected:** Exit code 0. Output contains `=== MAP_SHOTS ===`, `=== MANIFEST ===`, and `=== CHANNEL_DNA ===` sections. MAP_SHOTS section reports "(No map shots found)" since Duplessis Orphans shotlist has no map-type entries.

### 2. CLI status command shows coverage stats

1. Run: `PYTHONPATH=.claude/skills/animation/scripts python -m animation status "Duplessis Orphans"`
2. **Expected:** Exit code 0. Output shows "Map Shot Coverage for 'Duplessis Orphans'" header, "Map shots: 0", and "No map shots to render."

### 3. CLI load filters only map shots from mixed shotlist

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_load_prints_map_shots_section -v`
2. **Expected:** Test creates a shotlist with map + non-map entries, verifies only map entries appear in MAP_SHOTS section output.

### 4. CLI render calls Remotion subprocess with correct arguments

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_render_calls_subprocess_with_correct_args -v`
2. **Expected:** Test verifies subprocess.run called with `["npx", "remotion", "render", "src/index.ts", "MapComposition", <output_path>, "--props=<props_path>"]` and `cwd` pointing to the Remotion project directory. Only map-type shots rendered (2 out of 3 in fixture).

### 5. Manifest merge creates new manifest and appends assets

1. Run: `pytest tests/test_animation/test_manifest.py -v`
2. **Expected:** 7 tests pass: creates manifest.json when absent, appends new entries without overwriting existing, skips duplicate filenames, updates gap status from pending_generation to filled, writes valid JSON atomically, verifies required fields (filename, folder, description, mapped_shots, acquired_by), empty manifest has correct skeleton.

### 6. Remotion scaffold renders map animation

1. `cd .claude/skills/animation/remotion`
2. Run: `npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json`
3. **Expected:** Exit code 0. Renders 180/180 frames. Output file `out/test.mp4` exists.
4. Run: `ffprobe out/test.mp4` (if available)
5. **Expected:** 1920×1080, h264, 30fps, ~6 seconds duration.

### 7. Building block to variant mapping

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_render_merges_manifest -v`
2. **Expected:** Manifest entries include correct variant names derived from building_block strings via BUILDING_BLOCK_TO_VARIANT lookup. Entries have `acquired_by: "agent_animation"` and `folder: "animations"`.

### 8. Gap lifecycle update on render

1. Run: `pytest tests/test_animation/test_cli.py -k "gap" -v` (if test exists) or check test_manifest.py::TestManifestMerge::test_gap_status_update
2. **Expected:** Gaps with matching shot_id transition from `pending_generation` to `filled` status after render.

## Edge Cases

### Missing shotlist.json

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_load_missing_shotlist_exits_1 -v`
2. **Expected:** CLI exits with code 1 and prints error message about missing shotlist.

### No map shots in shotlist

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_load_no_map_shots_message -v`
2. **Expected:** CLI exits 0 with informational message — no error, just nothing to render.

### Subprocess render failure

1. Run: `pytest tests/test_animation/test_cli.py::test_cmd_render_subprocess_failure_exits_1 -v`
2. **Expected:** When Remotion subprocess returns non-zero exit, CLI exits 1 with error output including shot ID and stderr.

### Ambiguous project directory match

1. Run: `pytest tests/test_animation/test_cli.py::test_resolve_project_dir_ambiguous_raises -v`
2. **Expected:** SystemExit raised when multiple project directories match the topic substring.

## Failure Signals

- Any of the 22 pytest tests fail
- CLI commands return non-zero exit for valid inputs
- Remotion render produces 0-byte or corrupt .mp4
- Manifest merge overwrites existing entries or produces invalid JSON
- Map shot filter lets non-map entries through to rendering

## Requirements Proved By This UAT

- R007 (Remotion animated maps) — Contract-tested: CLI filters, subprocess invocation, manifest merge. Scaffold smoke render proves .mp4 output.
- R010 (Gap lifecycle tracking) — Gap status transitions verified in test_manifest.py::test_gap_status_update

## Not Proven By This UAT

- Real end-to-end rendering with a shotlist that actually contains map entries (deferred to S06)
- Visual quality of rendered animations (human review needed)
- Location extraction heuristics from visual_need text (agent enrichment expected)
- Multiple concurrent renders or large batches
- Custom font rendering in Remotion compositions

## Notes for Tester

- The Duplessis Orphans shotlist currently has 0 map shots, so `load` and `status` will always report no map shots. This is expected — the contract tests use synthetic fixtures with map entries.
- First Remotion render on a fresh machine downloads Chrome Headless Shell (~108MB). Subsequent renders are fast.
- The `render` subcommand is tested with mocked subprocess — running it for real requires the Remotion project's npm deps to be installed.
