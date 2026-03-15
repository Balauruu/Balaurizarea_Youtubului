"""CLI entry point for the graphics generator skill.

Subcommands:
    load     -- Aggregate shotlist.json + manifest.json + channel.md
                and print them to stdout for Claude to consume.
    generate -- Route animation shots to Pillow renderers, produce PNGs,
                update manifest.json.
    status   -- Print generation coverage stats from manifest + shotlist.

Usage:
    PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator load "Duplessis Orphans"
    PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator generate "Duplessis Orphans"
    PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator status "Duplessis Orphans"
"""
import argparse
import io
import json
import os
import sys
import tempfile
from pathlib import Path

from graphics_generator.renderers import COMFYUI_BLOCKS, RENDERER_REGISTRY, is_comfyui_block, render_comfyui


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

    Falls back to .claude/scratch/graphics-generator/{topic} if no match found.

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

    scratch_dir = root / ".claude" / "scratch" / "graphics-generator" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


def _slugify(name: str) -> str:
    """Convert building block name to filename slug."""
    return name.lower().replace(" ", "_").replace("/", "_")


def cmd_load(topic: str) -> None:
    """Aggregate context files and print them to stdout for Claude."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    manifest_path = project_dir / "assets" / "manifest.json"
    channel_path = root / "context" / "channel" / "channel.md"
    prompt_path = (
        root / ".claude" / "skills" / "graphics-generator" / "prompts" / "generation.md"
    )

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

    shotlist_content = shotlist_path.read_text(encoding="utf-8")
    channel_content = channel_path.read_text(encoding="utf-8")

    print("=== Shotlist ===")
    print(shotlist_content)
    print()
    print("---")
    print()

    if manifest_path.exists():
        manifest_content = manifest_path.read_text(encoding="utf-8")
        print("=== Manifest ===")
        print(manifest_content)
    else:
        print("=== Manifest ===")
        print("(No manifest.json found — will be created on generate)")
    print()
    print("---")
    print()

    print("=== Channel DNA ===")
    print(channel_content)
    print()
    print("---")
    print()

    print(f"Generation prompt: {prompt_path}")


def cmd_generate(topic: str, code_gen_only: bool = False) -> None:
    """Route animation shots to renderers, produce PNGs, update manifest."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    if not shotlist_path.exists():
        print(f"Error: shotlist.json not found: {shotlist_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(shotlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {shotlist_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    shots = data.get("shots", [])
    animation_shots = [s for s in shots if s.get("shotlist_type") == "animation"]

    if not animation_shots:
        print("No animation shots found in shotlist.", file=sys.stderr)
        sys.exit(0)

    output_dir = project_dir / "assets" / "vectors"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ComfyUI client if needed
    comfyui_client = None
    comfyui_available = False
    if not code_gen_only:
        from graphics_generator.comfyui.client import ComfyUIClient, ComfyUIUnavailableError

        comfyui_client = ComfyUIClient()
        comfyui_available = comfyui_client.is_available()
        if not comfyui_available:
            # Check if any shots actually need ComfyUI
            comfyui_shots = [s for s in animation_shots if is_comfyui_block(s.get("building_block", ""))]
            if comfyui_shots:
                print(
                    f"Warning: ComfyUI server at {comfyui_client.address} is not available. "
                    f"{len(comfyui_shots)} shots require ComfyUI. "
                    f"Use --code-gen-only to skip ComfyUI blocks.",
                    file=sys.stderr,
                )

    generated: list[dict] = []
    skipped: list[dict] = []
    errors: list[tuple[dict, str]] = []

    for shot in animation_shots:
        shot_id = shot.get("id", "???")
        bb = shot.get("building_block", "")
        slug = _slugify(bb)

        # Check if this is a code-gen (Pillow) block
        renderer = RENDERER_REGISTRY.get(bb)
        if renderer is not None:
            print(f"Generating {shot_id} ({slug})...", file=sys.stderr)
            try:
                out_path = renderer(shot, output_dir)
                generated.append({"shot": shot, "path": out_path})
                print(f"  → {out_path.name}", file=sys.stderr)
            except Exception as exc:
                msg = f"Error rendering {shot_id} ({bb}): {exc}"
                print(msg, file=sys.stderr)
                errors.append((shot, str(exc)))
            continue

        # ComfyUI block handling
        if is_comfyui_block(bb):
            if code_gen_only:
                print(
                    f"Skipping {shot_id} ({bb}) — ComfyUI block (--code-gen-only mode)",
                    file=sys.stderr,
                )
                skipped.append(shot)
                continue

            if not comfyui_available:
                print(
                    f"Skipping {shot_id} ({bb}) — ComfyUI unavailable at {comfyui_client.address}",
                    file=sys.stderr,
                )
                skipped.append(shot)
                continue

            # Render via ComfyUI
            print(f"Generating {shot_id} ({slug}) via ComfyUI...", file=sys.stderr)
            try:
                out_path = render_comfyui(shot, output_dir, comfyui_client)
                generated.append({"shot": shot, "path": out_path, "source": "comfyui"})
                print(f"  → {out_path.name}", file=sys.stderr)
            except Exception as exc:
                msg = f"Error rendering {shot_id} ({bb}) via ComfyUI: {exc}"
                print(msg, file=sys.stderr)
                errors.append((shot, str(exc)))
            continue

        # Unknown building block — skip
        print(
            f"Skipping {shot_id} ({bb}) — no renderer registered",
            file=sys.stderr,
        )
        skipped.append(shot)

    # Update manifest
    _merge_manifest(project_dir, data, generated)

    # Summary
    print(
        f"\nGeneration complete: {len(generated)} generated, "
        f"{len(skipped)} skipped (ComfyUI), {len(errors)} errors",
        file=sys.stderr,
    )

    if errors:
        sys.exit(1)


def _merge_manifest(
    project_dir: Path,
    shotlist_data: dict,
    generated: list[dict],
) -> None:
    """Read existing manifest.json (if any), append new assets, update gaps."""
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
            "folder": "vectors",
            "source": entry.get("source", "code_gen"),
            "source_url": f"local://graphics_generator/{_slugify(bb)}",
            "description": f"{bb} graphic for {shot.get('visual_need', shot_id)}",
            "license": "generated",
            "mapped_shots": [shot_id],
            "acquired_by": "agent_graphics",
        }
        manifest["assets"].append(asset_entry)

    # Update gap statuses
    for gap in manifest.get("gaps", []):
        if gap.get("shot_id") in generated_shot_ids:
            if gap.get("status") == "pending_generation":
                gap["status"] = "filled"

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


