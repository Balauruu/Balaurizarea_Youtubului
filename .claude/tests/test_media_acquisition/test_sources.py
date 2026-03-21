"""Tests for media acquisition source adapters.

All HTTP is mocked — no real API calls. Tests verify:
- Common interface (SearchResult/DownloadResult dataclasses)
- Each source's search() and download() functions
- Rate limiter behavior
- Missing API key handling
- Source registry
"""
import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from media_acquisition.sources import (
    SearchResult, DownloadResult, SOURCE_REGISTRY, get_source,
    rate_limit, reset_rate_limiter, RATE_LIMITS,
    _streaming_download, DEFAULT_MAX_DOWNLOAD_BYTES,
)


# === Common Interface Tests ===

class TestDataclasses:
    def test_search_result_fields(self):
        r = SearchResult(
            url="https://example.com/img.jpg",
            title="Test Image",
            description="A test",
            source="test_source",
            license="CC0",
            media_type="image",
            thumbnail_url="https://example.com/thumb.jpg",
        )
        assert r.url == "https://example.com/img.jpg"
        assert r.source == "test_source"
        assert r.media_type == "image"

    def test_search_result_default_thumbnail(self):
        r = SearchResult(url="u", title="t", description="d",
                         source="s", license="l", media_type="image")
        assert r.thumbnail_url == ""

    def test_download_result_success(self):
        r = DownloadResult(success=True, filepath="/tmp/x.jpg",
                           filename="x.jpg", size_bytes=1024)
        assert r.success is True
        assert r.error == ""

    def test_download_result_failure(self):
        r = DownloadResult(success=False, error="HTTP 404")
        assert r.success is False
        assert r.filepath == ""


class TestSourceRegistry:
    def test_registry_has_all_sources(self):
        expected = {"archive_org", "wikimedia_commons", "pexels", "pixabay",
                    "smithsonian", "youtube_cc", "direct_url"}
        assert set(SOURCE_REGISTRY.keys()) == expected

    def test_get_source_valid(self):
        mod = get_source("direct_url")
        assert hasattr(mod, "search")
        assert hasattr(mod, "download")

    def test_get_source_invalid(self):
        with pytest.raises(KeyError, match="Unknown source"):
            get_source("nonexistent_source")

    def test_all_sources_importable(self):
        for name in SOURCE_REGISTRY:
            mod = get_source(name)
            assert callable(getattr(mod, "search", None)), f"{name} missing search()"
            assert callable(getattr(mod, "download", None)), f"{name} missing download()"


class TestRateLimiter:
    def setup_method(self):
        reset_rate_limiter()

    def test_first_call_no_delay(self):
        start = time.time()
        rate_limit("direct_url")  # 0.2s delay
        elapsed = time.time() - start
        # First call should be near-instant (no prior request)
        assert elapsed < 0.3

    def test_second_call_respects_delay(self):
        rate_limit("direct_url")  # 0.2s delay
        start = time.time()
        rate_limit("direct_url")
        elapsed = time.time() - start
        assert elapsed >= 0.15  # Allow small timing variance

    def test_different_sources_independent(self):
        rate_limit("direct_url")
        start = time.time()
        rate_limit("wikimedia_commons")  # Different source — no wait
        elapsed = time.time() - start
        assert elapsed < 0.3

    def teardown_method(self):
        reset_rate_limiter()


# === Streaming Download Tests ===

class TestStreamingDownload:
    def test_successful_download(self, tmp_path):
        reset_rate_limiter()
        content = b"fake image data here"
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.iter_content.return_value = [content]
        mock_resp.raise_for_status.return_value = None

        with patch("media_acquisition.sources.requests.get", return_value=mock_resp):
            result = _streaming_download(
                "https://example.com/photo.jpg",
                tmp_path, None, "test_source"
            )
        assert result.success is True
        assert result.filename == "photo.jpg"
        assert result.size_bytes == len(content)
        assert Path(result.filepath).exists()

    def test_content_type_rejection(self, tmp_path):
        reset_rate_limiter()
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.raise_for_status.return_value = None

        with patch("media_acquisition.sources.requests.get", return_value=mock_resp):
            result = _streaming_download(
                "https://example.com/page.html",
                tmp_path, None, "test_source",
                allowed_content_types={"image/jpeg", "image/png"},
            )
        assert result.success is False
        assert "Rejected Content-Type" in result.error

    def test_size_limit_exceeded(self, tmp_path):
        reset_rate_limiter()
        # Simulate large file via streaming
        big_chunk = b"x" * 1024
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.iter_content.return_value = [big_chunk] * 100  # 100KB
        mock_resp.raise_for_status.return_value = None

        with patch("media_acquisition.sources.requests.get", return_value=mock_resp):
            result = _streaming_download(
                "https://example.com/huge.jpg",
                tmp_path, None, "test_source",
                max_bytes=50 * 1024,  # 50KB limit
            )
        assert result.success is False
        assert "limit" in result.error.lower()

    def test_http_error(self, tmp_path):
        reset_rate_limiter()
        import requests as req_lib
        with patch("media_acquisition.sources.requests.get",
                    side_effect=req_lib.ConnectionError("connection refused")):
            result = _streaming_download(
                "https://example.com/fail.jpg",
                tmp_path, None, "test_source"
            )
        assert result.success is False
        assert "HTTP error" in result.error


