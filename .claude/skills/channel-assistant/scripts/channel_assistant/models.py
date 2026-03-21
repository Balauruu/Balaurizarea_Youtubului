"""Data models for the channel assistant skill."""

from dataclasses import dataclass, field


@dataclass
class Channel:
    """Represents a YouTube channel."""

    name: str
    youtube_id: str
    handle: str | None = None
    url: str | None = None
    subscribers: int | None = None
    total_views: int | None = None
    description: str | None = None
    scraped_at: str | None = None


@dataclass
class Video:
    """Represents a YouTube video."""

    video_id: str
    channel_id: str
    title: str
    url: str | None = None
    views: int | None = None
    upload_date: str | None = None
    description: str | None = None
    duration: int | None = None
    tags: list[str] | None = None
    likes: int | None = None
    scraped_at: str | None = None
