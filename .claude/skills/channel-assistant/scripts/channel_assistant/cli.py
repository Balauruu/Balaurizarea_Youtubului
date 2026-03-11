"""CLI entry point for the channel assistant skill.

Provides subcommands: add, scrape, status, migrate, analyze, topics, trends.
"""

import argparse
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .analyzer import (
    compute_channel_stats,
    detect_outliers,
    format_stats_table,
    serialize_videos_for_analysis,
)
from .database import Database
from .registry import Registry
from .scraper import scrape_all_channels, scrape_single_channel
from .migrate import run_migration, delete_old_files
from .topics import load_topic_inputs
from .project_init import load_project_inputs
from .trend_scanner import (
    scrape_autocomplete,
    scrape_search_results,
    get_recent_competitor_videos,
    derive_keywords,
    update_analysis_with_trends,
)


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


def cmd_analyze(args: argparse.Namespace, db: Database, root: Path) -> None:
    """Handle 'analyze' subcommand: compute stats, detect outliers, write report."""
    db.init_db()

    channels = db.get_all_channels()
    if not channels:
        print("No channels in database. Run 'scrape' first.")
        return

    # Freshness check
    now = datetime.now(timezone.utc)
    for ch in channels:
        ch_stats = db.get_channel_stats(ch.youtube_id)
        last_scraped = ch_stats.get("last_scraped")
        if last_scraped:
            try:
                scraped_dt = datetime.fromisoformat(
                    last_scraped.replace("Z", "+00:00")
                )
                age_days = (now - scraped_dt).days
                if age_days > 7:
                    print(
                        f"Warning: {ch.name} data is {age_days} days old "
                        f"(last scraped: {last_scraped[:10]})"
                    )
            except (ValueError, TypeError):
                pass

    # Compute stats and outliers for each channel
    all_stats = []
    all_outliers = []
    all_videos_by_channel: dict[str, list] = {}
    total_video_count = 0

    for ch in channels:
        videos = db.get_videos_by_channel(ch.youtube_id)
        total_video_count += len(videos)

        stats = compute_channel_stats(ch, videos)
        all_stats.append(stats)

        outliers = detect_outliers(ch, videos)
        all_outliers.extend(outliers)

        all_videos_by_channel[ch.name] = videos

    # Sort all outliers by multiplier descending
    all_outliers.sort(key=lambda x: x["multiplier"], reverse=True)

    # Build report
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stats_table = format_stats_table(all_stats)

    report_lines = [
        "# Competitor Analysis Report",
        "",
        f"*Generated: {timestamp}*",
        "",
        "## Channel Stats",
        "",
        stats_table,
        "",
        "## Outlier Videos",
        "",
    ]

    if all_outliers:
        for o in all_outliers:
            report_lines.append(
                f"- **{o['title']}** ({o['channel']}) -- "
                f"{o['views']:,} views -- {o['multiplier']}x median"
            )
    else:
        report_lines.append(
            "No outlier videos detected (threshold: 2x channel median)."
        )

    report_lines.extend([
        "",
        "## Topic Clusters",
        "",
        "<!-- HEURISTIC: To be completed by Claude reasoning over video_data_for_analysis.md -->",
        "",
        "## Title Patterns",
        "",
        "<!-- HEURISTIC: To be completed by Claude reasoning over video_data_for_analysis.md -->",
        "",
    ])

    # Write report
    report_path = root / "context" / "competitors" / "analysis.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    # Write serialized video data for heuristic analysis
    scratch_path = root / ".claude" / "scratch" / "video_data_for_analysis.md"
    scratch_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = serialize_videos_for_analysis(all_videos_by_channel)
    scratch_header = (
        "# Video Data for Heuristic Analysis\n\n"
        "This file contains all competitor video data grouped by channel, "
        "sorted by views descending.\n"
        "Use this data for topic clustering and title pattern analysis.\n\n"
    )
    scratch_path.write_text(scratch_header + serialized, encoding="utf-8")

    # Summary
    print(
        f"Analysis complete. {len(channels)} channels, "
        f"{total_video_count} videos analyzed. "
        f"{len(all_outliers)} outliers found. "
        f"Full report: context/competitors/analysis.md"
    )


