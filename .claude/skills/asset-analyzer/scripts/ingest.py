# .claude/skills/asset-analyzer/scripts/ingest.py
"""FFmpeg video decode → frames in memory or to disk."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _check_nvdec() -> bool:
    """Check if NVDEC hardware acceleration is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hwaccels"],
            capture_output=True, text=True, timeout=5,
        )
        return "cuda" in result.stdout.lower()
    except Exception:
        return False


def extract_frames(
    video_path: str,
    fps: int = 1,
    size: int = 336,
    use_hwaccel: bool = True,
) -> list[np.ndarray]:
    """Decode video to a list of RGB numpy arrays at the given fps and resolution.

    Returns list of np.ndarray with shape (size, size, 3), dtype uint8.
    """
    hwaccel_args = []
    hwdownload_filter = ""
    if use_hwaccel and _check_nvdec():
        hwaccel_args = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        hwdownload_filter = "hwdownload,format=nv12,"

    cmd = [
        "ffmpeg",
        *hwaccel_args,
        "-i", video_path,
        "-vf", f"{hwdownload_filter}fps={fps},scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "rgb24",
        "-f", "rawvideo",
        "-v", "error",
        "pipe:1",
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_bytes = proc.stdout.read()
    proc.wait()

    if proc.returncode != 0:
        err = proc.stderr.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg failed (exit {proc.returncode}): {err}")

    frame_size = size * size * 3
    n_frames = len(raw_bytes) // frame_size
    frames = []
    for i in range(n_frames):
        offset = i * frame_size
        frame = np.frombuffer(raw_bytes[offset:offset + frame_size], dtype=np.uint8)
        frame = frame.reshape(size, size, 3)
        frames.append(frame)

    return frames


def save_frames(
    video_path: str,
    output_dir: str,
    fps: int = 1,
    size: int = 336,
    start_sec: float | None = None,
    end_sec: float | None = None,
) -> list[str]:
    """Extract frames from video and save as JPEG files. Returns list of saved paths."""
    os.makedirs(output_dir, exist_ok=True)

    seek_args = []
    if start_sec is not None:
        seek_args += ["-ss", str(start_sec)]
    duration_args = []
    if start_sec is not None and end_sec is not None:
        duration_args += ["-t", str(end_sec - start_sec)]

    cmd = [
        "ffmpeg",
        *seek_args,
        "-i", video_path,
        *duration_args,
        "-vf", f"fps={fps},scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2",
        "-q:v", "2",
        "-v", "error",
        os.path.join(output_dir, "frame_%06d.jpg"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    saved = sorted(Path(output_dir).glob("frame_*.jpg"))
    return [str(p) for p in saved]


def main():
    parser = argparse.ArgumentParser(description="Extract frames from video via FFmpeg")
    parser.add_argument("--input", required=True, help="Path to video file")
    parser.add_argument("--fps", type=int, default=1, help="Frames per second to extract")
    parser.add_argument("--size", type=int, default=336, help="Output frame size (square)")
    parser.add_argument("--output-dir", help="Save frames to directory as JPEG")
    parser.add_argument("--start", type=float, help="Start time in seconds")
    parser.add_argument("--end", type=float, help="End time in seconds")
    parser.add_argument("--pipe", action="store_true", help="Pipe raw RGB to stdout")
    args = parser.parse_args()

    if args.output_dir:
        paths = save_frames(args.input, args.output_dir, args.fps, args.size, args.start, args.end)
        print(f"Saved {len(paths)} frames to {args.output_dir}")
    elif args.pipe:
        frames = extract_frames(args.input, args.fps, args.size)
        for frame in frames:
            sys.stdout.buffer.write(frame.tobytes())
    else:
        frames = extract_frames(args.input, args.fps, args.size)
        print(f"Extracted {len(frames)} frames ({args.size}x{args.size} RGB)")


if __name__ == "__main__":
    main()
