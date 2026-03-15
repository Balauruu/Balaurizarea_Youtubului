# S05: Asset Manager Skill — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: Asset manager is deterministic file operations (rename, move, manifest update) — all behavior is verifiable through filesystem state and JSON output without a running server

## Preconditions

- Python 3.10+ with pytest installed
- PYTHONPATH includes both `.claude/skills/asset-manager/scripts` and `.claude/skills/media-acquisition/scripts`
- No running services required
- For test cases 5-8: a real or mock project directory with shotlist.json and manifest.json in `assets/`

## Smoke Test

Run `pytest tests/test_asset_manager/ -v` — all 28 tests pass, confirming organize logic, CLI routing, and manifest validation work.

## Test Cases

### 1. Sequential numbering follows shotlist order

1. Create a shotlist with shots S001, S002, S003 in that order
2. Create a manifest with assets mapped to S002, S003, S001 respectively
3. Run `cmd_organize()`
4. **Expected:** Assets get prefixes 002_, 003_, 001_ respectively (matching their shot's position in the shotlist array, not the shot ID number)

### 2. Multi-shot asset gets earliest shot's number

1. Create shotlist: S001 (position 1), S005 (position 2), S010 (position 3)
2. Create asset mapped to `["S005", "S010"]`
3. Run `cmd_organize()`
4. **Expected:** Asset gets prefix `002_` (S005 is position 2, which is earlier than S010 at position 3)

### 3. Multiple assets on same shot share prefix

1. Create shotlist with S001
2. Create two assets both mapped to `["S001"]`
3. Run `cmd_organize()`
4. **Expected:** Both assets get prefix `001_`

### 4. Unmapped assets move to _pool/

1. Create manifest with one asset mapped to shots and one asset with `mapped_shots: []`
2. Run `cmd_organize()`
3. **Expected:** Unmapped asset file moved to `_pool/` directory, removed from manifest assets array. Mapped asset stays in its type folder with numeric prefix.

### 5. Gap finalization

1. Create manifest with gaps: `[{"shot_id": "S003", "status": "pending_generation"}, {"shot_id": "S004", "status": "filled"}]`
2. Run `cmd_organize()`
3. **Expected:** S003 gap status changes to `"unfilled"`. S004 gap status remains `"filled"` (already terminal).

### 6. Idempotent re-run

1. Run `cmd_organize()` on a project with assets
2. Note the resulting filenames and manifest state
3. Run `cmd_organize()` again on the same project
4. **Expected:** Filenames and manifest are identical after the second run. No duplicate prefixes (e.g., no `001_001_file.jpg`).

### 7. Manifest validity after organize

1. Run `cmd_organize()` on a project
2. Call `validate_manifest()` on the resulting manifest.json
3. **Expected:** Validation passes. Manifest has correct schema with assets array (no pooled items) and gaps array (no pending_generation status).

### 8. Status command output

1. Set up a project with 3 numbered assets, 1 pool asset, 2 filled gaps, 1 unfilled gap
2. Run `cmd_status()`
3. **Expected:** Output shows `Numbered: 3`, pool count `1`, gap breakdown with filled/unfilled counts

### 9. CLI subcommand routing

1. Run `python -m asset_manager load "TopicName"`
2. Run `python -m asset_manager organize "TopicName"`
3. Run `python -m asset_manager status "TopicName"`
4. **Expected:** Each routes to the correct handler without errors (may exit 1 if project doesn't exist, but routing works)

## Edge Cases

### Cross-folder numbering is global

1. Create assets in `archival_photos/` (mapped to S001) and `broll/` (mapped to S002)
2. Run `cmd_organize()`
3. **Expected:** `archival_photos/001_photo.jpg` and `broll/002_clip.mp4` — numbering is global across all type folders, not restarting at 001 per folder

### Asset mapped to shots not in shotlist

1. Create asset with `mapped_shots: ["S999"]` where S999 doesn't exist in shotlist.json
2. Run `cmd_organize()`
3. **Expected:** Asset treated as unmapped, moved to `_pool/`

### Empty manifest and shotlist

1. Create empty shotlist `[]` and manifest with empty assets `[]` and gaps `[]`
2. Run `cmd_organize()`
3. **Expected:** Completes successfully, manifest remains valid, no crashes

### Pool directory collision

1. Create `_pool/` with an existing file that has the same name as an asset being pooled
2. Run `cmd_organize()`
3. **Expected:** No file overwritten — collision handling prevents data loss

## Failure Signals

- Any test in `tests/test_asset_manager/` failing
- `cmd_organize()` producing duplicate numeric prefixes (e.g., two files both starting with `001_` in different folders mapping to different shots)
- Manifest failing `validate_manifest()` after organize
- Files with double prefixes after re-run (e.g., `001_001_file.jpg`)
- `pending_generation` gaps still present after organize
- Pooled assets still present in manifest assets array
- Non-zero exit from organize on valid input

## Requirements Proved By This UAT

- R008 — Test cases 1-3 and cross-folder edge case prove sequential numbering by shotlist order
- R009 — Test case 4 and shots-not-in-shotlist edge case prove _pool/ handling
- R010 — Test case 5 proves gap lifecycle finalization
- R011 — No test case modifies file content; organize only renames (prefix changes)

## Not Proven By This UAT

- Live pipeline integration (S06) — no real acquired/generated assets exist yet in Duplessis project
- ComfyUI or Remotion asset handling in practice — only tested with mock files
- Performance with large asset counts (100+ files) — tested with small sets only

## Notes for Tester

- The `status "Duplessis Orphans"` command will exit 1 until S02 media-acquisition has been run on that project to produce manifest.json. This is correct behavior, not a bug.
- All 28 pytest tests use tmp_dir fixtures with synthetic data — no real project files are modified during testing.
- The pre-existing `test_ddg_links_extraction` failure in crawl4ai tests is unrelated to this slice.
