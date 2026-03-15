"""CLI entry point for the visual orchestrator skill.

Subcommands:
    load     -- Aggregate context files (Script.md, VISUAL_STYLE_GUIDE.md, channel.md)
                and print them to stdout for Claude to consume before shotlist generation.
    validate -- Read shotlist.json from project dir and run schema validation.

Usage:
    PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"
    PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator validate "Duplessis Orphans"
"""
import argparse
import io
import json
import sys
from pathlib import Path


def _ensure_utf8_stdout() -> None:
    """Reconfigure stdout to use UTF-8 encoding on Windows."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )


def _get_project_root() -> Path:
    """Walk up from this file looking for CLAUDE.md as the project root marker.

    Returns:
        Project root Path. Falls back to cwd if CLAUDE.md not found.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def resolve_project_dir(root: Path, topic: str) -> Path:
    """Find the project directory for a topic by case-insensitive substring match.

    Searches projects/ subdirectories for a name containing topic (case-insensitive).
    Falls back to .claude/scratch/visual-orchestrator/{topic} if no match found.

    Args:
        root: Project root directory.
        topic: Topic string to match against directory names.

    Returns:
        Matching project directory Path (or scratch fallback).

    Raises:
        ValueError: When multiple project directories match the topic string.
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

    # Fallback: scratch directory
    scratch_dir = root / ".claude" / "scratch" / "visual-orchestrator" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


def _resolve_guide_path(root: Path, guide: str | None) -> Path:
    """Resolve the VISUAL_STYLE_GUIDE.md path.

    If --guide is provided, looks for that name under context/visual-references/.
    Otherwise, picks the first directory found.

    Args:
        root: Project root directory.
        guide: Optional guide directory name.

    Returns:
        Path to VISUAL_STYLE_GUIDE.md.

    Raises:
        ValueError: When the guide directory doesn't exist or no guides are found.
    """
    vr_dir = root / "context" / "visual-references"

    if guide:
        guide_path = vr_dir / guide / "VISUAL_STYLE_GUIDE.md"
        if not guide_path.exists():
            raise ValueError(
                f"Guide not found: {guide_path}. "
                f"Available guides: {[d.name for d in vr_dir.iterdir() if d.is_dir()]}"
            )
        return guide_path

    # Default: first directory in visual-references/
    if not vr_dir.is_dir():
        raise ValueError(f"No visual-references directory found at {vr_dir}")

    dirs = sorted(d for d in vr_dir.iterdir() if d.is_dir())
    if not dirs:
        raise ValueError(f"No guide directories found in {vr_dir}")

    return dirs[0] / "VISUAL_STYLE_GUIDE.md"


def cmd_load(topic: str, guide: str | None = None) -> None:
    """Aggregate context files and print them to stdout for Claude.

    Reads Script.md, VISUAL_STYLE_GUIDE.md, and channel.md. Prints each with a
    labeled section separated by --- dividers. Also prints the resolved output
    path for shotlist.json and the generation prompt path.

    Args:
        topic: Topic string used to resolve the project directory.
        guide: Optional guide directory name under context/visual-references/.

    Exits:
        sys.exit(1) if any required input file is missing.
    """
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    script_path = project_dir / "Script.md"
    guide_path = _resolve_guide_path(root, guide)
    channel_path = root / "context" / "channel" / "channel.md"
    output_path = project_dir / "shotlist.json"
    prompt_path = (
        root / ".claude" / "skills" / "visual-orchestrator" / "prompts" / "generation.md"
    )

    # Validate all required input files exist
    missing: list[Path] = []
    for path in (script_path, guide_path, channel_path):
        if not path.exists():
            missing.append(path)

    if missing:
        for path in missing:
            print(f"Error: required file not found: {path}", file=sys.stderr)
        sys.exit(1)

    script_content = script_path.read_text(encoding="utf-8")
    guide_content = guide_path.read_text(encoding="utf-8")
    channel_content = channel_path.read_text(encoding="utf-8")

    # Print labeled context package
    print("=== Script ===")
    print(script_content)
    print()
    print("---")
    print()
    print(f"=== Visual Style Guide ({guide_path.parent.name}) ===")
    print(guide_content)
    print()
    print("---")
    print()
    print("=== Channel DNA ===")
    print(channel_content)
    print()
    print("---")
    print()
    print(f"Output path: {output_path}")
    print(f"Generation prompt: {prompt_path}")


def cmd_validate(topic: str) -> None:
    """Validate shotlist.json against the schema contract.

    Reads shotlist.json from the project directory and runs schema validation.
    Prints errors to stderr and exits 1 if any validation errors are found.

    Args:
        topic: Topic string used to resolve the project directory.

    Exits:
        sys.exit(1) if shotlist.json is missing or has validation errors.
    """
    from visual_orchestrator.schema import validate_shotlist

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

    errors = validate_shotlist(data)

    if errors:
        print(f"Validation FAILED — {len(errors)} error(s):", file=sys.stderr)
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Validation PASSED — shotlist.json is valid ({len(data.get('shots', []))} shots)")


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="visual_orchestrator",
        description="Visual orchestrator skill — shotlist generation context loader and validator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files for a topic and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")
    load_parser.add_argument(
        "--guide",
        default=None,
        help="Name of visual reference directory to use (default: first found)",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate shotlist.json against the schema contract",
    )
    validate_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic, guide=args.guide)
        elif args.command == "validate":
            cmd_validate(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
