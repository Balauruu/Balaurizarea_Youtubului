"""CLI entry point for the researcher skill.

Subcommands:
    survey  — Pass 1: resolve output dir, fetch initial URLs, write src_*.json files.

Usage:
    PYTHONPATH=.claude/skills/researcher/scripts python -m researcher survey "Jonestown Massacre"
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from researcher.fetcher import fetch_with_retry
from researcher.url_builder import (
    _get_project_root,
    build_survey_urls,
    resolve_output_dir,
)

logger = logging.getLogger(__name__)


def cmd_survey(topic: str) -> None:
    """Run a survey pass for a topic.

    Steps:
      a. Resolve project root.
      b. Resolve output directory (project research/ or standalone scratch).
      c. Clean previous src_*.json and source_manifest.json from scratch dir.
      d. Build initial URL list for topic.
      e. Fetch each URL, write result to src_NNN.json.
      f. Write source_manifest.json (lightweight index, no content field).
      g. Print summary.

    Args:
        topic: Topic string to research (e.g. "Jonestown Massacre").
    """
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)
    print(f"Output directory: {output_dir}")

    # Clean previous run artifacts from output dir
    for old_file in output_dir.glob("src_*.json"):
        old_file.unlink()
    manifest_path = output_dir / "source_manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()

    urls = build_survey_urls(topic)
    sources = []
    succeeded = 0
    failed = 0
    skipped = 0

    for idx, url in enumerate(urls, start=1):
        print(f"  [{idx}/{len(urls)}] Fetching {url} ...", end=" ", flush=True)
        result = fetch_with_retry(url)

        status = result["fetch_status"]
        word_count = len(result["content"].split()) if result["content"] else 0

        if status == "ok":
            succeeded += 1
            print(f"ok ({word_count} words)")
        elif status == "skipped_tier3":
            skipped += 1
            print("skipped (tier 3)")
        else:
            failed += 1
            print(f"failed — {result['error']}")

        # Write full source file (includes content)
        src_filename = f"src_{idx:03d}.json"
        src_data = {
            "index": idx,
            "url": url,
            "tier": _get_tier_from_url(url),
            "word_count": word_count,
            "fetch_status": status,
            "error": result["error"],
            "content": result["content"],
        }
        (output_dir / src_filename).write_text(
            json.dumps(src_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Lightweight entry for manifest (no content field)
        sources.append({
            "index": idx,
            "filename": src_filename,
            "url": url,
            "tier": src_data["tier"],
            "word_count": word_count,
            "fetch_status": status,
        })

    # Write source manifest
    manifest = {
        "topic": topic,
        "run_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": sources,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total = len(urls)
    print(
        f"\nSurvey complete: {total} sources — "
        f"{succeeded} succeeded, {failed} failed, {skipped} skipped"
    )
    print(f"Manifest: {manifest_path}")


def _get_tier_from_url(url: str) -> int:
    """Return tier for a URL using tiers.classify_domain."""
    from researcher.tiers import classify_domain  # noqa: PLC0415
    return classify_domain(url)


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="researcher",
        description="Researcher skill — documentary video research pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # survey subcommand
    survey_parser = subparsers.add_parser(
        "survey",
        help="Pass 1: fetch initial sources for a topic",
    )
    survey_parser.add_argument(
        "topic",
        help="Topic string (e.g. 'Jonestown Massacre')",
    )

    args = parser.parse_args()

    if args.command == "survey":
        try:
            cmd_survey(args.topic)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