def cmd_topics(args: argparse.Namespace, root: Path) -> None:
    """Handle 'topics' subcommand: load context for topic generation.

    Loads competitor analysis, channel DNA, and past topics from disk.
    Prints a structured summary to stdout for Claude to reason over.
    Claude (the agent running this command) then performs the [HEURISTIC]
    generation, scoring, and deduplication steps.

    Does NOT call any LLM API — context-loader only.
    """
    try:
        inputs = load_topic_inputs(root)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'analyze' first to generate context/competitors/analysis.md")
        sys.exit(1)

    analysis = inputs["analysis"]
    channel_dna = inputs["channel_dna"]
    past_topics = inputs["past_topics"]

    # Print Competitor Analysis summary (first 50 lines or full if short)
    analysis_lines = analysis.splitlines()
    print("## Competitor Analysis Summary")
    print()
    if len(analysis_lines) <= 50:
        print(analysis)
    else:
        print("\n".join(analysis_lines[:50]))
        print(f"... [{len(analysis_lines) - 50} more lines — full file at context/competitors/analysis.md]")
    print()

    # Print Past Topics list
    print("## Past Topics")
    print()
    if past_topics:
        for title in past_topics:
            print(f"- {title}")
    else:
        print("None yet")
    print()

    # Print Channel DNA (content pillars section)
    print("## Channel DNA")
    print()
    # Extract just the content pillars section if possible, else print full content
    pillar_start = channel_dna.find("## Core Content Pillars")
    criteria_end = channel_dna.find("## Differentiation Strategy")
    if pillar_start != -1 and criteria_end != -1:
        print(channel_dna[pillar_start:criteria_end].strip())
    elif pillar_start != -1:
        # Print from pillars to end of topic selection criteria
        print(channel_dna[pillar_start:].strip()[:1500])
    else:
        print(channel_dna[:1500])
    print()

    # Print generation prompt path
    prompt_path = root / ".claude" / "skills" / "channel-assistant" / "prompts" / "topic_generation.md"
    print("## Generation Prompt")
    print()
    print(f"Prompt file: {prompt_path}")
    print()

    # Print output target
    output_path = root / "context" / "topics" / "topic_briefs.md"
    print("## Output Target")
    print()
    print(f"{output_path}")
    print()

    # Instruction line for Claude
    print(
        "Context loaded. Use the generation prompt to generate 10-15 topic briefs. "
        "Write results using write_topic_briefs() and format_chat_cards() "
        "from channel_assistant.topics"
    )

    # Project initialization guidance (printed after topic briefs are generated
    # and the user selects a topic number)
    prompt_path = root / ".claude" / "skills" / "channel-assistant" / "prompts" / "project_init.md"
    print()
    print("## Project Initialization")
    print()
    print("After generating topic briefs and the user selects a topic by number [N]:")
    print("1. Call load_project_inputs(root, N) to get the selected brief and title patterns")
    print("2. Read the project_init prompt: .claude/skills/channel-assistant/prompts/project_init.md")
    print("3. Generate 5 title variants + 1 description (HEURISTIC)")
    print("4. Call init_project() with structured data (DETERMINISTIC)")
    print()
    print(f"Prompt file: {prompt_path}")


