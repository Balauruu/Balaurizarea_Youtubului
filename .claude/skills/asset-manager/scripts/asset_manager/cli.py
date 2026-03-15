"""CLI entry point for the asset-manager skill.

Subcommands:
    load     -- Aggregate shotlist.json + manifest.json + channel.md
                and print them to stdout for Claude to consume.
    organize -- Number assets by shotlist order, pool unmapped, finalize gaps.
    status   -- Print asset organization stats.

Usage:
    PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager load "Duplessis Orphans"
    PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager organize "Duplessis Orphans"
    PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager status "Duplessis Orphans"
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from media_acquisition.schema import VALID_FOLDERS, validate_manifest


# ---------------------------------------------------------------------------
# Shared helpers (mirrored from established skill pattern)
# ---------------------------------------------------------------------------

def _ensure_utf8_stdout() -> None:
    """Reconfigure stdout to use UTF-8 encoding on Windows."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )


def _get_project_root() -> Path:
    """Walk up from this file looking for CLAUDE.md as the project root marker."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def resolve_project_dir(root: Path, topic: str) -> Path:
    """Find the project directory for a topic by case-insensitive substring match.

    Falls back to .claude/scratch/asset-manager/{topic} if no match found.

    Raises:
        ValueError: When multiple project directories match.
    """
    projects_dir = root / "projects"
    if projects_dir.is_dir():
        query = topic.lower()
        matches = [
            d for d in projects_dir.iterdir()
            if d.is_dir() and query in d.name.lower()
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(f'"{m.name}"' for m in sorted(matches))
            raise ValueError(
                f"Multiple project directories match '{topic}': {names}. "
                "Please use a more specific topic string."
            )

    scratch_dir = root / ".claude" / "scratch" / "asset-manager" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


# ---------------------------------------------------------------------------
# Prefix helpers
# ---------------------------------------------------------------------------

_PREFIX_PATTERN = re.compile(r"^\d{3}_")


def _strip_existing_prefix(filename: str) -> str:
    """Remove an existing NNN_ prefix for idempotent re-runs."""
    return _PREFIX_PATTERN.sub("", filename)


def _add_prefix(seq_num: int, filename: str) -> str:
    """Add NNN_ prefix to a filename (strip existing prefix first)."""
    bare = _strip_existing_prefix(filename)
    return f"{seq_num:03d}_{bare}"


# ---------------------------------------------------------------------------
# Core organize logic
# ---------------------------------------------------------------------------

def _build_shot_order(shotlist_data: dict) -> dict[str, int]:
    """Map shot_id → 1-based sequence number from shotlist array order.

    Returns:
        Dict like {"S001": 1, "S002": 2, ...}
    """
    order = {}
    for i, shot in enumerate(shotlist_data.get("shots", []), start=1):
        shot_id = shot.get("id", "")
        if shot_id and shot_id not in order:
            order[shot_id] = i
    return order


def _compute_numbering(
    manifest_assets: list[dict],
    shot_order: dict[str, int],
) -> tuple[list[tuple[dict, int]], list[dict]]:
    """Compute sequence numbers for assets based on their mapped shots.

    For each asset, finds the earliest mapped_shot in shot_order and assigns
    that sequence number.

    Returns:
        (numbered, unmapped) — numbered is list of (asset, seq_num) tuples,
        unmapped is list of assets with no mapped shots in the shotlist.
    """
    numbered: list[tuple[dict, int]] = []
    unmapped: list[dict] = []

    for asset in manifest_assets:
        mapped_shots = asset.get("mapped_shots", [])
        if not mapped_shots:
            unmapped.append(asset)
            continue

        # Find earliest shot in shotlist order
        min_seq = None
        for shot_id in mapped_shots:
            seq = shot_order.get(shot_id)
            if seq is not None:
                if min_seq is None or seq < min_seq:
                    min_seq = seq

        if min_seq is None:
            # Asset has mapped_shots but none appear in shotlist
            unmapped.append(asset)
        else:
            numbered.append((asset, min_seq))

    return numbered, unmapped


def _atomic_write_manifest(manifest_path: Path, manifest: dict) -> None:
    """Write manifest.json atomically using temp file + os.replace."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(manifest_path.parent), suffix=".json.tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, str(manifest_path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_load(topic: str) -> None:
    """Aggregate context files and print to stdout for Claude."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    manifest_path = project_dir / "assets" / "manifest.json"
    channel_path = root / "context" / "channel" / "channel.md"

    missing: list[Path] = []
    if not shotlist_path.exists():
        missing.append(shotlist_path)
    if not manifest_path.exists():
        missing.append(manifest_path)
    if not channel_path.exists():
        missing.append(channel_path)

    if missing:
        for path in missing:
            print(f"Error: required file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # === SHOTLIST ===
    print("=== SHOTLIST ===")
    print(shotlist_path.read_text(encoding="utf-8"))
    print()
    print("---")
    print()

    # === MANIFEST ===
    print("=== MANIFEST ===")
    print(manifest_path.read_text(encoding="utf-8"))
    print()
    print("---")
    print()

    # === CHANNEL_DNA ===
    print("=== CHANNEL_DNA ===")
    print(channel_path.read_text(encoding="utf-8"))
    print()
    print("---")


def cmd_organize(topic: str) -> None:
    """Number assets by shotlist order, pool unmapped, finalize gaps."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    manifest_path = project_dir / "assets" / "manifest.json"

    # Validate required files exist
    for path, name in [(shotlist_path, "shotlist.json"), (manifest_path, "manifest.json")]:
        if not path.exists():
            print(f"Error: {name} not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load data
    try:
        shotlist_data = json.loads(shotlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in shotlist.json: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in manifest.json: {exc}", file=sys.stderr)
        sys.exit(1)

    # Pre-validate manifest
    pre_errors = validate_manifest(manifest)
    if pre_errors:
        print("Error: manifest.json is invalid before organize:", file=sys.stderr)
        for err in pre_errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    assets_dir = project_dir / "assets"

    # Build shot ordering
    shot_order = _build_shot_order(shotlist_data)
    print(f"Shot order: {len(shot_order)} shots in shotlist", file=sys.stderr)

    # Compute numbering
    numbered, unmapped = _compute_numbering(manifest.get("assets", []), shot_order)
    print(
        f"Numbering: {len(numbered)} assets to number, "
        f"{len(unmapped)} unmapped",
        file=sys.stderr,
    )

    # --- Rename numbered assets ---
    rename_count = 0
    for asset, seq_num in numbered:
        old_filename = asset["filename"]
        new_filename = _add_prefix(seq_num, old_filename)

        if old_filename == new_filename:
            continue  # Already correctly named

        folder = asset.get("folder", "")
        folder_path = assets_dir / folder

        old_path = folder_path / old_filename
        new_path = folder_path / new_filename

        if old_path.exists():
            # Handle case where target already exists (shouldn't on clean run)
            if new_path.exists() and old_path != new_path:
                print(
                    f"  Warning: target already exists, overwriting: {new_path}",
                    file=sys.stderr,
                )
            os.replace(str(old_path), str(new_path))
            print(f"  Renamed: {folder}/{old_filename} → {new_filename}", file=sys.stderr)
            rename_count += 1
        else:
            print(
                f"  Warning: asset file not found, skipping rename: {old_path}",
                file=sys.stderr,
            )

        # Update manifest entry
        asset["filename"] = new_filename

    print(f"Renamed {rename_count} files", file=sys.stderr)

    # --- Move unmapped assets to _pool/ ---
    pool_dir = assets_dir / "_pool"
    pool_count = 0
    for asset in unmapped:
        folder = asset.get("folder", "")
        filename = asset["filename"]
        src = assets_dir / folder / filename

        if src.exists():
            pool_dir.mkdir(parents=True, exist_ok=True)
            dst = pool_dir / filename
            # Avoid collision in pool
            if dst.exists():
                stem = src.stem
                suffix = src.suffix
                counter = 1
                while dst.exists():
                    dst = pool_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            shutil.move(str(src), str(dst))
            print(f"  Pooled: {folder}/{filename} → _pool/{dst.name}", file=sys.stderr)
            pool_count += 1
        else:
            print(
                f"  Warning: unmapped asset file not found: {src}",
                file=sys.stderr,
            )

    print(f"Moved {pool_count} unmapped assets to _pool/", file=sys.stderr)

    # Remove unmapped assets from manifest
    unmapped_filenames = {a["filename"] for a in unmapped}
    manifest["assets"] = [
        a for a in manifest.get("assets", [])
        if a["filename"] not in unmapped_filenames
    ]

    # --- Finalize gaps ---
    gap_finalized = 0
    for gap in manifest.get("gaps", []):
        if gap.get("status") == "pending_generation":
            gap["status"] = "unfilled"
            gap_finalized += 1
    print(f"Finalized {gap_finalized} gaps: pending_generation → unfilled", file=sys.stderr)

    # Update timestamp
    manifest["updated"] = datetime.now(timezone.utc).isoformat()

    # Post-validate manifest
    post_errors = validate_manifest(manifest)
    if post_errors:
        print("Error: manifest is invalid after organize (NOT writing):", file=sys.stderr)
        for err in post_errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)

    # Atomic write
    _atomic_write_manifest(manifest_path, manifest)
    print(f"Manifest written: {manifest_path}", file=sys.stderr)
    print("Organize complete.", file=sys.stderr)


def cmd_status(topic: str) -> None:
    """Print asset organization stats."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    manifest_path = project_dir / "assets" / "manifest.json"
    assets_dir = project_dir / "assets"

    print(f"Asset Manager Status for '{topic}'")
    print(f"{'=' * 40}")

    # Load manifest
    if not manifest_path.exists():
        print("No manifest.json found.", file=sys.stderr)
        sys.exit(1)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in manifest.json: {exc}", file=sys.stderr)
        sys.exit(1)

    assets = manifest.get("assets", [])
    gaps = manifest.get("gaps", [])

    # Count numbered vs unnumbered
    numbered = sum(1 for a in assets if _PREFIX_PATTERN.match(a.get("filename", "")))
    unnumbered = len(assets) - numbered

    # Scan pool
    pool_dir = assets_dir / "_pool"
    pool_files = list(pool_dir.iterdir()) if pool_dir.exists() else []

    # Scan type folder files
    type_folder_files = 0
    for folder_name in VALID_FOLDERS:
        folder_path = assets_dir / folder_name
        if folder_path.exists():
            type_folder_files += sum(1 for f in folder_path.iterdir() if f.is_file())

    # Gap breakdown
    gap_filled = sum(1 for g in gaps if g.get("status") == "filled")
    gap_unfilled = sum(1 for g in gaps if g.get("status") == "unfilled")
    gap_pending = sum(1 for g in gaps if g.get("status") == "pending_generation")

    print(f"\nManifest assets: {len(assets)}")
    print(f"  Numbered (NNN_): {numbered}")
    print(f"  Unnumbered:      {unnumbered}")
    print(f"\nFiles on disk:")
    print(f"  In type folders: {type_folder_files}")
    print(f"  In _pool/:       {len(pool_files)}")
    print(f"\nGaps ({len(gaps)} total):")
    print(f"  filled:             {gap_filled}")
    print(f"  unfilled:           {gap_unfilled}")
    print(f"  pending_generation: {gap_pending}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="asset_manager",
        description="Asset Manager — organize and number assets by shotlist order",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    organize_parser = subparsers.add_parser(
        "organize",
        help="Number assets by shotlist order, pool unmapped, finalize gaps",
    )
    organize_parser.add_argument("topic", help="Topic string")

    status_parser = subparsers.add_parser(
        "status",
        help="Show asset organization stats",
    )
    status_parser.add_argument("topic", help="Topic string")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
        elif args.command == "organize":
            cmd_organize(args.topic)
        elif args.command == "status":
            cmd_status(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
