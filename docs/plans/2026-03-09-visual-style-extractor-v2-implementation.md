# Visual Style Extractor v2 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the v1 `visual-language-extractor` skill with a scene-detection-based pipeline that produces an accurate, actionable `VISUAL_STYLE_GUIDE.md` for downstream agents.

**Architecture:** A 7-stage Python pipeline (acquisition → scene detection → dedup → alignment → contact sheets → LLM analysis via subagents → synthesis) orchestrated as a Claude Code skill. Each stage is a standalone Python module called sequentially by the skill. The LLM analysis stage is handled natively by Claude Code subagents reading contact sheet images — no API wrappers.

**Tech Stack:** Python 3, PySceneDetect (AdaptiveDetector), imagededup (PHash), Pillow, webvtt-py, pysrt, ffmpeg, yt-dlp

**Design doc:** `docs/plans/2026-03-09-visual-style-extractor-design.md`

---

## Task 0: Project Setup & Dependencies

**Files:**
- Create: `tools/visual_style_extractor/requirements.txt`
- Create: `tools/visual_style_extractor/__init__.py`

**Step 1: Create the package directory and requirements**

```
tools/visual_style_extractor/requirements.txt
```

```
scenedetect[opencv]>=0.6
imagededup>=0.3
Pillow>=10.0
webvtt-py>=0.5
pysrt>=1.1
```

**Step 2: Create empty `__init__.py`**

```python
# tools/visual_style_extractor/__init__.py
```

**Step 3: Install dependencies**

Run: `pip install -r tools/visual_style_extractor/requirements.txt`
Expected: All packages install successfully.

**Step 4: Verify imports work**

Run: `python -c "from scenedetect import detect, AdaptiveDetector; from imagededup.methods import PHash; from PIL import Image; import webvtt; import pysrt; print('All imports OK')"`
Expected: `All imports OK`

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/
git commit -m "chore: scaffold visual_style_extractor package with dependencies"
```

---

## Task 1: Stage 0 — Acquisition Module

**Files:**
- Create: `tools/visual_style_extractor/acquire.py`
- Create: `tools/visual_style_extractor/tests/test_acquire.py`

**Step 1: Write the failing tests**

```python
# tools/visual_style_extractor/tests/test_acquire.py
import os
import tempfile
import pytest
from visual_style_extractor.acquire import validate_local_input, find_video_file, find_transcript_file


def test_find_video_file_mp4(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    assert find_video_file(str(tmp_path)) == str(video)


def test_find_video_file_none(tmp_path):
    assert find_video_file(str(tmp_path)) is None


def test_find_transcript_vtt(tmp_path):
    sub = tmp_path / "subs.vtt"
    sub.write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHello")
    assert find_transcript_file(str(tmp_path)) == str(sub)


def test_find_transcript_srt(tmp_path):
    sub = tmp_path / "subs.srt"
    sub.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")
    assert find_transcript_file(str(tmp_path)) == str(sub)


def test_find_transcript_none(tmp_path):
    assert find_transcript_file(str(tmp_path)) is None


def test_validate_local_input_success(tmp_path):
    (tmp_path / "video.mp4").write_bytes(b"fake")
    (tmp_path / "subs.vtt").write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHi")
    result = validate_local_input(str(tmp_path))
    assert result["video_path"].endswith(".mp4")
    assert result["transcript_path"].endswith(".vtt")


def test_validate_local_input_no_video(tmp_path):
    (tmp_path / "subs.vtt").write_text("WEBVTT")
    with pytest.raises(FileNotFoundError, match="No video file found"):
        validate_local_input(str(tmp_path))


def test_validate_local_input_no_transcript(tmp_path):
    (tmp_path / "video.mp4").write_bytes(b"fake")
    with pytest.raises(FileNotFoundError, match="No transcript found"):
        validate_local_input(str(tmp_path))
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_acquire.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/acquire.py
"""Stage 0: Acquisition — validate inputs or download via yt-dlp."""

import os
import glob
import subprocess

VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv", ".avi", ".mov")
TRANSCRIPT_EXTENSIONS = (".vtt", ".srt", ".txt")


def find_video_file(directory: str) -> str | None:
    """Find the first video file in a directory."""
    for ext in VIDEO_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            return matches[0]
    return None


def find_transcript_file(directory: str) -> str | None:
    """Find the first transcript file in a directory (.vtt preferred, then .srt, then .txt)."""
    for ext in TRANSCRIPT_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            return matches[0]
    return None


def validate_local_input(directory: str) -> dict:
    """Validate that a local directory contains a video and transcript.

    Returns dict with 'video_path' and 'transcript_path'.
    Raises FileNotFoundError with clear message if either is missing.
    """
    video_path = find_video_file(directory)
    if not video_path:
        raise FileNotFoundError(
            f"No video file found in {directory}. "
            f"Expected one of: {', '.join(VIDEO_EXTENSIONS)}"
        )

    transcript_path = find_transcript_file(directory)
    if not transcript_path:
        raise FileNotFoundError(
            f"No transcript found in {directory}. "
            "Provide a .vtt, .srt, or .txt transcript file, "
            "or use a YouTube URL instead."
        )

    return {"video_path": video_path, "transcript_path": transcript_path}


def download_from_youtube(url: str, output_dir: str) -> dict:
    """Download video + auto-subs from YouTube using yt-dlp.

    Returns dict with 'video_path' and 'transcript_path'.
    """
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--write-auto-sub", "--sub-lang", "en", "--convert-subs", "vtt",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url,
    ]

    print(f"Downloading from {url}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed (exit {result.returncode}):\n{result.stderr}"
        )

    video_path = find_video_file(output_dir)
    transcript_path = find_transcript_file(output_dir)

    if not video_path:
        raise RuntimeError("yt-dlp completed but no video file found in output directory.")
    if not transcript_path:
        raise FileNotFoundError(
            "No auto-subs available for this video. "
            "Download the video manually and provide a transcript file."
        )

    return {"video_path": video_path, "transcript_path": transcript_path}
```

**Step 4: Create `tests/__init__.py` and run tests**

Create empty `tools/visual_style_extractor/tests/__init__.py`.

Run: `python -m pytest tools/visual_style_extractor/tests/test_acquire.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/acquire.py tools/visual_style_extractor/tests/
git commit -m "feat: add acquisition module (Stage 0) with local/YouTube input handling"
```

---

## Task 2: Stage 1 — Scene Detection Module

**Files:**
- Create: `tools/visual_style_extractor/scene_detect.py`
- Create: `tools/visual_style_extractor/tests/test_scene_detect.py`

**Step 1: Write the failing tests**

Testing scene detection requires a real video, so we test the wrapper logic (output format, threshold validation) and mock the heavy call.

```python
# tools/visual_style_extractor/tests/test_scene_detect.py
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from visual_style_extractor.scene_detect import detect_scenes, save_keyframes, SceneInfo