# === Archive.org Tests ===

class TestArchiveOrg:
    def setup_method(self):
        reset_rate_limiter()

    @patch("media_acquisition.sources.archive_org.internetarchive")
    def test_search(self, mock_ia):
        mock_ia.search_items.return_value = [{"identifier": "test-item-001"}]
        mock_item = MagicMock()
        mock_item.metadata = {
            "title": "Test Historical Photo",
            "description": "A historical photograph",
            "licenseurl": "https://creativecommons.org/publicdomain/zero/1.0/",
        }
        mock_item.files = [
            {"name": "photo.jpg", "format": "JPEG", "size": "50000"},
        ]
        mock_ia.get_item.return_value = mock_item

        from media_acquisition.sources import archive_org
        results = archive_org.search("historical photo", "image", 5)
        assert len(results) == 1
        assert results[0].source == "archive_org"
        assert results[0].media_type == "image"
        assert "photo.jpg" in results[0].url

    @patch("media_acquisition.sources.requests.get")
    def test_download(self, mock_get, tmp_path):
        content = b"fake jpeg data"
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.iter_content.return_value = [content]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import archive_org
        result = archive_org.download(
            "https://archive.org/download/test/photo.jpg", tmp_path
        )
        assert result.success is True
        assert result.filename == "photo.jpg"


# === Wikimedia Tests ===

class TestWikimedia:
    def setup_method(self):
        reset_rate_limiter()

    @patch("media_acquisition.sources.wikimedia.requests.get")
    def test_search(self, mock_get):
        # First call: search
        search_resp = MagicMock()
        search_resp.json.return_value = {
            "query": {"search": [{"title": "File:Test.jpg"}]}
        }
        search_resp.raise_for_status.return_value = None

        # Second call: imageinfo
        info_resp = MagicMock()
        info_resp.json.return_value = {
            "query": {"pages": {"12345": {
                "title": "File:Test.jpg",
                "imageinfo": [{
                    "url": "https://upload.wikimedia.org/test.jpg",
                    "size": 50000,
                    "mime": "image/jpeg",
                    "extmetadata": {
                        "LicenseShortName": {"value": "CC BY-SA 4.0"},
                        "ImageDescription": {"value": "A test image"},
                    },
                }],
            }}}
        }
        info_resp.raise_for_status.return_value = None

        mock_get.side_effect = [search_resp, info_resp]

        from media_acquisition.sources import wikimedia
        results = wikimedia.search("test query", "image", 5)
        assert len(results) == 1
        assert results[0].source == "wikimedia_commons"
        assert results[0].license == "CC BY-SA 4.0"

    @patch("media_acquisition.sources.requests.get")
    def test_download(self, mock_get, tmp_path):
        content = b"wiki image bytes"
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/png"}
        mock_resp.iter_content.return_value = [content]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import wikimedia
        result = wikimedia.download(
            "https://upload.wikimedia.org/test.png", tmp_path
        )
        assert result.success is True


# === Pexels Tests ===

