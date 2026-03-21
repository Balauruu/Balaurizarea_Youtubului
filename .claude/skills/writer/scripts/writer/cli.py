"""CLI entry point for the writer skill.

Subcommands:
    load  -- Aggregate context files (Research.md, STYLE_PROFILE.md, channel.md)
              and print them to stdout for Claude to consume before script generation.

Usage:
    PYTHONPATH=.claude/skills/writer/scripts python -m writer load "Duplessis Orphans"
"""
import argparse
import sys
from pathlib import Path


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
    Falls back to .claude/scratch/writer/{topic} if no match found.

    Args:
        root: Project root directory.
        topic: Topic string to match against directory names.

    Returns:
        Matching project directory Path (or scratch fallback). Does not guarantee
        Research.md exists inside it.

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
    scratch_dir = root / ".claude" / "scratch" / "writer" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


def cmd_load(topic: str) -> None:
    """Aggregate context files and print them to stdout for Claude.

    Reads Research.md, STYLE_PROFILE.md, and channel.md. Prints each with a
    labeled section separated by --- dividers. Also prints the resolved output
    path for Script.md and the generation prompt path.

    Args:
        topic: Topic string used to resolve the project directory.

    Exits:
        sys.exit(1) if any required input file is missing.
    """
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    research_path = project_dir / "research" / "Research.md"
    style_path = root / "reference" / "voice" / "WRITTING_STYLE_PROFILE.md"
    channel_path = root / "strategy" / "channel" / "channel.md"
    output_path = project_dir / "Script.md"
    prompt_path = root / ".claude" / "skills" / "writer" / "prompts" / "generation.md"

    # Validate all required input files exist
    missing: list[Path] = []
    for path in (research_path, style_path, channel_path):
        if not path.exists():
            missing.append(path)

    if missing:
        for path in missing:
            print(f"Error: required file not found: {path}", file=sys.stderr)
        sys.exit(1)

    research_content = research_path.read_text(encoding="utf-8")
    style_content = style_path.read_text(encoding="utf-8")
    channel_content = channel_path.read_text(encoding="utf-8")

    # Print labeled context package
    print("=== Research Dossier ===")
    print(research_content)
    print()
    print("---")
    print()
    print("=== Style Profile ===")
    print(style_content)
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


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="writer",
        description="Writer skill — documentary script generation context loader",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files for a topic and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
