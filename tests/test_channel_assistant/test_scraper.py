"""Tests for the yt-dlp scraper module."""

import json
import time
from unittest.mock import MagicMock, patch, call
import subprocess

import pytest

from channel_assistant.scraper import (
    ScrapeError,
    scrape_channel,
    scrape_all_channels,
    scrape_single_channel,
    VIDEO_FIELD_MAP,
    CHANNEL_FIELD_MAP,
)
from channel_assistant.models import Channel, Video
from channel_assistant.database import Database
from channel_assistant.registry import Registry


# --- Fixtures ---


def _make_ytdlp_video(
    video_id="abc123",
    title="Test Video",
    webpage_url="https://www.youtube.com/watch?v=abc123",
    view_count=100000,
    upload_date="20210830",
    description="A test video.",
    duration=2884,
    tags=None,
    like_count=5000,
    channel="Test Channel",
    channel_id="UCtest123",
    uploader_id="@TestChannel",
    channel_url="https://www.youtube.com/@TestChannel",
    channel_follower_count=50000,
):
    """Build a dict mimicking yt-dlp JSON output for one video."""
    if tags is None:
        tags = ["dark web", "mystery"]
    return {
        "id": video_id,
        "title": title,
        "webpage_url": webpage_url,
        "view_count": view_count,
        "upload_date": upload_date,
        "description": description,
        "duration": duration,
        "tags": tags,
        "like_count": like_count,
        "channel": channel,
        "channel_id": channel_id,
        "uploader_id": uploader_id,
        "channel_url": channel_url,
        "channel_follower_count": channel_follower_count,
        # extra fields that yt-dlp returns (should be ignored)
        "formats": [],
        "thumbnails": [],
    }


@pytest.fixture
def ytdlp_two_videos():
    """Two JSON-lines of yt-dlp output."""
    v1 = _make_ytdlp_video(video_id="vid001", title="Video One", upload_date="20230115")
    v2 = _make_ytdlp_video(video_id="vid002", title="Video Two", upload_date="20231031")
    return json.dumps(v1) + "\n" + json.dumps(v2) + "\n"


@pytest.fixture
def ytdlp_single_video():
    """Single JSON-line of yt-dlp output."""
    v = _make_ytdlp_video()
    return json.dumps(v) + "\n"


# --- Tests: scrape_channel ---


