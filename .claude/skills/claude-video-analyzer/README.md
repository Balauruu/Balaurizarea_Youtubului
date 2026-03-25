# claude-video-analyzer

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue) ![ffmpeg](https://img.shields.io/badge/ffmpeg-required-orange) ![OpenCV](https://img.shields.io/badge/OpenCV-headless-green) ![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple)

A Claude Code skill that analyzes video files for content understanding, technical quality (FPS/smoothness), frame and clip export, and generates detailed markdown reports using Claude's vision capabilities.

Point Claude at any `.mp4`, `.mov`, `.avi`, `.mkv`, or `.webm` file and it will probe the video, estimate the token cost, wait for your confirmation, then extract frames and run batched vision analysis — producing a full timestamped report with optional still exports and MP4 clip cuts.

---

## Installation

### 1. Install the skill

```bash
cp video-analyzer.skill ~/.claude/skills/
```

Once installed, Claude Code automatically activates the skill whenever you reference a video file or use phrases like "analyze this video", "check FPS", "export stills", "find key moments", etc.

### 2. Install dependencies

**macOS**
```bash
brew install ffmpeg && pip install opencv-python-headless numpy
```

**Linux / WSL**
```bash
sudo apt-get install -y ffmpeg && pip install opencv-python-headless numpy --break-system-packages
```

**Windows**
```bash
winget install ffmpeg && pip install opencv-python-headless numpy
```

### 3. Verify

```bash
ffmpeg -version
ffprobe -version
python3 -c "import cv2, numpy; print('OK')"
```

---

## How It Works

Every analysis follows the same 5-step pipeline:

```
1. Probe     → Read video metadata: resolution, FPS, duration, codec, bitrate
2. Estimate  → Calculate token and cost breakdown — shown to you before anything runs
3. Extract   → ffmpeg pulls frames at the rate determined by your chosen mode
4. Analyze   → Frames are sent to Claude vision in batches of 15 for description
5. Export    → Stills, MP4 clips, or a full markdown report — based on your request
```

**Token cost is always estimated and confirmed before any frames are extracted or vision calls are made.** You can approve, cancel, switch modes, or limit to a time range from the confirmation prompt.

---

## Analysis Modes

| Mode | Frame Rate | Best For |
|------|-----------|----------|
| `quick` | 1 fps | Long videos (5+ min), rough overview, podcasts, vlogs |
| `standard` | 2 fps | Default — most content, good balance of detail and cost |
| `detailed` | 5 fps | Fast edits, action sequences, music videos, short clips |
| `technical` | Every frame | FPS/smoothness QA, dropped frame detection |
| `keyframes` | I-frames only | Scene detection, efficient summarization of long content |

---

## Token Cost

Token costs for **10 seconds of 60fps 1080p video** (600 raw frames) across modes:

| Mode | Frames Sent | Input Tokens | Output Tokens | Total | API Cost (Sonnet) |
|------|-------------|-------------|---------------|-------|-------------------|
| `quick` | 10 | ~16,000 | ~400 | ~16,600 | ~$0.0056 |
| `standard` | 20 | ~32,400 | ~800 | ~33,200 | ~$0.0112 |
| `detailed` | 50 | ~80,800 | ~1,600 | ~82,400 | ~$0.0277 |
| `technical` | 600 | ~968,000 | ~16,000 | ~984,000 | ~$0.3312 |
| `keyframes` | ~2-3 | ~5,000 | ~400 | ~5,400 | ~$0.0018 |

> For Claude Code subscription users: no per-token billing, but heavy jobs consume usage quota. A 10-minute video in standard mode is a large job — consider `quick` mode or limiting to a time range.

> Technical mode is intended only for short clips or specific time ranges. A 1-minute 60fps video in technical mode = ~5.9M tokens.

**Resolution scaling:** Calculations above assume 1080p (~1,600 tokens/frame). For 720p, multiply by ~0.69 (~1,100 tokens/frame). For 480p or below, multiply by ~0.5 (~800 tokens/frame).

---

## Usage

Just talk to Claude naturally. No slash commands needed.

### Analyze a video

```
analyze promo.mp4
what's in this video? tutorial.mp4
give me a timeline breakdown of keynote.mp4
```

### Check smoothness / FPS

```
check FPS and smoothness of gameplay.mp4
is gameplay.mp4 smooth? check from 0:30 to 1:00
check for dropped frames in promo.mov
```

### Export stills

```
export stills from every scene change in promo.mp4
export a still every 5 seconds between 1:00 and 2:00 in tutorial.mp4
export stills at 0:30, 1:15, and 2:45 from interview.mp4
give me the best frames from highlights.mp4
```

### Export MP4 clips

```
export the intro clip from 0:00 to 0:15 of promo.mp4
cut out clips for each scene in the video
export the key moments from keynote.mp4 as separate clips
export clip from 1:23.5 to 1:45.0 from promo.mp4, re-encode for accuracy
```

### Find key moments

```
find the key moments and export them as clips from demo.mp4
what are the most important scenes in this video?
analyze minutes 2 through 5 of tutorial.mp4 in detailed mode
```

---

## Output

All outputs land in your working directory under `outputs/`:

```
outputs/
├── video_report.md        ← full analysis with timeline + technical QA
├── stills/
│   ├── still_001_00-01-23.jpg
│   ├── still_002_00-02-45.jpg
│   └── ...
└── clips/
    ├── clip_001_intro_00-00-00.mp4
    ├── clip_002_scene2_00-00-45.mp4
    └── ...
```

The `video_report.md` includes:
- Video metadata table (resolution, codec, FPS, file size, bitrate, audio)
- Technical QA section with smoothness score, dropped frame count, and stutter timestamps
- Full content timeline with `[HH:MM:SS]` descriptions
- Key moments section with still image references
- List of all exported stills and clips

---

## Combining with screen-recorder

`video-analyzer` pairs well with the `screen-recorder` skill. A common workflow:

1. Use `screen-recorder` to capture a session or demo
2. Hand the output `.mp4` to `video-analyzer` to get a timestamped transcript, detect key moments, and export highlight clips

```
record my screen for the next 2 minutes
[... recording ...]
now analyze the recording and export the key moments as clips
```

---

## Scripts Reference

The `scripts/` directory contains standalone Python utilities that the skill orchestrates:

| Script | What it does |
|--------|-------------|
| `probe_video.py` | Runs ffprobe and returns structured JSON metadata |
| `estimate_cost.py` | Calculates token and API cost estimates before analysis |
| `extract_frames.py` | Extracts frames via ffmpeg, builds manifest + technical data |
| `export_clips.py` | Cuts MP4 clips by timestamp, keypoints, or scene detection |
| `export_stills.py` | Exports selected frames as JPEG or PNG stills |
| `generate_report.py` | Assembles all analysis data into a markdown report |

The `references/vision_prompts.md` file contains specialized prompts for different content types: general, promotional, tutorial, gameplay, talking head, music video, and security footage.

---

## Requirements

- Python 3.8+
- ffmpeg + ffprobe (bundled together)
- `opencv-python-headless`
- `numpy`
- Claude Code with an active session

---

## License

MIT — see [LICENSE](LICENSE)
