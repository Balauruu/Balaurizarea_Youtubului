"""Smithsonian Open Access source adapter.

REST API with api_key query parameter. Free registration at api.si.edu.
"""
from pathlib import Path
from typing import Optional

import requests

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    _streaming_download, _get_api_key,
)

SOURCE_NAME = "smithsonian"
API_BASE = "https://api.si.edu/openaccess/api/v1.0"


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Search Smithsonian Open Access API.

    Args:
        query: Search terms.
        media_type: "image", "video", or "document".
        limit: Max results.

    Returns:
        List of SearchResult.
    """
    rate_limit(SOURCE_NAME)
    key = _get_api_key("SMITHSONIAN_API_KEY", SOURCE_NAME)

    params = {
        "api_key": key,
        "q": query,
        "rows": min(limit, 100),
    }
    resp = requests.get(f"{API_BASE}/search", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results: list[SearchResult] = []
    rows = data.get("response", {}).get("rows", [])
    for row in rows[:limit]:
        content = row.get("content", {})
        descriptive = content.get("descriptiveNonRepeating", {})
        freetext = content.get("freetext", {})

        title = descriptive.get("title", {}).get("content", "Unknown")
        # Get online media
        online_media = descriptive.get("online_media", {})
        media_list = online_media.get("media", [])
        if not media_list:
            continue

        media_item = media_list[0]
        media_url = media_item.get("content", "")
        thumbnail = media_item.get("thumbnail", "")

        if not media_url:
            continue

        # Extract description from freetext
        notes = freetext.get("notes", [])
        description = notes[0].get("content", "") if notes else ""

        results.append(SearchResult(
            url=media_url,
            title=title[:200],
            description=description[:500],
            source=SOURCE_NAME,
            license="Smithsonian Open Access (CC0)",
            media_type=media_type,
            thumbnail_url=thumbnail,
        ))

    return results


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download from Smithsonian.

    Args:
        url: Direct media URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(url, dest_dir, filename, SOURCE_NAME)
