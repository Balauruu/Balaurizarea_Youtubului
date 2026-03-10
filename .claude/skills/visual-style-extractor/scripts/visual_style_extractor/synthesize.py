"""Stage 6: Synthesis — aggregate analysis results into VISUAL_STYLE_GUIDE.md.

v3: Hierarchical output with 5 asset categories, open-ended subtypes,
and richer per-subtype entries (Description, Use, Implementation, Variants, Stats, Examples).
Transitions are excluded from output.
"""

import os
import json
from datetime import date
from collections import defaultdict, Counter


# 5 asset categories — transitions are filtered out
CATEGORIES = {
    "b_roll": "B-Roll",
    "archival_photos": "Archival Photos",
    "graphics_animation": "Graphics & Animation",
    "text_elements": "Text Elements",
    "evidence_documentation": "Evidence & Documentation",
}

# Category display order
CATEGORY_ORDER = [
    "b_roll",
    "archival_photos",
    "graphics_animation",
    "text_elements",
    "evidence_documentation",
]

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
    "silhouette_animation": "ai_generated",
    "date_card": "animation",
    "chapter_header": "text_overlay",
    "evidence_document": "document_scan",
    "portrait": "archival_photo",
    "location_shot": "archival_photo",
    "keyword_stinger": "text_overlay",
}

# Fallback: if no category field, infer from scene_type
SCENE_TYPE_TO_CATEGORY = {
    "archival_video": "b_roll",
    "b_roll_footage": "b_roll",
    "news_clip": "b_roll",
    "archival_photo": "archival_photos",
    "portrait": "archival_photos",
    "location_shot": "archival_photos",
    "animated_graphic": "graphics_animation",
    "silhouette": "graphics_animation",
    "silhouette_animation": "graphics_animation",
    "map_animation": "graphics_animation",
    "date_card": "graphics_animation",
    "title_card": "text_elements",
    "text_overlay": "text_elements",
    "quote_card": "text_elements",
    "chapter_header": "text_elements",
    "keyword_stinger": "text_elements",
    "evidence_document": "evidence_documentation",
    "screen_recording": "evidence_documentation",
    "document_scan": "evidence_documentation",
}


def _normalize_scene_type(scene_type: str) -> str:
    """Normalize scene types — merge variants, strip prefixes."""
    st = scene_type.strip().lower().replace(" ", "_")
    # Merge common black/transition variants
    if any(kw in st for kw in [
        "black_screen", "transition_black", "black_transition",
        "fade_to_black", "color_hold", "film_leader",
        "solid_color", "transition_color",
    ]):
        return "_transition"
    # Strip "other:" prefix
    if st.startswith("other:"):
        inner = st[6:].strip().replace(" ", "_")
        return inner
    if st.startswith("other_"):
        inner = st[6:]
        return inner
    return st


def _infer_category(frame: dict, scene_type: str) -> str:
    """Get category from frame data, falling back to scene_type mapping."""
    cat = frame.get("category", "").strip().lower().replace(" ", "_")
    if cat in CATEGORIES:
        return cat
    if cat == "transition":
        return "_transition"
    # Fallback: infer from scene_type
    return SCENE_TYPE_TO_CATEGORY.get(scene_type, "graphics_animation")


def aggregate_by_category_and_type(
    analysis_results: list[dict],
    min_confidence: int = 3,
) -> dict[str, dict[str, list[dict]]]:
    """Group frames by category -> scene_type, filtering transitions and low-confidence."""
    grouped = defaultdict(lambda: defaultdict(list))
    for frame in analysis_results:
        if frame.get("confidence", 0) < min_confidence:
            continue
        scene_type = _normalize_scene_type(frame.get("scene_type", "unknown"))
        category = _infer_category(frame, scene_type)
        # Skip transitions entirely
        if category == "_transition" or scene_type == "_transition":
            continue
        grouped[category][scene_type].append(frame)
    return {cat: dict(types) for cat, types in grouped.items()}


