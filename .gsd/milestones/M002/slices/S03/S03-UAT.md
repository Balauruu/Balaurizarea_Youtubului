# S03: Graphics Generator Skill — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven for Pillow renderers, mocked for ComfyUI)
- Why this mode is sufficient: Pillow renderers produce real PNGs verifiable on disk. ComfyUI requires a running server — mocked tests prove the integration contract, live validation deferred to S06.

## Preconditions

- Python 3.13+ with Pillow installed (`pip install Pillow`)
- Working directory: `Channel-automation V3/`
- Duplessis Orphans project exists at `projects/1. The Duplessis Orphans/` with `shotlist.json`
- PYTHONPATH includes `.claude/skills/graphics-generator/scripts` (or use `sys.path.insert`)

## Smoke Test

Run `pytest tests/test_graphics_generator/ -v` — expect 69 passed, 0 failed. If this passes, the skill is fundamentally working.

## Test Cases

### 1. CLI load prints structured context

1. Run: `python -c "import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts'); from graphics_generator.cli import cmd_load; cmd_load('Duplessis Orphans')"`
2. **Expected:** Output contains `=== Shotlist ===` section with JSON, `=== Channel DNA ===` section, and `=== Generation Prompt ===` section with file path. Exit code 0.

### 2. CLI load fails on missing shotlist

1. Run: `python -c "import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts'); from graphics_generator.cli import cmd_load; cmd_load('Nonexistent Project')"`
2. **Expected:** Prints error about project not found or shotlist missing. Exit code 1.

### 3. CLI status reports coverage

1. Run: `python -c "import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts'); from graphics_generator.cli import cmd_status; cmd_status('Duplessis Orphans')"`
2. **Expected:** Output reports "No animation shots in shotlist" (since current shotlist has only archival_video type). Exit code 0.

### 4. Silhouette renderer produces valid PNG

1. Run in Python:
   ```python
   import sys, tempfile; sys.path.insert(0, '.claude/skills/graphics-generator/scripts')
   from pathlib import Path
   from graphics_generator.renderers.silhouette import render
   shot = {"id": "S042", "visual_need": "Dark figure standing", "building_block": "Silhouette Figure"}
   out = render(shot, Path(tempfile.mkdtemp()))
   from PIL import Image; img = Image.open(out)
   print(f"Size: {img.size}, Mode: {img.mode}, File: {out.name}")
   ```
2. **Expected:** Size: (1920, 1080), Mode: RGBA, filename contains "S042"

### 5. All 7 renderers produce correct dimensions

1. Run `pytest tests/test_graphics_generator/test_renderers.py -v -k "produces_valid_png"`
2. **Expected:** 7 tests pass, each confirming 1920×1080 RGBA PNG output

### 6. Renderer registry routes all code-gen blocks

1. Run in Python:
   ```python
   import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts')
   from graphics_generator.renderers import RENDERER_REGISTRY
   expected = ["Silhouette Figure", "Symbolic Icon", "Abstract Texture", "Glitch Stinger",
                "Static Noise / Corruption", "Static Noise", "Retro Code Screen", "Character Profile Card"]
   for name in expected:
       assert name in RENDERER_REGISTRY, f"Missing: {name}"
   print(f"All {len(expected)} blocks registered")
   ```
2. **Expected:** All 8 entries (7 unique + 1 alias) registered, no assertion errors

### 7. ComfyUI blocks identified correctly

1. Run in Python:
   ```python
   import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts')
   from graphics_generator.renderers import is_comfyui_block, COMFYUI_BLOCKS
   assert is_comfyui_block("Concept Diagram")
   assert is_comfyui_block("Ritual Illustration")
   assert is_comfyui_block("Glitch Icon")
   assert is_comfyui_block("Data Moshing")
   assert not is_comfyui_block("Silhouette Figure")
   print(f"ComfyUI blocks: {COMFYUI_BLOCKS}")
   ```
