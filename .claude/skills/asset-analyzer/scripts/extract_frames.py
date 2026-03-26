#!/usr/bin/env python3
"""Extract frames from video — documentary analysis modes only."""

import sys
import os
import json
import subprocess
import argparse
import hashlib
import math
from pathlib import Path

MODES = {
    "triage": {"fps": 1, "quality": 3},
    "full":   {"fps": 2, "quality": 2},
}


def extract_frames(input_path, output_dir, mode="full", start=None, end=None, max_width=None):
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    cfg = MODES.get(mode, MODES["full"])

    # Build ffmpeg filter
    vf_parts = [f"fps={cfg['fps']}"]
    if max_width:
        vf_parts.append(f"scale={max_width}:-2")
    vf = ",".join(vf_parts)

    cmd = ["ffmpeg", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", input_path]
    if end is not None:
        duration = end - (start or 0)
        cmd += ["-t", str(duration)]

    cmd += [
        "-vf", vf,
        "-vsync", "vfr",
        "-frame_pts", "1",
        "-q:v", str(cfg["quality"]),
        "-f", "image2",
        os.path.join(frames_dir, "frame_%06d.jpg")
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    frame_files = sorted(Path(frames_dir).glob("frame_*.jpg"))

    frames_manifest = []
    prev_hash = None

    for i, frame_file in enumerate(frame_files):
        with open(frame_file, "rb") as f:
            content = f.read(4096)
            frame_hash = hashlib.md5(content).hexdigest()[:8]

        is_duplicate = (frame_hash == prev_hash)
        prev_hash = frame_hash

        ts = round((i / cfg["fps"]) + (start or 0), 3)

        frames_manifest.append({
            "index": i,
            "file": str(frame_file),
            "filename": frame_file.name,
            "timestamp_sec": ts,
            "timestamp_human": f"{int(ts//3600):02d}:{int((ts%3600)//60):02d}:{ts%60:06.3f}",
            "hash": frame_hash,
            "is_duplicate": is_duplicate,
            "size_bytes": os.path.getsize(frame_file),
        })

    # Technical data
    intervals = []
    for i in range(1, len(frames_manifest)):
        interval = frames_manifest[i]["timestamp_sec"] - frames_manifest[i-1]["timestamp_sec"]
        intervals.append(interval)

    if intervals:
        avg_interval = sum(intervals) / len(intervals)
        measured_fps = round(1.0 / avg_interval, 2) if avg_interval > 0 else 0
        variance = sum((x - avg_interval)**2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        duplicate_count = sum(1 for f in frames_manifest if f["is_duplicate"])
    else:
        measured_fps = 0
        std_dev = 0
        avg_interval = 0
        duplicate_count = 0

    technical_data = {
        "mode": mode,
        "max_width": max_width,
        "total_frames_extracted": len(frames_manifest),
        "duplicate_frames": duplicate_count,
        "measured_fps": measured_fps,
        "avg_frame_interval_ms": round(avg_interval * 1000, 2),
        "frame_interval_std_ms": round(std_dev * 1000, 2),
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(frames_manifest, f, indent=2)

    technical_path = os.path.join(output_dir, "technical_data.json")
    with open(technical_path, "w") as f:
        json.dump(technical_data, f, indent=2)

    print(json.dumps({
        "success": True,
        "frames_extracted": len(frames_manifest),
        "frames_dir": frames_dir,
        "manifest": manifest_path,
        "technical_data": technical_path,
        "technical_summary": technical_data,
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="full", choices=list(MODES.keys()))
    parser.add_argument("--start", type=float, default=None)
    parser.add_argument("--end", type=float, default=None)
    parser.add_argument("--max-width", type=int, default=None,
                        help="Max frame width in pixels (e.g., 512)")
    args = parser.parse_args()
    extract_frames(args.input, args.output, args.mode, args.start, args.end, args.max_width)