def compute_proportions(
    all_frames_by_type: dict[str, list[dict]],
    manifest: dict,
) -> dict[str, dict]:
    """Compute runtime proportion for each scene type."""
    video_duration = manifest["video_duration"]
    frame_lookup = {f"F{f['frame_id']:03d}": f for f in manifest["frames"]}

    proportions = {}
    for scene_type, frames in all_frames_by_type.items():
        total_weighted = 0.0
        durations = []
        for frame in frames:
            raw_fid = frame.get("frame_id", "")
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
    """Extract a field from frame, checking top-level and inside implementation/asset_breakdown."""
    val = frame.get(key)
    if val and val != "unclear":
        return val
    # Check both old (asset_breakdown) and new (implementation) field names
    for container_key in ("implementation", "asset_breakdown"):
        breakdown = frame.get(container_key, {})
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
    if name.startswith("Other "):
        name = name[6:]
    return name


def _get_shotlist_type(frames: list[dict], scene_type: str) -> str:
    """Determine the shotlist visual_type for a scene type."""
    types = [f.get("shotlist_type") for f in frames if f.get("shotlist_type")]
    if types:
        return Counter(types).most_common(1)[0][0]
    base = scene_type.split(":")[0].strip() if ":" in scene_type else scene_type
    return DEFAULT_SHOTLIST_MAP.get(base, "ai_generated")


def _collect_variants(frames: list[dict]) -> list[str]:
    """Collect unique variant names from frames, excluding 'default'."""
    variants = []
    for f in frames:
        v = f.get("variants", f.get("variant", ""))
        if isinstance(v, str) and v.strip().lower() not in ("", "default", "unclear"):
            variants.append(v.strip())
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for v in variants:
        v_lower = v.lower()
        if v_lower not in seen:
            seen.add(v_lower)
            unique.append(v)
    return unique


def _build_implementation_text(frames: list[dict]) -> str:
    """Build implementation description from frame data."""
    backgrounds = _most_common(_collect_field_values(frames, "background"))
    main_elements = _most_common(_collect_field_values(frames, "main_element"))
    overlays_list = _most_common(_collect_field_values(frames, "overlays"))
    text_els = _most_common(_collect_field_values(frames, "text_elements"))
    colors = _most_common(_collect_field_values(frames, "dominant_colors"))

    parts = []
    if backgrounds:
        parts.append(f"Background: {', '.join(backgrounds)}")
    if main_elements:
        parts.append(f"Main element: {', '.join(main_elements)}")
    if overlays_list and overlays_list != ["none"]:
        parts.append(f"Overlays: {', '.join(overlays_list)}")
    if text_els and text_els != ["none"]:
        parts.append(f"Text: {', '.join(text_els)}")
    if colors:
        parts.append(f"Colors: {', '.join(colors)}")

    return "; ".join(parts) if parts else "N/A"


def _build_subtype_entry(
    scene_type: str,
    frames: list[dict],
    props: dict,
) -> list[str]:
    """Build markdown lines for a single asset subtype entry."""
    lines = []
    name = _format_scene_type_name(scene_type)
    shotlist_type = _get_shotlist_type(frames, scene_type)

    lines.append(f"#### {name}")
    lines.append(f"- **Shotlist type:** `{shotlist_type}`")

    # Description — synthesize from content_descriptions
    descriptions = _collect_field_values(frames, "content_description")
    if descriptions:
        lines.append(f"- **Description:** {descriptions[0]}")

    # Use — generalized narrative trigger
    triggers = _collect_field_values(frames, "narrative_trigger")
    if not triggers:
        triggers = _collect_field_values(frames, "narrative_function")
    if triggers:
        lines.append(f"- **Use:** {triggers[0]}")
        for t in triggers[1:3]:
            if t != triggers[0]:
                lines.append(f"  - Also: {t}")

    # Implementation
    impl = _build_implementation_text(frames)
    if impl != "N/A":
        lines.append(f"- **Implementation:** {impl}")

    # Variants
    variants = _collect_variants(frames)
    if variants:
        lines.append(f"- **Variants:** {', '.join(variants)}")

    # Stats (compact)
    dur_str = f"{props['avg_duration']:.1f}s avg"
    if props['count'] > 1 and props['min_duration'] != props['max_duration']:
        dur_str += f" ({props['min_duration']:.0f}-{props['max_duration']:.0f}s range)"
    lines.append(f"- **Stats:** {props['proportion'] * 100:.1f}% "
                 f"· {props['count']}x · {dur_str}")

    # Examples
    examples = [
        f for f in frames
        if f.get("content_description") and f["content_description"] != "unclear"
    ]
    if examples:
        lines.append("- **Examples:**")
        lines.append("")
        lines.append("  | Frame | Content |")
        lines.append("  |-------|---------|")
        for ex in examples[:3]:
            fid = ex.get("frame_id", "?")
            content = ex.get("content_description", "")
            lines.append(f"  | {fid} | {content} |")

    lines.append("")
    return lines


