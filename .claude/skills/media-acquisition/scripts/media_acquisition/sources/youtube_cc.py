"""YouTube Creative Commons source adapter.

Wraps yt-dlp subprocess to search for and download CC-licensed YouTube videos.
Downloads are limited to mp4 ≤720p.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    DEFAULT_MAX_DOWNLOAD_BYTES,
)

SOURCE_NAME = "youtube_cc"


def search(query: str, media_type: str = "video", limit: int = 10) -> list[SearchResult]:
    """Search YouTube for Creative Commons licensed videos.

    Uses yt-dlp's search functionality with CC license filter.

    Args:
        query: Search terms.
        media_type: Ignored (always "video" for YouTube).
        limit: Max results.

    Returns:
        List of SearchResult.
    """
    rate_limit(SOURCE_NAME)

    try:
        cmd = [
            "yt-dlp",
            f"ytsearch{limit}:{query}",
            "--match-filter", "license=Creative Commons",
            "--dump-json",
            "--no-download",
            "--flat-playlist",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace",
        )

        results: list[SearchResult] = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

            video_url = info.get("url") or info.get("webpage_url") or f"https://www.youtube.com/watch?v={info.get('id', '')}"
            results.append(SearchResult(
                url=video_url,
                title=info.get("title", "Unknown"),
                description=info.get("description", "")[:500],
                source=SOURCE_NAME,
                license="Creative Commons",
                media_type="video",
                thumbnail_url=info.get("thumbnail", ""),
            ))

        return results

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        _log_download(SOURCE_NAME, query, 0, False, f"yt-dlp error: {e}")
        return []


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download a YouTube CC video using yt-dlp.

    Downloads mp4 ≤720p. Respects size limits.

    Args:
        url: YouTube video URL.
        dest_dir: Directory to save to.
        filename: Override filename (without extension).

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(dest_dir / (filename or "%(title)s")) + ".%(ext)s"

    try:
        cmd = [
            "yt-dlp",
            url,
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", output_template,
            "--no-playlist",
            "--max-filesize", f"{DEFAULT_MAX_DOWNLOAD_BYTES}",
            "--print", "after_move:filepath",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace",
        )

        if result.returncode != 0:
            error = result.stderr.strip()[-200:] if result.stderr else "yt-dlp failed"
            _log_download(SOURCE_NAME, url, 0, False, error)
            return DownloadResult(success=False, error=error)

        # Get the output filepath from yt-dlp's stdout
        filepath = result.stdout.strip().split("\n")[-1].strip()
        if filepath and Path(filepath).exists():
            size = Path(filepath).stat().st_size
            _log_download(SOURCE_NAME, url, size, True)
            return DownloadResult(
                success=True,
                filepath=filepath,
                filename=Path(filepath).name,
                size_bytes=size,
            )
        else:
            # Try to find the downloaded file
            for f in dest_dir.iterdir():
                if f.suffix == ".mp4":
                    size = f.stat().st_size
                    _log_download(SOURCE_NAME, url, size, True)
                    return DownloadResult(
                        success=True,
                        filepath=str(f),
                        filename=f.name,
                        size_bytes=size,
                    )
            error = "yt-dlp completed but output file not found"
            _log_download(SOURCE_NAME, url, 0, False, error)
            return DownloadResult(success=False, error=error)

    except subprocess.TimeoutExpired:
        error = "yt-dlp download timed out (300s)"
        _log_download(SOURCE_NAME, url, 0, False, error)
        return DownloadResult(success=False, error=error)
    except FileNotFoundError:
        error = "yt-dlp not found — install with: pip install yt-dlp"
        _log_download(SOURCE_NAME, url, 0, False, error)
        return DownloadResult(success=False, error=error)
