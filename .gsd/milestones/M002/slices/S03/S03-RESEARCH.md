# S03: Graphics Generator Skill — Research

**Date:** 2026-03-15

## Summary

S03 must generate visual assets for all 11 building blocks with `shotlist_type: animation` from the VISUAL_STYLE_GUIDE. These split cleanly into two production modes per D007: code-gen (Pillow) for constrained flat graphics and ComfyUI for creative/artistic assets. The skill follows the established context-loader CLI pattern (D002) with `load`, `generate`, and `status` subcommands.

The primary risk is the ComfyUI integration — the local server at 127.0.0.1:8188 uses a REST API for prompt queuing and websocket for completion tracking. The Z-image-turbo model's ability to produce specific visual styles (neon line art, cultural iconography) is untested. Pillow code-gen is lower risk: the building blocks have highly specific production specs (flat black silhouettes on red backgrounds, monospaced text on black, random noise patterns) that translate directly to programmatic rendering.

Manifest integration is straightforward: S03 reads shotlist.json to find animation-type shots, generates assets into `assets/vectors/`, and updates `manifest.json` with new asset entries (`acquired_by: "agent_graphics"`). S02's gap identification deliberately skips animation/map types — S03 doesn't read gaps, it creates assets for all animation shots directly from the shotlist.

## Recommendation

Build the graphics generator skill in two tasks:

**T01 — CLI scaffold + Pillow code-gen engine:** Context-loader CLI with `load` (reads shotlist.json + manifest.json + channel.md), `generate` (runs code-gen for all animation shots), and `status` (shows generation coverage). Implement Pillow renderers for the 7 code-gen building blocks. Each renderer is a pure function: `(shot_dict, output_dir, resolution) → Path`. Schema tests + renderer output tests.

**T02 — ComfyUI client + integration:** REST client for ComfyUI prompt queue API (POST /prompt, GET /history, websocket completion). Implement workflow templates for the 4 ComfyUI building blocks. Prompt builder that takes shot context (narrative_context, visual_need, building_block_variant) and produces workflow JSON. Tests with mocked ComfyUI responses.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| HTTP downloads/uploads | `requests` (already installed) | ComfyUI REST API communication |
| Image generation | `Pillow 11.3.0` (already installed) | Code-gen building blocks — shapes, text, noise, gradients |
| WebSocket for ComfyUI | `websockets` or `websocket-client` | Track ComfyUI queue completion |
| Manifest schema validation | `media_acquisition.schema.validate_manifest()` | Already built in S02, reuse for validation |
| Project dir resolution | `_get_project_root()` / `resolve_project_dir()` | Duplicated pattern from writer → visual-orchestrator → media-acquisition |

