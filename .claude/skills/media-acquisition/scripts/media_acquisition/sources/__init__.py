"""Common interface for media source adapters.

Every source module exposes two functions:
    search(query, media_type, limit) -> list[SearchResult]
    download(url, dest_dir, filename=None) -> DownloadResult

The SOURCE_REGISTRY maps source name strings to module references.
Rate limiting is per-source via configurable sleep delays.
"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests  # noqa: F401 — module-level for mockability


@dataclass
class SearchResult:
    """A single search hit from any source."""
    url: str
    title: str
    description: str
    source: str  # e.g. "wikimedia_commons", "archive_org"
    license: str
    media_type: str  # "image", "video", "document"
    thumbnail_url: str = ""


@dataclass
class DownloadResult:
    """Outcome of a single download attempt."""
    success: bool
    filepath: str = ""
    filename: str = ""
    size_bytes: int = 0
    error: str = ""


# Per-source rate limit delays (seconds between requests)
RATE_LIMITS: dict[str, float] = {
    "archive_org": 1.0,
    "wikimedia_commons": 0.5,
    "pexels": 0.5,
    "pixabay": 0.5,
    "smithsonian": 0.5,
    "youtube_cc": 2.0,
    "direct_url": 0.2,
}

# Tracks last request time per source for rate limiting
_last_request_time: dict[str, float] = {}

# Default max download size in bytes (50 MB)
DEFAULT_MAX_DOWNLOAD_BYTES: int = 50 * 1024 * 1024


def rate_limit(source_name: str) -> None:
    """Sleep if needed to respect per-source rate limits.

    Call this before each HTTP request to a source.
    """
    delay = RATE_LIMITS.get(source_name, 0.5)
    last = _last_request_time.get(source_name, 0.0)
    elapsed = time.time() - last
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request_time[source_name] = time.time()


def reset_rate_limiter() -> None:
    """Reset rate limiter state (for testing)."""
    _last_request_time.clear()


def _log_download(source: str, url: str, size_bytes: int, success: bool, error: str = "") -> None:
    """Log download outcome to stderr for observability."""
    status = "OK" if success else "FAIL"
    size_kb = size_bytes / 1024 if size_bytes else 0
    msg = f"[{source}] {status} {url} ({size_kb:.1f} KB)"
    if error:
        msg += f" — {error}"
    print(msg, file=sys.stderr)


def _get_api_key(env_var: str, source_name: str) -> str:
    """Read an API key from environment, raise ValueError if missing."""
    import os
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise ValueError(
            f"Missing API key for {source_name}: set {env_var} environment variable"
        )
    return key


def _streaming_download(
    url: str,
    dest_dir: Path,
    filename: Optional[str],
    source_name: str,
    *,
    max_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
    allowed_content_types: Optional[set[str]] = None,
    headers: Optional[dict] = None,
) -> DownloadResult:
    """Shared streaming download logic used by multiple source modules.

    Args:
        url: Direct download URL.
        dest_dir: Directory to save the file.
        filename: Override filename. If None, derived from URL or Content-Disposition.
        source_name: For logging.
        max_bytes: Maximum file size.
        allowed_content_types: If set, reject responses with non-matching Content-Type.
        headers: Extra HTTP headers.

    Returns:
        DownloadResult with success/failure details.
    """
    from urllib.parse import urlparse, unquote

    try:
        resp = requests.get(url, stream=True, timeout=30, headers=headers or {})
        resp.raise_for_status()

        # Content-Type validation
        if allowed_content_types:
            ct = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if ct and ct not in allowed_content_types:
                error = f"Rejected Content-Type '{ct}'"
                _log_download(source_name, url, 0, False, error)
                return DownloadResult(success=False, error=error)

        # Check Content-Length if available
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            error = f"File too large: {int(content_length)} bytes > {max_bytes} limit"
            _log_download(source_name, url, 0, False, error)
            return DownloadResult(success=False, error=error)

        # Determine filename
        if not filename:
            # Try Content-Disposition first
            cd = resp.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('"\'')
            else:
                filename = unquote(urlparse(url).path.split("/")[-1]) or "download"

        # Sanitize filename
        filename = filename.replace("/", "_").replace("\\", "_")

        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        filepath = dest_dir / filename

        # Stream to file with size limit
        total = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                total += len(chunk)
                if total > max_bytes:
                    f.close()
                    filepath.unlink(missing_ok=True)
                    error = f"Download exceeded {max_bytes} byte limit at {total} bytes"
                    _log_download(source_name, url, total, False, error)
                    return DownloadResult(success=False, error=error)
                f.write(chunk)

        _log_download(source_name, url, total, True)
        return DownloadResult(
            success=True,
            filepath=str(filepath),
            filename=filename,
            size_bytes=total,
        )

    except requests.RequestException as e:
        error = f"HTTP error: {e}"
        _log_download(source_name, url, 0, False, error)
        return DownloadResult(success=False, error=error)


# --- Source Registry ---
# Lazy-loaded to avoid import errors when optional dependencies are missing.

def _get_source_module(name: str):
    """Import and return a source module by name."""
    import importlib
    return importlib.import_module(f"media_acquisition.sources.{name}")


# Registry maps source names to module names (lazy import).
_SOURCE_MODULE_NAMES: dict[str, str] = {
    "archive_org": "archive_org",
    "wikimedia_commons": "wikimedia",
    "pexels": "pexels",
    "pixabay": "pixabay",
    "smithsonian": "smithsonian",
    "youtube_cc": "youtube_cc",
    "direct_url": "direct_url",
}


def get_source(name: str):
    """Get a source module by registry name. Returns module with search/download."""
    if name not in _SOURCE_MODULE_NAMES:
        raise KeyError(f"Unknown source: '{name}'. Available: {sorted(_SOURCE_MODULE_NAMES)}")
    return _get_source_module(_SOURCE_MODULE_NAMES[name])


SOURCE_REGISTRY: dict[str, str] = dict(_SOURCE_MODULE_NAMES)
