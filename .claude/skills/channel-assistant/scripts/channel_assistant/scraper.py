"""yt-dlp scraper module for channel assistant.

Provides functions to scrape YouTube channel metadata and videos
using yt-dlp as a subprocess. Includes retry logic, rate limiting,
and graceful failure handling.
"""

import json
import logging
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .models import Channel, Video
from .database import Database
from .registry import Registry

logger = logging.getLogger(__name__)


class ScrapeError(Exception):
    """Raised when yt-dlp scraping fails after all retries."""


# Field mapping from yt-dlp JSON output to our schema
VIDEO_FIELD_MAP = {
    "id": "video_id",
    "title": "title",
    "webpage_url": "url",
    "view_count": "views",
    "upload_date": "upload_date",  # YYYYMMDD -> YYYY-MM-DD
    "description": "description",
    "duration": "duration",  # int seconds
    "tags": "tags",  # list[str]
    "like_count": "likes",  # int
}

CHANNEL_FIELD_MAP = {
    "channel": "name",
    "channel_id": "youtube_id",
    "uploader_id": "handle",
    "channel_url": "url",
    "channel_follower_count": "subscribers",
}


def _format_upload_date(date_str: str | None) -> str | None:
    """Convert YYYYMMDD to YYYY-MM-DD format."""
    if not date_str or len(date_str) != 8:
        return date_str
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_video(raw: dict, channel_id: str, scraped_at: str) -> Video:
    """Parse a single yt-dlp JSON object into a Video dataclass."""
    return Video(
        video_id=raw.get("id", ""),
        channel_id=channel_id,
        title=raw.get("title", ""),
        url=raw.get("webpage_url"),
        views=raw.get("view_count"),
        upload_date=_format_upload_date(raw.get("upload_date")),
        description=raw.get("description"),
        duration=raw.get("duration"),
        tags=raw.get("tags"),
        likes=raw.get("like_count"),
        scraped_at=scraped_at,
    )


def _parse_channel(raw: dict, scraped_at: str) -> Channel:
    """Extract Channel metadata from a yt-dlp video JSON object."""
    return Channel(
        name=raw.get("channel", ""),
        youtube_id=raw.get("channel_id", ""),
        handle=raw.get("uploader_id"),
        url=raw.get("channel_url"),
        subscribers=raw.get("channel_follower_count"),
        scraped_at=scraped_at,
    )


def scrape_channel(
    channel_url: str, timeout: int = 300
) -> tuple[Channel, list[Video]]:
    """Scrape all video metadata from a YouTube channel via yt-dlp.

    Args:
        channel_url: YouTube channel URL (e.g. https://www.youtube.com/@BarelySociable)
        timeout: Subprocess timeout in seconds.

    Returns:
        Tuple of (Channel, list[Video]).

    Raises:
        ScrapeError: After all retries exhausted.
    """
    url = channel_url.rstrip("/")
    if not url.endswith("/videos"):
        url = url + "/videos"

    cmd = [
        "yt-dlp",
        "--dump-json",
        "--skip-download",
        "--no-warnings",
        url,
    ]

    max_attempts = 3  # 1 initial + 2 retries
    delay = 5
    last_error = ""

    for attempt in range(max_attempts):
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )

        if result.returncode == 0 and result.stdout.strip():
            break

        last_error = result.stderr.strip() or "Unknown error"

        if attempt < max_attempts - 1:
            time.sleep(delay * (attempt + 1))
    else:
        raise ScrapeError(
            f"yt-dlp failed after {max_attempts} attempts: {last_error}"
        )

    # Parse JSON-lines output
    scraped_at = _now_iso()
    raw_videos = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line:
            raw_videos.append(json.loads(line))

    if not raw_videos:
        raise ScrapeError(f"No videos found for {channel_url}")

    # Extract channel from first video
    channel = _parse_channel(raw_videos[0], scraped_at)
    channel_id = channel.youtube_id

    # Parse all videos
    videos = [_parse_video(raw, channel_id, scraped_at) for raw in raw_videos]

    return channel, videos


