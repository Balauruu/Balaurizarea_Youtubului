import json
from pathlib import Path


def test_load_channels_empty(tmp_path):
    from asset_manager.download import load_channels

    channels_path = tmp_path / "channels.json"
    channels_path.write_text('{"channels": []}', encoding="utf-8")
    result = load_channels(channels_path)
    assert result == []


def test_load_channels_parses_entries(tmp_path):
    from asset_manager.download import load_channels

    data = {
        "channels": [
            {
                "slug": "test-channel",
                "youtube_url": "https://www.youtube.com/@TestChannel",
                "license": "PD",
                "max_quality": "720p",
                "indexed": False,
                "video_count": 0,
                "last_indexed": None,
            }
        ]
    }
    channels_path = tmp_path / "channels.json"
    channels_path.write_text(json.dumps(data), encoding="utf-8")
    result = load_channels(channels_path)
    assert len(result) == 1
    assert result[0]["slug"] == "test-channel"


def test_save_channels_roundtrip(tmp_path):
    from asset_manager.download import load_channels, save_channels

    channels = [{"slug": "test", "youtube_url": "https://example.com", "license": "PD",
                 "max_quality": "720p", "indexed": False, "video_count": 0, "last_indexed": None}]
    channels_path = tmp_path / "channels.json"
    save_channels(channels_path, channels)
    loaded = load_channels(channels_path)
    assert loaded == channels


def test_list_channel_videos_parses_yt_dlp_output(monkeypatch):
    """Verify that list_channel_videos correctly parses yt-dlp tab-separated output."""
    import subprocess
    from asset_manager.download import list_channel_videos

    fake_output = "abc123\tTest Video 1\t120\nxyz789\tTest Video 2\t300\n"

    def mock_run(*args, **kwargs):
        result = subprocess.CompletedProcess(args=args[0], returncode=0, stdout=fake_output, stderr="")
        return result

    monkeypatch.setattr(subprocess, "run", mock_run)
    videos = list_channel_videos("https://www.youtube.com/@FakeChannel")
    assert len(videos) == 2
    assert videos[0]["id"] == "abc123"
    assert videos[0]["title"] == "Test Video 1"
    assert videos[1]["id"] == "xyz789"


def test_download_video_builds_correct_format_spec(monkeypatch):
    """Verify download_video passes correct quality format to yt-dlp."""
    import subprocess
    from asset_manager.download import download_video

    captured_cmd = []

    def mock_run(cmd, **kwargs):
        captured_cmd.extend(cmd)
        # Create a fake output file
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)
    download_video("abc123", tmp_path := Path("/tmp/test_dl"), max_quality="720p")
    assert "bestvideo[height<=720]+bestaudio/best[height<=720]" in captured_cmd
