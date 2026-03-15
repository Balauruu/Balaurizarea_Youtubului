"""Direct URL downloader source adapter.

Downloads files from explicit URLs (e.g. from media_urls.md).
Validates Content-Type and enforces size limits.
"""
from pathlib import Path
from typing import Optional

from media_acquisition.sources import (
    SearchResult, DownloadResult, rate_limit, _streaming_download,
)

SOURCE_NAME = "direct_url"

# Allowed MIME types for download
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/tiff",
    "image/svg+xml",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/webm", "video/ogg", "video/quicktime",
}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/tiff",
}
ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOCUMENT_TYPES


def search(query: str, media_type: str = "image", limit: int = 10) -> list[SearchResult]:
    """Direct URL source doesn't support search.

    Returns empty list. Direct URLs come from media_urls.md, not search.
    """
    return []


def download(url: str, dest_dir: Path, filename: Optional[str] = None) -> DownloadResult:
    """Download a file from a direct URL.

    Validates Content-Type against allowed MIME types.
    Enforces size limits. Streams to disk.

    Args:
        url: Direct download URL.
        dest_dir: Directory to save to.
        filename: Override filename.

    Returns:
        DownloadResult.
    """
    rate_limit(SOURCE_NAME)
    return _streaming_download(
        url, dest_dir, filename, SOURCE_NAME,
        allowed_content_types=ALL_ALLOWED_TYPES,
    )
