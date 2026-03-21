from pathlib import Path


def test_detect_scenes_returns_list_of_tuples(tmp_path):
    """Scene detection should return (start_sec, end_sec) tuples."""
    import subprocess
    from asset_manager.scene_detect import detect_scenes

    # Create a 4-second synthetic video with a hard cut at 2s (black -> white)
    video_path = tmp_path / "test_video.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=2",
        "-f", "lavfi", "-i", "color=c=white:s=320x240:d=2",
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
        "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(video_path),
    ], capture_output=True, check=True)

    scenes = detect_scenes(video_path, threshold=27.0, min_scene_len=5)
    assert isinstance(scenes, list)
    assert len(scenes) >= 1
    for start, end in scenes:
        assert isinstance(start, float)
        assert isinstance(end, float)
        assert end > start


def test_extract_middle_frame_creates_image(tmp_path):
    """Middle frame extraction should produce a .jpg file."""
    import subprocess
    from asset_manager.scene_detect import extract_middle_frame

    # Create a 2-second synthetic video
    video_path = tmp_path / "test_video.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=red:s=320x240:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(video_path),
    ], capture_output=True, check=True)

    frame_path = tmp_path / "frame.jpg"
    result = extract_middle_frame(video_path, 1.0, frame_path)
    assert result == frame_path
    assert frame_path.exists()
    assert frame_path.stat().st_size > 0


def test_scene_list_to_frame_timestamps():
    """Convert scene list to middle-frame timestamps."""
    from asset_manager.scene_detect import scene_midpoints

    scenes = [(0.0, 10.0), (10.0, 25.0), (25.0, 30.0)]
    midpoints = scene_midpoints(scenes)
    assert midpoints == [5.0, 17.5, 27.5]
