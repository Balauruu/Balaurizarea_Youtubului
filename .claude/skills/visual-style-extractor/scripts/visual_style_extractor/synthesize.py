"""Stage 6: Synthesis — aggregate analysis results into VISUAL_STYLE_GUIDE.md."""

import os
import json
from datetime import date
from collections import defaultdict, Counter


# Maps scene_type -> shotlist visual_type (fallback if subagent doesn't provide one)
DEFAULT_SHOTLIST_MAP = {
    "title_card": "text_overlay",
    "archival_photo": "archival_photo",
    "archival_video": "archival_video",
    "news_clip": "news_clip",
    "map_animation": "map",
    "text_overlay": "text_overlay",
    "quote_card": "text_overlay",
    "b_roll_footage": "archival_video",
    "screen_recording": "archival_video",
    "animated_graphic": "animation",
    "silhouette": "ai_generated",
    "date_card": "animation",
    "chapter_header": "text_overlay",
    "evidence_document": "document_scan",
    "portrait": "archival_photo",
    "location_shot": "archival_video",
}


def aggregate_by_scene_type(
    analysis_results: list[dict],
    min_confidence: int = 3,
) -> dict[str, list[dict]]:
    """Group analyzed frames by scene_type, filtering low-confidence entries."""
    grouped = defaultdict(list)
    for frame in analysis_results:
        if frame.get("confidence", 0) < min_confidence:
            continue
        scene_type = _normalize_scene_type(frame.get("scene_type", "unknown"))
        grouped[scene_type].append(frame)
    return dict(grouped)


def _normalize_scene_type(scene_type: str) -> str:
    """Normalize scene types — merge 'other:' variants that are really transitions."""
    st = scene_type.strip().lower()
    # Merge common black/transition variants
    if any(kw in st for kw in ["black_screen", "transition_black", "black screen", "transition black", "fade_to_black"]):
        return "black_transition"
    # Strip "other:" prefix if it's a recognizable type
    if st.startswith("other:"):
        inner = st[6:].strip().replace(" ", "_")
        if inner in DEFAULT_SHOTLIST_MAP:
            return inner
        return f"other_{inner}"
    return st


def compute_proportions(
    grouped: dict[str, list[dict]],
    manifest: dict,
) -> dict[str, dict]:
    """Compute runtime proportion for each scene type."""
    video_duration = manifest["video_duration"]
    frame_lookup = {f"F{f['frame_id']:03d}": f for f in manifest["frames"]}

    proportions = {}
    for scene_type, frames in grouped.items():
        total_weighted = 0.0
        durations = []
        for frame in frames:
            raw_fid = frame.get("frame_id", "")
            # Normalize: accept "F001", "F23", 1, "1" etc.
            if isinstance(raw_fid, int):
                fid = f"F{raw_fid:03d}"
            else:
                digits = str(raw_fid).lstrip("Ff").lstrip("0") or "0"
                fid = f"F{int(digits):03d}"
            manifest_frame = frame_lookup.get(fid)
            if manifest_frame:
                weighted = manifest_frame["scene_duration"] * manifest_frame["represents_count"]
                total_weighted += weighted
                durations.append(manifest_frame["scene_duration"])

        proportions[scene_type] = {
            "proportion": total_weighted / video_duration if video_duration > 0 else 0,
            "total_seconds": total_weighted,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "count": len(frames),
        }

    return proportions


def _extract_field(frame: dict, key: str) -> str | None:
    """Extract a field from frame, checking both top-level and inside asset_breakdown."""
    val = frame.get(key)
    if val and val != "unclear":
        return val
    breakdown = frame.get("asset_breakdown", {})
    if isinstance(breakdown, dict):
        val = breakdown.get(key)
        if val and val != "unclear":
            return val
    return None


def _collect_field_values(frames: list[dict], key: str) -> list[str]:
    """Collect non-empty values for a key across frames."""
    values = []
    for f in frames:
        val = _extract_field(f, key)
        if val:
            if isinstance(val, list):
                values.extend(v for v in val if v and v != "unclear")
            else:
                values.append(val)
    return values


def _most_common(values: list[str], n: int = 3) -> list[str]:
    """Return up to n most common values."""
    if not values:
        return []
    return [v for v, _ in Counter(values).most_common(n)]


def _format_scene_type_name(scene_type: str) -> str:
    """Convert snake_case to Title Case."""
    name = scene_type.replace("_", " ").title()
    # Clean up "Other Xxx" prefix
    if name.startswith("Other "):
        name = name[6:]
    return name


