"""One-time migration of existing competitor data into SQLite.

Migrates data from:
- context/competitors/Barely Sociable.json (YouTube video data)
- context/competitors/unnamedTV.csv (vidIQ export)

Into the channel_assistant SQLite database.
"""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .database import Database
from .models import Channel, Video


def _parse_duration_hhmmss(duration_str: str) -> int | None:
    """Convert HH:MM:SS or MM:SS to total seconds."""
    if not duration_str:
        return None
    parts = duration_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return int(parts[0])
    except (ValueError, IndexError):
        return None


def _parse_iso_date(date_str: str) -> str | None:
    """Convert ISO 8601 datetime to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_us_date(date_str: str) -> str | None:
    """Convert M/D/YYYY to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_human_number(value: str) -> int | None:
    """Parse human-readable numbers like '67K', '1.1M', '2.4K' to integers."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None

    # Try plain integer first
    try:
        return int(value.replace(",", ""))
    except ValueError:
        pass

    # Parse K/M suffixes
    match = re.match(r"^([\d.]+)\s*([KkMm])$", value)
    if match:
        num = float(match.group(1))
        suffix = match.group(2).upper()
        multiplier = {"K": 1_000, "M": 1_000_000}
        return int(num * multiplier.get(suffix, 1))

    return None


def migrate_barely_sociable(source: Path, db: Database) -> int:
    """Migrate Barely Sociable JSON data into the database.

    Args:
        source: Path to Barely Sociable.json
        db: Database instance.

    Returns:
        Number of videos migrated.
    """
    if not source.exists():
        print(f"  Skipping: {source} not found")
        return 0

    data = json.loads(source.read_text(encoding="utf-8"))
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Extract channel info from first video
    if data:
        first = data[0]
        channel = Channel(
            name=first.get("channelName", "Barely Sociable"),
            youtube_id="@BarelySociable",
            handle="@BarelySociable",
            url=first.get("channelUrl", "https://www.youtube.com/@BarelySociable"),
            subscribers=first.get("numberOfSubscribers"),
            scraped_at=scraped_at,
        )
        db.upsert_channel(channel)

    # Migrate videos
    videos = []
    for entry in data:
        video = Video(
            video_id=entry.get("id", ""),
            channel_id="@BarelySociable",
            title=entry.get("title", ""),
            url=entry.get("url"),
            views=entry.get("viewCount"),
            upload_date=_parse_iso_date(entry.get("date", "")),
            description=None,  # Not in source
            duration=_parse_duration_hhmmss(entry.get("duration", "")),
            tags=None,  # Not in source
            likes=entry.get("likes"),
            scraped_at=scraped_at,
        )
        videos.append(video)

    db.upsert_videos(videos)
    return len(videos)


def migrate_unnamed_tv(source: Path, db: Database) -> int:
    """Migrate Unnamed TV CSV data into the database.

    Args:
        source: Path to unnamedTV.csv
        db: Database instance.

    Returns:
        Number of videos migrated.
    """
    if not source.exists():
        print(f"  Skipping: {source} not found")
        return 0

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Create channel entry
    channel = Channel(
        name="Unnamed TV",
        youtube_id="@unnamedTV",
        handle="@unnamedTV",
        url="https://www.youtube.com/@unnamedTV",
        scraped_at=scraped_at,
    )
    db.upsert_channel(channel)

    # Read CSV (handle BOM)
    with open(source, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        videos = []
        for row in reader:
            # Parse keywords into tags list
            keywords = row.get("KEYWORDS", "")
            tags = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None

            video = Video(
                video_id=row.get("ID", ""),
                channel_id="@unnamedTV",
                title=row.get("TITLE", ""),
                url=f"https://www.youtube.com/watch?v={row.get('ID', '')}" if row.get("ID") else None,
                views=int(row["VIEWS"]) if row.get("VIEWS") and row["VIEWS"].strip() else None,
                upload_date=_parse_us_date(row.get("DATE PUBLISHED", "")),
                description=row.get("DESCRIPTION"),
                duration=_parse_duration_hhmmss(row.get("DURATION", "")),
                tags=tags,
                likes=_parse_human_number(row.get("YT LIKES", "")),
                scraped_at=scraped_at,
            )
            videos.append(video)

    db.upsert_videos(videos)
    return len(videos)


def run_migration(db: Database, project_root: Path | None = None) -> None:
    """Run all migrations.

    Args:
        db: Database instance.
        project_root: Project root directory. If None, uses cwd.
    """
    root = project_root or Path.cwd()
    competitors_dir = root / "context" / "competitors"

    db.init_db()

    bs_count = migrate_barely_sociable(
        competitors_dir / "Barely Sociable.json", db
    )
    utv_count = migrate_unnamed_tv(
        competitors_dir / "unnamedTV.csv", db
    )

    print(
        f"Migrated {bs_count} videos from Barely Sociable, "
        f"{utv_count} videos from Unnamed TV"
    )


def delete_old_files(project_root: Path | None = None) -> None:
    """Delete old competitor data files after migration.

    Args:
        project_root: Project root directory. If None, uses cwd.
    """
    root = project_root or Path.cwd()
    competitors_dir = root / "context" / "competitors"

    old_files = [
        competitors_dir / "Barely Sociable.json",
        competitors_dir / "unnamedTV.csv",
        competitors_dir / "competitors.md",
    ]

    for path in old_files:
        if path.exists():
            path.unlink()
            print(f"  Deleted: {path.relative_to(root)}")
        else:
            print(f"  Already removed: {path.name}")
