"""Main pipeline orchestrator — chains all stages sequentially.

This module is called by the Claude Code skill. Stages 0-4 are automated Python.
Stage 5 (LLM analysis) requires Claude Code subagents — this script prepares
everything needed and outputs instructions for the skill to dispatch subagents.
Stage 6 (synthesis) prepares data for an LLM synthesis subagent.
"""

import os
import re
import json
import shutil
from dataclasses import dataclass

from visual_style_extractor.acquire import validate_local_input, download_from_youtube
from visual_style_extractor.scene_detect import detect_scenes
from visual_style_extractor.dedup import deduplicate_frames
from visual_style_extractor.align import parse_transcript, align_frames, build_manifest
from visual_style_extractor.contact_sheets import generate_contact_sheets
from visual_style_extractor.synthesize import prepare_synthesis_input


@dataclass
class PipelineConfig:
    source: str  # YouTube URL or local directory path
    output_dir: str | None = None
    adaptive_threshold: float = 3.0
    min_scene_len: int = 15
    dedup_threshold: int = 8

    @property
    def is_youtube(self) -> bool:
        return self.source.startswith("http://") or self.source.startswith("https://")


def _sanitize_dirname(name: str) -> str:
    """Sanitize a string for use as a directory name."""
    # Remove characters invalid on Windows
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Strip trailing dots (Windows forbids directory names ending with '.')
    name = name.rstrip('.')
    # Truncate to reasonable length
    return name[:120].rstrip('.') if name else "untitled"


