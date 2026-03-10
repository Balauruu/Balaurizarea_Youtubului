"""Stage 6: Synthesis — prepare aggregated data for LLM synthesis subagent.

v4: Frame-level data is aggregated by pattern_name, then passed to an LLM
subagent that produces the final VISUAL_STYLE_GUIDE.md decision framework.
Python handles data prep only — the LLM handles abstraction and generalization.
"""

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

# Fallback: if no category field, infer from pattern_name
PATTERN_TO_CATEGORY = {
    "archival_video": "b_roll",
    "archival_bw_footage": "b_roll",
    "b_roll_footage": "b_roll",
    "news_clip": "b_roll",
    "archival_photo": "archival_photos",
    "portrait": "archival_photos",
    "location_shot": "archival_photos",
    "animated_graphic": "graphics_animation",
    "silhouette_figure": "graphics_animation",
    "silhouette": "graphics_animation",
    "silhouette_animation": "graphics_animation",
    "location_map": "graphics_animation",
    "map_animation": "graphics_animation",
    "concept_diagram": "graphics_animation",
    "date_card": "graphics_animation",
    "title_card": "text_elements",
    "text_overlay": "text_elements",
    "quote_card": "text_elements",
    "chapter_header": "text_elements",
    "keyword_stinger": "text_elements",
    "evidence_document": "evidence_documentation",
    "document_scan": "evidence_documentation",
    "screen_recording": "evidence_documentation",
}


def _normalize_pattern_name(name: str) -> str:
    """Normalize pattern names — merge variants, strip prefixes."""
    pn = name.strip().lower().replace(" ", "_")
    # Merge common black/transition variants
    if any(kw in pn for kw in [
        "black_screen", "transition_black", "black_transition",
        "fade_to_black", "color_hold", "film_leader",
        "solid_color", "transition_color",
    ]):
        return "_transition"
    # Strip "other:" prefix
    if pn.startswith("other:"):
        return pn[6:].strip().replace(" ", "_")
    if pn.startswith("other_"):
        return pn[6:]
    return pn


def _infer_category(frame: dict, pattern_name: str) -> str:
    """Get category from frame data, falling back to pattern_name mapping."""
    cat = frame.get("category", "").strip().lower().replace(" ", "_")
    if cat in CATEGORIES:
        return cat
    if cat == "transition":
        return "_transition"
    return PATTERN_TO_CATEGORY.get(pattern_name, "graphics_animation")


