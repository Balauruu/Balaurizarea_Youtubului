---
estimated_steps: 6
estimated_files: 5
---

# T02: ComfyUI client + workflow templates + tests

**Slice:** S03 — Graphics Generator Skill
**Milestone:** M002

## Description

Add ComfyUI integration to the graphics generator: REST client, 4 workflow templates for creative building blocks, prompt builder, and `--code-gen-only` flag. This delivers R006 (ComfyUI creative assets) and retires the primary S03 risk (ComfyUI integration) at mock-test level. Live validation happens in S06.

## Steps

1. Create `comfyui/client.py`: `ComfyUIClient` class with `__init__(host, port)`, `queue_prompt(workflow_json) → prompt_id`, `poll_history(prompt_id) → status/outputs`, `download_image(filename, subfolder, output_dir) → Path`, `is_available() → bool`. Use `requests` for HTTP. Poll GET `/history/{prompt_id}` instead of websockets (avoids extra dependency). Handle `ConnectionError` / `Timeout` gracefully — raise `ComfyUIUnavailableError` with server address in message.
2. Create `comfyui/workflows.py`: 4 workflow template functions, each returning a ComfyUI API-format dict (nodes with class_type, inputs). Templates for: `concept_diagram`, `ritual_illustration`, `glitch_icon`, `data_moshing`. Each template accepts `prompt_text: str` and `resolution: tuple[int,int]` and fills in the Z-image-turbo checkpoint, KSampler params, and EmptyLatentImage at specified resolution. Prompt builder function: `build_prompt(shot: dict) → str` extracts narrative_context + visual_need + building_block to compose the generation prompt with style modifiers from the research classification table.
3. Wire ComfyUI blocks into renderer registry (`renderers/__init__.py`): Add entries for the 4 ComfyUI building blocks mapping to a `render_comfyui(shot, output_dir, client)` dispatcher that calls workflow template → queue → poll → download. The dispatcher is a thin wrapper.
4. Add `--code-gen-only` flag to `generate` subcommand: when set, skip ComfyUI blocks with stderr message listing which shots were skipped and why. When not set and ComfyUI unavailable, print clear error with server address and suggest `--code-gen-only`.
5. Write `tests/test_graphics_generator/test_comfyui.py`:
   - Mock `requests.post`/`requests.get` for queue and poll endpoints
   - Test successful queue → poll → download flow
   - Test connection failure raises `ComfyUIUnavailableError` with address
   - Test workflow template output structure (has required node types)
   - Test `build_prompt` extracts correct fields from shot dict
   - Test `--code-gen-only` flag skips ComfyUI blocks
6. Verify all tests pass together: `pytest tests/test_graphics_generator/ -v`

## Must-Haves

- [ ] ComfyUI REST client with queue/poll/download and graceful connection failure handling
- [ ] 4 workflow templates producing valid ComfyUI API-format dicts with 1920×1080 resolution
- [ ] Prompt builder composing generation prompts from shot context
- [ ] `--code-gen-only` flag with clear skip messages
- [ ] Connection failure message includes server address and suggests `--code-gen-only`
- [ ] All tests pass including mocked ComfyUI interactions

## Verification

- `pytest tests/test_graphics_generator/ -v` — all tests pass (T01 + T02 tests together)
- `python -m graphics_generator generate "Duplessis Orphans" --code-gen-only` — generates code-gen assets, skips ComfyUI with clear messages

## Observability Impact

- **New runtime signals:** ComfyUI client logs connection attempts, queue/poll cycle status, and download results to stderr. `--code-gen-only` flag produces explicit skip messages per shot with building block type and reason.
- **Inspection surface:** `python -m graphics_generator status "<topic>"` now distinguishes Pillow-routable vs ComfyUI-routable blocks (not just "skip"). Future agents can check ComfyUI availability via `ComfyUIClient(host, port).is_available()`.
- **Failure visibility:** `ComfyUIUnavailableError` includes server address (`host:port`) in message. CLI suggests `--code-gen-only` fallback when ComfyUI is unreachable. Poll timeout failures include prompt_id for debugging.

## Inputs

- T01 output: complete skill scaffold with CLI, renderers, manifest merge
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py` — registry to extend
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — generate command to add flag to
- S03 Research: ComfyUI building block classification table, prompt strategies

## Expected Output

- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py` — REST client
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py` — 4 templates + prompt builder
- `tests/test_graphics_generator/test_comfyui.py` — mocked integration tests
- Updated `renderers/__init__.py` with ComfyUI block routing
- Updated `cli.py` with `--code-gen-only` flag
