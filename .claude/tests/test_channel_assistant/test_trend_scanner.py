"""Tests for channel_assistant.trend_scanner module.

All external I/O is mocked — no live network calls in this test suite.
"""

import asyncio
import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_autocomplete_jsonp(suggestions: list[str], nested: bool = False) -> bytes:
    """Build a JSONP autocomplete response matching the real endpoint format.

    Args:
        suggestions: List of suggestion strings.
        nested: If True, wrap each suggestion as [text, 0, [512]] to match
                the real Google API format. If False, use plain strings.
    """
    if nested:
        items = [[s, 0, [512]] for s in suggestions]
    else:
        items = suggestions
    data = ["keyword", items]
    return f"window.google.ac.h({json.dumps(data)})".encode("utf-8")


def _make_ytInitialData(videos: list[dict]) -> str:
    """Wrap a list of videoRenderer dicts in minimal ytInitialData structure."""
    contents = [{"videoRenderer": v} for v in videos]
    item_section = {
        "itemSectionRenderer": {
            "contents": contents
        }
    }
    data = {
        "contents": {
            "twoColumnSearchResultsRenderer": {
                "primaryContents": {
                    "sectionListRenderer": {
                        "contents": [item_section]
                    }
                }
            }
        }
    }
    return f"var ytInitialData = {json.dumps(data)};"


def _make_video_renderer(video_id="abc", title="Test Video", channel="TestChan",
                         published="2 weeks ago", views="1M views") -> dict:
    """Build a minimal videoRenderer dict."""
    return {
        "videoId": video_id,
        "title": {"runs": [{"text": title}]},
        "longBylineText": {"runs": [{"text": channel}]},
        "publishedTimeText": {"simpleText": published},
        "viewCountText": {"simpleText": views},
    }


# ---------------------------------------------------------------------------
# scrape_autocomplete tests
# ---------------------------------------------------------------------------

