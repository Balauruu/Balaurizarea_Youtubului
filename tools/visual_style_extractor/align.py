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
