"""SQLite database layer for channel assistant.

Provides schema creation, idempotent upserts, and query operations
for channels and videos tables.
"""

import json
import sqlite3
from pathlib import Path

from .models import Channel, Video


class Database:
    """SQLite database for storing channel and video metadata."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Return a connection with Row factory and WAL mode."""
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self.connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS channels (
                    youtube_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    handle TEXT,
                    url TEXT,
                    subscribers INTEGER,
                    total_views INTEGER,
                    description TEXT,
                    scraped_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    views INTEGER,
                    upload_date TEXT,
                    description TEXT,
                    duration INTEGER,
                    tags TEXT,
                    likes INTEGER,
                    scraped_at TEXT NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels(youtube_id)
                );

                CREATE INDEX IF NOT EXISTS idx_videos_channel
                    ON videos(channel_id);
                CREATE INDEX IF NOT EXISTS idx_videos_views
                    ON videos(views DESC);
                CREATE INDEX IF NOT EXISTS idx_videos_upload_date
                    ON videos(upload_date DESC);
            """)
            conn.commit()
        finally:
            conn.close()

    def upsert_channel(self, channel: Channel) -> None:
        """Insert or update a channel record."""
        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO channels
                    (youtube_id, name, handle, url, subscribers, total_views,
                     description, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(youtube_id) DO UPDATE SET
                    name = excluded.name,
                    handle = excluded.handle,
                    url = excluded.url,
                    subscribers = excluded.subscribers,
                    total_views = excluded.total_views,
                    description = excluded.description,
                    scraped_at = excluded.scraped_at
                """,
                (
                    channel.youtube_id,
                    channel.name,
                    channel.handle,
                    channel.url,
                    channel.subscribers,
                    channel.total_views,
                    channel.description,
                    channel.scraped_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_video(self, video: Video) -> None:
        """Insert or update a video record."""
        tags_json = json.dumps(video.tags) if video.tags is not None else None
        conn = self.connect()
        try:
            conn.execute(
                """
                INSERT INTO videos
                    (video_id, channel_id, title, url, views, upload_date,
                     description, duration, tags, likes, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    views = excluded.views,
                    likes = excluded.likes,
                    title = excluded.title,
                    description = excluded.description,
                    tags = excluded.tags,
                    scraped_at = excluded.scraped_at
                """,
                (
                    video.video_id,
                    video.channel_id,
                    video.title,
                    video.url,
                    video.views,
                    video.upload_date,
                    video.description,
                    video.duration,
                    tags_json,
                    video.likes,
                    video.scraped_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_videos(self, videos: list[Video]) -> None:
        """Batch upsert videos in a single transaction."""
        conn = self.connect()
        try:
            for video in videos:
                tags_json = (
                    json.dumps(video.tags) if video.tags is not None else None
                )
                conn.execute(
                    """
                    INSERT INTO videos
                        (video_id, channel_id, title, url, views, upload_date,
                         description, duration, tags, likes, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(video_id) DO UPDATE SET
                        views = excluded.views,
                        likes = excluded.likes,
                        title = excluded.title,
                        description = excluded.description,
                        tags = excluded.tags,
                        scraped_at = excluded.scraped_at
                    """,
                    (
                        video.video_id,
                        video.channel_id,
                        video.title,
                        video.url,
                        video.views,
                        video.upload_date,
                        video.description,
                        video.duration,
                        tags_json,
                        video.likes,
                        video.scraped_at,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def get_videos_by_channel(self, channel_id: str) -> list[Video]:
        """Return all videos for a given channel_id."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM videos WHERE channel_id = ?", (channel_id,)
            )
            rows = cursor.fetchall()
            videos = []
            for row in rows:
                tags_raw = row["tags"]
                tags = json.loads(tags_raw) if tags_raw is not None else None
                videos.append(
                    Video(
                        video_id=row["video_id"],
                        channel_id=row["channel_id"],
                        title=row["title"],
                        url=row["url"],
                        views=row["views"],
                        upload_date=row["upload_date"],
                        description=row["description"],
                        duration=row["duration"],
                        tags=tags,
                        likes=row["likes"],
                        scraped_at=row["scraped_at"],
                    )
                )
            return videos
        finally:
            conn.close()

    def get_channel_stats(self, channel_id: str) -> dict:
        """Return stats for a channel: video_count, last_scraped, latest_upload."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as video_count,
                    MAX(scraped_at) as last_scraped,
                    MAX(upload_date) as latest_upload
                FROM videos
                WHERE channel_id = ?
                """,
                (channel_id,),
            )
            row = cursor.fetchone()
            return {
                "video_count": row["video_count"],
                "last_scraped": row["last_scraped"],
                "latest_upload": row["latest_upload"],
            }
        finally:
            conn.close()

    def get_all_channels(self) -> list[Channel]:
        """Return all channels."""
        conn = self.connect()
        try:
            cursor = conn.execute("SELECT * FROM channels")
            rows = cursor.fetchall()
            return [
                Channel(
                    name=row["name"],
                    youtube_id=row["youtube_id"],
                    handle=row["handle"],
                    url=row["url"],
                    subscribers=row["subscribers"],
                    total_views=row["total_views"],
                    description=row["description"],
                    scraped_at=row["scraped_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()
