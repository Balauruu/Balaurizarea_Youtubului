---
name: video-analyzer
description: >
  Analyze video files for content, quality, and technical metrics. Use this skill whenever the user
  wants to analyze a video file, extract frames, check FPS or smoothness, detect scene changes,
  export stills, identify key moments, or get a timeline breakdown of video content. Trigger on
  phrases like "analyze this video", "check video quality", "extract frames", "export stills",
  "find key moments", "check if video is smooth", "what happens in this video", or any task
  involving a .mp4, .mov, .avi, .mkv, .webm file. Always use this skill — don't try to wing it.
---

# Video Analyzer Skill

Analyze video files for content understanding, technical quality, and export useful artifacts.

## Capabilities

1. **Content Analysis** — Scene-by-scene description, object/person detection, on-screen text
2. **Technical QA** — FPS verification, dropped frame detection, motion smoothness scoring
3. **Keyframe Export** — Smart extraction of visually significant frames
4. **Still Export** — Export any frame or range of frames as images
5. **Timeline Report** — Timestamped markdown report of everything found

---

## Step 0: Check Dependencies

Before anything else, verify ffmpeg and Python deps are available:

```bash
ffmpeg -version 2>/dev/null | head -1 || echo "MISSING: ffmpeg"
python3 -c "import cv2, numpy, base64, json" 2>/dev/null || echo "MISSING: python deps"
```

If ffmpeg is missing:
```bash
sudo apt-get install -y ffmpeg
```

If Python deps missing:
```bash
pip install opencv-python-headless numpy --break-system-packages
```

---

## Step 1: Probe the Video

Always start by probing the file to understand what you're working with:

```bash
python3 /path/to/scripts/probe_video.py <video_path>
```

This returns:
- Duration, resolution, codec
- Declared FPS vs actual frame count
- File size and bitrate
- Audio track info

Use this to decide the analysis strategy (see Step 2).

---

## Step 1b: Token & Cost Estimation (ALWAYS do this before analysis)

After probing, **always** run the estimator and show it to the user before proceeding:

```bash
python3 scripts/estimate_cost.py --probe /tmp/video_probe.json --mode <mode>
```

This prints a formatted confirmation block like:

```
┌─────────────────────────────────────────────┐
│           VIDEO ANALYSIS ESTIMATE            │
└─────────────────────────────────────────────┘

  File        : promo_v2.mp4
  Duration    : 00:02:34
  Resolution  : 1920×1080
  Mode        : standard

  Frames      : ~308
  Batches     : 21
  Input tokens: ~339K
  Output tokens: ~8K
  Total tokens: ~347K

  ─────────────────────────────────────────
  💳 Subscription (Claude Code): No extra cost
     but will consume significant usage quota
  💰 API billing (if applicable):
     ~$1.0170 USD (Sonnet)
  ─────────────────────────────────────────

  ⏱  Estimated time: ~1.7 min

  Proceed with analysis? [yes / no / change mode]
```

**Wait for explicit user confirmation before extracting frames or running vision calls.**

If user says "change mode", re-run the estimator with their chosen mode and show again.
If user says "no", stop and ask what they'd like to do instead (shorter clip, different mode, etc).

Save probe JSON first so estimator can read it:
```bash
python3 scripts/probe_video.py <video_path> > /tmp/video_probe.json
```

---

## Step 2: Choose Analysis Mode

Based on probe results and user intent, pick a mode:

| Mode | When to Use | Frame Rate |
|------|-------------|-----------|
| `quick` | "Get the gist", long videos >5min | 1 fps |
| `standard` | Default for most content analysis | 2 fps |
| `detailed` | Action, fast cuts, short clips <2min | 5 fps |
| `technical` | FPS/smoothness QA, dropped frame check | Every frame |
| `keyframes` | Scene changes, efficient summarization | Keyframes only |

**Token budget awareness**: Each frame costs ~800-1200 vision tokens. Budget accordingly:
- Quick: ~60 frames/min
- Standard: ~120 frames/min  
- Technical: full frame count (use only for short clips or specific ranges)

---

## Step 3: Extract Frames

```bash
python3 scripts/extract_frames.py \
  --input <video_path> \
  --output /tmp/video_frames/ \
  --mode <mode> \
  --start 0 \          # optional: start time in seconds
  --end 60             # optional: end time in seconds
```

Outputs:
- `/tmp/video_frames/frames/` — extracted JPEGs named `frame_XXXXX_<timestamp_ms>.jpg`
- `/tmp/video_frames/manifest.json` — frame list with timestamps and metadata
- `/tmp/video_frames/technical_data.json` — frame intervals, FPS measurements, duplicate detection

---

## Step 4: Technical Analysis (if requested)

If user wants FPS/smoothness analysis, run BEFORE vision analysis:

```bash
python3 scripts/technical_analysis.py --manifest /tmp/video_frames/manifest.json
```

This computes:
- **Actual FPS** from PTS timestamps vs declared FPS
- **Dropped frames**: consecutive frames with identical pixel hashes = dropped
- **Smoothness score** (0-100): based on frame interval variance
- **Stutter events**: timestamps where frame intervals spike >2x normal
- **Motion intensity**: per-frame pixel delta as proxy for motion blur

Report these findings immediately — don't wait for content analysis.

---

## Step 5: Vision Analysis (Batched)

