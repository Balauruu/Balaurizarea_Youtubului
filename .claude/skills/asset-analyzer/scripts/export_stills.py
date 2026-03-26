#!/usr/bin/env python3
"""Export selected stills from extracted frames."""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path


def parse_timestamp(ts_str):
    """Parse HH:MM:SS or SS.ms into seconds."""
    ts_str = str(ts_str).strip()
    if ":" in ts_str:
        parts = ts_str.split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    return float(ts_str)


def find_closest_frame(manifest, target_sec):
    """Find the frame closest to a given timestamp."""
    best = min(manifest, key=lambda f: abs(f["timestamp_sec"] - target_sec))
    return best


def export_stills(frames_dir, output_dir, manifest_path, selection, fmt="jpg", quality=95):
    os.makedirs(output_dir, exist_ok=True)

    with open(manifest_path) as f:
        manifest = json.load(f)

    if not manifest:
        print(json.dumps({"error": "Empty manifest"}))
        sys.exit(1)

    exported = []

    if selection == "all":
        frames_to_export = manifest

    elif selection == "keyframes":
        # Export every non-duplicate frame (scene changes)
        frames_to_export = [f for f in manifest if not f.get("is_duplicate")]

    elif selection == "best":
        # Export largest file size frames (proxy for visual richness)
        sorted_frames = sorted(manifest, key=lambda f: f.get("size_bytes", 0), reverse=True)
        # Take top 10% or at least 5
        count = max(5, len(manifest) // 10)
        frames_to_export = sorted(sorted_frames[:count], key=lambda f: f["timestamp_sec"])

    elif selection.startswith("range:"):
        # range:00:01:00-00:01:30:every=5s
        parts = selection[6:]
        range_part, *options = parts.split(":")
        start_str, end_str = range_part.split("-")
        start = parse_timestamp(start_str)
        end = parse_timestamp(end_str)

        every_sec = 1.0
        for opt in options:
            if opt.startswith("every="):
                every_str = opt[6:].replace("s", "")
                every_sec = float(every_str)

        frames_to_export = []
        current = start
        while current <= end:
            frame = find_closest_frame(manifest, current)
            if frame not in frames_to_export:
                frames_to_export.append(frame)
            current += every_sec

    elif "," in selection or selection.replace(":", "").replace(".", "").isdigit():
        # Comma-separated timestamps
        timestamps = [t.strip() for t in selection.split(",")]
        frames_to_export = [find_closest_frame(manifest, parse_timestamp(ts)) for ts in timestamps]
    else:
        print(json.dumps({"error": f"Unknown selection mode: {selection}"}))
        sys.exit(1)

    for i, frame in enumerate(frames_to_export):
        src = frame["file"]
        if not os.path.exists(src):
            continue

        ts_clean = frame["timestamp_human"].replace(":", "-").replace(".", "_")
        dest_name = f"still_{i+1:03d}_{ts_clean}.{fmt}"
        dest = os.path.join(output_dir, dest_name)

        shutil.copy2(src, dest)

        exported.append({
            "index": i + 1,
            "file": dest,
            "filename": dest_name,
            "timestamp_sec": frame["timestamp_sec"],
            "timestamp_human": frame["timestamp_human"],
            "original_frame": frame["index"],
        })

    result = {
        "success": True,
        "stills_exported": len(exported),
        "output_dir": output_dir,
        "stills": exported,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--selection", default="keyframes",
                        help="all|keyframes|best|range:HH:MM:SS-HH:MM:SS:every=Ns|timestamp1,timestamp2")
    parser.add_argument("--format", default="jpg", choices=["jpg", "png"])
    parser.add_argument("--quality", type=int, default=95)
    args = parser.parse_args()

    export_stills(args.frames_dir, args.output, args.manifest, args.selection, args.format, args.quality)
