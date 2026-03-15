"""Archive.org source adapter.

Wraps the `internetarchive` Python library for searching and downloading
public domain / CC-licensed media from the Internet Archive.
"""
from pathlib import Path
from typing import Optional

import internetarchive

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _log_download,
    _streaming_download, DEFAULT_MAX_DOWNLOAD_BYTES,
)

SOURCE_NAME = "archive_org"

# Formats we accept for images and video
IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "TIFF"}
VIDEO_FORMATS = {"MPEG4", "h.264", "Ogg Video", "512Kb MPEG4"}


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Search Archive.org for items matching query.

    Args:
        query: Search terms.
        media_type: "image" or "video".
        limit: Max results to return.

    Returns:
        List of SearchResult with download URLs.
    """
    rate_limit(SOURCE_NAME)

    # Map media_type to Archive.org mediatype
    ia_mediatype = "image" if media_type in ("image", "document") else "movies"
    search_query = f"{query} AND mediatype:{ia_mediatype}"

    results: list[SearchResult] = []
    try:
        search_results = internetarchive.search_items(search_query)
        count = 0
        for result in search_results:
            if count >= limit:
                break
            identifier = result.get("identifier", "")
            if not identifier:
                continue

            rate_limit(SOURCE_NAME)
            item = internetarchive.get_item(identifier)
            metadata = item.metadata or {}

            # Find a suitable file
            target_formats = IMAGE_FORMATS if media_type in ("image", "document") else VIDEO_FORMATS
            best_file = None
            for f in item.files:
                fmt = f.get("format", "")
                if fmt in target_formats:
                    size = int(f.get("size", 0))
                    if size <= DEFAULT_MAX_DOWNLOAD_BYTES:
                        best_file = f
                        break

            if not best_file:
                continue

            file_url = f"https://archive.org/download/{identifier}/{best_file['name']}"
            license_url = metadata.get("licenseurl", "")
            license_str = "Public Domain" if "publicdomain" in license_url.lower() else (license_url or "Unknown")

            results.append(SearchResult(
                url=file_url,
                title=metadata.get("title", identifier),
                description=metadata.get("description", "")[:500] if metadata.get("description") else "",
                source=SOURCE_NAME,
                license=license_str,
                media_type=media_type,
                thumbnail_url=f"https://archive.org/services/img/{identifier}",
            ))
            count += 1
    except Exception as e:
        _log_download(SOURCE_NAME, query, 0, False, f"Search error: {e}")

    return results


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download a file from Archive.org.

    Args:
        url: Direct file URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(url, dest_dir, filename, SOURCE_NAME)
