"""CLI entry point for the animation skill.

Subcommands:
    load     -- Aggregate shotlist.json (map shots only) + manifest.json + channel.md
                and print them to stdout for Claude to consume.
    render   -- Render map shots via Remotion subprocess, produce .mp4 clips,
                update manifest.json.
    status   -- Print map-shot coverage stats from manifest + shotlist.

Usage:
    PYTHONPATH=.claude/skills/animation/scripts python -m animation load "Duplessis Orphans"
    PYTHONPATH=.claude/skills/animation/scripts python -m animation render "Duplessis Orphans"
    PYTHONPATH=.claude/skills/animation/scripts python -m animation status "Duplessis Orphans"
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Shared helpers (mirrored from graphics_generator pattern)
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

    Falls back to .claude/scratch/animation/{topic} if no match found.

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

    scratch_dir = root / ".claude" / "scratch" / "animation" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


def _slugify(name: str) -> str:
    """Convert a name to a filename-safe slug."""
    return name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")


def _empty_manifest(shotlist_data: dict) -> dict:
    """Create an empty manifest skeleton."""
    return {
        "project": shotlist_data.get("project", ""),
        "generated": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "assets": [],
        "gaps": [],
        "source_summary": {},
    }


def _merge_manifest(
    project_dir: Path,
    shotlist_data: dict,
    generated: list[dict],
) -> None:
    """Read existing manifest.json (if any), append new animation assets, update gaps."""
    manifest_path = project_dir / "assets" / "manifest.json"

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = _empty_manifest(shotlist_data)
    else:
        manifest = _empty_manifest(shotlist_data)

    existing_filenames = {a["filename"] for a in manifest.get("assets", [])}
    generated_shot_ids: set[str] = set()

    for entry in generated:
        shot = entry["shot"]
        path: Path = entry["path"]
        shot_id = shot.get("id", "???")
        bb = shot.get("building_block", "")
        generated_shot_ids.add(shot_id)

        if path.name in existing_filenames:
            continue

        asset_entry = {
            "filename": path.name,
            "folder": "animations",
            "source": "remotion_render",
            "source_url": f"local://animation/{_slugify(bb)}",
            "description": f"{bb} map animation for {shot.get('visual_need', shot_id)}",
            "license": "generated",
            "mapped_shots": [shot_id],
            "acquired_by": "agent_animation",
        }
        manifest["assets"].append(asset_entry)

    # Update gap statuses
    for gap in manifest.get("gaps", []):
        if gap.get("shot_id") in generated_shot_ids:
            if gap.get("status") == "pending_generation":
                gap["status"] = "filled"

    manifest["updated"] = datetime.now(timezone.utc).isoformat()

    # Atomic write
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
# Variant mapping
# ---------------------------------------------------------------------------

# Maps shotlist building_block values to Remotion MapComposition variant names
BUILDING_BLOCK_TO_VARIANT: dict[str, str] = {
    "illustrated map": "illustrated-map",
    "3d geographic visualization": "3d-geographic",
    "region highlight map": "region-highlight",
    "connection/arc map": "connection-arc",
    # Convenience aliases
    "connection arc map": "connection-arc",
    "connection arc": "connection-arc",
    "region highlight": "region-highlight",
    "illustrated-map": "illustrated-map",
    "3d-geographic": "3d-geographic",
    "region-highlight": "region-highlight",
    "connection-arc": "connection-arc",
}

DEFAULT_VARIANT = "connection-arc"
DEFAULT_DURATION_SECONDS = 8


def _map_shot_to_props(shot: dict) -> dict:
    """Convert a shotlist map entry to Remotion MapComposition props.

    Maps:
    - building_block → variant (via BUILDING_BLOCK_TO_VARIANT lookup)
    - visual_need → title (fallback to narrative_context)
    - narrative_context → used to extract location hints
    - Default 3 placeholder locations if none parsed
    """
    bb = shot.get("building_block", "").lower().strip()
    variant = BUILDING_BLOCK_TO_VARIANT.get(bb, DEFAULT_VARIANT)

    title = shot.get("visual_need", shot.get("narrative_context", "Map"))
    # Truncate long titles for the animation
    if len(title) > 60:
        title = title[:57] + "..."

    # Extract location hints from visual_need and narrative_context
    locations = _extract_locations(shot)
    if not locations:
        # Fallback: single centered location from the title
        locations = [{"name": title[:30], "x": 0.5, "y": 0.5}]

    # Build connections between sequential locations
    connections = []
    for i in range(len(locations) - 1):
        connections.append({"from": i, "to": i + 1})

    return {
        "variant": variant,
        "title": title,
        "locations": locations[:3],  # Max 3 per VISUAL_STYLE_GUIDE
        "connections": connections,
        "durationSeconds": DEFAULT_DURATION_SECONDS,
    }


def _extract_locations(shot: dict) -> list[dict]:
    """Extract location data from shot fields.

    This is a best-effort extraction — the agent calling `render` is expected
    to have enriched the shotlist with proper location data. For now we provide
    reasonable defaults based on the shot's context.
    """
    # Check if shot has explicit locations field (enriched by agent)
    if "locations" in shot:
        locs = shot["locations"]
        if isinstance(locs, list) and locs:
            return [
                {
                    "name": loc.get("name", f"Point {i+1}"),
                    "x": float(loc.get("x", 0.3 + i * 0.2)),
                    "y": float(loc.get("y", 0.4 + i * 0.1)),
                }
                for i, loc in enumerate(locs)
            ]

    # Fallback: generate placeholder locations from visual_need text
    visual_need = shot.get("visual_need", "")
    narrative = shot.get("narrative_context", "")
    combined = f"{visual_need} {narrative}"

    # Simple heuristic: if text mentions specific places, create spread locations
    # A more sophisticated version would use NLP or geocoding
    words = combined.split()
    # Use word count to vary position slightly so different shots look different
    seed = len(words) % 5
    positions = [
        (0.25 + seed * 0.05, 0.35),
        (0.55, 0.50 + seed * 0.03),
        (0.75 - seed * 0.04, 0.65),
    ]

    label = visual_need[:25] if visual_need else "Location"
    return [{"name": label, "x": positions[0][0], "y": positions[0][1]}]


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_load(topic: str) -> None:
    """Aggregate context files for map shots and print to stdout for Claude."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    manifest_path = project_dir / "assets" / "manifest.json"
    channel_path = root / "context" / "channel" / "channel.md"

    # Validate required files
    missing: list[Path] = []
    if not shotlist_path.exists():
        missing.append(shotlist_path)
    if not channel_path.exists():
        missing.append(channel_path)

    if missing:
        for path in missing:
            print(f"Error: required file not found: {path}", file=sys.stderr)
        sys.exit(1)

    shotlist_data = json.loads(shotlist_path.read_text(encoding="utf-8"))
    shots = shotlist_data.get("shots", [])
    map_shots = [s for s in shots if s.get("shotlist_type") == "map"]

    # === MAP_SHOTS ===
    print("=== MAP_SHOTS ===")
    if map_shots:
        print(json.dumps(map_shots, indent=2, ensure_ascii=False))
    else:
        print(f"(No map shots found — {len(shots)} total shots, none with shotlist_type 'map')")
    print()
    print("---")
    print()

    # === MANIFEST ===
    print("=== MANIFEST ===")
    if manifest_path.exists():
        print(manifest_path.read_text(encoding="utf-8"))
    else:
        print("(No manifest.json found — will be created on render)")
    print()
    print("---")
    print()

    # === CHANNEL_DNA ===
    print("=== CHANNEL_DNA ===")
    print(channel_path.read_text(encoding="utf-8"))
    print()
    print("---")


