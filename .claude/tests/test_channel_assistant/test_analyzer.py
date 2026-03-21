"""Tests for channel_assistant.analyzer module."""

import pytest
from channel_assistant.models import Channel, Video


class TestComputeChannelStats:
    """Tests for compute_channel_stats function."""

    def test_basic_stats(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import compute_channel_stats

        stats = compute_channel_stats(sample_channel, sample_videos_varied)
        assert stats["total_videos"] == 5
        assert stats["avg_views"] == 1360
        assert stats["median_views"] == 500
        assert stats["most_recent_upload"] == "2026-02-10"

    def test_upload_frequency(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import compute_channel_stats

        stats = compute_channel_stats(sample_channel, sample_videos_varied)
        assert stats["upload_frequency_days"] == 10.0

    def test_empty_videos(self, sample_channel):
        from channel_assistant.analyzer import compute_channel_stats

        stats = compute_channel_stats(sample_channel, [])
        assert stats["total_videos"] == 0
        assert stats["avg_views"] == 0
        assert stats["median_views"] == 0
        assert stats["upload_frequency_days"] is None
        assert stats["most_recent_upload"] is None

    def test_none_views_filtered(self, sample_channel):
        from channel_assistant.analyzer import compute_channel_stats

        videos = [
            Video(video_id="a", channel_id="x", title="A", views=100),
            Video(video_id="b", channel_id="x", title="B", views=None),
            Video(video_id="c", channel_id="x", title="C", views=300),
        ]
        stats = compute_channel_stats(sample_channel, videos)
        assert stats["avg_views"] == 200
        assert stats["median_views"] == 200

    def test_single_video_no_frequency(self, sample_channel):
        from channel_assistant.analyzer import compute_channel_stats

        videos = [
            Video(
                video_id="a",
                channel_id="x",
                title="A",
                views=100,
                upload_date="2026-01-01",
            )
        ]
        stats = compute_channel_stats(sample_channel, videos)
        assert stats["total_videos"] == 1
        assert stats["upload_frequency_days"] is None

    def test_yyyymmdd_date_format(self, sample_channel):
        """yt-dlp sometimes returns dates as YYYYMMDD without dashes."""
        from channel_assistant.analyzer import compute_channel_stats

        videos = [
            Video(video_id="a", channel_id="x", title="A", views=100, upload_date="20260101"),
            Video(video_id="b", channel_id="x", title="B", views=200, upload_date="20260111"),
        ]
        stats = compute_channel_stats(sample_channel, videos)
        assert stats["upload_frequency_days"] == 10.0
        assert stats["most_recent_upload"] == "20260111"


class TestDetectOutliers:
    """Tests for detect_outliers function."""

    def test_basic_outliers(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import detect_outliers

        outliers = detect_outliers(sample_channel, sample_videos_varied)
        assert len(outliers) == 2
        # Sorted by multiplier descending
        assert outliers[0]["title"] == "The Silk Road Deep Dive"
        assert outliers[0]["multiplier"] == 10.0
        assert outliers[1]["title"] == "Cicada 3301"
        assert outliers[1]["multiplier"] == 2.0

    def test_outlier_dict_keys(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import detect_outliers

        outliers = detect_outliers(sample_channel, sample_videos_varied)
        for o in outliers:
            assert "title" in o
            assert "channel" in o
            assert "views" in o
            assert "multiplier" in o
            assert "upload_date" in o

    def test_custom_threshold(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import detect_outliers

        outliers = detect_outliers(sample_channel, sample_videos_varied, threshold=5.0)
        assert len(outliers) == 1
        assert outliers[0]["title"] == "The Silk Road Deep Dive"

    def test_all_none_views(self, sample_channel):
        from channel_assistant.analyzer import detect_outliers

        videos = [
            Video(video_id="a", channel_id="x", title="A", views=None),
            Video(video_id="b", channel_id="x", title="B", views=None),
        ]
        outliers = detect_outliers(sample_channel, videos)
        assert outliers == []

    def test_zero_median(self, sample_channel):
        from channel_assistant.analyzer import detect_outliers

        videos = [
            Video(video_id="a", channel_id="x", title="A", views=0),
            Video(video_id="b", channel_id="x", title="B", views=0),
            Video(video_id="c", channel_id="x", title="C", views=100),
        ]
        outliers = detect_outliers(sample_channel, videos)
        assert outliers == []


class TestFormatStatsTable:
    """Tests for format_stats_table function."""

    def test_two_channels(self):
        from channel_assistant.analyzer import format_stats_table

        all_stats = [
            {
                "channel": "Barely Sociable",
                "total_videos": 47,
                "avg_views": 1234567,
                "median_views": 500000,
                "upload_frequency_days": 10.0,
                "most_recent_upload": "2026-02-15",
            },
            {
                "channel": "Fredrik Knudsen",
                "total_videos": 39,
                "avg_views": 890123,
                "median_views": 400000,
                "upload_frequency_days": None,
                "most_recent_upload": "2025-12-01",
            },
        ]
        table = format_stats_table(all_stats)
        assert "Barely Sociable" in table
        assert "Fredrik Knudsen" in table
        assert "1,234,567" in table
        assert "500,000" in table
        assert "10d" in table
        assert "n/a" in table
        # Has header separator
        lines = table.strip().split("\n")
        assert len(lines) >= 4  # header + separator + 2 data rows
        assert "---" in lines[1] or "---" in lines[1]

    def test_views_comma_formatted(self):
        from channel_assistant.analyzer import format_stats_table

        all_stats = [
            {
                "channel": "Test",
                "total_videos": 5,
                "avg_views": 999,
                "median_views": 100,
                "upload_frequency_days": 7.0,
                "most_recent_upload": "2026-01-01",
            }
        ]
        table = format_stats_table(all_stats)
        assert "999" in table


class TestSerializeVideos:
    """Tests for serialize_videos_for_analysis function."""

    def test_single_channel(self, sample_channel, sample_videos_varied):
        from channel_assistant.analyzer import serialize_videos_for_analysis

        data = {"Barely Sociable": sample_videos_varied}
        result = serialize_videos_for_analysis(data)
        assert "Barely Sociable" in result
        # Videos sorted by views descending - first line should be highest views
        lines = result.strip().split("\n")
        video_lines = [l for l in lines if "The Silk Road Deep Dive" in l]
        assert len(video_lines) == 1

    def test_videos_sorted_by_views_descending(self, sample_videos_varied):
        from channel_assistant.analyzer import serialize_videos_for_analysis

        data = {"Test Channel": sample_videos_varied}
        result = serialize_videos_for_analysis(data)
        # Find positions of video titles - higher views should come first
        pos_5000 = result.index("The Silk Road Deep Dive")
        pos_100 = result.index("The Dark Web Iceberg")
        assert pos_5000 < pos_100

    def test_includes_views_and_tags(self, sample_videos_varied):
        from channel_assistant.analyzer import serialize_videos_for_analysis

        data = {"Test": sample_videos_varied}
        result = serialize_videos_for_analysis(data)
        assert "5,000" in result
        assert "dark web" in result

    def test_multiple_channels(self, sample_videos_varied):
        from channel_assistant.analyzer import serialize_videos_for_analysis

        data = {
            "Channel A": sample_videos_varied[:2],
            "Channel B": sample_videos_varied[2:],
        }
        result = serialize_videos_for_analysis(data)
        assert "Channel A" in result
        assert "Channel B" in result