2. **Expected:** All 4 ComfyUI blocks identified, Pillow blocks not flagged as ComfyUI

### 8. Manifest merge appends without overwriting

1. Run `pytest tests/test_graphics_generator/test_manifest.py::TestManifestMerge::test_appends_without_overwriting -v`
2. **Expected:** Test passes — existing manifest assets preserved when new entries added

### 9. Manifest merge updates gap status

1. Run `pytest tests/test_graphics_generator/test_manifest.py::TestManifestMerge::test_gap_status_update -v`
2. **Expected:** Test passes — gaps matching generated shots change from pending_generation to filled

### 10. ComfyUI client handles connection failure

1. Run `pytest tests/test_graphics_generator/test_comfyui.py::TestComfyUIClient::test_queue_prompt_connection_error -v`
2. **Expected:** Test passes — ComfyUIUnavailableError raised with server address in message

### 11. --code-gen-only flag skips ComfyUI blocks

1. Run `pytest tests/test_graphics_generator/test_comfyui.py::TestCodeGenOnlyFlag -v`
2. **Expected:** 3 tests pass — ComfyUI blocks skipped with message, flag present in argparse, unavailable warning shown

### 12. Workflow templates produce valid ComfyUI API format

1. Run `pytest tests/test_graphics_generator/test_comfyui.py::TestWorkflowTemplates -v`
2. **Expected:** 14 tests pass — all 4 templates have required nodes, correct resolution, prompt text

## Edge Cases

### Empty shotlist (no animation shots)

1. Create a shotlist with only `archival_video` type shots (current Duplessis Orphans state)
2. Run generate command
3. **Expected:** "No animation shots in shotlist" message, exit code 0, no files created

### Duplicate filename in manifest merge

1. Run `pytest tests/test_graphics_generator/test_manifest.py::TestManifestMerge::test_skips_duplicate_filenames -v`
2. **Expected:** Test passes — duplicate filenames silently skipped, no duplicate entries in output

### Missing channel.md in project

1. Run `pytest tests/test_graphics_generator/test_cli.py::test_cmd_load_prints_channel_dna -v`
2. **Expected:** Test passes — channel DNA section still printed (from context/channel/ fallback)

## Failure Signals

- Any test in `pytest tests/test_graphics_generator/ -v` failing (currently 69/69 pass)
- Renderer producing non-PNG output or wrong dimensions (should be 1920×1080 RGBA)
- Manifest merge corrupting existing entries or leaving gaps as pending_generation after fill
- CLI commands exiting with non-zero when they should succeed
- ComfyUI connection errors not including server address in message

## Requirements Proved By This UAT

- R005 (Code-generated flat graphics) — Tests 4-6 prove 7 renderers produce correct PNGs with VISUAL_STYLE_GUIDE-faithful effects
- R006 (ComfyUI creative asset generation) — Tests 7, 10-12 prove client contract, workflow templates, and fallback mode (mocked)
- R010 (Gap lifecycle tracking) — Test 9 proves manifest merge updates gap status correctly

## Not Proven By This UAT

- Live ComfyUI server rendering — requires running ComfyUI with Z-image-turbo model (deferred to S06)
- End-to-end generate on a shotlist with actual animation shots — current Duplessis Orphans shotlist has none (deferred to S06)
- Visual quality of generated assets — requires human review of actual PNGs (deferred to S06)

## Notes for Tester

- The Duplessis Orphans shotlist currently has only 1 shot (archival_video type). To test the full generate path with Pillow renderers, you'd need a shotlist with `shotlist_type: animation` shots. The unit tests create synthetic shots for this purpose.
- ComfyUI tests are fully mocked — no ComfyUI server needed. Live ComfyUI testing happens in S06.
- The `python -m graphics_generator` invocation requires PYTHONPATH. The inline `sys.path.insert` approach in test cases above avoids this.
