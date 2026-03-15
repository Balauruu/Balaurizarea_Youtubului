"""Download orchestrator and gap analysis for media acquisition.

Reads a search_plan.json, executes searches/downloads via source adapters,
builds manifest.json with asset-to-shot mappings, and identifies gaps
by comparing shotlist.json shot IDs against acquired assets.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from media_acquisition.schema import validate_manifest
from media_acquisition.sources import get_source, SearchResult, DownloadResult


# Shotlist types that are acquisition-relevant.
# Animation/map gaps are expected — handled by S03/S04.
ACQUISITION_RELEVANT_TYPES = frozenset({
    "archival_photo",
    "archival_video",
    "document_scan",
})

# Folder name for each dest_folder value in search_plan.json
DEST_FOLDER_MAP = {
    "archival_photos": "archival_photos",
    "archival_footage": "archival_footage",
    "documents": "documents",
    "broll": "broll",
}


def load_search_plan(path: Path) -> list[dict]:
    """Load and validate search_plan.json.

    Each entry must have: source, query, media_type, shot_ids, dest_folder, limit.

    Returns:
        List of plan entry dicts.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If JSON is invalid or entries are malformed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Search plan not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in search plan: {exc}")

    if not isinstance(data, list):
        raise ValueError("search_plan.json must be a JSON array")

    required_fields = {"source", "query", "media_type", "shot_ids", "dest_folder", "limit"}
    for i, entry in enumerate(data):
        missing = required_fields - set(entry.keys())
        if missing:
            raise ValueError(
                f"Search plan entry {i}: missing fields {sorted(missing)}"
            )

    return data