Send frames to Claude vision in batches. **Never send more than 20 frames per call** to stay within limits.

```python
# Pseudo-structure for batching
batches = chunk(frames, size=15)
results = []
for i, batch in enumerate(batches):
    context = f"Video segment {i+1}/{len(batches)}. Time range: {batch[0].ts}s - {batch[-1].ts}s"
    result = analyze_batch(batch, context, prior_summary=results[-1] if results else None)
    results.append(result)
```

**System prompt for vision calls:**
```
You are analyzing frames from a video. For each batch, describe:
1. What is happening (actions, people, objects, text on screen)
2. Scene changes or cuts between frames
3. Any notable visual artifacts or quality issues
4. Emotional tone or energy of the content
Be concise but specific. Reference timestamps when noting changes.
```

See `references/vision_prompts.md` for specialized prompts per content type (tutorial, promo, gameplay, etc).

---

## Step 6: Export MP4 Clips

Export specific segments of the video as standalone `.mp4` files:

```bash
python3 scripts/export_clips.py \
  --input <video_path> \
  --output /tmp/video_clips/ \
  --clips '<json_or_mode>' \
  --reencode   # optional: frame-perfect cuts (slower)
```

### Clip Selection Modes

**Specific ranges** (JSON array):
```bash
--clips '[{"start":"00:01:00","end":"00:01:30","label":"intro"},{"start":"00:02:15","end":"00:02:45","label":"cta"}]'
```

**Around keypoints** (auto-pads ±5s around each key moment):
```bash
--clips 'keypoints:/tmp/video_analysis_keypoints.json'
```

**Every detected scene** (uses manifest from frame extraction):
```bash
--clips 'scenes:/tmp/video_frames/manifest.json'
```

### Stream Copy vs Re-encode
- Default (no `--reencode`): **stream copy** — instant, lossless, but cuts align to nearest keyframe (±1s)
- With `--reencode`: **re-encode** — frame-perfect cuts, slightly larger file, takes longer

Use re-encode when: cut precision matters, source codec is incompatible, or clips need to be edited downstream.

---

## Step 6b: Export Stills & Keypoints

### Export Stills
User can request stills by:
- Specific timestamp: `--timestamp 00:01:23`
- Range: `--start 00:01:00 --end 00:01:30 --every 5s`
- "All scene changes" — use keyframe mode
- "Best frames" — use quality scoring from technical analysis

```bash
python3 scripts/export_stills.py \
  --frames-dir /tmp/video_frames/frames/ \
  --output /tmp/video_stills/ \
  --selection <timestamps_or_mode> \
  --format jpg \        # jpg or png
  --quality 95
```

### Export Keypoints Report
```bash
python3 scripts/export_keypoints.py \
  --analysis-results /tmp/video_analysis.json \
  --output /tmp/video_keypoints.md
```

Keypoints report includes:
- Timestamped list of major events/scenes
- Thumbnail path for each keypoint
- Technical flags (drops, artifacts) with timestamps
- Summary statistics

---

## Step 7: Generate Final Report

Always produce a report at the end:

```bash
python3 scripts/generate_report.py \
  --analysis /tmp/video_analysis.json \
  --technical /tmp/video_frames/technical_data.json \
  --keypoints /tmp/video_keypoints.md \
  --stills-dir /tmp/video_stills/ \
  --output /mnt/user-data/outputs/video_report.md
```

Report structure:
```
# Video Analysis: <filename>

## Overview
- Duration, resolution, codec, file size
- Declared vs actual FPS
- Smoothness score

## Technical QA
- FPS analysis with chart
- Dropped frame events (timestamped)
- Stutter events
- Motion intensity timeline

## Content Timeline
[HH:MM:SS] Scene description...
[HH:MM:SS] Scene change → new scene...

## Key Moments
- [timestamp] — description (with exported still path)

## Exported Stills
- still_001.jpg — [timestamp] — description
...

## Issues Found
- Any artifacts, drops, quality problems
```

---

## Output Files

Always copy final outputs to `/mnt/user-data/outputs/`:
- `video_report.md` — full analysis report
- `stills/` — exported still images
- `clips/` — exported MP4 clips
- `keypoints.md` — keypoints-only summary (if requested)

Use `present_files` to share with user.

---

## Common Workflows

### "Analyze this video"
→ Probe → save probe JSON → **estimate + confirm** → standard mode → extract frames → vision analysis → report

### "Is this video smooth / check the FPS"
→ Probe → save probe JSON → **estimate + confirm** (technical mode) → extract frames → technical analysis → report

### "Export stills from this video"
→ Probe → ask: specific timestamps, scene changes, or best frames? → extract → export stills → present

### "Export clips / cut this video"
→ Probe → ask: which segments? (timestamps, scenes, or keypoints) → `export_clips.py` → present

### "Find the key moments and export them as clips"
→ Probe → **estimate + confirm** → keyframes mode → vision analysis → export keypoint clips → report

### "Check video quality"
→ Probe → **estimate + confirm** (technical mode) → full report with QA focus

---

## Notes

- Always clean up `/tmp/video_frames/` after analysis to save space
- For videos >30 min, strongly recommend limiting to a time range unless user explicitly wants full analysis
- If video has audio, note that audio analysis is not currently supported — flag this to user
- Prefer `jpg` over `png` for stills unless user needs transparency or lossless quality
