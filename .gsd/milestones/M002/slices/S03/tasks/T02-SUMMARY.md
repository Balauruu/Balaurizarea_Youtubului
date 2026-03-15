---
id: T02
parent: S03
milestone: M002
provides:
  - ComfyUI REST client with queue/poll/download and graceful connection failure handling
  - 4 workflow templates (concept_diagram, ritual_illustration, glitch_icon, data_moshing) producing valid ComfyUI API-format dicts
  - Prompt builder composing generation prompts from shot context (narrative_context, visual_need, building_block)
  - --code-gen-only CLI flag with explicit skip messages per ComfyUI block
  - ComfyUI blocks wired into renderer registry alongside Pillow blocks
key_files:
  - .claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/cli.py
  - tests/test_graphics_generator/test_comfyui.py
key_decisions:
  - HTTP polling via GET /history/{prompt_id} instead of websockets — avoids extra dependency, sufficient for batch generation
  - Standard txt2img pipeline shared across all 4 workflow templates — differentiation is in prompt text and style modifiers, not node structure
  - ComfyUI import deferred inside cmd_generate function body — avoids import errors when ComfyUI package isn't needed (code-gen-only mode)
patterns_established:
  - "ComfyUI dispatcher: render_comfyui(shot, output_dir, client) → build_prompt → select template → queue → poll → download"
  - "Workflow templates return plain dicts with string node IDs — no ComfyUI SDK dependency"
  - "is_comfyui_block() predicate for routing decisions; COMFYUI_BLOCKS set in renderers/__init__.py"
observability_surfaces:
  - ComfyUI connection status logged to stderr during generate (available/unavailable with address)
  - Per-shot skip messages include building block type and reason (--code-gen-only or server unavailable)
  - ComfyUIUnavailableError includes server address and suggests --code-gen-only fallback
  - status subcommand distinguishes Pillow vs ComfyUI routing per building block
duration: 25min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: ComfyUI client + workflow templates + tests

**Added ComfyUI REST client, 4 workflow templates, prompt builder, --code-gen-only flag, and 35 tests — all 69 graphics generator tests pass.**

## What Happened

Built the ComfyUI integration layer in three modules:

**client.py** — `ComfyUIClient` with `queue_prompt()`, `poll_history()`, `download_image()`, and `is_available()`. All connection failures raise `ComfyUIUnavailableError` with the server address and actionable suggestion. Uses `requests` for HTTP, polling GET `/history/{prompt_id}` instead of websockets.

**workflows.py** — 4 template functions (`concept_diagram`, `ritual_illustration`, `glitch_icon`, `data_moshing`) each returning a ComfyUI API-format dict with CheckpointLoaderSimple → EmptyLatentImage → CLIPTextEncode → KSampler → VAEDecode → SaveImage pipeline. All share a `_build_standard_workflow()` base with the Z-image-turbo checkpoint. `build_prompt()` composes prompts from shot `visual_need` + `narrative_context` + style modifiers per building block type.

**Registry + CLI wiring** — Extended `renderers/__init__.py` with `COMFYUI_BLOCKS` set, `is_comfyui_block()` predicate, and `render_comfyui()` dispatcher. Updated `cli.py` with `--code-gen-only` flag: when set, ComfyUI blocks are skipped with explicit messages; when not set and ComfyUI is unavailable, a warning with server address and `--code-gen-only` suggestion is printed. The `status` subcommand now distinguishes Pillow vs ComfyUI routing.

Also fixed `pytest.ini` to include graphics-generator scripts in pythonpath (was missing from T01).

## Verification

- `pytest tests/test_graphics_generator/ -v` — **69 passed** (34 T01 + 35 T02)
- T02 tests cover: client queue/poll/download success, connection failure errors with address, end-to-end queue→poll→download flow, all 4 workflow template structures, prompt builder field extraction, registry ComfyUI block registration, --code-gen-only skip behavior, ComfyUI-unavailable warning
- `python -m graphics_generator status "Duplessis Orphans"` — exits 0 (no animation shots in current project shotlist)
- `python -m graphics_generator generate "Duplessis Orphans" --code-gen-only` — exits 0 with "No animation shots" message

### Slice-Level Verification Status
- ✅ `pytest tests/test_graphics_generator/ -v` — 69 passed
- ✅ `python -m graphics_generator status "Duplessis Orphans"` — exits 0

## Diagnostics

- `ComfyUIClient(host, port).is_available()` — programmatic ComfyUI reachability check
- Generate stderr shows per-shot progress: queuing, polling, download, skip reasons
- `ComfyUIUnavailableError` message always includes `host:port` and suggests `--code-gen-only`
- `status` subcommand shows per-building-block routing (Pillow / ComfyUI / unknown)

## Deviations

- Added `graphics-generator/scripts` to `pytest.ini` pythonpath — was missing, required for tests to run via pytest (T01 likely used explicit PYTHONPATH)
- Manifest merge now uses `entry.get("source", "code_gen")` to distinguish ComfyUI vs Pillow source in manifest entries

## Known Issues

- Current Duplessis Orphans shotlist has no `shotlist_type: animation` shots — live CLI verification limited to "no animation shots" path. Full end-to-end with real animation shots deferred to S06.

## Files Created/Modified

- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/__init__.py` — package init
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py` — REST client with queue/poll/download
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py` — 4 workflow templates + prompt builder
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py` — extended with COMFYUI_BLOCKS, is_comfyui_block(), render_comfyui() dispatcher
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — added --code-gen-only flag, ComfyUI routing in generate
- `tests/test_graphics_generator/test_comfyui.py` — 35 tests for client, workflows, prompt builder, registry, CLI flag
- `pytest.ini` — added graphics-generator scripts to pythonpath
- `.gsd/milestones/M002/slices/S03/tasks/T02-PLAN.md` — added Observability Impact section