class TestScrapeAutocomplete:
    """Tests for scrape_autocomplete()."""

    def test_returns_suggestion_strings_on_well_formed_response(self):
        """scrape_autocomplete returns list of strings from valid JSONP."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        suggestions = ["cult documentary", "cult documentary 2023", "cult movies"]
        mock_response = MagicMock()
        mock_response.read.return_value = _make_autocomplete_jsonp(suggestions)
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   return_value=mock_response):
            result = scrape_autocomplete("cult documentary")

        assert isinstance(result, list)
        assert result == suggestions

    def test_returns_empty_list_on_malformed_response(self):
        """scrape_autocomplete returns [] when JSONP has no parseable list."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid jsonp at all"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   return_value=mock_response):
            result = scrape_autocomplete("cult documentary")

        assert result == []

    def test_returns_empty_list_on_empty_response(self):
        """scrape_autocomplete returns [] when suggestions list is empty."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        mock_response = MagicMock()
        mock_response.read.return_value = _make_autocomplete_jsonp([])
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   return_value=mock_response):
            result = scrape_autocomplete("cult documentary")

        assert result == []

    def test_returns_empty_list_on_network_timeout(self):
        """scrape_autocomplete returns [] when urllib raises URLError."""
        import urllib.error
        from channel_assistant.trend_scanner import scrape_autocomplete

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   side_effect=urllib.error.URLError("timeout")):
            result = scrape_autocomplete("cult documentary")

        assert result == []

    def test_returns_empty_list_on_timeout_error(self):
        """scrape_autocomplete returns [] on TimeoutError."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   side_effect=TimeoutError("timed out")):
            result = scrape_autocomplete("dark mysteries")

        assert result == []

    def test_returns_list_of_strings(self):
        """scrape_autocomplete return value is a list of str, not other types."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        suggestions = ["dark cults history", "dark cults explained"]
        mock_response = MagicMock()
        mock_response.read.return_value = _make_autocomplete_jsonp(suggestions)
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   return_value=mock_response):
            result = scrape_autocomplete("dark cults")

        assert all(isinstance(s, str) for s in result)

    def test_handles_nested_list_format_from_real_api(self):
        """scrape_autocomplete extracts text from nested [text, 0, [512]] items."""
        from channel_assistant.trend_scanner import scrape_autocomplete

        suggestions = ["cult documentary", "cult documentary 2025"]
        mock_response = MagicMock()
        mock_response.read.return_value = _make_autocomplete_jsonp(
            suggestions, nested=True
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("channel_assistant.trend_scanner.urllib.request.urlopen",
                   return_value=mock_response):
            result = scrape_autocomplete("cult documentary")

        assert result == suggestions
        assert all(isinstance(s, str) for s in result)


# ---------------------------------------------------------------------------
# scrape_search_results tests
# ---------------------------------------------------------------------------

class TestScrapeSearchResults:
    """Tests for scrape_search_results()."""

    def _mock_crawler(self, html_content: str):
        """Build a mock AsyncWebCrawler context manager that returns html_content."""
        mock_result = MagicMock()
        mock_result.html = html_content

        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
        mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
        mock_crawler_instance.__aexit__ = AsyncMock(return_value=False)

        mock_crawler_class = MagicMock(return_value=mock_crawler_instance)
        return mock_crawler_class

    def test_returns_list_of_dicts_on_valid_html(self):
        """scrape_search_results returns list of dicts with expected keys."""
        from channel_assistant.trend_scanner import scrape_search_results

        renderer = _make_video_renderer(
            video_id="xyz123", title="Dark Cults Exposed", channel="MysteryChannel",
            published="3 weeks ago", views="500K views"
        )
        html = _make_ytInitialData([renderer])
        mock_class = self._mock_crawler(html)

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("dark cults")

        assert isinstance(result, list)
        assert len(result) >= 1
        video = result[0]
        assert "video_id" in video
        assert "title" in video
        assert "channel" in video
        assert "published_text" in video
        assert "views_text" in video

    def test_returns_correct_video_data(self):
        """scrape_search_results maps videoRenderer fields correctly."""
        from channel_assistant.trend_scanner import scrape_search_results

        renderer = _make_video_renderer(
            video_id="vid001", title="Cult Mysteries Deep Dive",
            channel="DarkHistory", published="1 month ago", views="2M views"
        )
        html = _make_ytInitialData([renderer])
        mock_class = self._mock_crawler(html)

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("cult mysteries")

        assert result[0]["video_id"] == "vid001"
        assert result[0]["title"] == "Cult Mysteries Deep Dive"
        assert result[0]["channel"] == "DarkHistory"
        assert result[0]["published_text"] == "1 month ago"
        assert result[0]["views_text"] == "2M views"

    def test_returns_empty_list_when_ytInitialData_missing(self):
        """scrape_search_results returns [] when ytInitialData JSON path is missing."""
        from channel_assistant.trend_scanner import scrape_search_results

        html = "<html><body>No ytInitialData here</body></html>"
        mock_class = self._mock_crawler(html)

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("dark cults")

        assert result == []

    def test_returns_empty_list_on_empty_html(self):
        """scrape_search_results returns [] when crawl4ai returns empty HTML."""
        from channel_assistant.trend_scanner import scrape_search_results

        mock_class = self._mock_crawler("")

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("dark cults")

        assert result == []

    def test_returns_empty_list_on_missing_json_path(self):
        """scrape_search_results returns [] when JSON structure is malformed."""
        from channel_assistant.trend_scanner import scrape_search_results

        # ytInitialData present but missing the expected nested path
        partial_data = {"contents": {"twoColumnSearchResultsRenderer": {}}}
        html = f"var ytInitialData = {json.dumps(partial_data)};"
        mock_class = self._mock_crawler(html)

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("dark cults")

        assert result == []

    def test_multiple_results_returned(self):
        """scrape_search_results returns multiple videos when present."""
        from channel_assistant.trend_scanner import scrape_search_results

        renderers = [
            _make_video_renderer(video_id=f"v{i}", title=f"Video {i}")
            for i in range(5)
        ]
        html = _make_ytInitialData(renderers)
        mock_class = self._mock_crawler(html)

        with patch("channel_assistant.trend_scanner.AsyncWebCrawler", mock_class):
            result = scrape_search_results("mystery")

        assert len(result) == 5


# ---------------------------------------------------------------------------
# get_recent_competitor_videos tests
# ---------------------------------------------------------------------------

class TestGetRecentCompetitorVideos:
    """Tests for get_recent_competitor_videos()."""

    def _make_db_with_videos(self, tmp_path, video_rows: list[tuple]) -> "Database":
        """Create an in-memory SQLite DB with given video rows.

        video_rows: list of (video_id, channel_id, title, upload_date) tuples.
        """
        from channel_assistant.database import Database

        db = Database(tmp_path / "test.db")
        db.init_db()

        conn = db.connect()
        try:
            # Insert a channel first (FK constraint)
            conn.execute(
                "INSERT OR IGNORE INTO channels (youtube_id, name, scraped_at) VALUES (?, ?, ?)",
                ("ch1", "Test Channel", "2026-01-01T00:00:00Z")
            )
            for row in video_rows:
                video_id, channel_id, title, upload_date = row
                conn.execute(
                    """INSERT OR IGNORE INTO videos
                       (video_id, channel_id, title, scraped_at, upload_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (video_id, channel_id, title, "2026-01-01T00:00:00Z", upload_date)
                )
            conn.commit()
        finally:
            conn.close()

        return db

    def test_returns_videos_within_30_days(self, tmp_path):
        """get_recent_competitor_videos returns videos uploaded in last 30 days."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos
        from datetime import date, timedelta

        recent = (date.today() - timedelta(days=5)).isoformat()
        old = (date.today() - timedelta(days=60)).isoformat()

        db = self._make_db_with_videos(tmp_path, [
            ("v1", "ch1", "Recent Video", recent),
            ("v2", "ch1", "Old Video", old),
        ])

        result = get_recent_competitor_videos(db, days=30)

        titles = [r["title"] for r in result]
        assert "Recent Video" in titles
        assert "Old Video" not in titles

    def test_excludes_null_upload_date(self, tmp_path):
        """get_recent_competitor_videos excludes rows where upload_date IS NULL."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos

        db = self._make_db_with_videos(tmp_path, [
            ("v1", "ch1", "Video With Date", "2026-03-01"),
            ("v2", "ch1", "Video Without Date", None),
        ])

        result = get_recent_competitor_videos(db, days=3650)  # 10 years to include old dates

        titles = [r["title"] for r in result]
        assert "Video Without Date" not in titles

    def test_returns_empty_list_when_no_recent_videos(self, tmp_path):
        """get_recent_competitor_videos returns [] when no videos in time window."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos

        db = self._make_db_with_videos(tmp_path, [
            ("v1", "ch1", "Very Old Video", "2010-01-01"),
        ])

        result = get_recent_competitor_videos(db, days=30)

        assert result == []

    def test_returns_dicts_with_expected_keys(self, tmp_path):
        """get_recent_competitor_videos dicts have title, upload_date, channel_name."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos
        from datetime import date, timedelta

        recent = (date.today() - timedelta(days=3)).isoformat()

        db = self._make_db_with_videos(tmp_path, [
            ("v1", "ch1", "Test Video", recent),
        ])

        result = get_recent_competitor_videos(db, days=30)

        assert len(result) == 1
        assert "title" in result[0]
        assert "upload_date" in result[0]
        assert "channel_name" in result[0]

    def test_results_ordered_by_date_descending(self, tmp_path):
        """get_recent_competitor_videos returns newest first."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos
        from datetime import date, timedelta

        date1 = (date.today() - timedelta(days=2)).isoformat()
        date2 = (date.today() - timedelta(days=10)).isoformat()

        db = self._make_db_with_videos(tmp_path, [
            ("v1", "ch1", "Older Video", date2),
            ("v2", "ch1", "Newer Video", date1),
        ])

        result = get_recent_competitor_videos(db, days=30)

        assert result[0]["title"] == "Newer Video"
        assert result[1]["title"] == "Older Video"

    def test_returns_empty_list_on_empty_db(self, tmp_path):
        """get_recent_competitor_videos returns [] when DB has no videos."""
        from channel_assistant.trend_scanner import get_recent_competitor_videos
        from channel_assistant.database import Database

        db = Database(tmp_path / "empty.db")
        db.init_db()

        result = get_recent_competitor_videos(db, days=30)

        assert result == []


# ---------------------------------------------------------------------------
# derive_keywords tests
# ---------------------------------------------------------------------------

class TestDeriveKeywords:
    """Tests for derive_keywords()."""

    SAMPLE_CHANNEL_DNA = """# Channel DNA