def load_shotlist(path: Path) -> dict:
    """Load shotlist.json and return a dict of shot_id -> shot info.

    Returns:
        Dict mapping shot ID (e.g. "S001") to dict with visual_need, shotlist_type.
    """
    if not path.exists():
        raise FileNotFoundError(f"Shotlist not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    shots = data.get("shots", [])
    return {
        shot["id"]: {
            "visual_need": shot.get("visual_need", ""),
            "shotlist_type": shot.get("shotlist_type", ""),
        }
        for shot in shots
        if "id" in shot
    }


def execute_plan(
    plan: list[dict],
    assets_dir: Path,
    *,
    source_summary: Optional[dict] = None,
) -> tuple[list[dict], dict]:
    """Execute a search plan: search + download for each entry.

    Args:
        plan: List of search plan entries.
        assets_dir: Root assets directory (typed subdirs created within).
        source_summary: Existing source_summary dict to update (for incremental).

    Returns:
        Tuple of (new_assets list, updated source_summary dict).
    """
    if source_summary is None:
        source_summary = {}

    new_assets: list[dict] = []

    for entry in plan:
        source_name = entry["source"]
        query = entry["query"]
        media_type = entry["media_type"]
        shot_ids = entry["shot_ids"]
        dest_folder = entry["dest_folder"]
        limit = entry.get("limit", 5)

        # Initialize source summary counters
        if source_name not in source_summary:
            source_summary[source_name] = {"searched": 0, "downloaded": 0}

        # Resolve destination directory
        folder_name = DEST_FOLDER_MAP.get(dest_folder, dest_folder)
        dest_path = assets_dir / folder_name
        dest_path.mkdir(parents=True, exist_ok=True)

        # Search
        try:
            source_module = get_source(source_name)
            results: list[SearchResult] = source_module.search(query, media_type, limit)
            source_summary[source_name]["searched"] += len(results)
        except Exception as exc:
            print(
                f"[acquire] Search failed for {source_name} query='{query}': {exc}",
                file=sys.stderr,
            )
            continue

        # Download top results
        for result in results:
            try:
                dl: DownloadResult = source_module.download(
                    result.url, str(dest_path)
                )
            except Exception as exc:
                print(
                    f"[acquire] Download failed {result.url}: {exc}",
                    file=sys.stderr,
                )
                continue

            if dl.success:
                source_summary[source_name]["downloaded"] += 1
                asset = {
                    "filename": dl.filename,
                    "folder": folder_name,
                    "source": result.source,
                    "source_url": result.url,
                    "description": result.description or result.title,
                    "license": result.license,
                    "mapped_shots": list(shot_ids),
                    "acquired_by": "media_acquisition",
                }
                new_assets.append(asset)

    return new_assets, source_summary


def identify_gaps(
    shotlist: dict,
    assets: list[dict],
) -> list[dict]:
    """Compare shotlist shot IDs against manifest mapped_shots to find gaps.

    Only flags gaps for acquisition-relevant types (archival_photo, archival_video,
    document_scan). Animation/map gaps are expected and handled by later slices.

    Args:
        shotlist: Dict of shot_id -> {visual_need, shotlist_type}.
        assets: List of asset dicts with mapped_shots arrays.

    Returns:
        List of gap dicts with shot_id, visual_need, shotlist_type, status.
    """
    # Collect all shots covered by assets
    covered_shots: set[str] = set()
    for asset in assets:
        for shot_id in asset.get("mapped_shots", []):
            covered_shots.add(shot_id)

    gaps: list[dict] = []
    for shot_id, info in sorted(shotlist.items()):
        if shot_id in covered_shots:
            continue

        shotlist_type = info.get("shotlist_type", "")
        # Only flag acquisition-relevant types as gaps
        if shotlist_type not in ACQUISITION_RELEVANT_TYPES:
            continue

        gaps.append({
            "shot_id": shot_id,
            "visual_need": info.get("visual_need", ""),
            "shotlist_type": shotlist_type,
            "status": "pending_generation",
        })

    return gaps


def merge_assets(
    existing_assets: list[dict],
    new_assets: list[dict],
) -> list[dict]:
    """Merge new assets into existing, deduplicating by source_url.

    Existing assets take priority — new assets with the same source_url are skipped.

    Args:
        existing_assets: Assets already in manifest.json.
        new_assets: Newly downloaded assets.

    Returns:
        Merged asset list.
    """
    existing_urls = {a.get("source_url") for a in existing_assets}
    merged = list(existing_assets)
    for asset in new_assets:
        if asset.get("source_url") not in existing_urls:
            merged.append(asset)
            existing_urls.add(asset.get("source_url"))
    return merged


def build_manifest(
    project_name: str,
    assets: list[dict],
    gaps: list[dict],
    source_summary: dict,
) -> dict:
    """Build a complete manifest.json dict.

    Returns:
        Dict matching the manifest schema contract.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "project": project_name,
        "generated": now,
        "updated": now,
        "assets": assets,
        "gaps": gaps,
        "source_summary": source_summary,
    }


def write_manifest_atomic(manifest: dict, manifest_path: Path) -> None:
    """Write manifest.json atomically via temp file + rename.

    Writes to a temp file in the same directory, then renames to avoid
    partial writes corrupting the manifest.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest, indent=2, ensure_ascii=False)

    # Write to temp file in same directory, then rename
    fd, tmp_path = tempfile.mkstemp(
        dir=str(manifest_path.parent),
        prefix=".manifest_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        # On Windows, must remove target first if it exists
        if manifest_path.exists():
            manifest_path.unlink()
        Path(tmp_path).rename(manifest_path)
    except Exception:
        # Clean up temp file on failure
        Path(tmp_path).unlink(missing_ok=True)
        raise


def run_acquire(
    project_dir: Path,
    search_plan_path: Path,
    project_name: str,
) -> dict:
    """Full acquisition pipeline: plan → search → download → manifest → gaps.

    Args:
        project_dir: Project directory containing shotlist.json.
        search_plan_path: Path to search_plan.json.
        project_name: Project name for manifest.

    Returns:
        The final manifest dict.
    """
    # Load inputs
    plan = load_search_plan(search_plan_path)
    shotlist_path = project_dir / "shotlist.json"
    shotlist = load_shotlist(shotlist_path)

    assets_dir = project_dir / "assets"
    manifest_path = assets_dir / "manifest.json"

    # Load existing manifest for incremental merge
    existing_assets: list[dict] = []
    existing_summary: dict = {}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing_assets = existing.get("assets", [])
            existing_summary = existing.get("source_summary", {})
        except (json.JSONDecodeError, KeyError):
            print(
                f"[acquire] Warning: existing manifest at {manifest_path} is invalid, starting fresh",
                file=sys.stderr,
            )

    # Execute search plan
    new_assets, source_summary = execute_plan(
        plan, assets_dir, source_summary=existing_summary
    )

    # Merge assets (dedup by source_url)
    all_assets = merge_assets(existing_assets, new_assets)

    # Identify gaps
    gaps = identify_gaps(shotlist, all_assets)

    # Build and validate manifest
    manifest = build_manifest(project_name, all_assets, gaps, source_summary)
    errors = validate_manifest(manifest)
    if errors:
        print("[acquire] Warning: manifest validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)

    # Atomic write
    write_manifest_atomic(manifest, manifest_path)

    # Print summary
    print(f"=== Acquisition Complete: {project_name} ===")
    print(f"Assets: {len(all_assets)} ({len(new_assets)} new)")
    print(f"Gaps: {len(gaps)} (pending_generation)")
    print(f"Sources used: {len(source_summary)}")
    for src, stats in sorted(source_summary.items()):
        print(f"  {src}: {stats['downloaded']} downloaded / {stats['searched']} searched")
    print(f"Manifest: {manifest_path}")

    return manifest