def generate_style_guide(
    analysis_results: list[dict],
    manifest: dict,
    video_title: str,
    video_source: str,
    output_path: str,
) -> str:
    """Generate the final VISUAL_STYLE_GUIDE.md from aggregated analysis."""
    categorized = aggregate_by_category_and_type(analysis_results)

    # Flatten all types for proportion calculation
    all_types = {}
    for cat_types in categorized.values():
        all_types.update(cat_types)
    proportions = compute_proportions(all_types, manifest)

    lines = []

    # Header
    lines.append("# Visual Style Guide")
    lines.append(f"> Source: {video_title} ({video_source})")
    dur_min = int(manifest['video_duration'] // 60)
    dur_sec = int(manifest['video_duration'] % 60)
    total_frames = sum(len(frames) for types in categorized.values() for frames in types.values())
    total_types = sum(len(types) for types in categorized.values())
    lines.append(
        f"> Duration: {dur_min}:{dur_sec:02d} "
        f"| Scenes detected: {manifest['total_scenes_detected']} "
        f"| Unique frames analyzed: {manifest['unique_frames_after_dedup']}"
    )
    lines.append(f"> Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Asset Types (hierarchical)
    lines.append("## 1. Asset Types")
    lines.append("")

    for cat_key in CATEGORY_ORDER:
        if cat_key not in categorized:
            continue
        cat_name = CATEGORIES[cat_key]
        cat_types = categorized[cat_key]

        # Sort subtypes by proportion (descending)
        sorted_subtypes = sorted(
            cat_types.keys(),
            key=lambda t: proportions.get(t, {}).get("proportion", 0),
            reverse=True,
        )

        lines.append(f"### {cat_name}")
        lines.append("")

        for scene_type in sorted_subtypes:
            frames = cat_types[scene_type]
            props = proportions.get(scene_type, {
                "proportion": 0, "count": len(frames),
                "avg_duration": 0, "min_duration": 0, "max_duration": 0,
            })
            lines.extend(_build_subtype_entry(scene_type, frames, props))

    lines.append("---")
    lines.append("")

    # Section 2: Type Mapping (quick-reference)
    lines.append("## 2. Type Mapping (Scene Type -> Shotlist)")
    lines.append("")
    lines.append("| # | Category | Extracted Type | Shotlist `visual_type` | Proportion | Frequency |")
    lines.append("|---|----------|---------------|----------------------|------------|-----------|")

    row_num = 1
    for cat_key in CATEGORY_ORDER:
        if cat_key not in categorized:
            continue
        cat_name = CATEGORIES[cat_key]
        cat_types = categorized[cat_key]
        sorted_subtypes = sorted(
            cat_types.keys(),
            key=lambda t: proportions.get(t, {}).get("proportion", 0),
            reverse=True,
        )
        for scene_type in sorted_subtypes:
            name = _format_scene_type_name(scene_type)
            shotlist_type = _get_shotlist_type(cat_types[scene_type], scene_type)
            props = proportions.get(scene_type, {"proportion": 0, "count": 0})
            lines.append(
                f"| {row_num} | {cat_name} | {name} | `{shotlist_type}` | "
                f"{props['proportion'] * 100:.1f}% | {props['count']}x |"
            )
            row_num += 1

    lines.append("")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    cat_count = sum(1 for c in CATEGORY_ORDER if c in categorized)
    print(f"\n[Stage 6/6] Synthesizing style guide...")
    print(f"  Done: VISUAL_STYLE_GUIDE.md ({cat_count} categories, {total_types} asset types)")

    return output_path