## Existing Code and Patterns

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — Context-loader pattern to follow. `resolve_project_dir()` finds project by substring match. S03 CLI will be identical structure.
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — shotlist.json validator. S03 reads shotlist and filters `shotlist_type == "animation"`. Uses `VALID_SHOTLIST_TYPES`, `REQUIRED_SHOT_FIELDS`.
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — manifest.json validator. S03 must produce manifest entries conforming to: `filename`, `folder` ("vectors"), `source` ("code_gen" or "comfyui"), `source_url` ("local://..."), `description`, `license` ("generated"), `mapped_shots` (array with shot ID), `acquired_by` ("agent_graphics").
- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py` — `cmd_acquire` shows pattern for creating asset subdirectories and writing manifest.json atomically.
- `tests/test_visual_orchestrator/test_schema.py` — Test pattern: shared fixtures, each test modifies minimally to trigger one error class.
- `_ensure_utf8_stdout()` — Copy from any existing skill; required on Windows for Unicode in context files.

## Building Block → Production Mode Classification

### Code-Gen (Pillow) — 7 blocks

| Building Block | Why Code-Gen | Key Production Spec |
|---|---|---|
| **Silhouette Figure** | Flat black shapes on solid red/black — no artistic nuance | Deep red gradient bg, black silhouette shape, optional white label text, fog overlay |
| **Symbolic Icon** | Bold flat icon on crimson with scanlines — geometric | Crimson bg with scanline texture, centered icon silhouette, 2-5s stinger |
| **Abstract Texture** | Non-representational dark streaks — random generation | Crimson bg, random dark vertical streaks/drips, heavy scanline overlay |
| **Glitch Stinger** | Digital corruption — pure noise/geometric patterns | Black bg, vertical red bars, horizontal scanline distortion, RGB split |
| **Static Noise / Corruption** | TV static — literally random noise | Full-frame noise field with faint dark silhouette shape |
| **Retro Code Screen** | Monospaced text on black — trivial code-gen | Black bg, white monospaced text, phosphor glow effect, scanlines |
| **Character Profile Card** | Layout-driven — stacked photos with text labels | Dark bg, vertical magenta bars, placeholder photo regions with black redaction bars, teal text |

### ComfyUI — 4 blocks

| Building Block | Why ComfyUI | Prompt Strategy |
|---|---|---|
| **Concept Diagram** | Profile heads with internal layers, medical imagery — needs artistic interpretation | "dark background, profile head silhouette with concentric internal shapes, subtle glow, concept diagram, flat graphic style" + variant-specific modifiers |
| **Ritual Illustration** | Stylized neon line art of cultural/religious scenes — artistic | "black background, stylized flat neon line art, [color] glow, ritual scene, abstract symbolic" + cultural variant |
| **Glitch Icon** | Organic serpentine forms with chromatic aberration — needs generation | "deep blue-purple gradient, stylized icon, heavy chromatic aberration, RGB split, dot-matrix LED" |
| **Data Moshing Montage** | Collage of distorted video fragments — needs source material to corrupt | "black background, collage distorted video fragments, horizontal red scanline bars, digital corruption, datamoshing aesthetic" |

## Constraints

- **Python only** for all scripts (per project coding standard)
- **Pillow 11.3.0** already installed — no pycairo available, so all vector work uses Pillow (PIL.ImageDraw for shapes, PIL.ImageFilter for effects, PIL.ImageFont for text)
- **ComfyUI at 127.0.0.1:8188** — not always running; client must handle connection failures gracefully with clear error messages
- **Z-image-turbo model** — fast generation but quality/style adherence uncertain for specific visual aesthetics
- **Assets go to `assets/vectors/`** — the manifest folder for generated graphics (per S02 schema: valid folder)
- **1920×1080 default resolution** — documentary footage standard; all generated images should match
- **Raw delivery (D008)** — no film grain, scanlines, or post-effects on delivered assets. Wait — the production specs describe scanlines, grain, CRT effects as *part of the building block definition*. These are generative elements, not post-production. The building block IS a scanlined graphic. D008 means no *additional* post-styling beyond what the building block spec calls for.
- **Windows filesystem** — `_ensure_utf8_stdout()` pattern required; path handling must work on Windows
- **Font availability** — Windows has arial.ttf, but building blocks call for "bold sans-serif", "condensed stencil-style", "monospaced" — use `arial.ttf`/`arialbd.ttf`/`consola.ttf` (Consolas) as defaults, with fallback to Pillow default font

## Architecture

### CLI Subcommands

```
python -m graphics_generator load "<topic>"     # Aggregate context for Claude
python -m graphics_generator generate "<topic>"  # Run code-gen + ComfyUI pipeline
python -m graphics_generator status "<topic>"    # Show generation coverage
```

### Module Structure

```
.claude/skills/graphics-generator/
├── CONTEXT.md
├── SKILL.md
├── prompts/
│   └── generation.md            # Prompt for Claude to plan generation params
└── scripts/
    └── graphics_generator/
        ├── __init__.py
        ├── __main__.py
        ├── cli.py                # Context-loader CLI (load/generate/status)
        ├── renderers/
        │   ├── __init__.py       # Registry: building_block → renderer function
        │   ├── silhouette.py     # Silhouette Figure renderer
        │   ├── icon.py           # Symbolic Icon renderer
        │   ├── texture.py        # Abstract Texture renderer
        │   ├── glitch.py         # Glitch Stinger renderer
        │   ├── noise.py          # Static Noise renderer
        │   ├── code_screen.py    # Retro Code Screen renderer
        │   └── profile_card.py   # Character Profile Card renderer
        └── comfyui/
            ├── __init__.py
            ├── client.py         # REST + websocket client for ComfyUI
            └── workflows.py      # Workflow templates per building block
