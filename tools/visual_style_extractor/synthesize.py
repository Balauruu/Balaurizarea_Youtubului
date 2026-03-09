"""Stage 6: Synthesis — aggregate analysis results into VISUAL_STYLE_GUIDE.md."""

import os
import json
from datetime import date
from collections import defaultdict, Counter


def aggregate_by_scene_type(
    analysis_results: list[dict],
    min_confidence: int = 3,
) -> dict[str, list[dict]]:
    """Group analyzed frames by scene_type, filtering low-confidence entries."""
    grouped = defaultdict(list)
    for frame in analysis_results:
        if frame.get("confidence", 0) < min_confidence:
            continue
        grouped[frame["scene_type"]].append(frame)
    return dict(grouped)


def compute_proportions(
    grouped: dict[str, list[dict]],
    manifest: dict,
) -> dict[str, dict]:
    """Compute runtime proportion for each scene type.

    Uses scene_duration * represents_count from manifest.
    Returns dict mapping scene_type -> {proportion, total_seconds, avg_duration, count}.
    """
    video_duration = manifest["video_duration"]
    frame_lookup = {f"F{f['frame_id']:03d}": f for f in manifest["frames"]}

    proportions = {}
    for scene_type, frames in grouped.items():
        total_weighted = 0.0
        durations = []
        for frame in frames:
            fid = frame["frame_id"]
            manifest_frame = frame_lookup.get(fid)
            if manifest_frame:
                weighted = manifest_frame["scene_duration"] * manifest_frame["represents_count"]
                total_weighted += weighted
                durations.append(manifest_frame["scene_duration"])

        proportions[scene_type] = {
            "proportion": total_weighted / video_duration if video_duration > 0 else 0,
            "total_seconds": total_weighted,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "count": len(frames),
        }

    return proportions


def _find_common_elements(frames: list[dict], key: str) -> list[str]:
    """Extract common values for a given key across frames."""
    values = []
    for f in frames:
        val = f.get(key)
        if val and val != "unclear":
            if isinstance(val, list):
                values.extend(val)
            else:
                values.append(val)
    counts = Counter(values)
    return [v for v, _ in counts.most_common()]


def _format_scene_type_name(scene_type: str) -> str:
    """Convert snake_case to Title Case."""
    return scene_type.replace("_", " ").title()


