---
name: visual-style-extractor
description: Extracts the visual style from a documentary or YouTube video and produces a VISUAL_STYLE_GUIDE.md that maps every visual asset type used, its narrative function, and proportion of screen time. Use this whenever the user says things like "extract the visual style", "analyze this reference video", "what visual assets does this channel use", "copy the look of this video", "figure out how this video is edited", or wants to understand how a specific YouTube channel structures its visuals. Accepts a YouTube URL or a local folder with a video + transcript.
---

# Visual Style Extractor v2

Extracts the visual style from a documentary reference video, producing a `VISUAL_STYLE_GUIDE.md` that the Visual Orchestrator (Agent 1.4) and Generative Visual Engine (Agent 2.2) use to determine what visual assets to create.

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

### 2. Run Stages 0–4 (Automated Python)

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import run_stages_0_to_4, PipelineConfig
import json

config = PipelineConfig(source='USER_INPUT_HERE')
result = run_stages_0_to_4(config)
print(json.dumps(result, indent=2))
"
```

Capture the output JSON — you need `contact_sheet_paths`, `manifest_path`, `output_dir`, `video_title`, `video_source`, and `prompt_path`.

If scene count warnings appear, ask the user if they want to re-run with adjusted threshold.

### 3. Run Stage 5: LLM Analysis (Subagents)

For each contact sheet image:

1. Read the contact sheet image using the Read tool
2. Read the corresponding slice of `frames_manifest.json` for full narration context
3. Read the analysis prompt from `prompt_path`
4. Spawn a subagent (Agent tool, type: general-purpose) with:
   - The contact sheet image path to read
   - The manifest data for those frames
   - The analysis prompt
   - Instructions to output a JSON array

Dispatch subagents **in parallel** (one per contact sheet, or group 2 sheets per subagent if there are many).

Collect all JSON array outputs and merge them into a single flat list.

**Confidence gating:** Remove any frame entries with `confidence < 3` — flag them to the user as needing manual review.

Save the merged list to a file using the bundled helper (write the JSON to a temp file first, then pass it):
```bash
# Write merged JSON to temp file, then save via helper
python .claude/skills/visual-style-extractor/scripts/save_analysis.py OUTPUT_DIR '[...merged json array...]'
```
Or write it directly with Python's `json.dump` to `OUTPUT_DIR/analysis_results.json`.

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
- The top 3-5 asset types by proportion
- Any low-confidence frames that need manual review
- The path to `VISUAL_STYLE_GUIDE.md`

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
1. **Scene Taxonomy** — each asset type with proportion, appearance, narrative trigger, content descriptions
2. **Global Aesthetic** — persistent overlays, color palette, motion language
3. **Structural Flow** — pacing, chapter transitions, opening/closing patterns
4. **Constraints** — what NOT to do
5. **Quick Reference Table** — summary for the Visual Orchestrator
