---
name: visual-style-extractor
description: Extracts the visual style from a documentary or YouTube video and produces a VISUAL_STYLE_GUIDE.md that maps every visual asset type used, its narrative function, and proportion of screen time. Use this whenever the user says things like "extract the visual style", "analyze this reference video", "what visual assets does this channel use", "copy the look of this video", "figure out how this video is edited", or wants to understand how a specific YouTube channel structures its visuals. Accepts a YouTube URL or a local folder with a video + transcript.
---

# Visual Style Extractor v3

Extracts the visual style from a documentary reference video, producing a `VISUAL_STYLE_GUIDE.md` that the Visual Orchestrator (Agent 1.4) and Generative Visual Engine (Agent 2.2) use to determine what visual assets to create.

The output is a **decision framework** — not an analysis report. Asset types are organized hierarchically under 5 categories, with each subtype entry providing Description, Use, Implementation, Variants, Stats, and Examples.

## Prerequisites

Ensure dependencies are installed:
```bash
pip install -r .claude/skills/visual-style-extractor/scripts/requirements.txt
```

Verify ffmpeg is available:
```bash
ffmpeg -version
```

## Process

### 1. Determine Input

Ask the user for either:
- **A YouTube URL** (preferred — downloads video + auto-subs automatically)
- **A local directory path** containing a video file and a `.vtt`/`.srt`/`.txt` transcript

### 2. Run Stages 0-4 (Automated Python)

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import run_stages_0_to_4, PipelineConfig
import json

config = PipelineConfig(source='USER_INPUT_HERE')
result = run_stages_0_to_4(config)

# Write result to scratch pad — do NOT keep in context
with open('.claude/scratch/pipeline_result.json', 'w') as f:
    json.dump(result, f, indent=2)
print('Pipeline result saved to .claude/scratch/pipeline_result.json')
print(f'Output dir: {result[\"output_dir\"]}')
print(f'Contact sheets: {len(result[\"contact_sheet_paths\"])}')
print(f'Video title: {result[\"video_title\"]}')
"
```

Read back only the fields you need from `.claude/scratch/pipeline_result.json` using grep or targeted reads. You need: `output_dir`, `contact_sheet_paths` (count and paths), `manifest_path`, `video_title`, `video_source`, `prompt_path`.

**Output directory:** For YouTube URLs, a subfolder named after the video title is created under `context/visual-references/`. For local input, the source directory is used as-is.

**Progress output:** Stages 0-4 print progress to stdout automatically. The dedup stage also writes `dedup_report.json` to the output directory for auditing which frames were merged.

If scene count warnings appear, ask the user if they want to re-run with adjusted threshold.

### 3. Run Stage 5: LLM Analysis (Subagents)

**Preparation — generate manifest slices for each batch:**

Group contact sheets into batches of 3-4 sheets each. For each batch, generate a manifest slice:

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import slice_manifest
# Repeat for each batch — adjust start/end indices (9 frames per sheet)
slice_manifest('MANIFEST_PATH', start_idx=0, end_idx=27, output_path='.claude/scratch/manifest_slice_0.json')
slice_manifest('MANIFEST_PATH', start_idx=27, end_idx=54, output_path='.claude/scratch/manifest_slice_1.json')
# ... continue for remaining batches
print('Manifest slices ready')
"
```

**Dispatch subagents in parallel.** For each batch, spawn one subagent (Agent tool, type: general-purpose) with this prompt:

> You are analyzing documentary video frames to extract visual style information.
>
> 1. Read the analysis prompt from: `PROMPT_PATH`
> 2. Read the manifest slice from: `.claude/scratch/manifest_slice_N.json`
> 3. For each contact sheet in your batch, read the image using the Read tool:
>    - `CONTACT_SHEET_PATH_1`
>    - `CONTACT_SHEET_PATH_2`
>    - `CONTACT_SHEET_PATH_3`
> 4. Analyze every frame following the prompt instructions
> 5. Write your JSON array result to: `.claude/scratch/analysis_batch_N.json`
> 6. Return only a 1-line summary: "Analyzed X frames, wrote to .claude/scratch/analysis_batch_N.json"

Do NOT pass the prompt text, manifest data, or image contents in the subagent prompt. The subagent reads everything from files itself.

**After all subagents complete — merge results:**

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import merge_analysis_batches
import glob

batch_paths = sorted(glob.glob('.claude/scratch/analysis_batch_*.json'))
kept, removed = merge_analysis_batches(batch_paths, 'OUTPUT_DIR/analysis_results.json')
print(f'[Stage 5/6] Merged {kept} frames ({removed} removed for low confidence)')
"
```

If `removed > 0`, tell the user how many low-confidence frames were dropped.

### 4. Run Stage 6: Synthesis

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import run_stage_6
result = run_stage_6(
    analysis_results_path='OUTPUT_DIR/analysis_results.json',
    manifest_path='MANIFEST_PATH',
    video_title='VIDEO_TITLE',
    video_source='VIDEO_SOURCE',
    output_dir='OUTPUT_DIR',
)
print(f'Style guide saved to: {result}')
"
```

### 5. Present Results

Show the user:
- How many scenes were detected and unique frames analyzed
- The top 3-5 asset types by proportion (grouped by category)
- Any low-confidence frames that need manual review
- The path to `VISUAL_STYLE_GUIDE.md`
- The path to `dedup_report.json` (for auditing frame deduplication)

## Error Handling

| Issue | Action |
|-------|--------|
| yt-dlp fails | Show error, suggest manual download |
| No subtitles on YouTube | Tell user to provide transcript manually |
| < 10 scenes detected | Suggest re-running with `adaptive_threshold=2.0` |
| > 200 scenes detected | Suggest re-running with `adaptive_threshold=4.0` |
| > 90% frames deduped | Warn: video may be too uniform |
| Read tool fails on contact sheet | Re-generate at 1200px and retry |

## Output

`VISUAL_STYLE_GUIDE.md` in the output directory, structured as:

1. **Asset Types** — Hierarchically organized under 5 categories:
   - **B-Roll** — live-action/stock footage
   - **Archival Photos** — still photographs (portraits, locations, historical)
   - **Graphics & Animation** — motion graphics, silhouettes, maps, date cards
   - **Text Elements** — quote cards, title cards, text overlays, stingers
   - **Evidence & Documentation** — documents, screen recordings, newspaper scans

   Each subtype within a category has:
   - Shotlist `visual_type` mapping (for the Visual Orchestrator)
   - **Description**: What it looks like
   - **Use**: Generalized narrative trigger (when to deploy)
   - **Implementation**: How to recreate it (background, elements, overlays, colors)
   - **Variants**: Named sub-variants observed
   - **Stats**: Proportion, frequency, avg duration (compact)
   - **Examples**: 2-3 frame content descriptions

   Subtypes are open-ended — discovered from the video, not a fixed list.
   Transitions (black frames, color holds) are excluded.

2. **Type Mapping** — Quick-reference table mapping extracted types to shotlist `visual_type` values, grouped by category
