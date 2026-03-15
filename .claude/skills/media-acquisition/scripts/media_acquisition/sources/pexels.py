"""Pexels source adapter.

REST API with Authorization header. 200 req/hr limit.
All Pexels content is free to use (Pexels license).
"""
from pathlib import Path
from typing import Optional

import requests

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    _streaming_download, _get_api_key,
)

SOURCE_NAME = "pexels"
API_BASE = "https://api.pexels.com/v1"
VIDEO_API_BASE = "https://api.pexels.com/videos"


def _get_headers() -> dict:
    """Get auth headers with API key."""
    key = _get_api_key("PEXELS_API_KEY", SOURCE_NAME)
    return {"Authorization": key}


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Search Pexels for photos or videos.

    Args:
        query: Search terms.
        media_type: "image" or "video".
        limit: Max results.

    Returns:
        List of SearchResult.
    """
    rate_limit(SOURCE_NAME)
    headers = _get_headers()

    if media_type == "video":
        url = f"{VIDEO_API_BASE}/search"
        params = {"query": query, "per_page": min(limit, 80)}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for v in data.get("videos", [])[:limit]:
            # Pick the smallest HD file
            video_files = sorted(v.get("video_files", []), key=lambda f: f.get("width", 9999))
            best = next((f for f in video_files if f.get("width", 0) <= 1280), video_files[0] if video_files else None)
            if not best:
                continue
            results.append(SearchResult(
                url=best["link"],
                title=v.get("url", "").split("/")[-2] if v.get("url") else "",
                description=f"Pexels video by {v.get('user', {}).get('name', 'Unknown')}",
                source=SOURCE_NAME,
                license="Pexels License (free)",
                media_type="video",
                thumbnail_url=v.get("image", ""),
            ))
        return results
    else:
        url = f"{API_BASE}/search"
        params = {"query": query, "per_page": min(limit, 80)}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for photo in data.get("photos", [])[:limit]:
            src = photo.get("src", {})
            results.append(SearchResult(
                url=src.get("original", src.get("large2x", "")),
                title=photo.get("alt", ""),
                description=f"Photo by {photo.get('photographer', 'Unknown')} on Pexels",
                source=SOURCE_NAME,
                license="Pexels License (free)",
                media_type="image",
                thumbnail_url=src.get("medium", ""),
            ))
        return results


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download from Pexels.

    Args:
        url: Direct media URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(url, dest_dir, filename, SOURCE_NAME)
