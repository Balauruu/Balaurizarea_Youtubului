"""Schema validation for shotlist.json.

Validates the shotlist contract that all downstream skills (media acquisition,
graphics, animation, asset manager) depend on.
"""
import re

# Valid shotlist_type values — these map to downstream skill routing
VALID_SHOTLIST_TYPES = frozenset({
    "archival_video",
    "archival_photo",
    "animation",
    "map",
    "text_overlay",
    "document_scan",
})

# Top-level required keys
REQUIRED_TOP_LEVEL_KEYS = {"project", "guide_source", "generated", "shots"}

# Per-shot required fields
REQUIRED_SHOT_FIELDS = {
    "id",
    "chapter",
    "chapter_title",
    "narrative_context",
    "visual_need",
    "building_block",
    "shotlist_type",
}

# Shot ID pattern: S001 through S999
_ID_PATTERN = re.compile(r"^S\d{3}$")

# Glitch-type building blocks (for sequencing constraint: no back-to-back)
GLITCH_BUILDING_BLOCKS = frozenset({
    "Glitch Stinger",
    "Static Noise / Corruption",
    "Static Noise",
    "Data Moshing Montage",
    "Data Moshing",
})


def validate_shotlist(data: dict) -> list[str]:
    """Validate a shotlist.json dict against the schema contract.

    Args:
        data: Parsed shotlist.json content.

    Returns:
        List of human-readable error strings. Empty list means valid.
        Each error includes shot ID context where applicable.
    """
    errors: list[str] = []

    # (a) Top-level required keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if "shots" not in data:
        return errors  # Can't validate shots if the key is missing

    shots = data["shots"]
    if not isinstance(shots, list):
        errors.append("'shots' must be an array")
        return errors

    if not shots:
        errors.append("'shots' array is empty — expected at least one shot")
        return errors

    # Track IDs for sequential check
    seen_ids: list[str] = []

    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f"Shot at index {i}: expected object, got {type(shot).__name__}")
            continue

        shot_id = shot.get("id", f"index-{i}")

        # (b) Required fields per shot
        for field in REQUIRED_SHOT_FIELDS:
            if field not in shot:
                errors.append(f"Shot {shot_id}: missing required field '{field}'")

        # (c) ID format S001-S999
        if "id" in shot:
            if not _ID_PATTERN.match(shot["id"]):
                errors.append(
                    f"Shot {shot_id}: invalid ID format '{shot['id']}' "
                    f"(expected S001-S999)"
                )
            else:
                id_num = int(shot["id"][1:])
                if id_num < 1 or id_num > 999:
                    errors.append(f"Shot {shot_id}: ID number out of range (1-999)")
            seen_ids.append(shot["id"])

        # (d) shotlist_type in valid enum
        if "shotlist_type" in shot:
            if shot["shotlist_type"] not in VALID_SHOTLIST_TYPES:
                errors.append(
                    f"Shot {shot_id}: invalid shotlist_type '{shot['shotlist_type']}'. "
                    f"Valid types: {sorted(VALID_SHOTLIST_TYPES)}"
                )

        # (e) text_content rules — populated iff shotlist_type is text_overlay
        stype = shot.get("shotlist_type")
        text_content = shot.get("text_content")
        has_text_content = text_content is not None and text_content != ""

        if stype == "text_overlay" and not has_text_content:
            errors.append(
                f"Shot {shot_id}: shotlist_type is 'text_overlay' but "
                f"'text_content' is missing or empty (R002: must include actual text)"
            )
        elif stype and stype != "text_overlay" and has_text_content:
            errors.append(
                f"Shot {shot_id}: 'text_content' is populated but shotlist_type "
                f"is '{stype}' (text_content should only be set for text_overlay)"
            )

    # (c) Sequential ID check
    _validate_id_sequence(seen_ids, errors)

    # (f) Sequencing constraints
    _validate_sequencing(shots, errors)

    return errors


def _validate_id_sequence(ids: list[str], errors: list[str]) -> None:
    """Check that shot IDs are sequential starting from S001."""
    if not ids:
        return

    for i, shot_id in enumerate(ids):
        if not _ID_PATTERN.match(shot_id):
            continue
        expected_num = i + 1
        actual_num = int(shot_id[1:])
        if actual_num != expected_num:
            errors.append(
                f"Shot {shot_id}: ID out of sequence "
                f"(expected S{expected_num:03d} at position {i + 1})"
            )


def _validate_sequencing(shots: list[dict], errors: list[str]) -> None:
    """Validate sequencing constraints from the visual style guide.

    Constraints checked:
    - No back-to-back glitch/distortion elements
    - Max 3 consecutive text_overlay shots
    - Max 3 consecutive animation shots with building_block "Silhouette Figure"
    """
    for i in range(1, len(shots)):
        prev = shots[i - 1]
        curr = shots[i]
        prev_id = prev.get("id", f"index-{i - 1}")
        curr_id = curr.get("id", f"index-{i}")

        # No back-to-back glitch elements
        prev_bb = prev.get("building_block", "")
        curr_bb = curr.get("building_block", "")
        if prev_bb in GLITCH_BUILDING_BLOCKS and curr_bb in GLITCH_BUILDING_BLOCKS:
            errors.append(
                f"Shots {prev_id}-{curr_id}: back-to-back glitch/distortion elements "
                f"('{prev_bb}' → '{curr_bb}')"
            )

    # Max 3 consecutive text_overlay
    _check_consecutive_run(
        shots,
        key=lambda s: s.get("shotlist_type") == "text_overlay",
        max_run=3,
        label="text_overlay",
        errors=errors,
    )

    # Max 3 consecutive Silhouette Figure animation
    _check_consecutive_run(
        shots,
        key=lambda s: (
            s.get("shotlist_type") == "animation"
            and s.get("building_block") == "Silhouette Figure"
        ),
        max_run=3,
        label="consecutive Silhouette Figure animation",
        errors=errors,
    )


def _check_consecutive_run(
    shots: list[dict],
    key,
    max_run: int,
    label: str,
    errors: list[str],
) -> None:
    """Check for runs of consecutive shots matching a predicate exceeding max_run."""
    run_start = 0
    run_length = 0

    for i, shot in enumerate(shots):
        if key(shot):
            if run_length == 0:
                run_start = i
            run_length += 1
        else:
            if run_length > max_run:
                start_id = shots[run_start].get("id", f"index-{run_start}")
                end_id = shots[run_start + run_length - 1].get(
                    "id", f"index-{run_start + run_length - 1}"
                )
                errors.append(
                    f"Shots {start_id}-{end_id}: {run_length} consecutive {label} "
                    f"(max {max_run})"
                )
            run_length = 0

    # Check final run
    if run_length > max_run:
        start_id = shots[run_start].get("id", f"index-{run_start}")
        end_id = shots[run_start + run_length - 1].get(
            "id", f"index-{run_start + run_length - 1}"
        )
        errors.append(
            f"Shots {start_id}-{end_id}: {run_length} consecutive {label} "
            f"(max {max_run})"
        )
