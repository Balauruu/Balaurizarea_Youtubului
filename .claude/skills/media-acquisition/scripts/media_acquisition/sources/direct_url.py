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
    """For direct_url source, the query IS the URL to download.

    Returns a single SearchResult wrapping the URL so the acquire pipeline
    can download it through the standard search→download flow.
    """
    # Treat query as a direct URL if it starts with http
    if query.startswith("http://") or query.startswith("https://"):
        from urllib.parse import urlparse, unquote
        parsed = urlparse(query)
        filename = unquote(parsed.path.split("/")[-1]) or "download"
        return [SearchResult(
            url=query,
            title=filename,
            description=f"Direct download from {parsed.netloc}",
            source=SOURCE_NAME,
            license="Unknown",
            media_type=media_type,
        )]
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
    # Wikimedia and other sites require a User-Agent header
    headers = {
        "User-Agent": "DarkMysteriesChannel-MediaAcquisition/1.0 (documentary research)"
    }
    return _streaming_download(
        url, dest_dir, filename, SOURCE_NAME,
        allowed_content_types=ALL_ALLOWED_TYPES,
        headers=headers,
    )