def generate_style_guide(
    analysis_results: list[dict],
    manifest: dict,
    video_title: str,
    video_source: str,
    output_path: str,
) -> str:
    """Generate the final VISUAL_STYLE_GUIDE.md from aggregated analysis."""
    grouped = aggregate_by_scene_type(analysis_results)
    proportions = compute_proportions(grouped, manifest)

    # Sort scene types by proportion (descending)
    sorted_types = sorted(proportions.keys(), key=lambda t: proportions[t]["proportion"], reverse=True)

    lines = []
    lines.append("# Visual Style Guide")
    lines.append(f"> Source: {video_title} ({video_source})")
    lines.append(f"> Duration: {int(manifest['video_duration'] // 60)}:{int(manifest['video_duration'] % 60):02d} "
                 f"| Scenes detected: {manifest['total_scenes_detected']} "
                 f"| Unique frames analyzed: {manifest['unique_frames_after_dedup']}")
    lines.append(f"> Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Scene Taxonomy
    lines.append("## 1. Scene Taxonomy")
    lines.append("")

    for scene_type in sorted_types:
        frames = grouped[scene_type]
        props = proportions[scene_type]
        name = _format_scene_type_name(scene_type)

        lines.append(f"### {name}")
        lines.append(f"- **Proportion:** {props['proportion'] * 100:.1f}% of runtime "
                     f"(~{props['avg_duration']:.1f}s average per occurrence)")
        lines.append(f"- **Frequency:** {props['count']} occurrences")

        backgrounds = _find_common_elements(frames, "background")
        main_elements = _find_common_elements(frames, "main_element")
        overlays = _find_common_elements(frames, "overlays")
        text_elements = _find_common_elements(frames, "text_elements")

        lines.append("- **Appearance:**")
        lines.append(f"  - Background: {', '.join(backgrounds[:3]) if backgrounds else 'N/A'}")
        lines.append(f"  - Main element: {', '.join(main_elements[:3]) if main_elements else 'N/A'}")

        if overlays:
            lines.append(f"- **Overlays/Effects:** {', '.join(overlays)}")
        if text_elements:
            lines.append(f"- **Text elements:** {', '.join(text_elements)}")

        functions = _find_common_elements(frames, "narrative_function")
        if functions:
            lines.append(f"- **Narrative trigger:** {functions[0]}")
            if len(functions) > 1:
                for func in functions[1:3]:
                    lines.append(f"  - Also: {func}")

        content_frames = [f for f in frames if f.get("content_description") and f["content_description"] != "unclear"]
        if content_frames:
            lines.append("- **Content descriptions:**")
            lines.append("  | Narration concept | Footage used | Metaphor |")
            lines.append("  |-------------------|-------------|----------|")
            for cf in content_frames[:5]:
                narr_func = cf.get("narrative_function", "")
                content = cf.get("content_description", "")
                lines.append(f"  | {narr_func} | {content} | — |")

        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 2: Global Aesthetic
    lines.append("## 2. Global Aesthetic")
    lines.append("")

    all_overlays = []
    for frames in grouped.values():
        for f in frames:
            if f.get("overlays"):
                all_overlays.extend(f["overlays"] if isinstance(f["overlays"], list) else [f["overlays"]])
    overlay_counts = Counter(all_overlays)
    persistent = [o for o, c in overlay_counts.most_common() if c >= len(grouped) * 0.5]

    lines.append("### Persistent Overlays")
    if persistent:
        for o in persistent:
            lines.append(f"- {o}")
    else:
        lines.append("- None identified across all scene types")
    lines.append("")

    lines.append("### Color Palette")
    lines.append("| Role | Description | Usage |")
    lines.append("|------|-------------|-------|")
    lines.append("| *(Extracted from analysis — fill manually or re-run with programmatic extraction)* | | |")
    lines.append("")

    lines.append("### Motion Language")
    lines.append("- *(To be derived from video analysis — contact sheets capture stills only)* ")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Section 3: Structural Flow
    lines.append("## 3. Structural Flow")
    lines.append("")
    lines.append("### Pacing")
    lines.append("| Segment | Dominant Asset Types | Avg Scene Duration |")
    lines.append("|---------|---------------------|--------------------|")

    all_frames = sorted(analysis_results, key=lambda f: f.get("timestamp", ""))
    quarter = len(all_frames) // 4 if len(all_frames) >= 4 else 1
    segments = {
        "Opening": all_frames[:quarter],
        "Early-mid": all_frames[quarter:quarter * 2],
        "Late-mid": all_frames[quarter * 2:quarter * 3],
        "Closing": all_frames[quarter * 3:],
    }
    for seg_name, seg_frames in segments.items():
        types_count = Counter(f["scene_type"] for f in seg_frames if f.get("confidence", 0) >= 3)
        top_types = ", ".join(t for t, _ in types_count.most_common(2))
        lines.append(f"| {seg_name} | {top_types or 'N/A'} | — |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 4: Constraints
    lines.append("## 4. Constraints (What NOT to Do)")
    lines.append("- *(Derive from analysis: note any asset types conspicuously absent)*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 5: Quick Reference
    lines.append("## 5. Asset Type Summary (Quick Reference)")
    lines.append("")
    lines.append("| # | Asset Type | Proportion | Avg Duration | Frequency | Narrative Trigger |")
    lines.append("|---|-----------|------------|--------------|-----------|-------------------|")
    for i, scene_type in enumerate(sorted_types, 1):
        props = proportions[scene_type]
        name = _format_scene_type_name(scene_type)
        trigger = _find_common_elements(grouped[scene_type], "narrative_function")
        trigger_text = trigger[0] if trigger else "—"
        lines.append(f"| {i} | {name} | {props['proportion'] * 100:.1f}% | "
                     f"{props['avg_duration']:.1f}s | {props['count']}x | {trigger_text} |")

    lines.append("")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated VISUAL_STYLE_GUIDE.md at {output_path}")
    return output_path
