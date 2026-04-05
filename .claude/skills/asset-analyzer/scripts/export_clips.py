"""Extract clip segments from source videos using FFmpeg."""

import argparse
import json
import os
import subprocess
import sys


def parse_ts(ts: str) -> float:
    """Parse M:SS or H:MM:SS timestamp to seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return float(ts)


def export_clip(
    input_path: str,
    output_path: str,
    start: str,
    end: str,
) -> dict:
    """Extract a clip segment. Returns summary dict."""
    start_sec = parse_ts(start)
    end_sec = parse_ts(end)
    duration = end_sec - start_sec

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",
        "-v", "error",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {
            "status": "error",
            "error": result.stderr.strip(),
            "output": output_path,
        }

    size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0
    return {
        "status": "ok",
        "output": output_path,
        "duration_sec": duration,
        "size_mb": round(size_mb, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract clips from source video")
    parser.add_argument("--input", required=True, help="Source video path")
    parser.add_argument("--output", required=True, help="Output clip path")
    parser.add_argument("--clips", required=True,
                        help='JSON array: [{"start": "M:SS", "end": "M:SS", "label": "name"}]')
    args = parser.parse_args()

    clips = json.loads(args.clips)
    results = []
    for clip in clips:
        out_dir = os.path.dirname(args.output) or "."
        ext = os.path.splitext(args.input)[1]
        out_path = os.path.join(out_dir, f"{clip['label']}{ext}")
        result = export_clip(args.input, out_path, clip["start"], clip["end"])
        result["label"] = clip["label"]
        results.append(result)
        print(f"  {clip['label']}: {result['status']} ({result.get('duration_sec', 0):.0f}s, {result.get('size_mb', 0):.1f}MB)")

    print(f"\nDone: {sum(1 for r in results if r['status'] == 'ok')}/{len(results)} clips exported")


if __name__ == "__main__":
    main()
