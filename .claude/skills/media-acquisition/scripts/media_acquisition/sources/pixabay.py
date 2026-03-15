"""Pixabay source adapter.

REST API with key as query parameter. All content is royalty-free.
"""
from pathlib import Path
from typing import Optional

import requests

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    _streaming_download, _get_api_key,
)

SOURCE_NAME = "pixabay"
API_BASE = "https://pixabay.com/api/"
VIDEO_API_BASE = "https://pixabay.com/api/videos/"


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Search Pixabay.

    Args:
        query: Search terms.
        media_type: "image" or "video".
        limit: Max results.

    Returns:
        List of SearchResult.
    """
    rate_limit(SOURCE_NAME)
    key = _get_api_key("PIXABAY_API_KEY", SOURCE_NAME)

    if media_type == "video":
        url = VIDEO_API_BASE
        params = {"key": key, "q": query, "per_page": min(limit, 200)}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for hit in data.get("hits", [])[:limit]:
            videos = hit.get("videos", {})
            # Prefer "medium" quality
            medium = videos.get("medium", videos.get("small", {}))
            results.append(SearchResult(
                url=medium.get("url", ""),
                title=hit.get("tags", ""),
                description=f"Pixabay video by {hit.get('user', 'Unknown')}",
                source=SOURCE_NAME,
                license="Pixabay License (royalty-free)",
                media_type="video",
                thumbnail_url=hit.get("userImageURL", ""),
            ))
        return results
    else:
        url = API_BASE
        params = {"key": key, "q": query, "per_page": min(limit, 200), "image_type": "photo"}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for hit in data.get("hits", [])[:limit]:
            results.append(SearchResult(
                url=hit.get("largeImageURL", hit.get("webformatURL", "")),
                title=hit.get("tags", ""),
                description=f"Pixabay image by {hit.get('user', 'Unknown')}",
                source=SOURCE_NAME,
                license="Pixabay License (royalty-free)",
                media_type="image",
                thumbnail_url=hit.get("previewURL", ""),
            ))
        return results


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download from Pixabay.

    Args:
        url: Direct media URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(url, dest_dir, filename, SOURCE_NAME)