def scrape_all_channels(registry: Registry, db: Database) -> dict:
    """Scrape all channels in the registry.

    Args:
        registry: Competitor registry instance.
        db: Database instance.

    Returns:
        Summary dict with keys: succeeded, failed, total_new, total_updated.
    """
    channels = registry.list_channels()
    total = len(channels)
    succeeded = []
    failed = []
    total_new = 0
    total_updated = 0

    print(f"Scraping {total} channels...")

    for i, ch_entry in enumerate(channels):
        name = ch_entry.get("name", "Unknown")
        url = ch_entry.get("url", "")

        try:
            channel, videos = scrape_channel(url)

            # Count existing videos for this channel to determine new vs updated
            existing = db.get_videos_by_channel(channel.youtube_id)
            existing_ids = {v.video_id for v in existing}
            new_count = sum(1 for v in videos if v.video_id not in existing_ids)
            updated_count = len(videos) - new_count

            db.upsert_channel(channel)
            db.upsert_videos(videos)

            total_new += new_count
            total_updated += updated_count
            succeeded.append(name)

            print(f"\u2713 {name}: {len(videos)} videos ({new_count} new)")

        except ScrapeError as e:
            reason = str(e)
            failed.append({"name": name, "reason": reason})

            # Fall back to cached data
            # Try to find channel in DB by looking up youtube_id from registry entry
            cached_videos = []
            all_db_channels = db.get_all_channels()
            for db_ch in all_db_channels:
                if db_ch.name.lower() == name.lower():
                    cached_videos = db.get_videos_by_channel(db_ch.youtube_id)
                    cached_date = db_ch.scraped_at or "unknown"
                    break

            logger.warning("Failed to scrape %s: %s", name, reason)
            print(f"\u2717 {name}: {reason}")
            if cached_videos:
                print(
                    f"  \u2192 Using cached data "
                    f"({len(cached_videos)} videos from {cached_date[:10]})"
                )

        # Jittered delay between channels (not after the last one)
        if i < total - 1:
            time.sleep(random.uniform(3, 8))

    # Summary
    failed_count = len(failed)
    if failed_count:
        print(f"\nDone. {failed_count} channel(s) failed (cached data used).")
    else:
        print(f"\nDone. All {total} channels scraped successfully.")

    return {
        "succeeded": succeeded,
        "failed": failed,
        "total_new": total_new,
        "total_updated": total_updated,
    }


def scrape_single_channel(
    name: str, registry: Registry, db: Database
) -> dict | None:
    """Scrape a single channel by name.

    Args:
        name: Channel name (partial match via registry).
        registry: Competitor registry instance.
        db: Database instance.

    Returns:
        Summary dict, or None if channel not found.
    """
    ch_entry = registry.get_by_name(name)
    if not ch_entry:
        print(f"Channel '{name}' not found in registry.")
        return None

    ch_name = ch_entry.get("name", "Unknown")
    url = ch_entry.get("url", "")

    print(f"Scraping {ch_name}...")

    try:
        channel, videos = scrape_channel(url)

        existing = db.get_videos_by_channel(channel.youtube_id)
        existing_ids = {v.video_id for v in existing}
        new_count = sum(1 for v in videos if v.video_id not in existing_ids)

        db.upsert_channel(channel)
        db.upsert_videos(videos)

        print(f"\u2713 {ch_name}: {len(videos)} videos ({new_count} new)")
        return {
            "succeeded": [ch_name],
            "failed": [],
            "total_new": new_count,
            "total_updated": len(videos) - new_count,
        }

    except ScrapeError as e:
        print(f"\u2717 {ch_name}: {e}")
        return {
            "succeeded": [],
            "failed": [{"name": ch_name, "reason": str(e)}],
            "total_new": 0,
            "total_updated": 0,
        }
