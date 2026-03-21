from pathlib import Path


def test_extract_clip_builds_correct_command():
    from asset_manager.extract import build_extract_command

    cmd = build_extract_command(
        video_path=Path("channels/ch/v1.mp4"),
        start_sec=10.0,
        end_sec=20.0,
        output_path=Path("output/clip.mp4"),
        padding_sec=1.0,
    )
    assert "ffmpeg" in cmd[0]
    assert "-ss" in cmd
    # Start should be 9.0 (10.0 - 1.0 padding)
    ss_idx = cmd.index("-ss")
    assert cmd[ss_idx + 1] == "9.0"
    # Should use stream copy
    assert "-c" in cmd
    assert "copy" in cmd


def test_extract_clip_clamps_negative_start():
    from asset_manager.extract import build_extract_command

    cmd = build_extract_command(
        video_path=Path("v.mp4"),
        start_sec=0.5,
        end_sec=5.0,
        output_path=Path("out.mp4"),
        padding_sec=2.0,
    )
    ss_idx = cmd.index("-ss")
    assert cmd[ss_idx + 1] == "0.0"  # clamped, not -1.5
