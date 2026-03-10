"""Stage 2: Perceptual hash deduplication using imagededup."""

import os
import numpy as np
from PIL import Image
from imagededup.methods import PHash
from visual_style_extractor.scene_detect import SceneInfo


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def _is_near_black(image_path: str, threshold: int = 25, black_ratio: float = 0.92) -> bool:
    """Check if a frame is nearly all black.

    Args:
        image_path: Path to the image file.
        threshold: Pixel brightness below which a pixel counts as "black".
        black_ratio: Fraction of pixels that must be black to classify the frame.
    """
    try:
        img = Image.open(image_path).convert("L")  # grayscale
        arr = np.array(img)
        return float((arr < threshold).mean()) >= black_ratio
    except (FileNotFoundError, OSError):
        return False


def deduplicate_frames(
    scenes: list[SceneInfo],
    frames_dir: str,
    max_distance_threshold: int = 6,
) -> list[dict]:
    """Deduplicate keyframes using perceptual hashing.

    Groups visually similar frames and keeps one representative per group
    (the one closest to the group's median timestamp).

    Near-black frames (transitions, fades) are pre-grouped before hashing
    to prevent duplicates that PHash misses due to noise variation.

    Args:
        scenes: List of SceneInfo from scene detection.
        frames_dir: Directory containing extracted keyframe images.
        max_distance_threshold: Hamming distance threshold for grouping.

    Returns:
        List of dicts with frame_id, frame_path, timestamp, scene_duration, represents_count.
    """
    if not scenes:
        return []

    # Build filename -> SceneInfo lookup
    scene_by_filename = {}
    for s in scenes:
        fname = os.path.basename(s.keyframe_path)
        scene_by_filename[fname] = s

    # Pre-group near-black frames
    black_filenames = set()
    normal_filenames = []
    for fname in scene_by_filename:
        fpath = os.path.join(frames_dir, fname)
        if _is_near_black(fpath):
            black_filenames.add(fname)
        else:
            normal_filenames.append(fname)

    if black_filenames:
        print(f"Near-black frames detected: {len(black_filenames)} (will be grouped as one)")

    # Run PHash on non-black frames only
    phasher = PHash()
    encodings = phasher.encode_images(image_dir=frames_dir)

    # Remove black frames from encodings so they don't interfere
    filtered_encodings = {k: v for k, v in encodings.items() if k not in black_filenames}

    duplicates = phasher.find_duplicates(
        encoding_map=filtered_encodings,
        max_distance_threshold=max_distance_threshold,
    )

    # Build groups from PHash results
    assigned = set()
    groups = []

    for fname, dupes in duplicates.items():
        if fname in assigned:
            continue
        group = [fname] + [d for d in dupes if d not in assigned]
        for f in group:
            assigned.add(f)
        groups.append(group)

    # Add black frames as a single group (if any)
    if black_filenames:
        groups.append(list(black_filenames))

    # Select representative per group (closest to median timestamp)
    result = []
    frame_id = 1

    for group in groups:
        group_scenes = [scene_by_filename[f] for f in group if f in scene_by_filename]
        if not group_scenes:
            continue

        timestamps = [s.start_time for s in group_scenes]
        median_ts = sorted(timestamps)[len(timestamps) // 2]

        # Pick the scene closest to median
        representative = min(group_scenes, key=lambda s: abs(s.start_time - median_ts))

        result.append({
            "frame_id": frame_id,
            "frame_path": representative.keyframe_path,
            "timestamp": _format_timestamp(representative.start_time),
            "scene_duration": representative.duration,
            "represents_count": len(group_scenes),
        })
        frame_id += 1

    # Sort by timestamp
    result.sort(key=lambda r: r["frame_id"])
    # Re-number sequentially
    for i, r in enumerate(result):
        r["frame_id"] = i + 1

    print(f"Deduplication: {len(scenes)} frames -> {len(result)} unique ({len(scenes) - len(result)} removed)")

    if len(result) < len(scenes) * 0.1:
        print("WARNING: Dedup removed >90% of frames. Video may be too visually uniform for meaningful analysis.")

    return result