def _get_shotlist_type(frames: list[dict], scene_type: str) -> str:
    """Determine the shotlist visual_type for a scene type."""
    # Check if subagents provided shotlist_type
    types = [f.get("shotlist_type") for f in frames if f.get("shotlist_type")]
    if types:
        return Counter(types).most_common(1)[0][0]
    # Fall back to default mapping
    base = scene_type.split(":")[0].strip() if ":" in scene_type else scene_type
    return DEFAULT_SHOTLIST_MAP.get(base, "ai_generated")


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

    sorted_types = sorted(
        proportions.keys(),
        key=lambda t: proportions[t]["proportion"],
        reverse=True,
    )

    lines = []

    # Header
    lines.append("# Visual Style Guide")
    lines.append(f"> Source: {video_title} ({video_source})")
    dur_min = int(manifest['video_duration'] // 60)
    dur_sec = int(manifest['video_duration'] % 60)
    lines.append(
        f"> Duration: {dur_min}:{dur_sec:02d} "
        f"| Scenes detected: {manifest['total_scenes_detected']} "
        f"| Unique frames analyzed: {manifest['unique_frames_after_dedup']}"
    )
    lines.append(f"> Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Asset Type Menu
    lines.append("## 1. Asset Type Menu")
    lines.append("")

    for scene_type in sorted_types:
        frames = grouped[scene_type]
        props = proportions[scene_type]
        name = _format_scene_type_name(scene_type)
        shotlist_type = _get_shotlist_type(frames, scene_type)

        lines.append(f"### {name}")
        lines.append(f"- **Shotlist type:** `{shotlist_type}`")
        lines.append(f"- **Proportion:** {props['proportion'] * 100:.1f}% of runtime")
        lines.append(f"- **Frequency:** {props['count']}x")

        dur_str = f"{props['avg_duration']:.1f}s avg"
        if props['count'] > 1 and props['min_duration'] != props['max_duration']:
            dur_str += f" ({props['min_duration']:.0f}\u2013{props['max_duration']:.0f}s range)"
        lines.append(f"- **Duration:** {dur_str}")

        # When to use (generalized narrative trigger)
        triggers = _collect_field_values(frames, "narrative_trigger")
        if not triggers:
            triggers = _collect_field_values(frames, "narrative_function")
        if triggers:
            lines.append(f"- **When to use:** {triggers[0]}")
            if len(triggers) > 1:
                for t in triggers[1:3]:
                    lines.append(f"  - Also: {t}")

        # Visual spec
        backgrounds = _most_common(_collect_field_values(frames, "background"))
        main_elements = _most_common(_collect_field_values(frames, "main_element"))
        overlays_list = _most_common(_collect_field_values(frames, "overlays"))
        colors = _most_common(_collect_field_values(frames, "dominant_colors"))

        spec_parts = []
        if backgrounds:
            spec_parts.append(f"Background: {', '.join(backgrounds)}")
        if main_elements:
            spec_parts.append(f"Main element: {', '.join(main_elements)}")
        if overlays_list and overlays_list != ["none"]:
            spec_parts.append(f"Overlays: {', '.join(overlays_list)}")
        if colors:
            spec_parts.append(f"Colors: {', '.join(colors)}")

        if spec_parts:
            lines.append(f"- **Visual spec:** {'; '.join(spec_parts)}")

        # Example content descriptions with frame IDs
        examples = [
            f for f in frames
            if f.get("content_description") and f["content_description"] != "unclear"
        ]
        if examples:
            lines.append("- **Examples:**")
            lines.append("")
            lines.append("  | Frame | Content |")
            lines.append("  |-------|---------|")
            for ex in examples[:4]:
                fid = ex.get("frame_id", "?")
                content = ex.get("content_description", "")
                lines.append(f"  | {fid} | {content} |")

        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 2: Color Palette & Aesthetic
    lines.append("## 2. Color Palette & Aesthetic")
    lines.append("")

    # Aggregate dominant colors across all frames
    all_colors = []
    for frames in grouped.values():
        for f in frames:
            dc = f.get("dominant_colors")
            if isinstance(dc, list):
                all_colors.extend(dc)
            elif isinstance(dc, str) and dc != "unclear":
                all_colors.append(dc)

    if all_colors:
        color_counts = Counter(all_colors)
        lines.append("### Dominant Colors")
        lines.append("| Color | Occurrences |")
        lines.append("|-------|-------------|")
        for color, count in color_counts.most_common(10):
            lines.append(f"| {color} | {count}x |")
    else:
        lines.append("*(No color data extracted \u2014 re-run with updated analysis prompt)*")

    lines.append("")

    # Persistent overlays
    all_overlays = []
    for frames in grouped.values():
        for f in frames:
            ov = _extract_field(f, "overlays")
            if ov and ov != "none":
                if isinstance(ov, list):
                    all_overlays.extend(ov)
                else:
                    all_overlays.append(ov)

    if all_overlays:
        overlay_counts = Counter(all_overlays)
        lines.append("### Persistent Overlays & Effects")
        for ov, count in overlay_counts.most_common(5):
            lines.append(f"- {ov} ({count}x)")
    else:
        lines.append("### Persistent Overlays & Effects")
        lines.append("- None identified")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 3: Type Mapping
    lines.append("## 3. Type Mapping (Scene Type \u2192 Shotlist)")
    lines.append("")
    lines.append("| # | Extracted Type | Shotlist `visual_type` | Proportion | Frequency |")
    lines.append("|---|---------------|----------------------|------------|-----------|")

    for i, scene_type in enumerate(sorted_types, 1):
        name = _format_scene_type_name(scene_type)
        shotlist_type = _get_shotlist_type(grouped[scene_type], scene_type)
        props = proportions[scene_type]
        lines.append(
            f"| {i} | {name} | `{shotlist_type}` | "
            f"{props['proportion'] * 100:.1f}% | {props['count']}x |"
        )

    lines.append("")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated VISUAL_STYLE_GUIDE.md at {output_path}")
    return output_path
