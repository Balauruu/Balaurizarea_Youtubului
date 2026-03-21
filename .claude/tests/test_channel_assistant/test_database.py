"""Tests for the Database module."""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / ".claude"
        / "skills"
        / "channel-assistant"
        / "scripts"
    ),
)

from channel_assistant.database import Database
from channel_assistant.models import Channel, Video


class TestInitDb:
    """Tests for database initialization."""

    def test_creates_channels_table(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        conn = db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='channels'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_creates_videos_table(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        conn = db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_channels_has_correct_columns(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        conn = db.connect()
        cursor = conn.execute("PRAGMA table_info(channels)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "youtube_id",
            "name",
            "handle",
            "url",
            "subscribers",
            "total_views",
            "description",
            "scraped_at",
        }
        assert expected == columns
        conn.close()

    def test_videos_has_correct_columns(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        conn = db.connect()
        cursor = conn.execute("PRAGMA table_info(videos)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "video_id",
            "channel_id",
            "title",
            "url",
            "views",
            "upload_date",
            "description",
            "duration",
            "tags",
            "likes",
            "scraped_at",
        }
        assert expected == columns
        conn.close()

    def test_creates_indexes(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        conn = db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_videos_channel" in indexes
        assert "idx_videos_views" in indexes
        assert "idx_videos_upload_date" in indexes
        conn.close()


class TestUpsertChannel:
    """Tests for channel upsert operations."""

    def test_insert_new_channel(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test Channel",
            youtube_id="UC123",
            handle="@TestChannel",
            url="https://www.youtube.com/@TestChannel",
            subscribers=1000,
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)
        channels = db.get_all_channels()
        assert len(channels) == 1
        assert channels[0].name == "Test Channel"
        assert channels[0].youtube_id == "UC123"

    def test_upsert_updates_existing_channel(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch1 = Channel(
            name="Old Name",
            youtube_id="UC123",
            handle="@Test",
            subscribers=100,
            scraped_at="2026-03-10T10:00:00Z",
        )
        db.upsert_channel(ch1)

        ch2 = Channel(
            name="New Name",
            youtube_id="UC123",
            handle="@TestUpdated",
            url="https://example.com",
            subscribers=200,
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch2)

        channels = db.get_all_channels()
        assert len(channels) == 1  # No duplicate
        assert channels[0].name == "New Name"
        assert channels[0].subscribers == 200
        assert channels[0].handle == "@TestUpdated"


class TestUpsertVideo:
    """Tests for video upsert operations."""

    def test_insert_new_video(self, tmp_db_path, sample_video_data):
        db = Database(tmp_db_path)
        db.init_db()
        # Insert channel first for FK
        ch = Channel(
            name="Test",
            youtube_id="@BarelySociable",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        v = Video(**sample_video_data)
        db.upsert_video(v)

        videos = db.get_videos_by_channel("@BarelySociable")
        assert len(videos) == 1
        assert videos[0].title == "The Dark Side of the Silk Road"
        assert videos[0].views == 13100000

    def test_upsert_updates_existing_video(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        v1 = Video(
            video_id="vid1",
            channel_id="@Test",
            title="Old Title",
            views=100,
            likes=10,
            description="Old desc",
            tags=["old"],
            scraped_at="2026-03-10T10:00:00Z",
        )
        db.upsert_video(v1)

        v2 = Video(
            video_id="vid1",
            channel_id="@Test",
            title="New Title",
            views=200,
            likes=20,
            description="New desc",
            tags=["new", "updated"],
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_video(v2)

        videos = db.get_videos_by_channel("@Test")
        assert len(videos) == 1  # No duplicate
        assert videos[0].title == "New Title"
        assert videos[0].views == 200
        assert videos[0].likes == 20
        assert videos[0].description == "New desc"
        assert videos[0].scraped_at == "2026-03-11T10:00:00Z"


class TestTagsSerialization:
    """Tests for tags JSON round-trip."""

    def test_tags_roundtrip(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        original_tags = ["dark web", "true crime", "documentary"]
        v = Video(
            video_id="vid1",
            channel_id="@Test",
            title="Test",
            tags=original_tags,
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_video(v)

        videos = db.get_videos_by_channel("@Test")
        assert videos[0].tags == original_tags
        assert isinstance(videos[0].tags, list)

    def test_none_tags_roundtrip(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        v = Video(
            video_id="vid1",
            channel_id="@Test",
            title="Test",
            tags=None,
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_video(v)

        videos = db.get_videos_by_channel("@Test")
        assert videos[0].tags is None


class TestGetVideosByChannel:
    """Tests for querying videos by channel."""

    def test_returns_all_videos_for_channel(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        for i in range(3):
            v = Video(
                video_id=f"vid{i}",
                channel_id="@Test",
                title=f"Video {i}",
                scraped_at="2026-03-11T10:00:00Z",
            )
            db.upsert_video(v)

        videos = db.get_videos_by_channel("@Test")
        assert len(videos) == 3


class TestGetChannelStats:
    """Tests for channel statistics."""

    def test_returns_stats_dict(self, tmp_db_path):
        db = Database(tmp_db_path)
        db.init_db()
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_channel(ch)

        v1 = Video(
            video_id="vid1",
            channel_id="@Test",
            title="Video 1",
            upload_date="2026-01-15",
            scraped_at="2026-03-10T10:00:00Z",
        )
        v2 = Video(
            video_id="vid2",
            channel_id="@Test",
            title="Video 2",
            upload_date="2026-02-20",
            scraped_at="2026-03-11T10:00:00Z",
        )
        db.upsert_video(v1)
        db.upsert_video(v2)

        stats = db.get_channel_stats("@Test")
        assert stats["video_count"] == 2
        assert stats["last_scraped"] == "2026-03-11T10:00:00Z"
        assert stats["latest_upload"] == "2026-02-20"
