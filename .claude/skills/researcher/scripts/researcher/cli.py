"""CLI entry point for the researcher skill.

Subcommands:
    survey  — Pass 1: resolve output dir, fetch initial URLs, write src_*.json files.

Usage:
    PYTHONPATH=.claude/skills/researcher/scripts python -m researcher survey "Jonestown Massacre"
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from researcher.fetcher import fetch_with_retry
from researcher.url_builder import (
    _get_project_root,
    build_survey_urls,
    make_ddg_url,
    resolve_output_dir,
)

logger = logging.getLogger(__name__)

_WIKI_NOISE_HEADINGS: frozenset[str] = frozenset({
    "references", "see also", "notes", "external links",
    "bibliography", "further reading", "citations",
})


def _strip_wiki_noise(markdown: str) -> str:
    """Remove Wikipedia boilerplate sections from the end of markdown content.

    Removes everything from the first occurrence of a noise heading to the end
    of the document. If stripping would remove more than 50% of the content,
    returns the original markdown unchanged (pitfall guard).

    Args:
        markdown: Markdown string to clean.

    Returns:
        Cleaned markdown string.
    """
    if not markdown:
        return markdown

    lines = markdown.splitlines()
    cut_line = None

    for i, line in enumerate(lines):
        stripped = line.strip().lstrip("#").strip().lower()
        if stripped in _WIKI_NOISE_HEADINGS:
            cut_line = i
            break

    if cut_line is None:
        return markdown

    stripped_content = "\n".join(lines[:cut_line])

    # Pitfall guard: if stripped < 50% of original word count, skip stripping
    original_words = len(markdown.split())
    stripped_words = len(stripped_content.split())
    if original_words > 0 and stripped_words < (original_words * 0.5):
        return markdown

    return stripped_content


async def _fetch_ddg_with_links(url: str) -> dict:
    """Fetch a DDG HTML page and extract all links using crawl4ai.

    Args:
        url: DuckDuckGo HTML endpoint URL.

    Returns:
        dict with keys: success (bool), links (dict), content (str), error (str).
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode  # noqa: PLC0415
    browser_conf = BrowserConfig(
        browser_type="chromium",
        headless=True,
        use_persistent_context=False,
        verbose=False,
    )
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extract_links=True)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)
    return {
        "success": result.success,
        "links": result.links if result.success else {},
        "content": result.markdown.raw_markdown if result.success else "",
        "error": result.error_message or "",
    }


def _parse_ddg_result_urls(ddg_result: dict, max_urls: int = 12) -> list[str]:
    """Extract non-DDG external HTTPS URLs from a DDG crawl result.

    Filters out Tier 3 social domains and any duckduckgo.com URLs.
    Handles DDG redirect URLs in format "/l/?uddg=<encoded>".

    Args:
        ddg_result: Result dict from _fetch_ddg_with_links.
        max_urls: Maximum number of URLs to return.

    Returns:
        List of external URL strings (up to max_urls).
    """
    from researcher.tiers import classify_domain, TIER_3_DOMAINS  # noqa: PLC0415

    external_links = ddg_result.get("links", {}).get("external", [])
    if not external_links:
        # Some crawl4ai versions may return a list rather than list-of-dicts
        external_links = []

    collected: list[str] = []

    for link in external_links:
        # link may be a dict with "href" key or a plain string
        if isinstance(link, dict):
            href = link.get("href", "")
        else:
            href = str(link)

        if not href:
            continue

        # Handle DDG redirect URLs: /l/?uddg=<encoded_url>
        if not href.startswith("https://"):
            try:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)
                uddg = qs.get("uddg", [None])[0]
                if uddg and uddg.startswith("https://"):
                    href = uddg
                else:
                    continue
            except Exception:
                continue

        # Skip DDG itself
        if "duckduckgo.com" in href:
            continue

        # Skip Tier 3 social domains
        domain = urlparse(href).hostname or ""
        domain = domain.removeprefix("www.")
        if domain in TIER_3_DOMAINS:
            continue

        collected.append(href)
        if len(collected) >= max_urls:
            break

    return collected


