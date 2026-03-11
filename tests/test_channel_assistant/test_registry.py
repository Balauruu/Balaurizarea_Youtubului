"""Tests for the Registry module and data models."""

import json
import sys
from pathlib import Path

import pytest

# Add skill scripts to path
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

from channel_assistant.models import Channel, Video
from channel_assistant.registry import Registry


class TestChannelDataclass:
    """Tests for Channel dataclass."""

    def test_channel_has_required_fields(self):
        ch = Channel(
            name="Test",
            youtube_id="@Test",
            handle="@Test",
            url="https://www.youtube.com/@Test",
            subscribers=1000,
            total_views=50000,
            description="A test channel",
            scraped_at="2026-03-11T10:00:00Z",
        )
        assert ch.name == "Test"
        assert ch.youtube_id == "@Test"
        assert ch.handle == "@Test"
        assert ch.url == "https://www.youtube.com/@Test"
        assert ch.subscribers == 1000
        assert ch.total_views == 50000
        assert ch.description == "A test channel"
        assert ch.scraped_at == "2026-03-11T10:00:00Z"

    def test_channel_nullable_fields(self):
        ch = Channel(name="Test", youtube_id="@Test")
        assert ch.handle is None
        assert ch.url is None
        assert ch.subscribers is None
        assert ch.total_views is None
        assert ch.description is None
        assert ch.scraped_at is None


class TestVideoDataclass:
    """Tests for Video dataclass."""

    def test_video_has_required_fields(self):
        v = Video(
            video_id="abc123",
            channel_id="@Test",
            title="Test Video",
            url="https://www.youtube.com/watch?v=abc123",
            views=1000,
            upload_date="2026-01-01",
            description="A test video",
            duration=300,
            tags=["test", "video"],
            likes=100,
            scraped_at="2026-03-11T10:00:00Z",
        )
        assert v.video_id == "abc123"
        assert v.channel_id == "@Test"
        assert v.title == "Test Video"
        assert v.url == "https://www.youtube.com/watch?v=abc123"
        assert v.views == 1000
        assert v.upload_date == "2026-01-01"
        assert v.description == "A test video"
        assert v.duration == 300
        assert v.tags == ["test", "video"]
        assert v.likes == 100
        assert v.scraped_at == "2026-03-11T10:00:00Z"

    def test_video_nullable_fields(self):
        v = Video(video_id="abc123", channel_id="@Test", title="Test")
        assert v.url is None
        assert v.views is None
        assert v.upload_date is None
        assert v.description is None
        assert v.duration is None
        assert v.tags is None
        assert v.likes is None
        assert v.scraped_at is None


class TestRegistryLoad:
    """Tests for loading competitors.json."""

    def test_load_returns_list_of_channel_dicts(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        channels = reg.load()
        assert isinstance(channels, list)
        assert len(channels) == 1
        ch = channels[0]
        assert "name" in ch
        assert "youtube_id" in ch
        assert "url" in ch
        assert "notes" in ch
        assert "added" in ch

    def test_load_has_required_fields(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        channels = reg.load()
        ch = channels[0]
        assert ch["name"] == "Barely Sociable"
        assert ch["youtube_id"] == "@BarelySociable"
        assert ch["url"] == "https://www.youtube.com/@BarelySociable"


class TestRegistryAdd:
    """Tests for adding channels."""

    def test_add_valid_channel(self, tmp_empty_competitors_json):
        reg = Registry(tmp_empty_competitors_json)
        result = reg.add(
            name="Test Channel",
            youtube_id="@TestChannel",
            url="https://www.youtube.com/@TestChannel",
            notes="A test channel",
        )
        assert result["name"] == "Test Channel"
        assert result["youtube_id"] == "@TestChannel"
        # Verify it persisted
        channels = reg.load()
        assert len(channels) == 1
        assert channels[0]["youtube_id"] == "@TestChannel"

    def test_add_missing_name_raises(self, tmp_empty_competitors_json):
        reg = Registry(tmp_empty_competitors_json)
        with pytest.raises(ValueError):
            reg.add(name="", youtube_id="@TestChannel", url="https://example.com")

    def test_add_missing_youtube_id_raises(self, tmp_empty_competitors_json):
        reg = Registry(tmp_empty_competitors_json)
        with pytest.raises(ValueError):
            reg.add(name="Test", youtube_id="", url="https://example.com")

    def test_add_duplicate_youtube_id_raises(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        with pytest.raises(ValueError, match="duplicate"):
            reg.add(
                name="Another Name",
                youtube_id="@BarelySociable",
                url="https://example.com",
            )

    def test_add_youtube_id_must_start_with_at(self, tmp_empty_competitors_json):
        reg = Registry(tmp_empty_competitors_json)
        with pytest.raises(ValueError, match="@"):
            reg.add(
                name="Test",
                youtube_id="NoAtSign",
                url="https://example.com",
            )


class TestRegistryListAndGet:
    """Tests for listing and getting channels."""

    def test_list_channels(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        channels = reg.list_channels()
        assert len(channels) == 1
        assert channels[0]["name"] == "Barely Sociable"

    def test_get_by_name_exact(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        ch = reg.get_by_name("Barely Sociable")
        assert ch is not None
        assert ch["youtube_id"] == "@BarelySociable"

    def test_get_by_name_case_insensitive(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        ch = reg.get_by_name("barely sociable")
        assert ch is not None
        assert ch["youtube_id"] == "@BarelySociable"

    def test_get_by_name_partial(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        ch = reg.get_by_name("barely")
        assert ch is not None
        assert ch["youtube_id"] == "@BarelySociable"

    def test_get_by_name_not_found(self, tmp_competitors_json):
        reg = Registry(tmp_competitors_json)
        ch = reg.get_by_name("Nonexistent Channel")
        assert ch is None
