#!/usr/bin/env python3
"""Extract frames from video with configurable modes."""

import sys
import os
import json
import subprocess
import argparse
import hashlib
from pathlib import Path

MODES = {
    "quick":     {"fps": 1,     "quality": 3},
    "standard":  {"fps": 2,     "quality": 2},
    "detailed":  {"fps": 5,     "quality": 2},
    "technical": {"fps": None,  "quality": 1},  # every frame
    "keyframes": {"fps": None,  "quality": 2},  # keyframes only
}

def extract_frames(input_path, output_dir, mode="standard", start=None, end=None):
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    cfg = MODES.get(mode, MODES["standard"])

    # Build ffmpeg filter
    vf_parts = []

    if mode == "keyframes":
        vf_parts.append("select=eq(pict_type\\,I)")
        vf_parts.append("showinfo")
        vsync = "vfr"
    elif cfg["fps"] is not None:
        vf_parts.append(f"fps={cfg['fps']}")
        vsync = "vfr"
    else:
        # Every frame
        vsync = "passthrough"

    vf = ",".join(vf_parts) if vf_parts else None

    cmd = ["ffmpeg", "-y"]

    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", input_path]
    if end is not None:
        duration = end - (start or 0)
        cmd += ["-t", str(duration)]

    if vf:
        cmd += ["-vf", vf]

    cmd += [
        "-vsync", vsync,
        "-frame_pts", "1",
        "-q:v", str(cfg["quality"]),
        "-f", "image2",
        os.path.join(frames_dir, "frame_%06d.jpg")
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Get frame timestamps using ffprobe on extracted frames
    # and build manifest
    frame_files = sorted(Path(frames_dir).glob("frame_*.jpg"))
    
    # Get PTS data from original video
    pts_cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "packet=pts_time,dts_time,duration_time,size",
        "-of", "json",
    ]
    if start is not None:
        pts_cmd += ["-read_intervals", f"%+{end - start if end else 9999}"]
    pts_cmd.append(input_path)

    pts_result = subprocess.run(pts_cmd, capture_output=True, text=True)
    
    frames_manifest = []
    prev_hash = None

    for i, frame_file in enumerate(frame_files):
        # Compute image hash for duplicate detection
        with open(frame_file, "rb") as f:
            content = f.read(4096)  # sample first 4KB for speed
            frame_hash = hashlib.md5(content).hexdigest()[:8]

        is_duplicate = (frame_hash == prev_hash)
        prev_hash = frame_hash

        # Estimate timestamp from index and mode fps
        if cfg["fps"]:
            ts = round((i / cfg["fps"]) + (start or 0), 3)
        else:
            ts = round(i / 30.0 + (start or 0), 3)  # fallback estimate

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

    # Technical data: frame intervals and FPS measurements
    intervals = []
    for i in range(1, len(frames_manifest)):
        interval = frames_manifest[i]["timestamp_sec"] - frames_manifest[i-1]["timestamp_sec"]
        intervals.append(interval)

    if intervals:
        avg_interval = sum(intervals) / len(intervals)
        measured_fps = round(1.0 / avg_interval, 2) if avg_interval > 0 else 0
        variance = sum((x - avg_interval)**2 for x in intervals) / len(intervals)
        import math
        std_dev = math.sqrt(variance)
        
        # Detect stutters: frames where interval > 2x normal
        stutters = []
        for i, interval in enumerate(intervals):
            if interval > avg_interval * 2.0:
                stutters.append({
                    "frame_index": i + 1,
                    "timestamp_sec": frames_manifest[i+1]["timestamp_sec"],
                    "interval_ms": round(interval * 1000, 1),
                    "expected_ms": round(avg_interval * 1000, 1),
                })

        # Smoothness score: 100 = perfect, decreases with variance and duplicates
        duplicate_count = sum(1 for f in frames_manifest if f["is_duplicate"])
        duplicate_penalty = min(50, (duplicate_count / max(len(frames_manifest), 1)) * 100)
        variance_penalty = min(50, (std_dev / avg_interval) * 50) if avg_interval > 0 else 0
        smoothness_score = round(max(0, 100 - duplicate_penalty - variance_penalty), 1)
    else:
        measured_fps = 0
        stutters = []
        smoothness_score = 0
        std_dev = 0
        avg_interval = 0
        duplicate_count = 0

    technical_data = {
        "mode": mode,
        "total_frames_extracted": len(frames_manifest),
        "duplicate_frames": duplicate_count,
        "measured_fps": measured_fps,
        "avg_frame_interval_ms": round(avg_interval * 1000, 2),
        "frame_interval_std_ms": round(std_dev * 1000, 2),
        "smoothness_score": smoothness_score,
        "stutter_events": stutters,
        "stutter_count": len(stutters),
    }

    # Save outputs
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
    parser.add_argument("--mode", default="standard", choices=list(MODES.keys()))
    parser.add_argument("--start", type=float, default=None)
    parser.add_argument("--end", type=float, default=None)
    args = parser.parse_args()
    extract_frames(args.input, args.output, args.mode, args.start, args.end)
