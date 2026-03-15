"""Schema validation for manifest.json.

Validates the manifest contract that all downstream skills (graphics,
animation, asset manager) depend on. This is the central coordination
artifact (D011) for the visual pipeline.
"""
import re

# Valid folder names for asset organization
VALID_FOLDERS = frozenset({
    "archival_photos",
    "archival_footage",
    "documents",
    "broll",
    "vectors",
    "animations",
})

# Valid gap statuses — the gap lifecycle (R010)
VALID_GAP_STATUSES = frozenset({
    "pending_generation",
    "filled",
    "unfilled",
})

# Top-level required keys
REQUIRED_TOP_LEVEL_KEYS = {"project", "generated", "updated", "assets", "gaps", "source_summary"}

# Per-asset required fields
REQUIRED_ASSET_FIELDS = {
    "filename",
    "folder",
    "source",
    "source_url",
    "description",
    "license",
    "mapped_shots",
    "acquired_by",
}

# Per-gap required fields
REQUIRED_GAP_FIELDS = {
    "shot_id",
    "visual_need",
    "shotlist_type",
    "status",
}

# Shot ID pattern: S001 through S999
_SHOT_ID_PATTERN = re.compile(r"^S\d{3}$")


def validate_manifest(data: dict) -> list[str]:
    """Validate a manifest.json dict against the schema contract.

    Args:
        data: Parsed manifest.json content.

    Returns:
        List of human-readable error strings. Empty list means valid.
        Each error includes asset/gap context where applicable.
    """
    errors: list[str] = []

    # (a) Top-level required keys
    for key in sorted(REQUIRED_TOP_LEVEL_KEYS):
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    # Validate project is a non-empty string
    if "project" in data:
        if not isinstance(data["project"], str) or not data["project"].strip():
            errors.append("'project' must be a non-empty string")

    # (b) Validate assets array
    if "assets" in data:
        _validate_assets(data["assets"], errors)

    # (c) Validate gaps array
    if "gaps" in data:
        _validate_gaps(data["gaps"], errors)

    # (d) Validate source_summary is a dict
    if "source_summary" in data:
        if not isinstance(data["source_summary"], dict):
            errors.append("'source_summary' must be an object")

    return errors


def _validate_assets(assets, errors: list[str]) -> None:
    """Validate the assets array."""
    if not isinstance(assets, list):
        errors.append("'assets' must be an array")
        return

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"Asset at index {i}: expected object, got {type(asset).__name__}")
            continue

        label = asset.get("filename", f"index-{i}")

        # Required fields
        for field in sorted(REQUIRED_ASSET_FIELDS):
            if field not in asset:
                errors.append(f"Asset '{label}': missing required field '{field}'")

        # Folder must be valid
        if "folder" in asset:
            if asset["folder"] not in VALID_FOLDERS:
                errors.append(
                    f"Asset '{label}': invalid folder '{asset['folder']}'. "
                    f"Valid folders: {sorted(VALID_FOLDERS)}"
                )

        # mapped_shots must be an array of valid shot IDs
        if "mapped_shots" in asset:
            mapped = asset["mapped_shots"]
            if not isinstance(mapped, list):
                errors.append(f"Asset '{label}': 'mapped_shots' must be an array")
            else:
                for shot_id in mapped:
                    if not isinstance(shot_id, str) or not _SHOT_ID_PATTERN.match(shot_id):
                        errors.append(
                            f"Asset '{label}': invalid shot ID '{shot_id}' in mapped_shots "
                            f"(expected S001-S999)"
                        )

        # source_url must be a string
        if "source_url" in asset:
            if not isinstance(asset["source_url"], str) or not asset["source_url"].strip():
                errors.append(f"Asset '{label}': 'source_url' must be a non-empty string")


def _validate_gaps(gaps, errors: list[str]) -> None:
    """Validate the gaps array."""
    if not isinstance(gaps, list):
        errors.append("'gaps' must be an array")
        return

    for i, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            errors.append(f"Gap at index {i}: expected object, got {type(gap).__name__}")
            continue

        shot_id = gap.get("shot_id", f"index-{i}")

        # Required fields
        for field in sorted(REQUIRED_GAP_FIELDS):
            if field not in gap:
                errors.append(f"Gap '{shot_id}': missing required field '{field}'")

        # Shot ID format
        if "shot_id" in gap:
            if not _SHOT_ID_PATTERN.match(gap["shot_id"]):
                errors.append(
                    f"Gap '{shot_id}': invalid shot_id format '{gap['shot_id']}' "
                    f"(expected S001-S999)"
                )

        # Status must be valid
        if "status" in gap:
            if gap["status"] not in VALID_GAP_STATUSES:
                errors.append(
                    f"Gap '{shot_id}': invalid status '{gap['status']}'. "
                    f"Valid statuses: {sorted(VALID_GAP_STATUSES)}"
                )