def slice_manifest(
    manifest_path: str,
    start_idx: int,
    end_idx: int,
    output_path: str,
) -> str:
    """Extract a slice of frames from the manifest and write to a new file.

    Args:
        manifest_path: Path to the full frames_manifest.json.
        start_idx: Start frame index (inclusive).
        end_idx: End frame index (exclusive).
        output_path: Where to write the sliced manifest.

    Returns:
        The output_path.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    sliced = {
        "video_duration": manifest["video_duration"],
        "total_scenes_detected": manifest["total_scenes_detected"],
        "unique_frames_after_dedup": manifest["unique_frames_after_dedup"],
        "frames": manifest["frames"][start_idx:end_idx],
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sliced, f, indent=2)

    return output_path


def merge_analysis_batches(
    batch_paths: list[str],
    output_path: str,
    min_confidence: int = 3,
) -> tuple[int, int]:
    """Merge per-subagent batch result files into a single JSON file.

    Args:
        batch_paths: List of paths to JSON files, each containing a JSON array.
        output_path: Where to write the merged results.
        min_confidence: Minimum confidence score to keep a frame entry.

    Returns:
        Tuple of (kept_count, removed_count).
    """
    all_frames = []
    for path in sorted(batch_paths):
        with open(path) as f:
            batch = json.load(f)
        if isinstance(batch, list):
            all_frames.extend(batch)

    kept = [f for f in all_frames if f.get("confidence", 0) >= min_confidence]
    removed_count = len(all_frames) - len(kept)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2)

    return len(kept), removed_count


def run_stages_0_to_4(config: PipelineConfig) -> dict:
    """Run deterministic pipeline stages (0-4).

    Returns a dict with:
        - output_dir: working directory
        - manifest_path: path to frames_manifest.json
        - contact_sheet_paths: list of contact sheet image paths
        - prompt_path: path to analysis prompt template
        - video_title: title of the source video
        - video_source: URL or path of the source
    """
    # Stage 0: Acquisition
    if config.is_youtube:
        # Download to a temp location first to learn the video title
        base_dir = config.output_dir or os.path.join("context", "visual-references")
        temp_dir = os.path.join(base_dir, "_download_temp")
        inputs = download_from_youtube(config.source, temp_dir)
        # Create output dir named after video title
        video_title = os.path.splitext(os.path.basename(inputs["video_path"]))[0]
        output_dir = os.path.join(base_dir, _sanitize_dirname(video_title))
        if output_dir != temp_dir:
            os.makedirs(output_dir, exist_ok=True)
            # Move downloaded files to named directory
            for fname in os.listdir(temp_dir):
                src = os.path.join(temp_dir, fname)
                dst = os.path.join(output_dir, fname)
                shutil.move(src, dst)
            os.rmdir(temp_dir)
            # Update paths after move
            inputs["video_path"] = os.path.join(
                output_dir, os.path.basename(inputs["video_path"])
            )
            inputs["transcript_path"] = os.path.join(
                output_dir, os.path.basename(inputs["transcript_path"])
            )
    else:
        output_dir = config.source
        inputs = validate_local_input(config.source)

    video_path = inputs["video_path"]
    transcript_path = inputs["transcript_path"]

    video_title = os.path.splitext(os.path.basename(video_path))[0]

    print(f"\n[Stage 0/6] Acquiring video...")
    print(f"  Done: {video_title}")
    print(f"  Output dir: {output_dir}")

    # Stage 1: Scene Detection
    print(f"\n[Stage 1/6] Detecting scenes...")
    scenes = detect_scenes(
        video_path, output_dir,
        adaptive_threshold=config.adaptive_threshold,
        min_scene_len=config.min_scene_len,
    )
    print(f"  Done: {len(scenes)} scenes detected (threshold: {config.adaptive_threshold})")

    # Stage 2: Deduplication
    print(f"\n[Stage 2/6] Deduplicating frames...")
    frames_dir = os.path.join(output_dir, "frames")
    report_path = os.path.join(output_dir, "dedup_report.json")
    unique_frames = deduplicate_frames(
        scenes, frames_dir, config.dedup_threshold, report_path=report_path,
    )

    # Stage 3: Alignment
    print(f"\n[Stage 3/6] Aligning transcript...")
    segments = parse_transcript(transcript_path)
    aligned_frames = align_frames(unique_frames, segments)
    print(f"  Done: {len(segments)} subtitle cues aligned")

    # Get video duration from last scene
    video_duration = scenes[-1].end_time if scenes else 0.0

    manifest_path = os.path.join(output_dir, "frames_manifest.json")
    build_manifest(aligned_frames, video_duration, len(scenes), manifest_path)

    # Stage 4: Contact Sheets
    print(f"\n[Stage 4/6] Generating contact sheets...")
    contact_sheets_dir = os.path.join(output_dir, "contact_sheets")
    contact_sheet_paths = generate_contact_sheets(aligned_frames, contact_sheets_dir)
    print(f"  Done: {len(contact_sheet_paths)} contact sheets ({len(aligned_frames)} frames)")

    # Locate prompt template
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "analysis_prompt.txt"
    )

    return {
        "output_dir": output_dir,
        "manifest_path": manifest_path,
        "contact_sheet_paths": contact_sheet_paths,
        "prompt_path": prompt_path,
        "video_title": video_title,
        "video_source": config.source,
    }


def run_stage_6(
    manifest_path: str,
    video_title: str,
    video_source: str,
    output_dir: str,
    analysis_results: list[dict] | None = None,
    analysis_results_path: str | None = None,
) -> str:
    """Prepare synthesis input for the LLM subagent.

    Args:
        manifest_path: Path to frames_manifest.json.
        video_title: Title of the source video.
        video_source: URL or path of the source.
        output_dir: Output directory (used to locate scratch files).
        analysis_results: Combined JSON from all subagent outputs (inline list).
        analysis_results_path: Path to a JSON file containing analysis results
            (alternative to passing analysis_results directly).

    Returns:
        Path to the synthesis input file (.claude/scratch/synthesis_input.txt).
    """
    if analysis_results is None and analysis_results_path is not None:
        with open(analysis_results_path) as f:
            analysis_results = json.load(f)
    elif analysis_results is None:
        raise ValueError("Must provide either analysis_results or analysis_results_path")

    with open(manifest_path) as f:
        manifest = json.load(f)

    synthesis_text = prepare_synthesis_input(
        analysis_results, manifest, video_title, video_source,
    )

    scratch_dir = os.path.join(".claude", "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    synthesis_input_path = os.path.join(scratch_dir, "synthesis_input.txt")
    with open(synthesis_input_path, "w", encoding="utf-8") as f:
        f.write(synthesis_text)

    print(f"\n[Stage 6/6] Synthesis input prepared")
    print(f"  Written to: {synthesis_input_path}")

    return synthesis_input_path
