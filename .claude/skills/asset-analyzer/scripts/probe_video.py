#!/usr/bin/env python3
"""Probe a video file and return metadata as JSON."""

import sys
import json
import subprocess
import os

def probe_video(video_path):
    if not os.path.exists(video_path):
        print(json.dumps({"error": f"File not found: {video_path}"}))
        sys.exit(1)

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(json.dumps({"error": result.stderr}))
        sys.exit(1)

    probe = json.loads(result.stdout)

    video_stream = next((s for s in probe.get("streams", []) if s["codec_type"] == "video"), None)
    audio_stream = next((s for s in probe.get("streams", []) if s["codec_type"] == "audio"), None)
    fmt = probe.get("format", {})

    if not video_stream:
        print(json.dumps({"error": "No video stream found"}))
        sys.exit(1)

    # Parse FPS
    fps_str = video_stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_str.split("/")
        fps = round(float(num) / float(den), 3)
    except Exception:
        fps = 0.0

    avg_fps_str = video_stream.get("avg_frame_rate", "0/1")
    try:
        num, den = avg_fps_str.split("/")
        avg_fps = round(float(num) / float(den), 3)
    except Exception:
        avg_fps = 0.0

    duration = float(fmt.get("duration", video_stream.get("duration", 0)))
    file_size = int(fmt.get("size", 0))
    bit_rate = int(fmt.get("bit_rate", 0))

    nb_frames = video_stream.get("nb_frames")
    if nb_frames:
        nb_frames = int(nb_frames)
    else:
        nb_frames = round(duration * fps) if fps > 0 else None

    summary = {
        "file": os.path.basename(video_path),
        "path": video_path,
        "duration_sec": round(duration, 2),
        "duration_human": f"{int(duration//3600):02d}:{int((duration%3600)//60):02d}:{int(duration%60):02d}",
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "codec": video_stream.get("codec_name"),
        "declared_fps": fps,
        "avg_fps": avg_fps,
        "total_frames": nb_frames,
        "file_size_mb": round(file_size / (1024*1024), 2),
        "bitrate_kbps": round(bit_rate / 1000, 1),
        "has_audio": audio_stream is not None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "pixel_format": video_stream.get("pix_fmt"),
        "color_space": video_stream.get("color_space"),
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: probe_video.py <video_path>")
        sys.exit(1)
    probe_video(sys.argv[1])