class TestPexels:
    def setup_method(self):
        reset_rate_limiter()

    @patch.dict(os.environ, {"PEXELS_API_KEY": "test-key-123"})
    @patch("media_acquisition.sources.pexels.requests.get")
    def test_search_images(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "photos": [{
                "alt": "Dark building",
                "photographer": "Test User",
                "src": {
                    "original": "https://images.pexels.com/photos/1/original.jpg",
                    "medium": "https://images.pexels.com/photos/1/medium.jpg",
                },
            }]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import pexels
        results = pexels.search("dark building", "image", 5)
        assert len(results) == 1
        assert results[0].source == "pexels"
        assert results[0].license == "Pexels License (free)"

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            os.environ.pop("PEXELS_API_KEY", None)
            from media_acquisition.sources import pexels
            with pytest.raises(ValueError, match="PEXELS_API_KEY"):
                pexels.search("test", "image")

    @patch.dict(os.environ, {"PEXELS_API_KEY": "test-key-123"})
    @patch("media_acquisition.sources.requests.get")
    def test_download(self, mock_get, tmp_path):
        content = b"pexels image bytes"
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.iter_content.return_value = [content]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import pexels
        result = pexels.download(
            "https://images.pexels.com/photos/1/original.jpg", tmp_path
        )
        assert result.success is True


# === Pixabay Tests ===

class TestPixabay:
    def setup_method(self):
        reset_rate_limiter()

    @patch.dict(os.environ, {"PIXABAY_API_KEY": "test-key-456"})
    @patch("media_acquisition.sources.pixabay.requests.get")
    def test_search_images(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "hits": [{
                "largeImageURL": "https://pixabay.com/get/large.jpg",
                "tags": "church, dark, gothic",
                "user": "TestPhotographer",
                "previewURL": "https://pixabay.com/get/preview.jpg",
            }]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import pixabay
        results = pixabay.search("gothic church", "image", 5)
        assert len(results) == 1
        assert results[0].source == "pixabay"

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PIXABAY_API_KEY", None)
            from media_acquisition.sources import pixabay
            with pytest.raises(ValueError, match="PIXABAY_API_KEY"):
                pixabay.search("test", "image")


# === Smithsonian Tests ===

class TestSmithsonian:
    def setup_method(self):
        reset_rate_limiter()

    @patch.dict(os.environ, {"SMITHSONIAN_API_KEY": "test-key-789"})
    @patch("media_acquisition.sources.smithsonian.requests.get")
    def test_search(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {"rows": [{
                "content": {
                    "descriptiveNonRepeating": {
                        "title": {"content": "Historical Artifact"},
                        "online_media": {"media": [{
                            "content": "https://ids.si.edu/img.jpg",
                            "thumbnail": "https://ids.si.edu/thumb.jpg",
                        }]},
                    },
                    "freetext": {
                        "notes": [{"content": "An important artifact"}],
                    },
                }
            }]}
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import smithsonian
        results = smithsonian.search("historical artifact", "image", 5)
        assert len(results) == 1
        assert results[0].source == "smithsonian"
        assert results[0].license == "Smithsonian Open Access (CC0)"

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SMITHSONIAN_API_KEY", None)
            from media_acquisition.sources import smithsonian
            with pytest.raises(ValueError, match="SMITHSONIAN_API_KEY"):
                smithsonian.search("test", "image")


# === YouTube CC Tests ===

class TestYouTubeCC:
    def setup_method(self):
        reset_rate_limiter()

    @patch("media_acquisition.sources.youtube_cc.subprocess.run")
    def test_search(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps({
                "id": "abc123",
                "title": "Documentary Footage",
                "description": "CC licensed footage",
                "url": "https://www.youtube.com/watch?v=abc123",
                "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
            }) + "\n",
            stderr="",
            returncode=0,
        )

        from media_acquisition.sources import youtube_cc
        results = youtube_cc.search("documentary footage", "video", 5)
        assert len(results) == 1
        assert results[0].source == "youtube_cc"
        assert results[0].license == "Creative Commons"

    @patch("media_acquisition.sources.youtube_cc.subprocess.run")
    def test_download(self, mock_run, tmp_path):
        # Create a fake output file
        fake_file = tmp_path / "test_video.mp4"
        fake_file.write_bytes(b"fake mp4 data")

        mock_run.return_value = MagicMock(
            stdout=str(fake_file) + "\n",
            stderr="",
            returncode=0,
        )

        from media_acquisition.sources import youtube_cc
        result = youtube_cc.download(
            "https://www.youtube.com/watch?v=abc123", tmp_path
        )
        assert result.success is True
        assert result.filename == "test_video.mp4"

    @patch("media_acquisition.sources.youtube_cc.subprocess.run",
           side_effect=FileNotFoundError("yt-dlp not found"))
    def test_ytdlp_not_found(self, mock_run):
        from media_acquisition.sources import youtube_cc
        results = youtube_cc.search("test", "video")
        assert results == []


# === Direct URL Tests ===

class TestDirectURL:
    def setup_method(self):
        reset_rate_limiter()

    def test_search_returns_empty(self):
        from media_acquisition.sources import direct_url
        results = direct_url.search("anything", "image")
        assert results == []

    @patch("media_acquisition.sources.requests.get")
    def test_download_image(self, mock_get, tmp_path):
        content = b"real image bytes"
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.iter_content.return_value = [content]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import direct_url
        result = direct_url.download(
            "https://cdn.example.com/photo.jpg", tmp_path
        )
        assert result.success is True
        assert result.size_bytes == len(content)

    @patch("media_acquisition.sources.requests.get")
    def test_download_rejects_html(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from media_acquisition.sources import direct_url
        result = direct_url.download(
            "https://example.com/not-an-image", tmp_path
        )
        assert result.success is False
        assert "Rejected Content-Type" in result.error