def _extract_section(content: str, header: str) -> str:
    """Extract text between '## Header' and next '## ' heading or EOF.

    Returns empty string if header not found.
    """
    pattern = re.compile(
        r"^## " + re.escape(header) + r"\s*\n(.*?)(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def cmd_trends(args: argparse.Namespace, db: Database, root: Path) -> None:
    """Handle 'trends' subcommand: scan YouTube trends and detect content gaps.

    Loads channel DNA and topic clusters, derives keywords, scrapes autocomplete
    and search results for each keyword, queries SQLite for 30-day competitor
    convergence data, then prints structured context to stdout for Claude
    to perform heuristic gap scoring and convergence framing.

    Does NOT call any LLM API — context-loader only.
    """
    db.init_db()

    # Load channel DNA
    channel_dna_path = root / "context" / "channel" / "channel.md"
    if not channel_dna_path.exists():
        print(f"Error: Channel DNA not found: {channel_dna_path}", file=sys.stderr)
        sys.exit(1)
    channel_dna = channel_dna_path.read_text(encoding="utf-8")

    # Load analysis.md and extract topic clusters (text between ## Topic Clusters and next ##)
    analysis_path = root / "context" / "competitors" / "analysis.md"
    topic_clusters: list[str] = []
    if analysis_path.exists():
        analysis_content = analysis_path.read_text(encoding="utf-8")
        cluster_section = _extract_section(analysis_content, "Topic Clusters")
        if cluster_section:
            # Parse cluster names: lines starting with "**" or numbered "1. **" or "- **"
            cluster_pattern = re.compile(r"(?:^[-\d.]*\s*)\*\*([^*]+)\*\*", re.MULTILINE)
            matches = cluster_pattern.findall(cluster_section)
            topic_clusters = [m.strip() for m in matches if m.strip()]

    # Derive keywords from channel DNA + topic clusters
    keywords = derive_keywords(channel_dna, topic_clusters)
    n = len(keywords)
    print(f"Scanning {n} keywords...", file=sys.stderr)

    # Scrape autocomplete and search results for each keyword
    all_autocomplete: dict[str, list[str]] = {}
    all_search_results: dict[str, list[dict]] = {}

    for i, keyword in enumerate(keywords, start=1):
        # Jittered delay between requests (skip delay before first request)
        if i > 1:
            time.sleep(random.uniform(0.5, 1.5))

        suggestions = scrape_autocomplete(keyword)
        results = scrape_search_results(keyword)

        all_autocomplete[keyword] = suggestions
        all_search_results[keyword] = results

        print(
            f"  [{i}/{n}] {keyword}: {len(suggestions)} suggestions, {len(results)} results",
            file=sys.stderr,
        )

    # Query 30-day competitor video convergence data
    competitor_videos = get_recent_competitor_videos(db, days=30)

    # Print structured context to stdout for Claude heuristic reasoning
    print("## Autocomplete Suggestions")
    print()
    for keyword, suggestions in all_autocomplete.items():
        print(f"### {keyword}")
        if suggestions:
            for s in suggestions:
                print(f"- {s}")
        else:
            print("- (no suggestions)")
        print()

    print("## Search Results")
    print()
    for keyword, results in all_search_results.items():
        print(f"### {keyword}")
        if results:
            for r in results:
                print(
                    f"- {r['title']} | {r['channel']} | {r.get('published_text', '')} | {r.get('views_text', '')}"
                )
        else:
            print("- (no results)")
        print()

    print("## Recent Competitor Videos (30-day window)")
    print()
    if competitor_videos:
        for v in competitor_videos:
            print(f"- {v['title']} | {v['channel_name']} | {v['upload_date']}")
    else:
        print("- (no competitor videos in last 30 days)")
    print()

    # Print prompt path
    prompt_path = root / ".claude" / "skills" / "channel-assistant" / "prompts" / "trends_analysis.md"
    print("## Prompt")
    print()
    print(f"Prompt file: {prompt_path}")
    print()

    # Print output target
    print("## Output Target")
    print()
    print("context/competitors/analysis.md (trend sections)")
    print()

    # Instruction line for Claude
    print(
        "Context loaded. Use the trends analysis prompt to score content gaps, "
        "frame convergence alerts, and synthesize trending topics. "
        "Write results using update_analysis_with_trends() from channel_assistant.trend_scanner"
    )


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

    # analyze subcommand
    subparsers.add_parser(
        "analyze", help="Analyze competitor channels: stats, outliers, and data export"
    )

    # topics subcommand
    subparsers.add_parser(
        "topics", help="Load context for topic generation (10-15 scored briefs)"
    )

    # trends subcommand
    subparsers.add_parser(
        "trends", help="Scan YouTube trends and detect content gaps"
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
    elif args.command == "analyze":
        cmd_analyze(args, db, root)
    elif args.command == "topics":
        cmd_topics(args, root)
    elif args.command == "trends":
        cmd_trends(args, db, root)


if __name__ == "__main__":
    main()
