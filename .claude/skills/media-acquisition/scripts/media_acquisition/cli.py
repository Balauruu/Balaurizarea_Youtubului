"""CLI entry point for the media acquisition skill.

Subcommands:
    load     -- Aggregate shotlist.json + media_urls.md + channel.md
                and print them to stdout for Claude to plan search queries.
    acquire  -- Execute search_plan.json: search, download, build manifest.json, identify gaps.
    status   -- Read manifest.json and print gap analysis summary.

Usage:
    PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition load "Duplessis Orphans"
    PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition acquire "Duplessis Orphans" search_plan.json
    PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition status "Duplessis Orphans"
"""
import argparse
import io
import json
import re
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
    Falls back to .claude/scratch/media-acquisition/{topic} if no match found.

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
    scratch_dir = root / ".claude" / "scratch" / "media-acquisition" / topic
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir


def parse_media_urls(text: str) -> list[dict]:
    """Parse media_urls.md format into structured records.

    Expected format per entry:
        - **URL:** https://example.com/image.jpg
          **Description:** A description of the media.
          **Source:** example.com

    Categories are determined by the ## heading above the entries.

    Args:
        text: Full text content of media_urls.md.

    Returns:
        List of dicts with keys: url, description, source, category.
    """
    results: list[str] = []
    current_category = "uncategorized"

    # Match category headings
    heading_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    # Match URL entries — capture URL, Description, Source across lines
    entry_pattern = re.compile(
        r"-\s+\*\*URL:\*\*\s*(.+?)\s*\n"
        r"\s+\*\*Description:\*\*\s*(.+?)\s*\n"
        r"\s+\*\*Source:\*\*\s*(.+?)(?:\s*\n|$)",
        re.MULTILINE,
    )

    # Split text by headings to track category
    lines = text.split("\n")
    current_pos = 0
    sections: list[tuple[str, str]] = []  # (category, section_text)

    for match in heading_pattern.finditer(text):
        heading_text = match.group(1).strip()
        heading_start = match.start()
        if current_pos < heading_start:
            sections.append((current_category, text[current_pos:heading_start]))
        current_category = heading_text
        current_pos = match.end()

    # Add remaining text
    if current_pos < len(text):
        sections.append((current_category, text[current_pos:]))

    results = []
    for category, section_text in sections:
        for m in entry_pattern.finditer(section_text):
            results.append({
                "url": m.group(1).strip(),
                "description": m.group(2).strip(),
                "source": m.group(3).strip(),
                "category": category,
            })

    return results


def cmd_load(topic: str) -> None:
    """Aggregate context files and print them to stdout for Claude.

    Reads shotlist.json, media_urls.md, and channel.md. Prints each with a
    labeled section separated by --- dividers.

    Args:
        topic: Topic string used to resolve the project directory.

    Exits:
        sys.exit(1) if any required input file is missing.
    """
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)

    shotlist_path = project_dir / "shotlist.json"
    media_urls_path = project_dir / "research" / "media_urls.md"
    channel_path = root / "context" / "channel" / "channel.md"

    # Validate all required input files exist
    missing: list[Path] = []
    for path in (shotlist_path, media_urls_path, channel_path):
        if not path.exists():
            missing.append(path)

    if missing:
        for path in missing:
            print(f"Error: required file not found: {path}", file=sys.stderr)
        sys.exit(1)

    shotlist_content = shotlist_path.read_text(encoding="utf-8")
    media_urls_content = media_urls_path.read_text(encoding="utf-8")
    channel_content = channel_path.read_text(encoding="utf-8")

    # Print labeled context package
    print("=== Shotlist ===")
    print(shotlist_content)
    print()
    print("---")
    print()
    print("=== Media URLs ===")
    print(media_urls_content)
    print()
    print("---")
    print()
    print("=== Channel DNA ===")
    print(channel_content)
    print()
    print("---")
    print()

    # Print paths for downstream reference
    assets_dir = project_dir / "assets"
    manifest_path = assets_dir / "manifest.json"
    print(f"Project directory: {project_dir}")
    print(f"Assets directory: {assets_dir}")
    print(f"Manifest path: {manifest_path}")