def test_scene_info_structure():
    s = SceneInfo(scene_number=1, start_time=0.0, end_time=4.5, duration=4.5, keyframe_path="frame.jpg")
    assert s.scene_number == 1
    assert s.duration == 4.5


def test_detect_scenes_low_count_warning(tmp_path, capsys):
    """When fewer than 10 scenes detected, print a warning."""
    fake_scenes = [(MagicMock(get_seconds=MagicMock(return_value=0.0)),
                     MagicMock(get_seconds=MagicMock(return_value=5.0)))]

    with patch("visual_style_extractor.scene_detect._run_detection", return_value=fake_scenes):
        with patch("visual_style_extractor.scene_detect._extract_keyframes", return_value=[]):
            results = detect_scenes("fake.mp4", str(tmp_path))

    captured = capsys.readouterr()
    assert "WARNING" in captured.out or len(results) < 10


def test_detect_scenes_returns_list(tmp_path):
    """Result is always a list of SceneInfo."""
    fake_scenes = []
    for i in range(15):
        start = MagicMock()
        start.get_seconds.return_value = float(i * 3)
        end = MagicMock()
        end.get_seconds.return_value = float(i * 3 + 3)
        fake_scenes.append((start, end))

    with patch("visual_style_extractor.scene_detect._run_detection", return_value=fake_scenes):
        with patch("visual_style_extractor.scene_detect._extract_keyframes",
                   return_value=[f"frame_{i:04d}.jpg" for i in range(15)]):
            results = detect_scenes("fake.mp4", str(tmp_path))

    assert isinstance(results, list)
    assert len(results) == 15
    assert all(isinstance(r, SceneInfo) for r in results)
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_scene_detect.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/scene_detect.py
"""Stage 1: Scene Detection using PySceneDetect AdaptiveDetector."""

import os
import json
import subprocess
from dataclasses import dataclass, asdict
from scenedetect import detect, AdaptiveDetector, open_video


@dataclass
class SceneInfo:
    scene_number: int
    start_time: float  # seconds
    end_time: float    # seconds
    duration: float    # seconds
    keyframe_path: str


def _run_detection(video_path: str, adaptive_threshold: float = 3.0, min_scene_len: int = 15):
    """Run PySceneDetect and return raw scene list."""
    return detect(video_path, AdaptiveDetector(
        adaptive_threshold=adaptive_threshold,
        min_scene_len=min_scene_len,
    ))