def cmd_render(topic: str) -> None:
    """Render map shots via Remotion subprocess, produce .mp4 clips, update manifest."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    if not shotlist_path.exists():
        print(f"Error: shotlist.json not found: {shotlist_path}", file=sys.stderr)
        sys.exit(1)

    try:
        shotlist_data = json.loads(shotlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {shotlist_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    shots = shotlist_data.get("shots", [])
    map_shots = [s for s in shots if s.get("shotlist_type") == "map"]

    if not map_shots:
        print("No map shots found in shotlist.", file=sys.stderr)
        sys.exit(0)

    # Resolve paths
    remotion_dir = root / ".claude" / "skills" / "animation" / "remotion"
    entry_point = "src/index.ts"
    output_dir = project_dir / "assets" / "animations"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not remotion_dir.exists():
        print(f"Error: Remotion project not found: {remotion_dir}", file=sys.stderr)
        sys.exit(1)

    # Check node_modules exist
    if not (remotion_dir / "node_modules").exists():
        print("Installing Remotion dependencies...", file=sys.stderr)
        install_result = subprocess.run(
            ["npm", "install"],
            cwd=str(remotion_dir),
            capture_output=True,
            text=True,
        )
        if install_result.returncode != 0:
            print(f"Error: npm install failed:\n{install_result.stderr}", file=sys.stderr)
            sys.exit(1)

    generated: list[dict] = []
    errors: list[tuple[dict, str]] = []

    for shot in map_shots:
        shot_id = shot.get("id", "???")
        bb = shot.get("building_block", "unknown")
        slug = _slugify(bb)

        # Map shot fields to Remotion props
        props = _map_shot_to_props(shot)
        output_filename = f"{shot_id}_{slug}.mp4"
        output_path = output_dir / output_filename

        # Write props to temp file
        props_fd, props_path = tempfile.mkstemp(suffix=".json", prefix=f"props_{shot_id}_")
        try:
            with os.fdopen(props_fd, "w", encoding="utf-8") as f:
                json.dump(props, f, indent=2)

            print(f"Rendering {shot_id} ({bb}) → {output_filename}...", file=sys.stderr)

            # Call Remotion render via subprocess
            cmd = [
                "npx", "remotion", "render",
                entry_point,
                "MapComposition",
                str(output_path),
                f"--props={props_path}",
            ]

            result = subprocess.run(
                cmd,
                cwd=str(remotion_dir),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per render
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                msg = f"Render failed for {shot_id} ({bb}): {error_msg}"
                print(msg, file=sys.stderr)
                errors.append((shot, error_msg))
            else:
                if output_path.exists():
                    generated.append({"shot": shot, "path": output_path})
                    print(f"  → {output_filename} ({output_path.stat().st_size // 1024}KB)", file=sys.stderr)
                else:
                    msg = f"Render completed but output file not found: {output_path}"
                    print(msg, file=sys.stderr)
                    errors.append((shot, msg))

        except subprocess.TimeoutExpired:
            msg = f"Render timed out for {shot_id} ({bb}) after 120s"
            print(msg, file=sys.stderr)
            errors.append((shot, msg))
        finally:
            # Clean up props temp file
            if os.path.exists(props_path):
                os.unlink(props_path)

    # Update manifest
    _merge_manifest(project_dir, shotlist_data, generated)

    # Summary
    print(
        f"\nRender complete: {len(generated)} rendered, {len(errors)} errors "
        f"(of {len(map_shots)} map shots)",
        file=sys.stderr,
    )

    if errors:
        print("\nFailed shots:", file=sys.stderr)
        for shot, err in errors:
            print(f"  {shot.get('id', '???')}: {err[:200]}", file=sys.stderr)
        sys.exit(1)


def cmd_status(topic: str) -> None:
    """Print map-shot coverage stats."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    if not shotlist_path.exists():
        print(f"Error: shotlist.json not found: {shotlist_path}", file=sys.stderr)
        sys.exit(1)

    try:
        shotlist_data = json.loads(shotlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    shots = shotlist_data.get("shots", [])
    map_shots = [s for s in shots if s.get("shotlist_type") == "map"]

    print(f"Map Shot Coverage for '{topic}'")
    print(f"{'=' * 40}")
    print(f"Total shots in shotlist: {len(shots)}")
    print(f"Map shots: {len(map_shots)}")

    if not map_shots:
        print("\nNo map shots to render.")
        return

    # Count by building block
    bb_counts: dict[str, int] = {}
    for shot in map_shots:
        bb = shot.get("building_block", "unknown")
        bb_counts[bb] = bb_counts.get(bb, 0) + 1

    print("\nBy building block:")
    for bb, count in sorted(bb_counts.items()):
        variant = BUILDING_BLOCK_TO_VARIANT.get(bb.lower().strip(), "?")
        print(f"  {bb}: {count} shots → variant '{variant}'")

    # Check rendered files
    animations_dir = project_dir / "assets" / "animations"
    rendered_files = list(animations_dir.glob("*.mp4")) if animations_dir.exists() else []

    # Check manifest for agent_animation entries
    manifest_path = project_dir / "assets" / "manifest.json"
    manifest_rendered = 0
    pending_count = 0
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_rendered = sum(
                1 for a in manifest.get("assets", [])
                if a.get("acquired_by") == "agent_animation"
            )
            pending_count = sum(
                1 for g in manifest.get("gaps", [])
                if g.get("status") == "pending_generation"
            )
        except json.JSONDecodeError:
            pass

    print(f"\nRendered .mp4 files: {len(rendered_files)}")
    print(f"Manifest entries (agent_animation): {manifest_rendered}")
    print(f"Pending generation gaps: {pending_count}")

    coverage = manifest_rendered / len(map_shots) * 100 if map_shots else 0
    print(f"\nCoverage: {manifest_rendered}/{len(map_shots)} ({coverage:.0f}%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="animation",
        description="Animation skill — render animated map clips via Remotion",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files for map shots and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    render_parser = subparsers.add_parser(
        "render",
        help="Render map shot .mp4 clips via Remotion",
    )
    render_parser.add_argument("topic", help="Topic string")

    status_parser = subparsers.add_parser(
        "status",
        help="Show map-shot coverage stats",
    )
    status_parser.add_argument("topic", help="Topic string")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
        elif args.command == "render":
            cmd_render(args.topic)
        elif args.command == "status":
            cmd_status(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