def aggregate_by_category_and_type(
    analysis_results: list[dict],
    min_confidence: int = 3,
) -> dict[str, dict[str, list[dict]]]:
    """Group frames by category -> pattern_name, filtering transitions and low-confidence.

    Supports both v3 (scene_type) and v4 (pattern_name) field names.
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for frame in analysis_results:
        if frame.get("confidence", 0) < min_confidence:
            continue
        # Support both v3 and v4 field names
        raw_name = frame.get("pattern_name") or frame.get("scene_type", "unknown")
        pattern_name = _normalize_pattern_name(raw_name)
        category = _infer_category(frame, pattern_name)
        # Skip transitions entirely
        if category == "_transition" or pattern_name == "_transition":
            continue
        grouped[category][pattern_name].append(frame)
    return {cat: dict(types) for cat, types in grouped.items()}


def compute_proportions(
    all_frames_by_type: dict[str, list[dict]],
    manifest: dict,
) -> dict[str, dict]:
    """Compute runtime proportion for each pattern type."""
    video_duration = manifest["video_duration"]
    frame_lookup = {f"F{f['frame_id']:03d}": f for f in manifest["frames"]}

    proportions = {}
    for pattern_name, frames in all_frames_by_type.items():
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

        proportions[pattern_name] = {
            "proportion": total_weighted / video_duration if video_duration > 0 else 0,
            "total_seconds": total_weighted,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "count": len(frames),
        }

    return proportions


def prepare_synthesis_input(
    analysis_results: list[dict],
    manifest: dict,
    video_title: str,
    video_source: str,
) -> str:
    """Aggregate frame data into structured text for the LLM synthesis subagent.

    Returns a text block containing aggregated pattern data organized by category,
    with proportions, visual recipes, narrative functions, and variants for each pattern.
    """
    categorized = aggregate_by_category_and_type(analysis_results)

    # Flatten all types for proportion calculation
    all_types = {}
    for cat_types in categorized.values():
        all_types.update(cat_types)
    proportions = compute_proportions(all_types, manifest)

    # Build structured text
    lines = []
    lines.append(f"VIDEO_TITLE: {video_title}")
    lines.append(f"VIDEO_SOURCE: {video_source}")
    dur_min = int(manifest['video_duration'] // 60)
    dur_sec = int(manifest['video_duration'] % 60)
    lines.append(f"DURATION: {dur_min}:{dur_sec:02d}")
    lines.append(f"DATE: {date.today().isoformat()}")
    lines.append(f"TOTAL_SCENES: {manifest['total_scenes_detected']}")
    lines.append(f"UNIQUE_FRAMES: {manifest['unique_frames_after_dedup']}")
    lines.append("")

    for cat_key in CATEGORY_ORDER:
        if cat_key not in categorized:
            continue
        cat_name = CATEGORIES[cat_key]
        cat_types = categorized[cat_key]

        lines.append(f"=== CATEGORY: {cat_name} ({cat_key}) ===")
        lines.append("")

        # Sort by proportion descending
        sorted_patterns = sorted(
            cat_types.keys(),
            key=lambda t: proportions.get(t, {}).get("proportion", 0),
            reverse=True,
        )

        for pattern_name in sorted_patterns:
            frames = cat_types[pattern_name]
            props = proportions.get(pattern_name, {})

            lines.append(f"--- PATTERN: {pattern_name} ---")
            lines.append(f"Count: {props.get('count', len(frames))} frames")
            lines.append(f"Proportion: {props.get('proportion', 0) * 100:.1f}%")
            lines.append(f"Duration: {props.get('avg_duration', 0):.1f}s avg"
                         f" ({props.get('min_duration', 0):.0f}-{props.get('max_duration', 0):.0f}s range)")

            # Collect shotlist types
            shotlist_types = [f.get("shotlist_type", "") for f in frames if f.get("shotlist_type")]
            if shotlist_types:
                most_common = Counter(shotlist_types).most_common(1)[0][0]
                lines.append(f"Shotlist type: {most_common}")

            # Collect unique visual recipes
            recipes = []
            for f in frames:
                recipe = f.get("visual_recipe", {})
                if isinstance(recipe, dict) and recipe:
                    recipes.append(recipe)
            if recipes:
                lines.append("Visual recipes:")
                # Collect unique values for each recipe field
                for field in ["background", "subject", "treatment", "color_palette", "text_style"]:
                    values = []
                    for r in recipes:
                        v = r.get(field, "")
                        if v and v != "unclear" and v != "none":
                            values.append(v)
                    if values:
                        unique = list(dict.fromkeys(values))[:5]  # Dedupe, keep order, max 5
                        lines.append(f"  {field}: {' | '.join(unique)}")

            # Collect narrative functions
            functions = []
            for f in frames:
                nf = f.get("narrative_function") or f.get("narrative_trigger", "")
                if nf and nf != "unclear":
                    functions.append(nf)
            if functions:
                unique_functions = list(dict.fromkeys(functions))[:5]
                lines.append("Narrative functions:")
                for nf in unique_functions:
                    lines.append(f"  - {nf}")

            # Collect variants
            variants = []
            for f in frames:
                v = f.get("variant_name") or f.get("variants", "")
                if isinstance(v, str) and v.strip().lower() not in ("", "default", "unclear"):
                    variants.append(v.strip())
            if variants:
                unique_variants = list(dict.fromkeys(variants))
                lines.append(f"Variants: {', '.join(unique_variants)}")

            lines.append("")

    return "\n".join(lines)