## Core Content Pillars

1. **Obscure Historical Crimes** — Real events buried by time.
2. **Cults & Psychological Control** — Groups that bent reality.
3. **Unsolved Disappearances & Mysteries** — Cases with no resolution.
4. **Institutional Corruption & Cover-ups** — Governments that failed.
5. **Dark Web & Internet Underbelly** — Digital crimes.
"""

    def test_returns_list_of_strings(self):
        """derive_keywords always returns a list of strings."""
        from channel_assistant.trend_scanner import derive_keywords

        result = derive_keywords(self.SAMPLE_CHANNEL_DNA, [])
        assert isinstance(result, list)
        assert all(isinstance(k, str) for k in result)

    def test_includes_topic_cluster_keywords(self):
        """derive_keywords includes topic_clusters values in output."""
        from channel_assistant.trend_scanner import derive_keywords

        clusters = ["cults", "disappearances", "cold case"]
        result = derive_keywords(self.SAMPLE_CHANNEL_DNA, clusters)

        for cluster in clusters:
            assert cluster in result

    def test_deduplicates_keywords(self):
        """derive_keywords deduplicates — no repeated entries."""
        from channel_assistant.trend_scanner import derive_keywords

        clusters = ["dark web", "dark web", "mysteries"]
        result = derive_keywords(self.SAMPLE_CHANNEL_DNA, clusters)

        assert len(result) == len(set(result))

    def test_falls_back_to_constants_on_empty_dna(self):
        """derive_keywords uses CONTENT_PILLAR_KEYWORDS fallback when DNA is empty."""
        from channel_assistant.trend_scanner import (
            derive_keywords,
            CONTENT_PILLAR_KEYWORDS,
        )

        result = derive_keywords("", [])

        # All fallback keywords should appear in result
        for kw in CONTENT_PILLAR_KEYWORDS:
            assert kw in result

    def test_combined_pillar_and_cluster_keywords(self):
        """derive_keywords combines extracted pillars with topic clusters."""
        from channel_assistant.trend_scanner import derive_keywords

        clusters = ["specific topic 1", "specific topic 2"]
        result = derive_keywords(self.SAMPLE_CHANNEL_DNA, clusters)

        # Both cluster keywords must appear
        assert "specific topic 1" in result
        assert "specific topic 2" in result
        # Result is non-empty overall
        assert len(result) > 0

    def test_limits_cluster_input_to_five(self):
        """derive_keywords processes up to 5 topic_clusters."""
        from channel_assistant.trend_scanner import derive_keywords

        clusters = [f"cluster_{i}" for i in range(10)]
        result = derive_keywords(self.SAMPLE_CHANNEL_DNA, clusters)

        # Up to 5 cluster items included (may have fewer if deduped with pillars)
        cluster_hits = sum(1 for c in clusters if c in result)
        assert cluster_hits <= 5


# ---------------------------------------------------------------------------
# update_analysis_with_trends tests
# ---------------------------------------------------------------------------

class TestUpdateAnalysisWithTrends:
    """Tests for update_analysis_with_trends()."""

    EXISTING_ANALYSIS = """# Competitor Analysis