class TestScrapeChannel:
    """Tests for scrape_channel function."""

    @patch("channel_assistant.scraper.subprocess.run")
    def test_calls_ytdlp_with_correct_args(self, mock_run, ytdlp_single_video):
        """scrape_channel calls yt-dlp subprocess with correct args."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_single_video, stderr=""
        )

        scrape_channel("https://www.youtube.com/@TestChannel")

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "yt-dlp" in cmd[0] or cmd[0] == "yt-dlp"
        assert "--dump-json" in cmd
        assert "--skip-download" in cmd
        assert "--no-warnings" in cmd
        assert cmd[-1].endswith("/videos")

    @patch("channel_assistant.scraper.subprocess.run")
    def test_parses_json_lines_into_videos(self, mock_run, ytdlp_two_videos):
        """scrape_channel parses JSON-lines output into list of Video dataclasses."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_two_videos, stderr=""
        )

        channel, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert len(videos) == 2
        assert all(isinstance(v, Video) for v in videos)

    @patch("channel_assistant.scraper.subprocess.run")
    def test_video_field_mapping(self, mock_run, ytdlp_single_video):
        """scrape_channel maps yt-dlp fields to Video dataclass correctly."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_single_video, stderr=""
        )

        channel, videos = scrape_channel("https://www.youtube.com/@TestChannel")
        v = videos[0]

        assert v.video_id == "abc123"
        assert v.title == "Test Video"
        assert v.url == "https://www.youtube.com/watch?v=abc123"
        assert v.views == 100000
        assert v.description == "A test video."
        assert v.duration == 2884
        assert v.likes == 5000

    @patch("channel_assistant.scraper.subprocess.run")
    def test_upload_date_format_conversion(self, mock_run, ytdlp_single_video):
        """scrape_channel converts upload_date from YYYYMMDD to YYYY-MM-DD."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_single_video, stderr=""
        )

        _, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert videos[0].upload_date == "2021-08-30"

    @patch("channel_assistant.scraper.subprocess.run")
    def test_channel_metadata_extraction(self, mock_run, ytdlp_single_video):
        """scrape_channel extracts Channel metadata from first video result."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_single_video, stderr=""
        )

        channel, _ = scrape_channel("https://www.youtube.com/@TestChannel")

        assert isinstance(channel, Channel)
        assert channel.name == "Test Channel"
        assert channel.youtube_id == "UCtest123"
        assert channel.handle == "@TestChannel"
        assert channel.url == "https://www.youtube.com/@TestChannel"
        assert channel.subscribers == 50000
        assert channel.scraped_at is not None

    @patch("channel_assistant.scraper.time.sleep")
    @patch("channel_assistant.scraper.subprocess.run")
    def test_retry_on_failure(self, mock_run, mock_sleep, ytdlp_single_video):
        """On yt-dlp failure, retries up to 2 times with increasing delay."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="Error"),
            MagicMock(returncode=1, stdout="", stderr="Error"),
            MagicMock(returncode=0, stdout=ytdlp_single_video, stderr=""),
        ]

        channel, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2
        assert len(videos) == 1

    @patch("channel_assistant.scraper.time.sleep")
    @patch("channel_assistant.scraper.subprocess.run")
    def test_raises_scrape_error_after_retries_exhausted(self, mock_run, mock_sleep):
        """After 2 failed retries, raises ScrapeError."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="yt-dlp timeout"
        )

        with pytest.raises(ScrapeError, match="yt-dlp timeout"):
            scrape_channel("https://www.youtube.com/@TestChannel")

        assert mock_run.call_count == 6  # 3 attempts (full) + 3 attempts (flat-playlist fallback)

    @patch("channel_assistant.scraper.subprocess.run")
    def test_tags_preserved_as_list(self, mock_run):
        """Tags field from yt-dlp (list) is preserved as list in Video dataclass."""
        v = _make_ytdlp_video(tags=["cult", "mystery", "true crime"])
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(v) + "\n", stderr=""
        )

        _, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert videos[0].tags == ["cult", "mystery", "true crime"]
        assert isinstance(videos[0].tags, list)

    @patch("channel_assistant.scraper.subprocess.run")
    def test_channel_id_set_on_videos(self, mock_run, ytdlp_single_video):
        """Each Video gets channel_id set from yt-dlp channel_id field."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_single_video, stderr=""
        )

        _, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert videos[0].channel_id == "UCtest123"

    @patch("channel_assistant.scraper.subprocess.run")
    def test_scraped_at_set_on_all_records(self, mock_run, ytdlp_two_videos):
        """scraped_at is set to current ISO timestamp on all records."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=ytdlp_two_videos, stderr=""
        )

        channel, videos = scrape_channel("https://www.youtube.com/@TestChannel")

        assert channel.scraped_at is not None
        for v in videos:
            assert v.scraped_at is not None
            # Should be ISO format (contains T)
            assert "T" in v.scraped_at


# --- Tests: scrape_all_channels ---


class TestScrapeAllChannels:
    """Tests for scrape_all_channels function."""

    @patch("channel_assistant.scraper.time.sleep")
    @patch("channel_assistant.scraper.scrape_channel")
    def test_jittered_delay_between_channels(self, mock_scrape, mock_sleep, tmp_path):
        """scrape_all_channels adds jittered delay (3-8s) between channels."""
        db = Database(tmp_path / "test.db")
        db.init_db()

        reg_path = tmp_path / "competitors.json"
        reg_path.write_text(json.dumps({"channels": [
            {"name": "Ch1", "youtube_id": "@Ch1", "url": "https://www.youtube.com/@Ch1"},
            {"name": "Ch2", "youtube_id": "@Ch2", "url": "https://www.youtube.com/@Ch2"},
        ]}), encoding="utf-8")
        registry = Registry(reg_path)

        ch = Channel(name="Ch1", youtube_id="UC1", scraped_at="2026-03-11T00:00:00Z")
        mock_scrape.return_value = (ch, [])

        scrape_all_channels(registry, db)

        # Sleep called once between the 2 channels (not before first, not after last)
        assert mock_sleep.call_count == 1
        sleep_val = mock_sleep.call_args[0][0]
        assert 3 <= sleep_val <= 8

    @patch("channel_assistant.scraper.time.sleep")
    @patch("channel_assistant.scraper.scrape_channel")
    def test_failure_fallback_continues(self, mock_scrape, mock_sleep, tmp_path):
        """On channel failure: logs error, falls back to cached DB data, continues."""
        db = Database(tmp_path / "test.db")
        db.init_db()

        # Pre-populate some cached data for Ch1
        cached_channel = Channel(name="Ch1", youtube_id="UC1", scraped_at="2026-03-05T00:00:00Z")
        db.upsert_channel(cached_channel)
        cached_video = Video(
            video_id="v1", channel_id="UC1", title="Cached",
            scraped_at="2026-03-05T00:00:00Z",
        )
        db.upsert_video(cached_video)

        reg_path = tmp_path / "competitors.json"
        reg_path.write_text(json.dumps({"channels": [
            {"name": "Ch1", "youtube_id": "@Ch1", "url": "https://www.youtube.com/@Ch1"},
            {"name": "Ch2", "youtube_id": "@Ch2", "url": "https://www.youtube.com/@Ch2"},
        ]}), encoding="utf-8")
        registry = Registry(reg_path)

        ch2 = Channel(name="Ch2", youtube_id="UC2", scraped_at="2026-03-11T00:00:00Z")
        mock_scrape.side_effect = [
            ScrapeError("timeout"),
            (ch2, []),
        ]

        result = scrape_all_channels(registry, db)

        # Should not crash -- continues after failure
        assert len(result["failed"]) == 1
        assert len(result["succeeded"]) == 1

    @patch("channel_assistant.scraper.time.sleep")
    @patch("channel_assistant.scraper.scrape_channel")
    def test_returns_summary_dict(self, mock_scrape, mock_sleep, tmp_path):
        """scrape_all_channels returns a result summary dict."""
        db = Database(tmp_path / "test.db")
        db.init_db()

        reg_path = tmp_path / "competitors.json"
        reg_path.write_text(json.dumps({"channels": [
            {"name": "Ch1", "youtube_id": "@Ch1", "url": "https://www.youtube.com/@Ch1"},
        ]}), encoding="utf-8")
        registry = Registry(reg_path)

        ch = Channel(name="Ch1", youtube_id="UC1", scraped_at="2026-03-11T00:00:00Z")
        v = Video(video_id="v1", channel_id="UC1", title="Vid", scraped_at="2026-03-11T00:00:00Z")
        mock_scrape.return_value = (ch, [v])

        result = scrape_all_channels(registry, db)

        assert "succeeded" in result
        assert "failed" in result
        assert "total_new" in result
        assert "total_updated" in result


# --- Tests: scrape_single_channel ---


class TestScrapeSingleChannel:
    """Tests for scrape_single_channel function."""

    @patch("channel_assistant.scraper.scrape_channel")
    def test_scrapes_by_name(self, mock_scrape, tmp_path):
        """scrape_single_channel looks up channel by name and scrapes it."""
        db = Database(tmp_path / "test.db")
        db.init_db()

        reg_path = tmp_path / "competitors.json"
        reg_path.write_text(json.dumps({"channels": [
            {"name": "Barely Sociable", "youtube_id": "@BarelySociable",
             "url": "https://www.youtube.com/@BarelySociable"},
        ]}), encoding="utf-8")
        registry = Registry(reg_path)

        ch = Channel(name="Barely Sociable", youtube_id="UC1", scraped_at="2026-03-11T00:00:00Z")
        mock_scrape.return_value = (ch, [])

        result = scrape_single_channel("Barely", registry, db)

        mock_scrape.assert_called_once()
        assert result is not None