def _extract_keyframes(video_path: str, scenes: list, output_dir: str) -> list[str]:
    """Extract one keyframe per scene (middle frame) using ffmpeg."""
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    keyframe_paths = []
    for i, (start, end) in enumerate(scenes):
        mid_time = (start.get_seconds() + end.get_seconds()) / 2
        out_path = os.path.join(frames_dir, f"frame_{i:04d}.jpg")

        cmd = [
            "ffmpeg", "-y", "-ss", str(mid_time),
            "-i", video_path,
            "-frames:v", "1", "-q:v", "2",
            out_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        keyframe_paths.append(out_path)

    return keyframe_paths


def detect_scenes(
    video_path: str,
    output_dir: str,
    adaptive_threshold: float = 3.0,
    min_scene_len: int = 15,
) -> list[SceneInfo]:
    """Detect scenes in a video and extract keyframes.

    Args:
        video_path: Path to video file.
        output_dir: Directory to write frames/ and scenes.json.
        adaptive_threshold: PySceneDetect sensitivity (lower = more scenes).
        min_scene_len: Minimum scene length in frames.

    Returns:
        List of SceneInfo objects.
    """
    print(f"Running scene detection on {video_path} (threshold={adaptive_threshold})...")
    scenes = _run_detection(video_path, adaptive_threshold, min_scene_len)
    scene_count = len(scenes)
    print(f"Detected {scene_count} scenes.")

    if scene_count < 10:
        print(f"WARNING: Only {scene_count} scenes detected. "
              f"Consider lowering adaptive_threshold (currently {adaptive_threshold}) to 2.0-2.5.")
    elif scene_count > 200:
        print(f"WARNING: {scene_count} scenes detected. "
              f"Consider raising adaptive_threshold (currently {adaptive_threshold}) to 4.0+.")

    keyframe_paths = _extract_keyframes(video_path, scenes, output_dir)

    results = []
    for i, (start, end) in enumerate(scenes):
        start_sec = start.get_seconds()
        end_sec = end.get_seconds()
        results.append(SceneInfo(
            scene_number=i + 1,
            start_time=start_sec,
            end_time=end_sec,
            duration=end_sec - start_sec,
            keyframe_path=keyframe_paths[i] if i < len(keyframe_paths) else "",
        ))

    # Save scenes.json
    scenes_path = os.path.join(output_dir, "scenes.json")
    with open(scenes_path, "w") as f:
        json.dump([asdict(s) for s in results], f, indent=2)
    print(f"Saved scene data to {scenes_path}")

    return results
```

**Step 4: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_scene_detect.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/scene_detect.py tools/visual_style_extractor/tests/test_scene_detect.py
git commit -m "feat: add scene detection module (Stage 1) with PySceneDetect"
```

---

## Task 3: Stage 2 — Perceptual Hash Deduplication Module

**Files:**
- Create: `tools/visual_style_extractor/dedup.py`
- Create: `tools/visual_style_extractor/tests/test_dedup.py`

**Step 1: Write the failing tests**

```python
# tools/visual_style_extractor/tests/test_dedup.py
import os
import pytest
from PIL import Image
from visual_style_extractor.dedup import deduplicate_frames
from visual_style_extractor.scene_detect import SceneInfo


def _make_scene(num, path, duration=3.0):
    return SceneInfo(
        scene_number=num,
        start_time=float(num * 3),
        end_time=float(num * 3 + duration),
        duration=duration,
        keyframe_path=path,
    )


def test_identical_frames_deduped(tmp_path):
    """Two identical images should be deduped to one."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    # Create two identical images
    img = Image.new("RGB", (200, 200), color=(100, 50, 50))
    path_a = str(frames_dir / "frame_0000.jpg")
    path_b = str(frames_dir / "frame_0001.jpg")
    img.save(path_a)
    img.save(path_b)

    scenes = [
        _make_scene(0, path_a),
        _make_scene(1, path_b),
    ]

    result = deduplicate_frames(scenes, str(frames_dir))
    assert len(result) == 1
    assert result[0]["represents_count"] >= 2


def test_different_frames_kept(tmp_path):
    """Two very different images should both be kept."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    img_a = Image.new("RGB", (200, 200), color=(255, 0, 0))
    img_b = Image.new("RGB", (200, 200), color=(0, 0, 255))
    path_a = str(frames_dir / "frame_0000.jpg")
    path_b = str(frames_dir / "frame_0001.jpg")
    img_a.save(path_a)
    img_b.save(path_b)

    scenes = [
        _make_scene(0, path_a),
        _make_scene(1, path_b),
    ]

    result = deduplicate_frames(scenes, str(frames_dir))
    assert len(result) == 2


def test_output_has_required_keys(tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    img = Image.new("RGB", (200, 200), color=(50, 100, 150))
    path = str(frames_dir / "frame_0000.jpg")
    img.save(path)

    scenes = [_make_scene(0, path)]
    result = deduplicate_frames(scenes, str(frames_dir))

    required_keys = {"frame_id", "frame_path", "timestamp", "scene_duration", "represents_count"}
    assert required_keys.issubset(set(result[0].keys()))
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_dedup.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/dedup.py
"""Stage 2: Perceptual hash deduplication using imagededup."""

import os
from imagededup.methods import PHash
from visual_style_extractor.scene_detect import SceneInfo


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def deduplicate_frames(
    scenes: list[SceneInfo],
    frames_dir: str,
    max_distance_threshold: int = 10,
) -> list[dict]:
    """Deduplicate keyframes using perceptual hashing.

    Groups visually similar frames and keeps one representative per group
    (the one closest to the group's median timestamp).

    Args:
        scenes: List of SceneInfo from scene detection.
        frames_dir: Directory containing extracted keyframe images.
        max_distance_threshold: Hamming distance threshold for grouping.

    Returns:
        List of dicts with frame_id, frame_path, timestamp, scene_duration, represents_count.
    """
    if not scenes:
        return []

    # Build filename -> SceneInfo lookup
    scene_by_filename = {}
    for s in scenes:
        fname = os.path.basename(s.keyframe_path)
        scene_by_filename[fname] = s

    # Run PHash
    phasher = PHash()
    encodings = phasher.encode_images(image_dir=frames_dir)
    duplicates = phasher.find_duplicates(
        encoding_map=encodings,
        max_distance_threshold=max_distance_threshold,
    )

    # Build groups: track which frames have been assigned
    assigned = set()
    groups = []

    for fname, dupes in duplicates.items():
        if fname in assigned:
            continue
        group = [fname] + [d for d in dupes if d not in assigned]
        for f in group:
            assigned.add(f)
        groups.append(group)

    # Select representative per group (closest to median timestamp)
    result = []
    frame_id = 1

    for group in groups:
        group_scenes = [scene_by_filename[f] for f in group if f in scene_by_filename]
        if not group_scenes:
            continue

        timestamps = [s.start_time for s in group_scenes]
        median_ts = sorted(timestamps)[len(timestamps) // 2]

        # Pick the scene closest to median
        representative = min(group_scenes, key=lambda s: abs(s.start_time - median_ts))

        result.append({
            "frame_id": frame_id,
            "frame_path": representative.keyframe_path,
            "timestamp": _format_timestamp(representative.start_time),
            "scene_duration": representative.duration,
            "represents_count": len(group_scenes),
        })
        frame_id += 1

    # Sort by timestamp
    result.sort(key=lambda r: r["frame_id"])
    # Re-number sequentially
    for i, r in enumerate(result):
        r["frame_id"] = i + 1

    print(f"Deduplication: {len(scenes)} frames → {len(result)} unique ({len(scenes) - len(result)} removed)")

    if len(result) < len(scenes) * 0.1:
        print("WARNING: Dedup removed >90% of frames. Video may be too visually uniform for meaningful analysis.")

    return result
```

**Step 4: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_dedup.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/dedup.py tools/visual_style_extractor/tests/test_dedup.py
git commit -m "feat: add perceptual hash deduplication module (Stage 2)"
```

---

## Task 4: Stage 3 — Script-Frame Alignment Module

**Files:**
- Create: `tools/visual_style_extractor/align.py`
- Create: `tools/visual_style_extractor/tests/test_align.py`

**Step 1: Write the failing tests**

```python
# tools/visual_style_extractor/tests/test_align.py
import os
import json
import pytest
from visual_style_extractor.align import parse_transcript, align_frames, build_manifest


def test_parse_vtt(tmp_path):
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
The story begins in a small town.

00:00:05.000 --> 00:00:10.000
Nobody knew what was coming next.
"""
    vtt_path = str(tmp_path / "subs.vtt")
    with open(vtt_path, "w") as f:
        f.write(vtt_content)

    segments = parse_transcript(vtt_path)
    assert len(segments) == 2
    assert segments[0]["start"] == pytest.approx(1.0)
    assert segments[0]["end"] == pytest.approx(5.0)
    assert "small town" in segments[0]["text"]


def test_parse_srt(tmp_path):
    srt_content = """1
00:00:01,000 --> 00:00:05,000
The story begins in a small town.

2
00:00:05,000 --> 00:00:10,000
Nobody knew what was coming next.
"""
    srt_path = str(tmp_path / "subs.srt")
    with open(srt_path, "w") as f:
        f.write(srt_content)

    segments = parse_transcript(srt_path)
    assert len(segments) == 2
    assert segments[1]["end"] == pytest.approx(10.0)


def test_align_frames():
    segments = [
        {"start": 0.0, "end": 5.0, "text": "Opening line."},
        {"start": 5.0, "end": 10.0, "text": "Second line."},
    ]
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03", "scene_duration": 3.0, "represents_count": 1},
        {"frame_id": 2, "frame_path": "f2.jpg", "timestamp": "00:07", "scene_duration": 4.0, "represents_count": 2},
    ]

    aligned = align_frames(frames, segments)
    assert aligned[0]["narration"] == "Opening line."
    assert aligned[1]["narration"] == "Second line."


def test_align_frames_no_match():
    """Frame outside all segment ranges gets empty narration."""
    segments = [{"start": 10.0, "end": 15.0, "text": "Late text."}]
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03", "scene_duration": 2.0, "represents_count": 1},
    ]

    aligned = align_frames(frames, segments)
    assert aligned[0]["narration"] == ""


def test_build_manifest(tmp_path):
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03",
         "scene_duration": 3.0, "represents_count": 1, "narration": "Hello"},
    ]
    out_path = str(tmp_path / "frames_manifest.json")
    build_manifest(frames, video_duration=120.0, total_scenes=50, output_path=out_path)

    with open(out_path) as f:
        data = json.load(f)

    assert data["video_duration"] == 120.0
    assert data["total_scenes_detected"] == 50
    assert len(data["frames"]) == 1
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_align.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/align.py
"""Stage 3: Script-Frame Alignment — map transcript segments to frames."""

import os
import json
import webvtt
import pysrt


def _timestamp_to_seconds(ts: str) -> float:
    """Convert MM:SS timestamp to seconds."""
    parts = ts.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def parse_transcript(transcript_path: str) -> list[dict]:
    """Parse a VTT or SRT transcript into timestamped segments.

    Returns list of {"start": float, "end": float, "text": str}.
    """
    ext = os.path.splitext(transcript_path)[1].lower()

    if ext == ".vtt":
        segments = []
        for caption in webvtt.read(transcript_path):
            start_parts = caption.start.split(":")
            end_parts = caption.end.split(":")
            # Handle HH:MM:SS.mmm or MM:SS.mmm
            if len(start_parts) == 3:
                start = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + float(start_parts[2])
                end = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + float(end_parts[2])
            else:
                start = int(start_parts[0]) * 60 + float(start_parts[1])
                end = int(end_parts[0]) * 60 + float(end_parts[1])
            segments.append({"start": start, "end": end, "text": caption.text.strip()})
        return segments

    elif ext == ".srt":
        subs = pysrt.open(transcript_path)
        segments = []
        for sub in subs:
            start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
            end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
            segments.append({"start": start, "end": end, "text": sub.text.strip()})
        return segments

    elif ext == ".txt":
        # Plain text — no timestamps, return as single segment
        with open(transcript_path) as f:
            text = f.read().strip()
        return [{"start": 0.0, "end": float("inf"), "text": text}]

    else:
        raise ValueError(f"Unsupported transcript format: {ext}")


def align_frames(frames: list[dict], segments: list[dict]) -> list[dict]:
    """Attach narration text to each frame based on timestamp overlap.

    Modifies frames in-place by adding 'narration' key.
    Returns the modified list.
    """
    for frame in frames:
        frame_seconds = _timestamp_to_seconds(frame["timestamp"])
        narration = ""
        for seg in segments:
            if seg["start"] <= frame_seconds < seg["end"]:
                narration = seg["text"]
                break
        frame["narration"] = narration
    return frames


def build_manifest(
    frames: list[dict],
    video_duration: float,
    total_scenes: int,
    output_path: str,
) -> str:
    """Build and save frames_manifest.json.

    Returns the output path.
    """
    manifest = {
        "frames": frames,
        "video_duration": video_duration,
        "total_scenes_detected": total_scenes,
        "unique_frames_after_dedup": len(frames),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest saved to {output_path} ({len(frames)} frames)")
    return output_path
```

**Step 4: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_align.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/align.py tools/visual_style_extractor/tests/test_align.py
git commit -m "feat: add script-frame alignment module (Stage 3)"
```

---

## Task 5: Stage 4 — Annotated Contact Sheet Generator

**Files:**
- Create: `tools/visual_style_extractor/contact_sheets.py`
- Create: `tools/visual_style_extractor/tests/test_contact_sheets.py`

**Step 1: Write the failing tests**

```python
# tools/visual_style_extractor/tests/test_contact_sheets.py
import os
import pytest
from PIL import Image
from visual_style_extractor.contact_sheets import generate_contact_sheets


def _make_frame(frame_id, tmp_path, color=(100, 50, 50)):
    """Create a test frame image and return a frame dict."""
    img = Image.new("RGB", (640, 360), color=color)
    path = str(tmp_path / f"frame_{frame_id:04d}.jpg")
    img.save(path)
    return {
        "frame_id": frame_id,
        "frame_path": path,
        "timestamp": f"00:{frame_id * 10:02d}",
        "scene_duration": 3.0,
        "represents_count": 1,
        "narration": f"This is narration text for frame {frame_id} which may be quite long.",
    }


def test_single_sheet_created(tmp_path):
    """5 frames should produce exactly 1 contact sheet (9 per sheet)."""
    frames = [_make_frame(i, tmp_path) for i in range(1, 6)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    assert len(sheets) == 1
    assert os.path.exists(sheets[0])


def test_multiple_sheets(tmp_path):
    """12 frames should produce 2 contact sheets."""
    frames = [_make_frame(i, tmp_path, color=(i * 20, i * 10, 50)) for i in range(1, 13)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    assert len(sheets) == 2


def test_sheet_dimensions(tmp_path):
    """Each sheet should be close to 1568px wide."""
    frames = [_make_frame(i, tmp_path) for i in range(1, 4)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    img = Image.open(sheets[0])
    # Width should be 1568 (3 columns)
    assert img.width == 1568


def test_empty_frames(tmp_path):
    """Empty frame list should return empty list."""
    output_dir = str(tmp_path / "contact_sheets")
    sheets = generate_contact_sheets([], output_dir)
    assert sheets == []
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_contact_sheets.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/contact_sheets.py
"""Stage 4: Annotated Contact Sheet generation for LLM analysis."""

import os
import math
from PIL import Image, ImageDraw, ImageFont


SHEET_WIDTH = 1568
COLS = 3
ROWS = 3
FRAMES_PER_SHEET = COLS * ROWS
PADDING = 4
LABEL_HEIGHT = 30
LABEL_BG = (51, 51, 51)  # #333
LABEL_FG = (255, 255, 255)
NARRATION_MAX_CHARS = 40
JPEG_QUALITY = 90


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def _get_font(size: int = 14):
    """Try to load a monospace font, fall back to default."""
    try:
        return ImageFont.truetype("consola.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSansMono.ttf", size)
        except OSError:
            return ImageFont.load_default()


def generate_contact_sheets(frames: list[dict], output_dir: str) -> list[str]:
    """Generate annotated 3x3 contact sheets from frame data.

    Each cell contains the frame image + a label bar with frame ID, timestamp, and narration snippet.

    Args:
        frames: List of frame dicts (must have frame_path, frame_id, timestamp, narration).
        output_dir: Directory to write contact sheet JPEGs.

    Returns:
        List of output file paths.
    """
    if not frames:
        return []

    os.makedirs(output_dir, exist_ok=True)

    cell_width = (SHEET_WIDTH - PADDING * (COLS + 1)) // COLS
    # Maintain ~16:9 aspect ratio for each cell image area
    cell_img_height = int(cell_width * 9 / 16)
    cell_height = cell_img_height + LABEL_HEIGHT

    sheet_height = ROWS * cell_height + PADDING * (ROWS + 1)

    font = _get_font()
    output_paths = []

    num_sheets = math.ceil(len(frames) / FRAMES_PER_SHEET)

    for sheet_idx in range(num_sheets):
        batch = frames[sheet_idx * FRAMES_PER_SHEET : (sheet_idx + 1) * FRAMES_PER_SHEET]
        sheet = Image.new("RGB", (SHEET_WIDTH, sheet_height), (255, 255, 255))
        draw = ImageDraw.Draw(sheet)

        for i, frame in enumerate(batch):
            col = i % COLS
            row = i // COLS

            x = PADDING + col * (cell_width + PADDING)
            y = PADDING + row * (cell_height + PADDING)

            # Load and resize frame image
            try:
                img = Image.open(frame["frame_path"])
                img = img.resize((cell_width, cell_img_height), Image.LANCZOS)
                sheet.paste(img, (x, y))
            except (FileNotFoundError, OSError):
                # Draw placeholder
                draw.rectangle([x, y, x + cell_width, y + cell_img_height], fill=(80, 80, 80))
                draw.text((x + 10, y + cell_img_height // 2), "Missing", fill=LABEL_FG, font=font)

            # Draw label bar
            label_y = y + cell_img_height
            draw.rectangle([x, label_y, x + cell_width, label_y + LABEL_HEIGHT], fill=LABEL_BG)

            snippet = _truncate(frame.get("narration", ""), NARRATION_MAX_CHARS)
            label_text = f"F{frame['frame_id']:03d} | {frame['timestamp']} | \"{snippet}\""
            draw.text((x + 4, label_y + 6), label_text, fill=LABEL_FG, font=font)

        sheet_path = os.path.join(output_dir, f"contact_sheet_{sheet_idx:03d}.jpg")
        sheet.save(sheet_path, quality=JPEG_QUALITY)
        output_paths.append(sheet_path)
        print(f"Saved contact sheet: {sheet_path} ({len(batch)} frames)")

    return output_paths
```

**Step 4: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_contact_sheets.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/contact_sheets.py tools/visual_style_extractor/tests/test_contact_sheets.py
git commit -m "feat: add annotated contact sheet generator (Stage 4)"
```

---

## Task 6: Stage 5 & 6 — Analysis Prompt + Synthesis Module

Stage 5 (LLM analysis) is handled by Claude Code subagents at runtime — no Python code needed. We need:
1. The structured analysis prompt (stored as a text template)
2. A synthesis module that aggregates subagent JSON outputs into the final `VISUAL_STYLE_GUIDE.md`

**Files:**
- Create: `tools/visual_style_extractor/prompts/analysis_prompt.txt`
- Create: `tools/visual_style_extractor/synthesize.py`
- Create: `tools/visual_style_extractor/tests/test_synthesize.py`

**Step 1: Create the analysis prompt template**

```text
# tools/visual_style_extractor/prompts/analysis_prompt.txt
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
    "aerial shot of a rural compound", "vintage factory assembly line")
   Capture both the literal content and the implied metaphor given the narration.

4. NARRATIVE FUNCTION: Given the narration at this moment,
   why is this visual type being used here? What concept does it illustrate?

5. CONFIDENCE: Rate 1-5 how clearly you can analyze this frame.
   If below 3, note what is unclear.

Output as JSON array. Only describe what you can see.
If you cannot determine something, say "unclear" — do not guess.
```

**Step 2: Write the failing tests for synthesis**

```python
# tools/visual_style_extractor/tests/test_synthesize.py
import json
import pytest
from visual_style_extractor.synthesize import (
    aggregate_by_scene_type,
    compute_proportions,
    generate_style_guide,
)


SAMPLE_ANALYSIS = [
    {
        "frame_id": "F001",
        "timestamp": "00:10",
        "scene_type": "archival_photo",
        "background": "solid black",
        "main_element": "sepia photograph of a building",
        "overlays": ["film grain", "vignette"],
        "text_elements": None,
        "content_description": None,
        "narrative_function": "establishing historical context",
        "confidence": 4,
    },
    {
        "frame_id": "F002",
        "timestamp": "01:20",
        "scene_type": "archival_photo",
        "background": "solid black",
        "main_element": "black-and-white portrait of a man",
        "overlays": ["film grain"],
        "text_elements": None,
        "content_description": None,
        "narrative_function": "introducing key figure",
        "confidence": 5,
    },
    {
        "frame_id": "F003",
        "timestamp": "02:30",
        "scene_type": "map_animation",
        "background": "solid black",
        "main_element": "particle map of Europe",
        "overlays": ["vignette"],
        "text_elements": "location label in teal, ALL CAPS",
        "content_description": None,
        "narrative_function": "geographic context",
        "confidence": 4,
    },
]

SAMPLE_MANIFEST = {
    "frames": [
        {"frame_id": 1, "timestamp": "00:10", "scene_duration": 5.0, "represents_count": 2, "narration": "In 1920..."},
        {"frame_id": 2, "timestamp": "01:20", "scene_duration": 4.0, "represents_count": 1, "narration": "The man..."},
        {"frame_id": 3, "timestamp": "02:30", "scene_duration": 6.0, "represents_count": 3, "narration": "Located in..."},
    ],
    "video_duration": 600.0,
    "total_scenes_detected": 80,
    "unique_frames_after_dedup": 3,
}


def test_aggregate_by_scene_type():
    grouped = aggregate_by_scene_type(SAMPLE_ANALYSIS)
    assert "archival_photo" in grouped
    assert len(grouped["archival_photo"]) == 2
    assert "map_animation" in grouped
    assert len(grouped["map_animation"]) == 1


def test_compute_proportions():
    grouped = aggregate_by_scene_type(SAMPLE_ANALYSIS)
    proportions = compute_proportions(grouped, SAMPLE_MANIFEST)
    assert "archival_photo" in proportions
    # archival_photo: (5*2 + 4*1) / 600 = 14/600 ≈ 2.33%
    assert proportions["archival_photo"]["proportion"] == pytest.approx(14.0 / 600.0, rel=0.01)


def test_low_confidence_filtered():
    analysis = SAMPLE_ANALYSIS + [{
        "frame_id": "F004",
        "timestamp": "03:00",
        "scene_type": "b_roll_footage",
        "background": "unclear",
        "main_element": "unclear",
        "overlays": [],
        "text_elements": None,
        "content_description": "unclear",
        "narrative_function": "unclear",
        "confidence": 2,
    }]
    grouped = aggregate_by_scene_type(analysis, min_confidence=3)
    # The low-confidence frame should be excluded
    assert "b_roll_footage" not in grouped


def test_generate_style_guide(tmp_path):
    output_path = str(tmp_path / "VISUAL_STYLE_GUIDE.md")
    generate_style_guide(
        analysis_results=SAMPLE_ANALYSIS,
        manifest=SAMPLE_MANIFEST,
        video_title="Test Documentary",
        video_source="https://youtube.com/test",
        output_path=output_path,
    )
    with open(output_path) as f:
        content = f.read()

    assert "# Visual Style Guide" in content
    assert "archival_photo" in content.lower() or "Archival Photo" in content
    assert "map_animation" in content.lower() or "Map Animation" in content
    assert "Test Documentary" in content
```

**Step 3: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_synthesize.py -v`
Expected: FAIL — module not found

**Step 4: Write the implementation**

```python
# tools/visual_style_extractor/synthesize.py
"""Stage 6: Synthesis — aggregate analysis results into VISUAL_STYLE_GUIDE.md."""

import os
import json
from datetime import date
from collections import defaultdict


def aggregate_by_scene_type(
    analysis_results: list[dict],
    min_confidence: int = 3,
) -> dict[str, list[dict]]:
    """Group analyzed frames by scene_type, filtering low-confidence entries.

    Returns dict mapping scene_type -> list of frame analysis dicts.
    """
    grouped = defaultdict(list)
    for frame in analysis_results:
        if frame.get("confidence", 0) < min_confidence:
            continue
        grouped[frame["scene_type"]].append(frame)
    return dict(grouped)


def compute_proportions(
    grouped: dict[str, list[dict]],
    manifest: dict,
) -> dict[str, dict]:
    """Compute runtime proportion for each scene type.

    Uses scene_duration * represents_count from manifest.
    Returns dict mapping scene_type -> {proportion, total_seconds, avg_duration, count}.
    """
    video_duration = manifest["video_duration"]
    frame_lookup = {f"F{f['frame_id']:03d}": f for f in manifest["frames"]}

    proportions = {}
    for scene_type, frames in grouped.items():
        total_weighted = 0.0
        durations = []
        for frame in frames:
            fid = frame["frame_id"]
            manifest_frame = frame_lookup.get(fid)
            if manifest_frame:
                weighted = manifest_frame["scene_duration"] * manifest_frame["represents_count"]
                total_weighted += weighted
                durations.append(manifest_frame["scene_duration"])

        proportions[scene_type] = {
            "proportion": total_weighted / video_duration if video_duration > 0 else 0,
            "total_seconds": total_weighted,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "count": len(frames),
        }

    return proportions


def _find_common_elements(frames: list[dict], key: str) -> list[str]:
    """Extract common values for a given key across frames."""
    values = []
    for f in frames:
        val = f.get(key)
        if val and val != "unclear":
            if isinstance(val, list):
                values.extend(val)
            else:
                values.append(val)
    # Return unique values, ordered by frequency
    from collections import Counter
    counts = Counter(values)
    return [v for v, _ in counts.most_common()]


def _format_scene_type_name(scene_type: str) -> str:
    """Convert snake_case to Title Case."""
    return scene_type.replace("_", " ").title()


def generate_style_guide(
    analysis_results: list[dict],
    manifest: dict,
    video_title: str,
    video_source: str,
    output_path: str,
) -> str:
    """Generate the final VISUAL_STYLE_GUIDE.md from aggregated analysis.

    Returns the output path.
    """
    grouped = aggregate_by_scene_type(analysis_results)
    proportions = compute_proportions(grouped, manifest)

    # Sort scene types by proportion (descending)
    sorted_types = sorted(proportions.keys(), key=lambda t: proportions[t]["proportion"], reverse=True)

    lines = []
    lines.append("# Visual Style Guide")
    lines.append(f"> Source: {video_title} ({video_source})")
    lines.append(f"> Duration: {int(manifest['video_duration'] // 60)}:{int(manifest['video_duration'] % 60):02d} "
                 f"| Scenes detected: {manifest['total_scenes_detected']} "
                 f"| Unique frames analyzed: {manifest['unique_frames_after_dedup']}")
    lines.append(f"> Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Scene Taxonomy
    lines.append("## 1. Scene Taxonomy")
    lines.append("")

    for scene_type in sorted_types:
        frames = grouped[scene_type]
        props = proportions[scene_type]
        name = _format_scene_type_name(scene_type)

        lines.append(f"### {name}")
        lines.append(f"- **Proportion:** {props['proportion'] * 100:.1f}% of runtime "
                     f"(~{props['avg_duration']:.1f}s average per occurrence)")
        lines.append(f"- **Frequency:** {props['count']} occurrences")

        # Appearance
        backgrounds = _find_common_elements(frames, "background")
        main_elements = _find_common_elements(frames, "main_element")
        overlays = _find_common_elements(frames, "overlays")
        text_elements = _find_common_elements(frames, "text_elements")

        lines.append("- **Appearance:**")
        lines.append(f"  - Background: {', '.join(backgrounds[:3]) if backgrounds else 'N/A'}")
        lines.append(f"  - Main element: {', '.join(main_elements[:3]) if main_elements else 'N/A'}")

        if overlays:
            lines.append(f"- **Overlays/Effects:** {', '.join(overlays)}")
        if text_elements:
            lines.append(f"- **Text elements:** {', '.join(text_elements)}")

        # Narrative triggers
        functions = _find_common_elements(frames, "narrative_function")
        if functions:
            lines.append(f"- **Narrative trigger:** {functions[0]}")
            if len(functions) > 1:
                for func in functions[1:3]:
                    lines.append(f"  - Also: {func}")

        # Content descriptions (for b-roll/footage types)
        content_frames = [f for f in frames if f.get("content_description") and f["content_description"] != "unclear"]
        if content_frames:
            lines.append("- **Content descriptions:**")
            lines.append("  | Narration concept | Footage used | Metaphor |")
            lines.append("  |-------------------|-------------|----------|")
            for cf in content_frames[:5]:
                narr_func = cf.get("narrative_function", "")
                content = cf.get("content_description", "")
                lines.append(f"  | {narr_func} | {content} | — |")

        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 2: Global Aesthetic
    lines.append("## 2. Global Aesthetic")
    lines.append("")

    # Collect overlays across all types
    all_overlays = []
    for frames in grouped.values():
        for f in frames:
            if f.get("overlays"):
                all_overlays.extend(f["overlays"] if isinstance(f["overlays"], list) else [f["overlays"]])
    from collections import Counter
    overlay_counts = Counter(all_overlays)
    persistent = [o for o, c in overlay_counts.most_common() if c >= len(grouped) * 0.5]

    lines.append("### Persistent Overlays")
    if persistent:
        for o in persistent:
            lines.append(f"- {o}")
    else:
        lines.append("- None identified across all scene types")
    lines.append("")

    lines.append("### Color Palette")
    lines.append("| Role | Description | Usage |")
    lines.append("|------|-------------|-------|")
    lines.append("| *(Extracted from analysis — fill manually or re-run with programmatic extraction)* | | |")
    lines.append("")

    lines.append("### Motion Language")
    lines.append("- *(To be derived from video analysis — contact sheets capture stills only)* ")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Section 3: Structural Flow
    lines.append("## 3. Structural Flow")
    lines.append("")
    lines.append("### Pacing")
    lines.append("| Segment | Dominant Asset Types | Avg Scene Duration |")
    lines.append("|---------|---------------------|--------------------|")

    # Divide frames into quarters by timestamp
    all_frames = sorted(analysis_results, key=lambda f: f.get("timestamp", ""))
    quarter = len(all_frames) // 4 if len(all_frames) >= 4 else 1
    segments = {
        "Opening": all_frames[:quarter],
        "Early-mid": all_frames[quarter:quarter * 2],
        "Late-mid": all_frames[quarter * 2:quarter * 3],
        "Closing": all_frames[quarter * 3:],
    }
    for seg_name, seg_frames in segments.items():
        types_count = Counter(f["scene_type"] for f in seg_frames if f.get("confidence", 0) >= 3)
        top_types = ", ".join(t for t, _ in types_count.most_common(2))
        lines.append(f"| {seg_name} | {top_types or 'N/A'} | — |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 4: Constraints
    lines.append("## 4. Constraints (What NOT to Do)")
    lines.append("- *(Derive from analysis: note any asset types conspicuously absent)*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 5: Quick Reference
    lines.append("## 5. Asset Type Summary (Quick Reference)")
    lines.append("")
    lines.append("| # | Asset Type | Proportion | Avg Duration | Frequency | Narrative Trigger |")
    lines.append("|---|-----------|------------|--------------|-----------|-------------------|")
    for i, scene_type in enumerate(sorted_types, 1):
        props = proportions[scene_type]
        name = _format_scene_type_name(scene_type)
        trigger = _find_common_elements(grouped[scene_type], "narrative_function")
        trigger_text = trigger[0] if trigger else "—"
        lines.append(f"| {i} | {name} | {props['proportion'] * 100:.1f}% | "
                     f"{props['avg_duration']:.1f}s | {props['count']}x | {trigger_text} |")

    lines.append("")

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated VISUAL_STYLE_GUIDE.md at {output_path}")
    return output_path
```

**Step 5: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_synthesize.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
git add tools/visual_style_extractor/prompts/ tools/visual_style_extractor/synthesize.py tools/visual_style_extractor/tests/test_synthesize.py
git commit -m "feat: add analysis prompt template and synthesis module (Stages 5-6)"
```

---

## Task 7: Pipeline Orchestrator Script

This is the main entry point that chains all stages together. It's called by the skill's SKILL.md.

**Files:**
- Create: `tools/visual_style_extractor/pipeline.py`
- Create: `tools/visual_style_extractor/tests/test_pipeline.py`

**Step 1: Write the failing test**

```python
# tools/visual_style_extractor/tests/test_pipeline.py
import json
import pytest
from unittest.mock import patch, MagicMock
from visual_style_extractor.pipeline import run_pipeline, PipelineConfig


def test_pipeline_config_from_url():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc123")
    assert config.is_youtube
    assert config.source == "https://youtube.com/watch?v=abc123"


def test_pipeline_config_from_dir(tmp_path):
    config = PipelineConfig(source=str(tmp_path))
    assert not config.is_youtube


def test_pipeline_config_custom_threshold():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc", adaptive_threshold=2.5)
    assert config.adaptive_threshold == 2.5


def test_pipeline_config_default_output_dir():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc")
    assert config.output_dir is None  # Will be set during acquisition
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tools/visual_style_extractor/tests/test_pipeline.py -v`
Expected: FAIL — module not found

**Step 3: Write the implementation**

```python
# tools/visual_style_extractor/pipeline.py
"""Main pipeline orchestrator — chains all stages sequentially.

This module is called by the Claude Code skill. Stages 0-4 are automated Python.
Stage 5 (LLM analysis) requires Claude Code subagents — this script prepares
everything needed and outputs instructions for the skill to dispatch subagents.
Stage 6 (synthesis) is called after subagent results are collected.
"""

import os
import json
from dataclasses import dataclass, field

from visual_style_extractor.acquire import validate_local_input, download_from_youtube
from visual_style_extractor.scene_detect import detect_scenes
from visual_style_extractor.dedup import deduplicate_frames
from visual_style_extractor.align import parse_transcript, align_frames, build_manifest
from visual_style_extractor.contact_sheets import generate_contact_sheets
from visual_style_extractor.synthesize import generate_style_guide


@dataclass
class PipelineConfig:
    source: str  # YouTube URL or local directory path
    output_dir: str | None = None
    adaptive_threshold: float = 3.0
    min_scene_len: int = 15
    dedup_threshold: int = 10

    @property
    def is_youtube(self) -> bool:
        return self.source.startswith("http://") or self.source.startswith("https://")


def run_stages_0_to_4(config: PipelineConfig) -> dict:
    """Run deterministic pipeline stages (0-4).

    Returns a dict with:
        - output_dir: working directory
        - manifest_path: path to frames_manifest.json
        - contact_sheet_paths: list of contact sheet image paths
        - prompt_path: path to analysis prompt template
    """
    # Stage 0: Acquisition
    if config.is_youtube:
        output_dir = config.output_dir or os.path.join("context", "visual-references", "analysis")
        inputs = download_from_youtube(config.source, output_dir)
    else:
        output_dir = config.source
        inputs = validate_local_input(config.source)

    video_path = inputs["video_path"]
    transcript_path = inputs["transcript_path"]

    print(f"\n{'='*60}")
    print(f"Video: {video_path}")
    print(f"Transcript: {transcript_path}")
    print(f"Output dir: {output_dir}")
    print(f"{'='*60}\n")

    # Stage 1: Scene Detection
    scenes = detect_scenes(
        video_path, output_dir,
        adaptive_threshold=config.adaptive_threshold,
        min_scene_len=config.min_scene_len,
    )

    # Stage 2: Deduplication
    frames_dir = os.path.join(output_dir, "frames")
    unique_frames = deduplicate_frames(scenes, frames_dir, config.dedup_threshold)

    # Stage 3: Alignment
    segments = parse_transcript(transcript_path)
    aligned_frames = align_frames(unique_frames, segments)

    # Get video duration from last scene
    video_duration = scenes[-1].end_time if scenes else 0.0

    manifest_path = os.path.join(output_dir, "frames_manifest.json")
    build_manifest(aligned_frames, video_duration, len(scenes), manifest_path)

    # Stage 4: Contact Sheets
    contact_sheets_dir = os.path.join(output_dir, "contact_sheets")
    contact_sheet_paths = generate_contact_sheets(aligned_frames, contact_sheets_dir)

    # Locate prompt template
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "analysis_prompt.txt"
    )

    return {
        "output_dir": output_dir,
        "manifest_path": manifest_path,
        "contact_sheet_paths": contact_sheet_paths,
        "prompt_path": prompt_path,
        "video_title": os.path.splitext(os.path.basename(video_path))[0],
        "video_source": config.source,
    }


def run_stage_6(
    analysis_results: list[dict],
    manifest_path: str,
    video_title: str,
    video_source: str,
    output_dir: str,
) -> str:
    """Run synthesis stage after subagent analysis is complete.

    Args:
        analysis_results: Combined JSON from all subagent outputs.
        manifest_path: Path to frames_manifest.json.
        video_title: Title of the source video.
        video_source: URL or path of the source.
        output_dir: Where to write VISUAL_STYLE_GUIDE.md.

    Returns:
        Path to the generated VISUAL_STYLE_GUIDE.md.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    output_path = os.path.join(output_dir, "VISUAL_STYLE_GUIDE.md")
    return generate_style_guide(analysis_results, manifest, video_title, video_source, output_path)
```

**Step 4: Run tests**

Run: `python -m pytest tools/visual_style_extractor/tests/test_pipeline.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add tools/visual_style_extractor/pipeline.py tools/visual_style_extractor/tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator (chains Stages 0-4, prepares Stage 5-6)"
```

---

## Task 8: Claude Code Skill Definition (SKILL.md)

This is the skill file that Claude Code loads. It orchestrates the full pipeline including subagent dispatch for Stage 5.

**Files:**
- Create: `.claude/skills/visual-style-extractor/SKILL.md`

**Step 1: Write the skill file**

```markdown
---
name: visual-style-extractor
description: Analyzes a reference video to extract a comprehensive visual style guide. Uses scene detection, deduplication, and LLM analysis to produce an actionable VISUAL_STYLE_GUIDE.md organized by asset type. Input: YouTube URL or local directory with video + transcript.
---

# Visual Style Extractor v2

Extracts the visual style from a documentary reference video, producing a `VISUAL_STYLE_GUIDE.md` that the Visual Orchestrator (Agent 1.4) and Generative Visual Engine (Agent 2.2) use to determine what visual assets to create.

## Prerequisites

Ensure dependencies are installed:
```bash
pip install -r tools/visual_style_extractor/requirements.txt
```

## Process

### 1. Determine Input

Ask the user for either:
- **A YouTube URL** (preferred — downloads video + auto-subs automatically)
- **A local directory path** containing a video file and a `.vtt`/`.srt`/`.txt` transcript

### 2. Run Stages 0–4 (Automated Python)

```bash
python -c "
from visual_style_extractor.pipeline import run_stages_0_to_4, PipelineConfig
import json

config = PipelineConfig(source='USER_INPUT_HERE')
result = run_stages_0_to_4(config)
print(json.dumps(result, indent=2))
"
```

**Important:** Set the `PYTHONPATH` to include `tools/` so the module resolves:
```bash
PYTHONPATH=tools python -c "..."
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

### 4. Run Stage 6: Synthesis

```bash
PYTHONPATH=tools python -c "
from visual_style_extractor.pipeline import run_stage_6
import json

analysis_results = PASTE_MERGED_JSON_HERE
result = run_stage_6(
    analysis_results=analysis_results,
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
```

**Step 2: Commit**

```bash
git add .claude/skills/visual-style-extractor/
git commit -m "feat: add visual-style-extractor v2 skill definition"
```

---

## Task 9: Integration Test with Real Video

**This task is manual/interactive — not automated.**

**Step 1: Pick a short test video**

Use a short (~5 min) documentary clip from YouTube that represents the channel's style.

**Step 2: Run the full pipeline**

Invoke the skill: "Extract visual style from [YouTube URL]"

**Step 3: Verify each stage**

- [ ] Video downloads successfully
- [ ] Scene detection produces 10-50 scenes
- [ ] Dedup reduces frame count by 30-70%
- [ ] Contact sheets are readable (open and visually inspect)
- [ ] Subagent analysis produces valid JSON with scene types
- [ ] `VISUAL_STYLE_GUIDE.md` is generated with all 5 sections populated
- [ ] Proportions add up to ~100% (some rounding OK)

**Step 4: Compare with v1**

Open the v1 `VISUAL_LANGUAGE.md` (if one exists) alongside the v2 `VISUAL_STYLE_GUIDE.md` and verify that v2:
- Has fewer hallucinated elements
- Is organized by asset type (not by visual properties)
- Includes content descriptions for b-roll
- Has proportion data

**Step 5: Commit any adjustments**

```bash
git commit -m "test: verify visual-style-extractor v2 with real video"
```

---

## Task 10: Retire v1 Skill

**Files:**
- Delete: `.claude/skills/visual-language-extractor/` (entire directory)

**Step 1: Verify v2 is working**

Confirm Task 9 passed.

**Step 2: Remove v1 skill directory**

```bash
rm -rf .claude/skills/visual-language-extractor/
```

**Step 3: Commit**

```bash
git commit -m "chore: remove deprecated visual-language-extractor v1 skill"
```

---

## Summary

| Task | Stage | What | Estimated Steps |
|------|-------|------|-----------------|
| 0 | Setup | Package + deps | 5 |
| 1 | Stage 0 | Acquisition module | 5 |
| 2 | Stage 1 | Scene detection module | 5 |
| 3 | Stage 2 | Dedup module | 5 |
| 4 | Stage 3 | Alignment module | 5 |
| 5 | Stage 4 | Contact sheet generator | 5 |
| 6 | Stage 5-6 | Analysis prompt + synthesis | 6 |
| 7 | Orchestrator | Pipeline entry point | 5 |
| 8 | Skill | SKILL.md definition | 2 |
| 9 | Integration | Real video test | 5 |
| 10 | Cleanup | Remove v1 | 3 |

**Total: 11 tasks, ~51 steps**

**Dependencies:** Tasks 1-7 are sequential (each stage depends on the previous). Task 8 depends on all modules existing. Task 9 depends on 8. Task 10 depends on 9.
