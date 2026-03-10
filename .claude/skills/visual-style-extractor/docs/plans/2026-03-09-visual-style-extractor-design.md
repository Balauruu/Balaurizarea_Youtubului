# Visual Style Extractor v2 — Design Document

> **Date:** 2026-03-09
> **Status:** Draft
> **Consumers:** Agent 1.4 (Visual Orchestrator), Agent 2.2 (Generative Visuals), manual reference

---

## 1. Problem Statement

The v1 skill (`visual-language-extractor`) produced unreliable output:
- **Hallucinated visual elements** (e.g., described fade transitions that don't exist) due to analyzing 320px thumbnail contact sheets of predominantly dark content
- **Missed significant scene types** because fixed 5-second sampling captures redundant frames while missing short but important scenes
- **Output structure was not actionable** — organized by visual properties (colors, typography) rather than by how assets are actually used in production

The new skill must produce a style guide that directly informs the Visual Orchestrator's shot-listing decisions: what asset types exist, when each is used narratively, and in what proportions.

---

## 2. Goals

1. **Accurate scene taxonomy** — identify every distinct visual asset type used in a reference video, without hallucinating elements that aren't there
2. **Narrative-asset correlation** — map each asset type to its narrative function (what is being said when this visual appears)
3. **Proportional data** — compute what percentage of runtime each asset type occupies, with average durations
4. **Actionable for downstream agents** — the Visual Orchestrator can use this guide to assign the correct asset type to each script segment; the Generative Visual Engine knows what styles to produce
5. **Reusable as channel identity** — analyze 1-3 reference videos to establish a visual identity, then use the guide across all future productions

---

## 3. Inputs & Outputs

### Inputs

| Input | Required | Source |
|-------|----------|--------|
| YouTube URL | Option A (default) | User provides in chat |
| Local video file + transcript | Option B | User points to directory containing video + `.vtt`/`.srt`/`.txt` file |

**No Whisper dependency.** If a local video has no transcript, the user must provide one or supply a YouTube URL instead.

### Output

`VISUAL_STYLE_GUIDE.md` — a layered document with asset-type-primary organization (detailed in Section 7).

---

## 4. Pipeline Architecture

```
┌─────────────────────────────────────────────┐
│  Stage 0: Acquisition                       │
│  yt-dlp → video + .vtt auto-subs            │
│  OR accept local video + transcript          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 1: Scene Detection                   │
│  PySceneDetect AdaptiveDetector             │
│  → keyframes with timestamps + durations     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 2: Perceptual Hash Deduplication     │
│  imagededup (PHash)                         │
│  → unique representative frames              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 3: Script-Frame Alignment            │
│  Python: map timestamps → narration segments │
│  → frames_manifest.json                      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 4: Annotated Contact Sheets          │
│  Python/PIL: 3x3 grid, 1568px, labeled      │
│  → contact_sheets/ directory                 │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 5: LLM Analysis (subagents)          │
│  Parallel subagents read contact sheets      │
│  + manifest context → structured JSON        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Stage 6: Synthesis                         │
│  Aggregate subagent outputs, compute         │
│  proportions → VISUAL_STYLE_GUIDE.md         │
└─────────────────────────────────────────────┘
```

---

## 5. Stage Details

### Stage 0: Acquisition

**If YouTube URL:**
```bash
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
  --write-auto-sub --sub-lang en --convert-subs vtt \
  -o "<output_dir>/%(title)s.%(ext)s" "<url>"
```
- Downloads best quality up to 1080p (higher is unnecessary for frame extraction)
- Auto-subs in VTT format with timestamps
- Output directory: user-specified or `context/visual-references/<video-title>/`

**If local files:**
- Skill checks the provided directory for a video file (`.mp4`, `.webm`, `.mkv`, `.avi`, `.mov`)
- Checks for transcript file (`.vtt`, `.srt`, `.txt`)
- If video exists but no transcript → error with clear message: "No transcript found. Provide a transcript file or use a YouTube URL."

### Stage 1: Scene Detection

**Tool:** PySceneDetect with `AdaptiveDetector`

```python
from scenedetect import detect, AdaptiveDetector, open_video
from scenedetect.scene_manager import save_images

video = open_video(video_path)
scenes = detect(video_path, AdaptiveDetector(
    adaptive_threshold=3.0,  # tuned for documentary content
    min_scene_len=15         # minimum 0.5s at 30fps — avoids flash-frame false positives
))
```

**Output:**
- Keyframe images saved to `frames/` directory
- `scenes.json`: list of `{scene_number, start_time, end_time, duration, keyframe_path}`

**Expected yield:** 60-150 keyframes for a 20-40 minute video (vs. 200-500 from fixed 5-second intervals).

**Threshold tuning note:** `adaptive_threshold=3.0` is the starting point. Documentary content with lots of dark-to-dark cuts may need a lower threshold (2.0-2.5). The script should log scene count so the operator can re-run with adjusted threshold if the count seems too low or high.

### Stage 2: Perceptual Hash Deduplication

**Tool:** imagededup with PHash

```python
from imagededup.methods import PHash

phasher = PHash()
encodings = phasher.encode_images(image_dir=frames_dir)
duplicates = phasher.find_duplicates(
    encoding_map=encodings,
    max_distance_threshold=10  # hamming distance — groups visually similar frames
)
```

**Logic:**
- Group frames by visual similarity
- Select one representative per group (the one closest to the group's median timestamp — preserves temporal spread)
- Preserve the timestamp and scene duration data from Stage 1

**Expected yield:** 30-60 unique frames from 60-150 keyframes (50-70% reduction).

**Output:** Updated `frames_manifest.json` with only unique frames, each retaining:
- `frame_id` (sequential)
- `frame_path`
- `timestamp` (MM:SS)
- `scene_duration` (seconds)
- `represents_count` (how many similar frames this one stands for — useful for proportion calculation)

### Stage 3: Script-Frame Alignment

**Input:** `frames_manifest.json` + transcript file (`.vtt` or `.srt`)

**Logic:**
1. Parse the transcript into timestamped segments (VTT/SRT parsing)
2. For each frame, find the transcript segment whose time range contains the frame's timestamp
3. Attach the narration text to the frame's manifest entry

**Output:** Enriched `frames_manifest.json`:
```json
{
  "frames": [
    {
      "frame_id": 1,
      "frame_path": "frames/frame_001.jpg",
      "timestamp": "00:45",
      "scene_duration": 4.2,
      "represents_count": 3,
      "narration": "In 1960, a small town in northern Mexico became the center of something unimaginable..."
    }
  ],
  "video_duration": 1228,
  "total_scenes_detected": 87,
  "unique_frames_after_dedup": 42
}
```

### Stage 4: Annotated Contact Sheets

**Purpose:** Package frames for LLM consumption in a format that maximizes analysis quality while respecting token limits.

**Specifications:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Grid size | 3x3 (9 frames per sheet) | ~520px per cell at 1568px total — well above Claude's 200px minimum |
| Total sheet dimensions | 1568x1568 px | Maximum before Claude downscales |
| Padding between cells | 4px white border | Prevents edge blending between adjacent frames |
| Label area | 30px strip below each cell | Space for metadata text |
| Label content | `F{id} \| {timestamp} \| "{narration_snippet}"` | Frame ID for reference, timestamp for temporal context, narration for semantic context |
| Label font | Monospace, white on dark gray (#333) bar | High contrast, readable at small sizes |
| Narration snippet | First 40 characters, truncated with "..." | Enough to establish narrative context |
| Image format | JPEG, quality 90 | Balance between file size and detail preservation |

**Cell layout (per frame):**
```
┌──────────────────────────┐
│                          │
│      Frame image         │
│      (~520 x 480 px)     │
│                          │
├──────────────────────────┤
│ F023 | 04:35 | "the com… │  ← 30px label strip
└──────────────────────────┘
```

**Contact sheet layout:**
```
┌────┬────┬────┐
│ F1 │ F2 │ F3 │
├────┼────┼────┤
│ F4 │ F5 │ F6 │
├────┼────┼────┤
│ F7 │ F8 │ F9 │
└────┴────┴────┘
```

**Expected output:** 4-7 contact sheets for 30-60 unique frames.

### Stage 5: LLM Analysis (Subagents)

**Strategy:** Parallel subagents, each analyzing 1-2 contact sheets (9-18 frames).

**Each subagent receives:**
1. The contact sheet image(s) via Read tool
2. The relevant slice of `frames_manifest.json` (full narration text, not just the truncated label)
3. A structured analysis prompt (see below)

**Analysis prompt structure:**
```
You are analyzing frames from a documentary video to extract its visual style.
Each frame is labeled with an ID, timestamp, and narration snippet.

For EACH frame in this contact sheet:

1. SCENE TYPE: Classify into one of these categories (or propose a new one):
   [title_card | archival_photo | archival_video | news_clip | map_animation |
    text_overlay | quote_card | b_roll_footage | screen_recording |
    animated_graphic | silhouette | date_card | chapter_header |
    evidence_document | portrait | location_shot | other: ___]

2. ASSET BREAKDOWN: What distinct visual elements compose this frame?
   - Background layer: (solid color, gradient, footage, etc.)
   - Main element: (photo, video, graphic, text, etc.)
   - Overlays/effects: (grain, scanlines, vignette, color filter, etc.)
   - Text elements: (if any — describe font style, position, color)

3. CONTENT DESCRIPTION (for footage/b-roll only):
   Describe WHAT is depicted in the footage.
   (e.g., "black-and-white cartoon of a man working at a desk",
    "aerial shot of a rural compound", "vintage factory assembly line",
    "old newsreel of a crowd gathering")
   This is critical — b-roll is chosen to metaphorically illustrate
   narrative concepts. The description must capture both the literal
   content and the implied metaphor given the narration context.

4. NARRATIVE FUNCTION: Given the narration at this moment,
   why is this visual type being used here?
   What concept does it illustrate?
   (e.g., "old cartoon of man working → illustrates 'daily routine'",
    "introducing a new location", "showing evidence",
    "emotional emphasis", "chapter transition")

4. CONFIDENCE: Rate 1-5 how clearly you can analyze this frame.
   If below 3, note what is unclear.

Output as JSON array. Only describe what you can see.
If you cannot determine something, say "unclear" — do not guess.
```

**Subagent output format:**
```json
[
  {
    "frame_id": "F023",
    "timestamp": "04:35",
    "scene_type": "map_animation",
    "background": "solid black",
    "main_element": "stippled particle map of Mexico, highlighted region in white",
    "overlays": ["subtle film grain", "vignette"],
    "text_elements": "location label top-right in teal, ALL CAPS sans-serif",
    "content_description": null,
    "narrative_function": "introducing geographic context for new location",
    "confidence": 4
  },
  {
    "frame_id": "F031",
    "timestamp": "06:12",
    "scene_type": "b_roll_footage",
    "background": "n/a (full-frame footage)",
    "main_element": "black-and-white cartoon of a man laboring in a field",
    "overlays": ["film grain", "vignette", "desaturation filter"],
    "text_elements": null,
    "content_description": "Vintage cartoon depicting agricultural labor — used as visual metaphor for 'the followers were put to work' in narration",
    "narrative_function": "illustrating forced labor concept via metaphorical b-roll",
    "confidence": 4
  }
]
```

**Confidence gating:** Frames with confidence < 3 are flagged for manual review rather than included in the style guide. This prevents low-quality analysis from polluting the output.

### Stage 6: Synthesis

**Input:** All subagent JSON outputs + `frames_manifest.json` (for duration/proportion data).

**Process:**
1. **Group frames by scene_type** — aggregate all frames classified as `archival_photo`, `map_animation`, etc.
2. **Compute proportions** — using `scene_duration` and `represents_count` from the manifest:
   ```
   proportion = sum(scene_duration * represents_count for frames in type) / total_video_duration
   ```
3. **Extract patterns per type** — find commonalities in background, overlays, text_elements across all frames of the same type
4. **Identify narrative triggers** — from the grouped `narrative_function` values, derive when each asset type is deployed
5. **Extract global patterns** — overlays/effects that appear across multiple scene types become the global aesthetic layer
6. **Generate the VISUAL_STYLE_GUIDE.md** using the output template (Section 7)

---

## 6. Dependencies

### Python packages
```
scenedetect[opencv]    # Scene detection (includes opencv-python)
imagededup             # Perceptual hash deduplication
Pillow                 # Contact sheet generation + labeling
webvtt-py              # VTT subtitle parsing
pysrt                  # SRT subtitle parsing (fallback)
```

### External tools
```
ffmpeg                 # Required by PySceneDetect for frame extraction
yt-dlp                 # Video + subtitle download (already installed as skill)
```

### No dependencies on
- Whisper / speech recognition
- Claude API / Anthropic SDK (all LLM work via Claude Code native)
- GPU / CUDA (all processing is CPU-bound)

---

## 7. Output Format: VISUAL_STYLE_GUIDE.md

```markdown
# Visual Style Guide
> Source: {video_title} ({video_url or file path})
> Duration: {MM:SS} | Scenes detected: {N} | Unique frames analyzed: {N}
> Generated: {date}

---

## 1. Scene Taxonomy

### {Scene Type 1, e.g., Archival Footage}
- **Proportion:** {X}% of runtime (~{N} seconds average per occurrence)
- **Frequency:** {N} occurrences across the video
- **Appearance:**
  - Background: {description}
  - Main element: {description}
  - Treatment: {description — e.g., desaturated, letterboxed, darkened}
- **Overlays/Effects:** {list of effects applied to this scene type}
- **Text elements:** {if any — font style, position, color}
- **Narrative trigger:** {when/why this visual type appears}
  - Examples from source: "{narration snippet}" → {this asset type}
- **Content descriptions (for footage/b-roll types):**
  Catalog of what is literally depicted and what narrative concept it illustrates.
  | Narration concept | Footage used | Metaphor |
  |-------------------|-------------|----------|
  | e.g., "forced labor" | vintage cartoon of man working in field | manual labor = servitude |
  | e.g., "isolation" | aerial shot of remote compound | physical remoteness = psychological isolation |
- **Assets needed to reproduce:**
  - {asset 1, e.g., historical photograph}
  - {asset 2, e.g., film grain overlay}

### {Scene Type 2, e.g., Title Cards}
...

### {Scene Type N}
...

---

## 2. Global Aesthetic

Properties that are shared across all or most scene types.

### Color Palette
| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| ... | ... | ... | ... |

### Persistent Overlays
Effects applied globally across the video, not specific to one scene type.
- {overlay 1 — e.g., film grain at X% opacity}
- {overlay 2 — e.g., vignette}

### Motion Language
- Default motion: {e.g., slow Ken Burns, static holds}
- {any other motion patterns}

---

## 3. Structural Flow

How asset types are sequenced throughout the video.

### Opening Pattern (first 60-90 seconds)
- {sequence of asset types used in the intro}

### Chapter Transitions
- {how the video signals topic/chapter changes}

### Evidence Presentation Pattern
- {typical sequence when presenting facts/sources}

### Pacing
| Segment | Dominant Asset Types | Avg Scene Duration |
|---------|---------------------|--------------------|
| Opening | ... | ... |
| Mid-video | ... | ... |
| Climax/Reveal | ... | ... |
| Closing | ... | ... |

---

## 4. Constraints (What NOT to Do)
- {constraint 1}
- {constraint 2}
- ...

---

## 5. Asset Type Summary (Quick Reference for Visual Orchestrator)

| # | Asset Type | Proportion | Avg Duration | Narrative Trigger | Primary Assets Needed |
|---|-----------|------------|--------------|-------------------|-----------------------|
| 1 | ... | ...% | ...s | ... | ... |
| 2 | ... | ...% | ...s | ... | ... |
| ... | | | | | |
```

---

## 8. Skill Invocation Flow

```
User: "Extract visual style from [YouTube URL]"
  OR: "Extract visual style from [directory path]"

Skill:
  1. Validate input (URL or directory with video + transcript)
  2. Run Stage 0 (acquisition if needed)
  3. Run Stage 1 (scene detection) — log scene count
  4. Run Stage 2 (deduplication) — log frame reduction
  5. Run Stage 3 (alignment) — generate manifest
  6. Run Stage 4 (contact sheets) — generate labeled grids
  7. Run Stage 5 (subagent analysis) — parallel, await all
  8. Run Stage 6 (synthesis) — generate VISUAL_STYLE_GUIDE.md
  9. Present summary to user with key findings
```

**Estimated runtime:** 3-5 minutes (dominated by video download + scene detection).
**Estimated token cost:** ~60-100K tokens for LLM analysis stages.

---

## 9. Error Handling

| Failure Point | Handling |
|---------------|----------|
| yt-dlp download fails | Error message with URL, suggest manual download |
| No subtitles available on YouTube | Error: "No auto-subs available. Download video manually and provide a transcript file." |
| PySceneDetect finds < 10 scenes | Warning + suggestion to lower `adaptive_threshold` to 2.0 |
| PySceneDetect finds > 200 scenes | Warning + suggestion to raise `adaptive_threshold` to 4.0 |
| Dedup removes > 90% of frames | Warning: video may be too visually uniform for meaningful analysis |
| Subagent confidence < 3 on a frame | Frame excluded from synthesis, flagged in output as "needs manual review" |
| Read tool fails on contact sheet | Fallback: re-generate at lower resolution (1200px) and retry |

---

## 10. Future Considerations (Not in Scope)

- **Multi-video analysis:** Run on 2-3 reference videos and merge into a single channel-wide style guide
- **Remotion component specs:** Add implementation-ready component blueprints under each asset type (Approach B from brainstorming)
- **Programmatic color extraction:** K-means per frame for verified hex values if LLM color identification proves unreliable
- **Scene detection threshold auto-tuning:** Automatically adjust threshold based on initial scene count
