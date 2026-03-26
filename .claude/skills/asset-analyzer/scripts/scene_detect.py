#!/usr/bin/env python3
"""PySceneDetect wrapper: detect scene boundaries and extract one mid-scene frame per scene."""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path

# Use scenedetect from dedicated venv
SCENEDETECT_PYTHON = "C:/Users/iorda/venvs/scenedetect/Scripts/python"


def detect_scenes(video_path, threshold=27.0):
    """Run PySceneDetect ContentDetector and return scene list."""
    script = f"""
import json
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

video = open_video("{video_path.replace(chr(92), '/')}")
sm = SceneManager()
sm.add_detector(ContentDetector(threshold={threshold}))
sm.detect_scenes(video)
scene_list = sm.get_scene_list()

scenes = []
for i, (start, end) in enumerate(scene_list):
    scenes.append({{
        "scene_num": i + 1,
        "start_sec": round(start.get_seconds(), 3),
        "end_sec": round(end.get_seconds(), 3),
        "duration_sec": round((end - start).get_seconds(), 3),
    }})

print(json.dumps(scenes))
"""
    result = subprocess.run(
        [SCENEDETECT_PYTHON, "-c", script],
        capture_output=True, text=True, timeout=600
    )

    if result.returncode != 0:
        print(f"ERROR: scene detection failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def extract_mid_frames(video_path, scenes, output_dir, max_width=512):
    """Extract one frame from the middle of each scene, downscaled to max_width."""
    frames_dir = os.path.join(output_dir, "triage_frames")
    os.makedirs(frames_dir, exist_ok=True)

    manifest = []
    for scene in scenes:
        mid_sec = round((scene["start_sec"] + scene["end_sec"]) / 2, 3)
        frame_name = f"scene_{scene['scene_num']:04d}_{mid_sec:.1f}s.jpg"
        frame_path = os.path.join(frames_dir, frame_name)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(mid_sec),
            "-i", video_path,
            "-vframes", "1",
            "-vf", f"scale={max_width}:-2",
            "-q:v", "3",
            frame_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0 and os.path.exists(frame_path):
            manifest.append({
                "scene_num": scene["scene_num"],
                "start_sec": scene["start_sec"],
                "end_sec": scene["end_sec"],
                "mid_sec": mid_sec,
                "duration_sec": scene["duration_sec"],
                "file": frame_path,
                "filename": frame_name,
            })

    return manifest


def run(video_path, output_dir, threshold=27.0, max_width=512):
    os.makedirs(output_dir, exist_ok=True)

    print(f"Detecting scenes in: {os.path.basename(video_path)}")
    scenes = detect_scenes(video_path, threshold)
    print(f"  Found {len(scenes)} scenes")

    print(f"Extracting mid-scene frames (max width {max_width}px)...")
    manifest = extract_mid_frames(video_path, scenes, output_dir, max_width)
    print(f"  Extracted {len(manifest)} frames")

    # Save outputs
    scenes_path = os.path.join(output_dir, "scenes.json")
    with open(scenes_path, "w") as f:
        json.dump(scenes, f, indent=2)

    manifest_path = os.path.join(output_dir, "triage_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    result = {
        "success": True,
        "video": os.path.basename(video_path),
        "total_scenes": len(scenes),
        "frames_extracted": len(manifest),
        "scenes_file": scenes_path,
        "triage_manifest": manifest_path,
        "triage_frames_dir": os.path.join(output_dir, "triage_frames"),
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Video file path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--threshold", type=float, default=27.0,
                        help="ContentDetector threshold (default 27.0)")
    parser.add_argument("--max-width", type=int, default=512,
                        help="Max frame width in pixels (default 512)")
    args = parser.parse_args()
    run(args.input, args.output, args.threshold, args.max_width)