def _empty_manifest(shotlist_data: dict) -> dict:
    """Create an empty manifest skeleton."""
    from datetime import datetime, timezone

    return {
        "project": shotlist_data.get("project", ""),
        "generated": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "assets": [],
        "gaps": [],
        "source_summary": {},
    }


def cmd_status(topic: str) -> None:
    """Print generation coverage stats."""
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    if not shotlist_path.exists():
        print(f"Error: shotlist.json not found: {shotlist_path}", file=sys.stderr)
        sys.exit(1)

    try:
        shotlist = json.loads(shotlist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    shots = shotlist.get("shots", [])
    animation_shots = [s for s in shots if s.get("shotlist_type") == "animation"]

    if not animation_shots:
        print("No animation shots in shotlist.")
        return

    # Count by building block
    bb_counts: dict[str, int] = {}
    for shot in animation_shots:
        bb = shot.get("building_block", "unknown")
        bb_counts[bb] = bb_counts.get(bb, 0) + 1

    # Check which have renderers
    pillow_count = 0
    comfyui_count = 0
    for bb, count in sorted(bb_counts.items()):
        if bb in RENDERER_REGISTRY:
            status = "Pillow"
            pillow_count += count
        elif is_comfyui_block(bb):
            status = "ComfyUI"
            comfyui_count += count
        else:
            status = "unknown"
            comfyui_count += count
        print(f"  {bb}: {count} shots [{status}]")

    # Check generated files
    vectors_dir = project_dir / "assets" / "vectors"
    generated_files = list(vectors_dir.glob("*.png")) if vectors_dir.exists() else []

    print(f"\nTotal animation shots: {len(animation_shots)}")
    print(f"  Pillow-routable: {pillow_count}")
    print(f"  ComfyUI (skipped): {comfyui_count}")
    print(f"  Generated files: {len(generated_files)}")


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="graphics_generator",
        description="Graphics generator skill — code-gen flat graphics for animation shots",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files for a topic and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate PNG assets for animation shots",
    )
    generate_parser.add_argument("topic", help="Topic string")
    generate_parser.add_argument(
        "--code-gen-only",
        action="store_true",
        default=False,
        help="Skip ComfyUI blocks — generate only Pillow code-gen assets",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Show generation coverage stats",
    )
    status_parser.add_argument("topic", help="Topic string")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
        elif args.command == "generate":
            cmd_generate(args.topic, code_gen_only=args.code_gen_only)
        elif args.command == "status":
            cmd_status(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
