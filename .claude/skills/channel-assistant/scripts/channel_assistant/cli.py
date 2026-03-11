"""CLI entry point for the channel assistant skill.

Provides subcommands: add, scrape, status, migrate.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .database import Database
from .registry import Registry
from .scraper import scrape_all_channels, scrape_single_channel
from .migrate import run_migration, delete_old_files


def _get_project_root() -> Path:
    """Find the project root (directory containing CLAUDE.md)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    # Fallback to cwd
    return Path.cwd()


def _default_registry_path(root: Path) -> Path:
    return root / "context" / "competitors" / "competitors.json"


def _default_db_path(root: Path) -> Path:
    return root / "data" / "channel_assistant.db"


def cmd_add(args: argparse.Namespace, registry: Registry) -> None:
    """Handle 'add' subcommand: register a new competitor channel."""
    url_or_handle = args.url.strip()

    # Resolve channel name via a quick yt-dlp call
    print(f"Resolving channel info for {url_or_handle}...")
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--skip-download",
                "--no-warnings",
                "--playlist-items", "1",
                url_or_handle,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip().split("\n")[0])
            channel_name = data.get("channel", "Unknown")
            handle = data.get("uploader_id", "")
            channel_url = data.get("channel_url", url_or_handle)
        else:
            print(f"Warning: Could not resolve channel info. Using URL as-is.")
            channel_name = url_or_handle
            handle = url_or_handle if url_or_handle.startswith("@") else ""
            channel_url = url_or_handle
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        print(f"Warning: Could not resolve channel info. Using URL as-is.")
        channel_name = url_or_handle
        handle = url_or_handle if url_or_handle.startswith("@") else ""
        channel_url = url_or_handle

    # Ensure handle starts with @
    youtube_id = handle if handle.startswith("@") else f"@{handle}" if handle else f"@{channel_name.replace(' ', '')}"

    try:
        entry = registry.add(
            name=channel_name,
            youtube_id=youtube_id,
            url=channel_url,
        )
        print(f"Added: {entry['name']} ({entry['youtube_id']})")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_scrape(args: argparse.Namespace, registry: Registry, db: Database) -> None:
    """Handle 'scrape' subcommand: scrape all or a specific channel."""
    db.init_db()

    if args.name:
        result = scrape_single_channel(args.name, registry, db)
    else:
        result = scrape_all_channels(registry, db)

    if result and result.get("failed"):
        sys.exit(1)


def cmd_status(args: argparse.Namespace, db: Database) -> None:
    """Handle 'status' subcommand: show channel summary table."""
    db.init_db()

    channels = db.get_all_channels()
    if not channels:
        print("No channels in database. Run 'scrape' or 'migrate' first.")
        return

    # Header
    name_width = max(len(ch.name) for ch in channels)
    name_width = max(name_width, len("Channel"))
    header = (
        f"{'Channel':<{name_width}}  "
        f"{'Videos':>6}  "
        f"{'Last Scraped':>12}  "
        f"{'Latest Upload':>13}"
    )
    separator = "-" * len(header)

    print(header)
    print(separator)

    for ch in channels:
        stats = db.get_channel_stats(ch.youtube_id)
        video_count = stats.get("video_count", 0)
        last_scraped = stats.get("last_scraped", "")
        latest_upload = stats.get("latest_upload", "")

        # Truncate timestamps to date only
        last_scraped_short = last_scraped[:10] if last_scraped else "never"
        latest_upload_short = latest_upload[:10] if latest_upload else "n/a"

        print(
            f"{ch.name:<{name_width}}  "
            f"{video_count:>6}  "
            f"{last_scraped_short:>12}  "
            f"{latest_upload_short:>13}"
        )


def cmd_migrate(args: argparse.Namespace, db: Database, root: Path) -> None:
    """Handle 'migrate' subcommand: import existing competitor data."""
    print("Migrating existing competitor data...")
    run_migration(db, project_root=root)

    print("\nCleaning up old files...")
    delete_old_files(project_root=root)
    print("\nMigration complete.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Channel Assistant - Competitor tracking and analysis"
    )
    subparsers = parser.add_subparsers(dest="command")

    # add subcommand
    add_parser = subparsers.add_parser(
        "add", help="Register a new competitor channel"
    )
    add_parser.add_argument(
        "url", help="YouTube channel URL or @handle"
    )

    # scrape subcommand
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape all or a specific channel"
    )
    scrape_parser.add_argument(
        "name", nargs="?", help="Channel name (optional, scrapes all if omitted)"
    )

    # status subcommand
    subparsers.add_parser(
        "status", help="Show channel summary table"
    )

    # migrate subcommand
    subparsers.add_parser(
        "migrate", help="Migrate existing competitor data into SQLite"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup paths
    root = _get_project_root()
    registry = Registry(_default_registry_path(root))
    db = Database(_default_db_path(root))

    if args.command == "add":
        cmd_add(args, registry)
    elif args.command == "scrape":
        cmd_scrape(args, registry, db)
    elif args.command == "status":
        cmd_status(args, db)
    elif args.command == "migrate":
        cmd_migrate(args, db, root)


if __name__ == "__main__":
    main()