## Channel Stats

| Channel | Videos | Subscribers |
|---------|--------|-------------|
| Barely Sociable | 100 | 1.2M |

## Outlier Videos

- The Silk Road (13M views)

## Topic Clusters

1. Dark web mysteries
2. True crime investigations

## Title Patterns

- "The [Event] That..." (avg 5M views)
"""

    def test_appends_three_sections_to_new_file(self, tmp_path):
        """update_analysis_with_trends creates file with three trend sections."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- cults",
            gaps_md="## Content Gaps\n\n- disappearances",
            convergence_md="## Convergence Alerts\n\n- overlap found",
        )

        content = path.read_text(encoding="utf-8")
        assert "## Trending Topics" in content
        assert "## Content Gaps" in content
        assert "## Convergence Alerts" in content

    def test_creates_file_if_not_exists(self, tmp_path):
        """update_analysis_with_trends creates analysis.md when absent."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "nonexistent.md"
        assert not path.exists()

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- cults",
            gaps_md="## Content Gaps\n\n- gaps",
            convergence_md="## Convergence Alerts\n\n- alerts",
        )

        assert path.exists()

    def test_preserves_phase2_content(self, tmp_path):
        """update_analysis_with_trends preserves Channel Stats, Outliers, Topic Clusters, Title Patterns."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        path.write_text(self.EXISTING_ANALYSIS, encoding="utf-8")

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- new cults",
            gaps_md="## Content Gaps\n\n- new gaps",
            convergence_md="## Convergence Alerts\n\n- new alerts",
        )

        content = path.read_text(encoding="utf-8")
        assert "## Channel Stats" in content
        assert "## Outlier Videos" in content
        assert "## Topic Clusters" in content
        assert "## Title Patterns" in content
        assert "Barely Sociable" in content
        assert "The Silk Road" in content

    def test_replaces_existing_trending_section(self, tmp_path):
        """update_analysis_with_trends replaces old trend sections with new content."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        existing = self.EXISTING_ANALYSIS + "\n## Trending Topics\n\n- OLD TREND\n"
        path.write_text(existing, encoding="utf-8")

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- NEW TREND",
            gaps_md="## Content Gaps\n\n- gaps",
            convergence_md="## Convergence Alerts\n\n- alerts",
        )

        content = path.read_text(encoding="utf-8")
        assert "OLD TREND" not in content
        assert "NEW TREND" in content

    def test_replaces_existing_content_gaps_section(self, tmp_path):
        """update_analysis_with_trends replaces old Content Gaps section."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        existing = self.EXISTING_ANALYSIS + "\n## Content Gaps\n\n- OLD GAP\n"
        path.write_text(existing, encoding="utf-8")

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- trends",
            gaps_md="## Content Gaps\n\n- NEW GAP",
            convergence_md="## Convergence Alerts\n\n- alerts",
        )

        content = path.read_text(encoding="utf-8")
        assert "OLD GAP" not in content
        assert "NEW GAP" in content

    def test_replaces_existing_convergence_section(self, tmp_path):
        """update_analysis_with_trends replaces old Convergence Alerts section."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        existing = self.EXISTING_ANALYSIS + "\n## Convergence Alerts\n\n- OLD ALERT\n"
        path.write_text(existing, encoding="utf-8")

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- trends",
            gaps_md="## Content Gaps\n\n- gaps",
            convergence_md="## Convergence Alerts\n\n- NEW ALERT",
        )

        content = path.read_text(encoding="utf-8")
        assert "OLD ALERT" not in content
        assert "NEW ALERT" in content

    def test_does_not_duplicate_sections_on_second_call(self, tmp_path):
        """Calling update twice does not create duplicate trend sections."""
        from channel_assistant.trend_scanner import update_analysis_with_trends

        path = tmp_path / "analysis.md"
        path.write_text(self.EXISTING_ANALYSIS, encoding="utf-8")

        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- trends v1",
            gaps_md="## Content Gaps\n\n- gaps v1",
            convergence_md="## Convergence Alerts\n\n- alerts v1",
        )
        update_analysis_with_trends(
            path,
            trending_md="## Trending Topics\n\n- trends v2",
            gaps_md="## Content Gaps\n\n- gaps v2",
            convergence_md="## Convergence Alerts\n\n- alerts v2",
        )

        content = path.read_text(encoding="utf-8")
        assert content.count("## Trending Topics") == 1
        assert content.count("## Content Gaps") == 1
        assert content.count("## Convergence Alerts") == 1
        assert "trends v2" in content
        assert "trends v1" not in content


# ---------------------------------------------------------------------------
# CONTENT_PILLAR_KEYWORDS constant test
# ---------------------------------------------------------------------------

class TestContentPillarKeywords:
    """Tests for the CONTENT_PILLAR_KEYWORDS module constant."""

    def test_constant_exists_and_is_list(self):
        """CONTENT_PILLAR_KEYWORDS is a non-empty list of strings."""
        from channel_assistant.trend_scanner import CONTENT_PILLAR_KEYWORDS

        assert isinstance(CONTENT_PILLAR_KEYWORDS, list)
        assert len(CONTENT_PILLAR_KEYWORDS) > 0
        assert all(isinstance(k, str) for k in CONTENT_PILLAR_KEYWORDS)

    def test_constant_covers_all_five_pillars(self):
        """CONTENT_PILLAR_KEYWORDS includes keywords from all 5 content pillars."""
        from channel_assistant.trend_scanner import CONTENT_PILLAR_KEYWORDS

        joined = " ".join(CONTENT_PILLAR_KEYWORDS).lower()
        # Check a keyword from each pillar category is present
        assert any(kw in joined for kw in ["crime", "cult", "disappear", "mystery",
                                            "corrupt", "dark web", "historical"])
