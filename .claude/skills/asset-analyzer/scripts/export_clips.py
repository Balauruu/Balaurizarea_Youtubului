#!/usr/bin/env python3
"""Export MP4 clips from a source video by timestamp ranges or keypoints."""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path


def parse_timestamp(ts_str):
    """Parse HH:MM:SS, MM:SS, or raw seconds into seconds float."""
    ts_str = str(ts_str).strip()
    if ":" in ts_str:
        parts = ts_str.split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    return float(ts_str)


def seconds_to_ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def export_clip(input_path, output_path, start_sec, end_sec, reencode=False):
    """Export a single clip using ffmpeg."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    duration = end_sec - start_sec

    if reencode:
        # Re-encode for accurate cuts and compatibility
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "18",
            output_path
        ]
    else:
        # Stream copy — fast, lossless, but cuts may be slightly imprecise
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"success": False, "error": result.stderr[-500:]}

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    return {
        "success": True,
        "file": output_path,
        "filename": os.path.basename(output_path),
        "start": seconds_to_ts(start_sec),
        "end": seconds_to_ts(end_sec),
        "duration_sec": round(duration, 2),
        "size_mb": round(size_mb, 2),
    }


def export_clips(input_path, output_dir, clips_spec, reencode=False):
    """
    clips_spec can be:
      - JSON string: [{"start": "00:01:00", "end": "00:01:30", "label": "intro"}, ...]
      - "keypoints:<keypoints_json_path>" — export around each keypoint (±padding)
      - "scenes:<manifest_path>" — export each detected scene as a clip
    """
    os.makedirs(output_dir, exist_ok=True)
    exported = []
    errors = []

    # Parse clips spec
    if clips_spec.startswith("keypoints:"):
        kp_path = clips_spec[10:]
        with open(kp_path) as f:
            keypoints = json.load(f)
        clips = []
        for kp in keypoints:
            ts = kp.get("timestamp_sec", 0)
            padding = kp.get("padding_sec", 5)
            clips.append({
                "start": max(0, ts - padding),
                "end": ts + padding,
                "label": kp.get("label", f"keypoint_{ts:.0f}s"),
            })
    elif clips_spec.startswith("scenes:"):
        manifest_path = clips_spec[7:]
        with open(manifest_path) as f:
            manifest = json.load(f)
        # Find scene change frames and build clip ranges
        scene_starts = [0.0]
        for frame in manifest:
            if frame.get("scene_change"):
                scene_starts.append(frame["timestamp_sec"])
        clips = []
        for i, start in enumerate(scene_starts):
            end = scene_starts[i + 1] if i + 1 < len(scene_starts) else None
            if end is None:
                continue  # skip last scene without known end
            clips.append({
                "start": start,
                "end": end,
                "label": f"scene_{i+1:03d}",
            })
    else:
        # Direct JSON spec
        clips = json.loads(clips_spec)

    for i, clip in enumerate(clips):
        start_sec = parse_timestamp(clip.get("start", 0))
        end_sec = parse_timestamp(clip.get("end", start_sec + 10))
        label = clip.get("label", f"clip_{i+1:03d}")
        # Sanitize label for filename
        label_clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        start_clean = seconds_to_ts(start_sec).replace(":", "-").replace(".", "_")
        filename = f"clip_{i+1:03d}_{label_clean}_{start_clean}.mp4"
        output_path = os.path.join(output_dir, filename)

        result = export_clip(input_path, output_path, start_sec, end_sec, reencode)
        result["label"] = label
        result["index"] = i + 1

        if result["success"]:
            exported.append(result)
        else:
            errors.append({"clip": label, "error": result.get("error")})

    summary = {
        "success": len(errors) == 0,
        "clips_exported": len(exported),
        "clips_failed": len(errors),
        "output_dir": output_dir,
        "total_size_mb": round(sum(c.get("size_mb", 0) for c in exported), 2),
        "clips": exported,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Source video path")
    parser.add_argument("--output", required=True, help="Output directory for clips")
    parser.add_argument("--clips", required=True,
                        help='JSON array of clips, or "keypoints:<path>", or "scenes:<manifest>"')
    parser.add_argument("--reencode", action="store_true",
                        help="Re-encode for accuracy (slower but frame-perfect cuts)")
    args = parser.parse_args()
    export_clips(args.input, args.output, args.clips, args.reencode)
