# S05: Asset Manager Skill — Research

**Date:** 2026-03-15

## Summary

The Asset Manager is the final consolidation step in the asset pipeline. It reads shotlist.json (for shot ordering) and manifest.json + all type folders (for actual assets), then: (1) assigns sequential numeric prefixes (`001_`, `002_`, ...) based on first appearance in shotlist order, (2) renames files in-place within their type folders, (3) moves unmapped assets to `_pool/`, and (4) sets remaining `pending_generation` gaps to terminal `unfilled` status in manifest.json.

This is a low-risk, deterministic slice. All upstream contracts are well-defined — manifest.json schema is validated by `schema.py` (S02), shot IDs follow `S001-S999` format, and folder names are constrained to a known set. The core logic is file renaming + manifest rewriting with no external dependencies, no API calls, and no heuristic reasoning. The main subtlety is handling assets mapped to multiple shots (use first appearance number) and ensuring the renaming is atomic enough to not leave a half-numbered state on failure.

## Recommendation

Follow the established CLI pattern (D002) with `load`, `organize`, and `status` subcommands. The `organize` command does all the work: read shotlist.json for ordering → read manifest.json for asset-to-shot mappings → compute numbering → rename files → move unmatched to `_pool/` → update manifest with numbered filenames and terminal gap statuses → atomic write. Single Python module under `.claude/skills/asset-manager/scripts/asset_manager/`, mirroring the structure of all other skills.

Key design choice: rename files **in-place** within their type folders rather than copying to a flat directory. This preserves the folder-based organization the editor expects in DaVinci Resolve (archival_footage/, vectors/, animations/, etc.) while adding the sequential prefix for timeline assembly order.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|-------------------|------------|
| Manifest schema validation | `media_acquisition.schema.validate_manifest()` | Reuse the same validator to verify manifest before and after organize |
| Atomic manifest writes | `tempfile.mkstemp` + `os.replace` pattern (S02/S03/S04) | Proven Windows-safe pattern used by 3 existing skills |
| Project directory resolution | `resolve_project_dir()` pattern | Copy from existing skills (5th duplication — noted but not blocked) |

## Existing Code and Patterns

- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — Manifest validator. Import it directly for pre/post validation. VALID_FOLDERS, VALID_GAP_STATUSES, validate_manifest() are the key exports. **"unfilled" is already a valid gap status.**
- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py` — Reference for `cmd_status()` pattern showing gap counts, coverage %. The asset manager's status command should show numbered vs unnumbered counts.
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — Reference for `_merge_manifest()` and atomic write. The asset manager's manifest update is simpler (rename filenames, finalize gaps) but should follow the same temp+replace pattern.
- `.claude/skills/animation/scripts/animation/cli.py` — Reference for the CLI scaffold and `_get_project_root()` / `resolve_project_dir()` / `_ensure_utf8_stdout()` helpers that will be copied again.
- `Architecture.md` line 213 — **Authoritative spec:** "Assigns sequential prefixes based on order of appearance in shotlist.json (e.g., `001_compound_aerial.mp4`). Assets mapped to multiple shots get the number of their first appearance. Moves unmatched assets to `_pool/`. Sets remaining gaps to `unfilled`."
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — VALID_FOLDERS = `{"archival_photos", "archival_footage", "documents", "broll", "vectors", "animations"}`. These are the folders the asset manager scans.

## Constraints

- **Python stdlib only** — No external dependencies needed. pathlib, json, shutil, os, tempfile, argparse.
- **Windows file paths** — `os.replace()` works on Windows but the target must be unlinked first if it exists (existing pattern handles this).
- **Manifest schema must remain valid** — After organize, manifest.json must still pass `validate_manifest()`. The "filename" field in each asset entry must be updated to the numbered version.
- **No pre-styling** (R011) — Asset manager only renames and moves files, never modifies content.
- **Sequential IDs are dense** — shotlist.json IDs are S001, S002, ... with no gaps. The numbering prefix follows the same order: first shot's asset = 001_, second = 002_, etc.
- **One asset can map to multiple shots** — `mapped_shots` is an array. The asset gets the number of its earliest shot in the sequence.
- **Multiple assets can map to the same shot** — All get the same number prefix. Ties broken by... nothing. Just same prefix, different filenames.

## Common Pitfalls

- **Renaming order matters on Windows** — If `001_photo.jpg` already exists from a previous run, renaming another file to it will fail. Must handle re-runs gracefully (skip already-numbered files, or strip existing prefixes first).
- **Cross-folder numbering** — An asset in `archival_photos/` and another in `vectors/` can both map to S003. Both get prefix `003_`. The numbering is global across all folders, not per-folder.
- **Partial failure state** — If renaming fails mid-way (disk full, permissions), some files are renamed and some aren't. The manifest and filesystem are out of sync. Mitigation: compute all renames first, validate no conflicts, then execute. On failure, log which renames succeeded.
- **`_pool/` is a new directory** — Not in VALID_FOLDERS. The schema validator will reject assets with `folder: "_pool"`. Solution: unmatched assets are removed from the manifest `assets` array entirely (they're in `_pool/` for human use, not pipeline tracking). OR: add `_pool` to VALID_FOLDERS in schema. Better: remove from assets array.
- **Idempotency** — Running organize twice should produce the same result. Detect already-numbered files by checking if filename starts with `\d{3}_` pattern.

## Open Risks

- **`_pool/` folder semantics vs manifest** — Assets moved to `_pool/` should probably be removed from manifest.assets (they're no longer pipeline-tracked). Need to decide: keep them in manifest with `folder: "_pool"` (requires schema change) or remove them (cleaner, matches "_pool/ is for human use" intent). **Recommendation: remove from manifest — `_pool/` is outside the pipeline.**
- **`resolve_project_dir` duplication** — Now copied in 5 skills. Not a blocker but worth noting for future shared-utils extraction.
- **Re-run behavior** — If assets were already numbered from a previous run, the organize command needs to either: (a) strip existing prefixes and re-number, or (b) detect and skip. Option (a) is safer for correctness but must handle the `001_` prefix detection regex carefully.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| File organization | claude-office-skills/skills@file-organizer | Not relevant — generic file organizer, not asset pipeline |
| Python pathlib/shutil | n/a | stdlib, no skill needed |

No external skills needed — this is pure Python stdlib file manipulation.

## Sources

- Architecture.md lines 211-214 — Asset Manager spec (source: project repo)
- S02 Summary forward intelligence — manifest.json is central artifact, gap lifecycle documented (source: .gsd)
- S03 Summary forward intelligence — graphics output in assets/vectors/ with `acquired_by: "agent_graphics"` (source: .gsd)
- S04 Summary forward intelligence — animation output in assets/animations/ with `acquired_by: "agent_animation"` (source: .gsd)
- media_acquisition/schema.py — VALID_FOLDERS and VALID_GAP_STATUSES enums (source: codebase)
