"""Stage 0: Acquisition — validate inputs or download via yt-dlp."""

import os
import glob
import subprocess

VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv", ".avi", ".mov")
TRANSCRIPT_EXTENSIONS = (".vtt", ".srt", ".txt")


def find_video_file(directory: str) -> str | None:
    """Find the first video file in a directory."""
    for ext in VIDEO_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            return matches[0]
    return None


def find_transcript_file(directory: str) -> str | None:
    """Find the first transcript file in a directory (.vtt preferred, then .srt, then .txt)."""
    for ext in TRANSCRIPT_EXTENSIONS:
        matches = glob.glob(os.path.join(directory, f"*{ext}"))
        if matches:
            return matches[0]
    return None


def validate_local_input(directory: str) -> dict:
    """Validate that a local directory contains a video and transcript.

    Returns dict with 'video_path' and 'transcript_path'.
    Raises FileNotFoundError with clear message if either is missing.
    """
    video_path = find_video_file(directory)
    if not video_path:
        raise FileNotFoundError(
            f"No video file found in {directory}. "
            f"Expected one of: {', '.join(VIDEO_EXTENSIONS)}"
        )

    transcript_path = find_transcript_file(directory)
    if not transcript_path:
        raise FileNotFoundError(
            f"No transcript found in {directory}. "
            "Provide a .vtt, .srt, or .txt transcript file, "
            "or use a YouTube URL instead."
        )

    return {"video_path": video_path, "transcript_path": transcript_path}


def download_from_youtube(url: str, output_dir: str) -> dict:
    """Download video + auto-subs from YouTube using yt-dlp.

    Returns dict with 'video_path' and 'transcript_path'.
    """
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--write-auto-sub", "--sub-lang", "en", "--convert-subs", "vtt",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url,
    ]

    print(f"Downloading from {url}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed (exit {result.returncode}):\n{result.stderr}"
        )

    video_path = find_video_file(output_dir)
    transcript_path = find_transcript_file(output_dir)

    if not video_path:
        raise RuntimeError("yt-dlp completed but no video file found in output directory.")
    if not transcript_path:
        raise FileNotFoundError(
            "No auto-subs available for this video. "
            "Download the video manually and provide a transcript file."
        )

    return {"video_path": video_path, "transcript_path": transcript_path}
