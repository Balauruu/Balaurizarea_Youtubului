"""Stage 1: Scene Detection using PySceneDetect AdaptiveDetector."""

import os
import json
import subprocess
from dataclasses import dataclass, asdict
from scenedetect import detect, AdaptiveDetector


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
