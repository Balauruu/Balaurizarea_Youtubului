"""Main pipeline orchestrator — chains all stages sequentially.

This module is called by the Claude Code skill. Stages 0-4 are automated Python.
Stage 5 (LLM analysis) requires Claude Code subagents — this script prepares
everything needed and outputs instructions for the skill to dispatch subagents.
Stage 6 (synthesis) is called after subagent results are collected.
"""

import os
import json
from dataclasses import dataclass, field

from visual_style_extractor.acquire import validate_local_input, download_from_youtube
from visual_style_extractor.scene_detect import detect_scenes
from visual_style_extractor.dedup import deduplicate_frames
from visual_style_extractor.align import parse_transcript, align_frames, build_manifest
from visual_style_extractor.contact_sheets import generate_contact_sheets
from visual_style_extractor.synthesize import generate_style_guide


@dataclass
class PipelineConfig:
    source: str  # YouTube URL or local directory path
    output_dir: str | None = None
    adaptive_threshold: float = 3.0
    min_scene_len: int = 15
    dedup_threshold: int = 10

    @property
    def is_youtube(self) -> bool:
        return self.source.startswith("http://") or self.source.startswith("https://")


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
        output_dir = config.output_dir or os.path.join("context", "visual-references", "analysis")
        inputs = download_from_youtube(config.source, output_dir)
    else:
        output_dir = config.source
        inputs = validate_local_input(config.source)

    video_path = inputs["video_path"]
    transcript_path = inputs["transcript_path"]

    print(f"\n{'='*60}")
    print(f"Video: {video_path}")
    print(f"Transcript: {transcript_path}")
    print(f"Output dir: {output_dir}")
    print(f"{'='*60}\n")

    # Stage 1: Scene Detection
    scenes = detect_scenes(
        video_path, output_dir,
        adaptive_threshold=config.adaptive_threshold,
        min_scene_len=config.min_scene_len,
    )

    # Stage 2: Deduplication
    frames_dir = os.path.join(output_dir, "frames")
    unique_frames = deduplicate_frames(scenes, frames_dir, config.dedup_threshold)

    # Stage 3: Alignment
    segments = parse_transcript(transcript_path)
    aligned_frames = align_frames(unique_frames, segments)

    # Get video duration from last scene
    video_duration = scenes[-1].end_time if scenes else 0.0

    manifest_path = os.path.join(output_dir, "frames_manifest.json")
    build_manifest(aligned_frames, video_duration, len(scenes), manifest_path)

    # Stage 4: Contact Sheets
    contact_sheets_dir = os.path.join(output_dir, "contact_sheets")
    contact_sheet_paths = generate_contact_sheets(aligned_frames, contact_sheets_dir)

    # Locate prompt template
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "analysis_prompt.txt"
    )

    return {
        "output_dir": output_dir,
        "manifest_path": manifest_path,
        "contact_sheet_paths": contact_sheet_paths,
        "prompt_path": prompt_path,
        "video_title": os.path.splitext(os.path.basename(video_path))[0],
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
    """Run synthesis stage after subagent analysis is complete.

    Args:
        manifest_path: Path to frames_manifest.json.
        video_title: Title of the source video.
        video_source: URL or path of the source.
        output_dir: Where to write VISUAL_STYLE_GUIDE.md.
        analysis_results: Combined JSON from all subagent outputs (inline list).
        analysis_results_path: Path to a JSON file containing analysis results
            (alternative to passing analysis_results directly).

    Returns:
        Path to the generated VISUAL_STYLE_GUIDE.md.
    """
    if analysis_results is None and analysis_results_path is not None:
        with open(analysis_results_path) as f:
            analysis_results = json.load(f)
    elif analysis_results is None:
        raise ValueError("Must provide either analysis_results or analysis_results_path")

    with open(manifest_path) as f:
        manifest = json.load(f)

    output_path = os.path.join(output_dir, "VISUAL_STYLE_GUIDE.md")
    return generate_style_guide(analysis_results, manifest, video_title, video_source, output_path)