def cmd_acquire(topic: str, search_plan_path: str) -> None:
    """Execute search plan: search, download, build manifest.json, identify gaps.

    Args:
        topic: Topic string used to resolve the project directory.
        search_plan_path: Path to search_plan.json file.

    Exits:
        sys.exit(1) if required files are missing or search plan is invalid.
    """
    _ensure_utf8_stdout()
    from media_acquisition.acquire import run_acquire

    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)
    plan_path = Path(search_plan_path)

    # Check shotlist exists
    shotlist_path = project_dir / "shotlist.json"
    if not shotlist_path.exists():
        print(f"Error: shotlist not found: {shotlist_path}", file=sys.stderr)
        sys.exit(1)

    # Resolve project name from shotlist
    try:
        shotlist_data = json.loads(shotlist_path.read_text(encoding="utf-8"))
        project_name = shotlist_data.get("project", topic)
    except (json.JSONDecodeError, KeyError):
        project_name = topic

    # Create asset subdirectories
    assets_dir = project_dir / "assets"
    for folder in ("archival_photos", "archival_footage", "documents", "broll"):
        (assets_dir / folder).mkdir(parents=True, exist_ok=True)

    try:
        run_acquire(project_dir, plan_path, project_name)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_status(topic: str) -> None:
    """Read manifest.json and print gap analysis summary.

    Args:
        topic: Topic string used to resolve the project directory.

    Exits:
        sys.exit(1) if manifest.json is not found or has invalid JSON.
    """
    _ensure_utf8_stdout()
    root = _get_project_root()
    project_dir = resolve_project_dir(root, topic)
    manifest_path = project_dir / "assets" / "manifest.json"

    if not manifest_path.exists():
        print(
            f"No manifest found at {manifest_path}. "
            "Run acquisition first to generate manifest.json.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {manifest_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    # Extract stats
    project_name = data.get("project", "Unknown")
    assets = data.get("assets", [])
    gaps = data.get("gaps", [])
    source_summary = data.get("source_summary", {})

    total_assets = len(assets)
    total_gaps = len(gaps)

    # Gap status breakdown
    pending = sum(1 for g in gaps if g.get("status") == "pending_generation")
    filled = sum(1 for g in gaps if g.get("status") == "filled")
    unfilled = sum(1 for g in gaps if g.get("status") == "unfilled")

    # Unique shots covered by assets
    covered_shots = set()
    for asset in assets:
        for shot_id in asset.get("mapped_shots", []):
            covered_shots.add(shot_id)

    # Print summary
    print(f"=== Media Acquisition Status: {project_name} ===")
    print()
    print(f"Assets: {total_assets}")
    print(f"Shots covered: {len(covered_shots)}")
    print(f"Gaps: {total_gaps}")
    if total_gaps > 0:
        print(f"  pending_generation: {pending}")
        print(f"  filled: {filled}")
        print(f"  unfilled: {unfilled}")
    print()

    # Coverage percentage
    all_gap_shots = {g.get("shot_id") for g in gaps if g.get("shot_id")}
    total_shots = len(covered_shots | all_gap_shots)
    if total_shots > 0:
        coverage = len(covered_shots) / total_shots * 100
        print(f"Coverage: {coverage:.0f}% ({len(covered_shots)}/{total_shots} shots)")
    else:
        print("Coverage: no shots tracked")
    print()

    # Source summary
    if source_summary:
        print("Source Summary:")
        for source, stats in sorted(source_summary.items()):
            searched = stats.get("searched", 0)
            downloaded = stats.get("downloaded", 0)
            print(f"  {source}: {downloaded} downloaded / {searched} searched")


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="media_acquisition",
        description="Media acquisition skill — download assets and manage manifest.json",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load",
        help="Aggregate context files for a topic and print to stdout",
    )
    load_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    acquire_parser = subparsers.add_parser(
        "acquire",
        help="Execute search plan: download assets, build manifest, identify gaps",
    )
    acquire_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")
    acquire_parser.add_argument("search_plan", help="Path to search_plan.json")

    status_parser = subparsers.add_parser(
        "status",
        help="Read manifest.json and print gap analysis summary",
    )
    status_parser.add_argument("topic", help="Topic string (e.g. 'Duplessis Orphans')")

    args = parser.parse_args()

    try:
        if args.command == "load":
            cmd_load(args.topic)
        elif args.command == "acquire":
            cmd_acquire(args.topic, args.search_plan)
        elif args.command == "status":
            cmd_status(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
