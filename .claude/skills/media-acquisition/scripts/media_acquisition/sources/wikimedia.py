"""Wikimedia Commons source adapter.

Uses the MediaWiki API to search for and download CC/public domain
media from Wikimedia Commons. Extracts license metadata via extmetadata.
"""
from pathlib import Path
from typing import Optional

import requests

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    _streaming_download,
)

SOURCE_NAME = "wikimedia_commons"

API_URL = "https://commons.wikimedia.org/w/api.php"

# Required by Wikimedia API policy
USER_AGENT = "DarkMysteriesChannel-MediaAcquisition/1.0 (documentary research; contact via GitHub)"


def _api_get(params: dict) -> dict:
    """Make a GET request to the MediaWiki API."""
    headers = {"User-Agent": USER_AGENT}
    params.setdefault("format", "json")
    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Search Wikimedia Commons.

    Args:
        query: Search terms.
        media_type: "image", "video", or "document".
        limit: Max results.

    Returns:
        List of SearchResult.
    """
    rate_limit(SOURCE_NAME)

    # Namespace 6 = File
    data = _api_get({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",
        "srlimit": str(limit),
    })

    titles = [hit["title"] for hit in data.get("query", {}).get("search", [])]
    if not titles:
        return []

    # Get image info + license metadata for all found files
    rate_limit(SOURCE_NAME)
    info_data = _api_get({
        "action": "query",
        "titles": "|".join(titles[:limit]),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
    })

    results: list[SearchResult] = []
    pages = info_data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1" or "imageinfo" not in page:
            continue
        info = page["imageinfo"][0]
        ext_meta = info.get("extmetadata", {})

        # Filter by media type
        mime = info.get("mime", "")
        if media_type == "image" and not mime.startswith("image/"):
            continue
        if media_type == "video" and not mime.startswith("video/"):
            continue

        license_short = ext_meta.get("LicenseShortName", {}).get("value", "Unknown")
        description = ext_meta.get("ImageDescription", {}).get("value", "")
        # Strip HTML tags from description
        import re
        description = re.sub(r"<[^>]+>", "", description)[:500]

        thumb_url = info.get("url", "").replace("/commons/", "/commons/thumb/")
        if thumb_url and not thumb_url.endswith("/"):
            thumb_url += "/320px-thumbnail.jpg"

        results.append(SearchResult(
            url=info["url"],
            title=page.get("title", "").replace("File:", ""),
            description=description,
            source=SOURCE_NAME,
            license=license_short,
            media_type=media_type,
            thumbnail_url=info.get("url", ""),
        ))

    return results


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download a file from Wikimedia Commons.

    Args:
        url: Direct file URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(
        url, dest_dir, filename, SOURCE_NAME,
        headers={"User-Agent": USER_AGENT},
    )
