"""Analyzer module: pure functions for channel stats, outlier detection, and formatting."""

from __future__ import annotations

import statistics
from datetime import datetime

from .models import Channel, Video


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string in YYYY-MM-DD or YYYYMMDD format."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def compute_channel_stats(channel: Channel, videos: list[Video]) -> dict:
    """Compute summary statistics for a channel's videos.

    Returns dict with: total_videos, avg_views, median_views,
    upload_frequency_days, most_recent_upload.
    """
    total_videos = len(videos)
    if total_videos == 0:
        return {
            "channel": channel.name,
            "total_videos": 0,
            "avg_views": 0,
            "median_views": 0,
            "upload_frequency_days": None,
            "most_recent_upload": None,
        }

    # Filter out None views
    valid_views = [v.views for v in videos if v.views is not None]

    if valid_views:
        avg_views = int(sum(valid_views) / len(valid_views))
        median_views = int(statistics.median(valid_views))
    else:
        avg_views = 0
        median_views = 0

    # Compute upload frequency from dates
    dates = []
    for v in videos:
        if v.upload_date:
            parsed = _parse_date(v.upload_date)
            if parsed:
                dates.append((parsed, v.upload_date))

    upload_frequency_days = None
    most_recent_upload = None

    if dates:
        dates.sort(key=lambda x: x[0])
        most_recent_upload = dates[-1][1]

        if len(dates) >= 2:
            total_span = (dates[-1][0] - dates[0][0]).days
            intervals = len(dates) - 1
            upload_frequency_days = round(total_span / intervals, 1)

    return {
        "channel": channel.name,
        "total_videos": total_videos,
        "avg_views": avg_views,
        "median_views": median_views,
        "upload_frequency_days": upload_frequency_days,
        "most_recent_upload": most_recent_upload,
    }


def detect_outliers(
    channel: Channel,
    videos: list[Video],
    threshold: float = 2.0,
) -> list[dict]:
    """Detect videos with views >= threshold * median views.

    Returns list of outlier dicts sorted by multiplier descending.
    Each dict has: title, channel, views, multiplier, upload_date.
    """
    valid_views = [v.views for v in videos if v.views is not None]
    if not valid_views:
        return []

    median = statistics.median(valid_views)
    if median == 0:
        return []

    outliers = []
    for v in videos:
        if v.views is None:
            continue
        multiplier = round(v.views / median, 1)
        if multiplier >= threshold:
            outliers.append(
                {
                    "title": v.title,
                    "channel": channel.name,
                    "views": v.views,
                    "multiplier": multiplier,
                    "upload_date": v.upload_date,
                }
            )

    outliers.sort(key=lambda x: x["multiplier"], reverse=True)
    return outliers


def format_stats_table(all_stats: list[dict]) -> str:
    """Format channel stats as an ASCII markdown table.

    Columns: Channel, Videos, Avg Views, Median Views, Upload Freq, Latest Upload.
    Views are comma-formatted. Upload frequency shown as 'Nd' or 'n/a'.
    """
    headers = ["Channel", "Videos", "Avg Views", "Median Views", "Upload Freq", "Latest Upload"]

    rows = []
    for s in all_stats:
        freq = f"{int(s['upload_frequency_days'])}d" if s["upload_frequency_days"] is not None else "n/a"
        rows.append(
            [
                s["channel"],
                str(s["total_videos"]),
                f"{s['avg_views']:,}",
                f"{s['median_views']:,}",
                freq,
                s.get("most_recent_upload") or "n/a",
            ]
        )

    # Compute column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            parts.append(cell.ljust(col_widths[i]))
        return "| " + " | ".join(parts) + " |"

    lines = [fmt_row(headers)]
    lines.append("| " + " | ".join("-" * w for w in col_widths) + " |")
    for row in rows:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def serialize_videos_for_analysis(all_videos_by_channel: dict[str, list[Video]]) -> str:
    """Serialize video data grouped by channel for LLM analysis.

    Videos sorted by views descending within each channel.
    Each line includes title, views (comma-formatted), upload_date, tags.
    """
    sections = []
    for channel_name, videos in all_videos_by_channel.items():
        lines = [f"## {channel_name}", ""]

        # Sort by views descending, None views last
        sorted_videos = sorted(
            videos,
            key=lambda v: v.views if v.views is not None else -1,
            reverse=True,
        )

        for v in sorted_videos:
            views_str = f"{v.views:,}" if v.views is not None else "n/a"
            date_str = v.upload_date or "n/a"
            tags_str = ", ".join(v.tags) if v.tags else ""
            lines.append(f"- {v.title} | views: {views_str} | date: {date_str} | tags: {tags_str}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)
