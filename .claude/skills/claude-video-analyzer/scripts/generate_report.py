#!/usr/bin/env python3
"""Generate final markdown report from all analysis data."""

import sys
import os
import json
import argparse
from datetime import datetime


def generate_report(analysis_path, technical_path, probe_path, stills_dir, output_path):
    # Load data
    analysis = {}
    if analysis_path and os.path.exists(analysis_path):
        with open(analysis_path) as f:
            analysis = json.load(f)

    technical = {}
    if technical_path and os.path.exists(technical_path):
        with open(technical_path) as f:
            technical = json.load(f)

    probe = {}
    if probe_path and os.path.exists(probe_path):
        with open(probe_path) as f:
            probe = json.load(f)

    stills = []
    if stills_dir and os.path.exists(stills_dir):
        stills_manifest = os.path.join(stills_dir, "stills_manifest.json")
        if os.path.exists(stills_manifest):
            with open(stills_manifest) as f:
                stills = json.load(f)

    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Header
    filename = probe.get("file", analysis.get("filename", "Unknown"))
    lines.append(f"# Video Analysis Report: {filename}")
    lines.append(f"*Generated: {now}*\n")

    # Overview
    lines.append("## Overview\n")
    if probe:
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Duration | {probe.get('duration_human', 'N/A')} ({probe.get('duration_sec', 'N/A')}s) |")
        lines.append(f"| Resolution | {probe.get('width')}×{probe.get('height')} |")
        lines.append(f"| Codec | {probe.get('codec', 'N/A')} |")
        lines.append(f"| Declared FPS | {probe.get('declared_fps', 'N/A')} |")
        lines.append(f"| File Size | {probe.get('file_size_mb', 'N/A')} MB |")
        lines.append(f"| Bitrate | {probe.get('bitrate_kbps', 'N/A')} kbps |")
        lines.append(f"| Audio | {'Yes - ' + probe.get('audio_codec', '') if probe.get('has_audio') else 'No'} |")
        lines.append("")

    # Technical QA
    if technical:
        lines.append("## Technical QA\n")
        score = technical.get("smoothness_score", 0)
        score_emoji = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
        lines.append(f"**Smoothness Score: {score}/100 {score_emoji}**\n")

        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Frames Analyzed | {technical.get('total_frames_extracted', 'N/A')} |")
        lines.append(f"| Measured FPS | {technical.get('measured_fps', 'N/A')} |")
        lines.append(f"| Avg Frame Interval | {technical.get('avg_frame_interval_ms', 'N/A')} ms |")
        lines.append(f"| Interval Std Dev | {technical.get('frame_interval_std_ms', 'N/A')} ms |")
        lines.append(f"| Duplicate Frames | {technical.get('duplicate_frames', 0)} |")
        lines.append(f"| Stutter Events | {technical.get('stutter_count', 0)} |")
        lines.append("")

        stutters = technical.get("stutter_events", [])
        if stutters:
            lines.append("### Stutter Events\n")
            for s in stutters:
                ts = s.get("timestamp_sec", 0)
                h, m, sec = int(ts//3600), int((ts%3600)//60), ts%60
                ts_human = f"{h:02d}:{m:02d}:{sec:06.3f}"
                lines.append(f"- `{ts_human}` — {s.get('interval_ms')}ms gap (expected {s.get('expected_ms')}ms)")
            lines.append("")

    # Content Timeline
    timeline = analysis.get("timeline", [])
    if timeline:
        lines.append("## Content Timeline\n")
        for entry in timeline:
            ts = entry.get("timestamp_human", entry.get("timestamp_sec", "?"))
            desc = entry.get("description", "")
            scene_change = " **[SCENE CHANGE]**" if entry.get("scene_change") else ""
            lines.append(f"- `{ts}`{scene_change} — {desc}")
        lines.append("")

    # Key Moments
    keypoints = analysis.get("keypoints", [])
    if keypoints:
        lines.append("## Key Moments\n")
        for kp in keypoints:
            ts = kp.get("timestamp_human", "?")
            desc = kp.get("description", "")
            still = kp.get("still_path", "")
            still_ref = f" → `{os.path.basename(still)}`" if still else ""
            lines.append(f"- `{ts}` — {desc}{still_ref}")
        lines.append("")

    # Exported Stills
    if stills:
        lines.append("## Exported Stills\n")
        for still in stills:
            lines.append(f"- `{still.get('filename')}` — `{still.get('timestamp_human')}`")
        lines.append("")

    # Summary
    summary = analysis.get("summary", "")
    if summary:
        lines.append("## Content Summary\n")
        lines.append(summary)
        lines.append("")

    # Issues
    issues = analysis.get("issues", []) + technical.get("issues", [])
    if issues:
        lines.append("## Issues Found\n")
        for issue in issues:
            lines.append(f"- ⚠️ {issue}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by video-analyzer skill*")

    report_text = "\n".join(lines)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_text)

    print(f"Report written to: {output_path}")
    print(f"Lines: {len(lines)}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", default=None)
    parser.add_argument("--technical", default=None)
    parser.add_argument("--probe", default=None)
    parser.add_argument("--stills-dir", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    generate_report(args.analysis, args.technical, args.probe, args.stills_dir, args.output)