def _print_summary_table(sources: list[dict]) -> None:
    """Print a formatted summary table of survey sources to stdout.

    Args:
        sources: List of source entry dicts (each has index, domain, tier,
                 word_count, fetch_status).
    """
    col_widths = {
        "#": 4,
        "Domain": 35,
        "Tier": 6,
        "Words": 8,
        "Status": 10,
    }

    header = (
        f"{'#':<{col_widths['#']}}"
        f"{'Domain':<{col_widths['Domain']}}"
        f"{'Tier':<{col_widths['Tier']}}"
        f"{'Words':<{col_widths['Words']}}"
        f"{'Status':<{col_widths['Status']}}"
    )
    separator = "-" * len(header)

    print()
    print(header)
    print(separator)

    succeeded = 0
    failed = 0
    skipped = 0

    for src in sources:
        idx = src.get("index", "")
        domain = src.get("domain", "")[:col_widths["Domain"] - 1]
        tier = src.get("tier", "")
        words = src.get("word_count", 0)
        status = src.get("fetch_status", "")

        if status == "ok":
            succeeded += 1
        elif status == "skipped_tier3":
            skipped += 1
            status = "skipped"
        else:
            failed += 1

        print(
            f"{str(idx):<{col_widths['#']}}"
            f"{domain:<{col_widths['Domain']}}"
            f"{str(tier):<{col_widths['Tier']}}"
            f"{str(words):<{col_widths['Words']}}"
            f"{status:<{col_widths['Status']}}"
        )

    total = len(sources)
    print(separator)
    print(f"Total: {total} — {succeeded} succeeded, {failed} failed, {skipped} skipped")
    print()


def cmd_survey(topic: str) -> None:
    """Run a survey pass for a topic.

    Steps:
      a. Resolve project root.
      b. Resolve output directory (project research/ or standalone scratch).
      c. Clean previous src_*.json and source_manifest.json from output dir.
      d. Fetch Wikipedia URL.
      e. Fetch DDG HTML page and extract result URLs.
      f. Fetch all URLs, write result to src_NNN.json with domain field.
      g. Print summary table.
      h. Write source_manifest.json (lightweight index, no content field).
      i. Print manifest path.

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

    # Step 1: Get Wikipedia URL
    wikipedia_url = build_survey_urls(topic)[0]

    # Step 2: Fetch DDG HTML and extract result URLs
    ddg_urls: list[str] = []
    try:
        ddg_result = asyncio.run(_fetch_ddg_with_links(make_ddg_url(topic)))
        ddg_urls = _parse_ddg_result_urls(ddg_result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DDG link extraction failed: %s", exc)

    # DDG fallback: if < 3 URLs extracted, try ddgs library
    if len(ddg_urls) < 3:
        try:
            from ddgs import DDGS  # noqa: PLC0415
            ddg_urls = [r["href"] for r in DDGS().text(topic, max_results=12) if r.get("href")]
        except ImportError:
            logger.warning("ddgs library not installed — proceeding with %d DDG URLs", len(ddg_urls))
        except Exception as exc:  # noqa: BLE001
            logger.warning("ddgs fallback failed: %s", exc)

    # Step 3: Build final URL list (Wikipedia first, then DDG results)
    # DDG HTML page itself is NEVER added to all_urls
    all_urls = [wikipedia_url] + ddg_urls

    sources = []

    for idx, url in enumerate(all_urls, start=1):
        print(f"  [{idx}/{len(all_urls)}] Fetching {url} ...", end=" ", flush=True)
        result = fetch_with_retry(url)

        status = result["fetch_status"]
        content = result["content"] or ""

        # Apply noise stripping to all content
        content = _strip_wiki_noise(content)
        word_count = len(content.split()) if content else 0

        domain = urlparse(url).hostname or ""
        domain = domain.removeprefix("www.")

        if status == "ok":
            print(f"ok ({word_count} words)")
        elif status == "skipped_tier3":
            print("skipped (tier 3)")
        else:
            print(f"failed — {result['error']}")

        # Write full source file (includes content, domain)
        src_filename = f"src_{idx:03d}.json"
        src_data = {
            "index": idx,
            "url": url,
            "domain": domain,
            "tier": _get_tier_from_url(url),
            "word_count": word_count,
            "fetch_status": status,
            "error": result["error"],
            "content": content,
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
            "domain": domain,
            "tier": src_data["tier"],
            "word_count": word_count,
            "fetch_status": status,
        })

    # Print summary table before manifest line
    _print_summary_table(sources)

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

    print(f"Manifest: {manifest_path}")


def _get_tier_from_url(url: str) -> int:
    """Return tier for a URL using tiers.classify_domain."""
    from researcher.tiers import classify_domain  # noqa: PLC0415
    return classify_domain(url)


def cmd_deepen(topic: str) -> None:
    """Pass 2: fetch targeted primary sources from evaluated source manifest.

    Stub — full implementation in Task 2.

    Args:
        topic: Topic string (same as used for survey).
    """
    raise NotImplementedError


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
