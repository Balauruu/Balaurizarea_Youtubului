"""Shared fixtures for channel assistant tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def sample_channel_data():
    """Sample channel data dict."""
    return {
        "name": "Barely Sociable",
        "youtube_id": "@BarelySociable",
        "url": "https://www.youtube.com/@BarelySociable",
        "notes": "Dark web + true crime crossover.",
        "added": "2026-03-11",
    }


@pytest.fixture
def sample_channel_data_2():
    """Second sample channel data dict."""
    return {
        "name": "Fredrik Knudsen",
        "youtube_id": "@FredrikKnudsen",
        "url": "https://www.youtube.com/@FredrikKnudsen",
        "notes": "Clinically neutral deep dives.",
        "added": "2026-03-11",
    }


@pytest.fixture
def sample_video_data():
    """Sample video data dict."""
    return {
        "video_id": "abc123",
        "channel_id": "@BarelySociable",
        "title": "The Dark Side of the Silk Road",
        "url": "https://www.youtube.com/watch?v=abc123",
        "views": 13100000,
        "upload_date": "2021-08-30",
        "description": "A deep dive into the Silk Road.",
        "duration": 4444,
        "tags": ["silk road", "dark web", "true crime"],
        "likes": 83000,
        "scraped_at": "2026-03-11T10:00:00Z",
    }


@pytest.fixture
def tmp_competitors_json(tmp_path):
    """Create a temporary competitors.json with seed data."""
    path = tmp_path / "competitors.json"
    data = {
        "channels": [
            {
                "name": "Barely Sociable",
                "youtube_id": "@BarelySociable",
                "url": "https://www.youtube.com/@BarelySociable",
                "notes": "Dark web + true crime crossover.",
                "added": "2026-03-11",
            }
        ]
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def tmp_empty_competitors_json(tmp_path):
    """Create an empty competitors.json."""
    path = tmp_path / "competitors.json"
    data = {"channels": []}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def sample_channel():
    """Return a Channel dataclass instance."""
    from channel_assistant.models import Channel

    return Channel(
        name="Barely Sociable",
        youtube_id="@BarelySociable",
        handle="@BarelySociable",
        url="https://www.youtube.com/@BarelySociable",
        subscribers=1200000,
        scraped_at="2026-03-11T10:00:00Z",
    )


@pytest.fixture
def sample_channel_2():
    """Return a second Channel dataclass instance."""
    from channel_assistant.models import Channel

    return Channel(
        name="Fredrik Knudsen",
        youtube_id="@FredrikKnudsen",
        handle="@FredrikKnudsen",
        url="https://www.youtube.com/@FredrikKnudsen",
        subscribers=800000,
        scraped_at="2026-03-11T10:00:00Z",
    )


@pytest.fixture
def sample_videos_varied():
    """Return 5 Video objects with diverse views, dates, and tags for a single channel."""
    from channel_assistant.models import Video

    return [
        Video(
            video_id="v1",
            channel_id="@BarelySociable",
            title="The Silk Road Deep Dive",
            views=5000,
            upload_date="2026-01-01",
            tags=["dark web", "crime"],
        ),
        Video(
            video_id="v2",
            channel_id="@BarelySociable",
            title="Cicada 3301",
            views=1000,
            upload_date="2026-01-11",
            tags=["mystery", "internet"],
        ),
        Video(
            video_id="v3",
            channel_id="@BarelySociable",
            title="The Most Dangerous Hacker",
            views=500,
            upload_date="2026-01-21",
            tags=["hacking"],
        ),
        Video(
            video_id="v4",
            channel_id="@BarelySociable",
            title="Lake City Quiet Pills",
            views=200,
            upload_date="2026-01-31",
            tags=["conspiracy"],
        ),
        Video(
            video_id="v5",
            channel_id="@BarelySociable",
            title="The Dark Web Iceberg",
            views=100,
            upload_date="2026-02-10",
            tags=["dark web", "iceberg"],
        ),
    ]