```

### Generation Flow

1. CLI reads shotlist.json, filters `shotlist_type == "animation"` shots
2. For each shot, looks up `building_block` → routes to code-gen renderer or ComfyUI
3. Code-gen: calls renderer function, saves PNG to `assets/vectors/`
4. ComfyUI: builds workflow JSON from template + shot context, queues via REST, downloads result
5. After all generation, reads existing `manifest.json` (if any), merges new asset entries
6. Writes updated manifest.json with atomic temp+rename

### Manifest Integration

Each generated asset gets a manifest entry:
```json
{
  "filename": "S042_silhouette_figure.png",
  "folder": "vectors",
  "source": "code_gen",
  "source_url": "local://graphics_generator/silhouette",
  "description": "Silhouette of faith healer on deep red background",
  "license": "generated",
  "mapped_shots": ["S042"],
  "acquired_by": "agent_graphics"
}
```

## Common Pitfalls

- **Scanlines as post-production vs generative** — The VISUAL_STYLE_GUIDE describes scanlines, grain, CRT effects as PART of the building block visual identity. These must be rendered INTO the asset, not applied as post-processing. D008 ("raw assets") means no *additional* styling beyond the block spec — it does NOT mean plain clean images.
- **ComfyUI not running** — The client must detect connection failure immediately and report which building blocks require ComfyUI, rather than silently skipping. Use `generate` with `--code-gen-only` flag for offline use.
- **Pillow font rendering quality** — Pillow's text rendering can look aliased at large sizes. Use `ImageDraw.Draw(img, "RGBA")` and render at 2x then downscale for antialiasing. Or use `font.getmask2()` for better results.
- **Filename collisions** — Multiple shots may use the same building block. Filename must include shot ID: `S042_silhouette_figure.png`.
- **Manifest merge race** — S02 and S03 both write manifest.json. The merge must be incremental (read existing + append new assets), not overwrite. S02's pattern of atomic temp+rename should be followed.
- **Silhouette shape variety** — "Flat black silhouette" needs actual human silhouette shapes. Pillow can't draw anatomically plausible humans from scratch. Options: (a) pre-made silhouette template PNGs that get composited, (b) very simple geometric human shapes (head circle + body trapezoid), (c) ComfyUI generates silhouettes too. Recommendation: use simple geometric humanoid shapes for code-gen, accept they'll be stylized/abstract rather than realistic.

## Open Risks

- **ComfyUI Z-image-turbo style adherence** — Untested whether the model can produce "neon line art ritual illustrations" or "profile heads with concentric internal layers" reliably. May need specific negative prompts, LoRAs, or workflow adjustments. This is the primary risk to retire in S03.
- **websocket dependency** — `websockets` or `websocket-client` may not be installed. Need to check and install, or use polling fallback (GET /history/{prompt_id}).
- **Silhouette shape quality** — Simple geometric shapes may look too primitive. If the code-gen silhouettes don't meet quality bar, these blocks could be reassigned to ComfyUI (D007 allows boundary shift).
- **Resolution consistency** — ComfyUI output resolution depends on workflow params. Must enforce 1920×1080 or scale to match.
- **Pre-made assets vs full generation** — Some blocks (Character Profile Card) need placeholder photos. These placeholders need to be generic enough to work with any topic.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| ComfyUI | `mckruz/comfyui-expert@comfyui-api` (146 installs) | available — covers REST API patterns, workflow building |
| ComfyUI | `mckruz/comfyui-expert@comfyui-workflow-builder` (136 installs) | available — workflow template construction |
| Pillow | — | none found (no skills on skills.sh) |

The ComfyUI skills could accelerate the ComfyUI client implementation in T02. The `comfyui-api` skill likely documents the exact REST endpoints and websocket protocol needed.

## Sources

- VISUAL_STYLE_GUIDE.md — 25 building blocks with full production specs, 11 with `shotlist_type: animation` (source: `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md`)
- shotlist.json schema — S001-S999 IDs, building_block + shotlist_type routing (source: `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py`)
- manifest.json schema — asset entries with folder/source/mapped_shots, gap lifecycle (source: `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py`)
- S02 forward intelligence — animation/map gaps deliberately not flagged by acquisition; S03 generates from shotlist directly (source: `.gsd/milestones/M002/slices/S02/S02-SUMMARY.md`)
- Pillow 11.3.0 — ImageDraw, ImageFont, ImageFilter, ImageChops for compositing (source: Context7 `/python-pillow/pillow`)
- D007 — Hybrid code-gen + ComfyUI strategy with shiftable boundary (source: `.gsd/DECISIONS.md`)
