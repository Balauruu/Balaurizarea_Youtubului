"""CLI entry point for the researcher skill.

Subcommands:
    survey  — Pass 1: resolve output dir, fetch initial URLs, write src_*.json files.
    deepen  — Pass 2: fetch targeted primary sources from evaluated manifest.
    write   — Pass 3: aggregate sources into synthesis_input.md.

Usage:
    PYTHONPATH=.claude/skills/researcher/scripts python -m researcher survey "Jonestown Massacre"
    PYTHONPATH=.claude/skills/researcher/scripts python -m researcher deepen "Jonestown Massacre"
    PYTHONPATH=.claude/skills/researcher/scripts python -m researcher write "Jonestown Massacre"
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
from researcher.tiers import TIER_3_DOMAINS, classify_domain
from researcher.url_builder import (
    _get_project_root,
    build_survey_urls,
    make_ddg_url,
    resolve_output_dir,
)
from researcher.writer import build_synthesis_input, load_source_files, write_synthesis_input

logger = logging.getLogger(__name__)

_WIKI_NOISE_HEADINGS: frozenset[str] = frozenset({
    "references", "see also", "notes", "external links",
    "bibliography", "further reading", "citations",
})


def _strip_trailing_sections(markdown: str) -> str:
    """Remove boilerplate trailing sections (references, see also, etc.) from markdown.

    Cuts from the first noise heading to end of document.
    Returns original if stripping would remove >50% of content.
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

    original_words = len(markdown.split())
    stripped_words = len(stripped_content.split())
    if original_words > 0 and stripped_words < (original_words * 0.5):
        return markdown

    return stripped_content


async def _fetch_ddg_with_links(url: str) -> dict:
    """Fetch a DDG HTML page and extract all links using crawl4ai."""
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

    Filters out Tier 3 social domains and duckduckgo.com URLs.
    Handles DDG redirect URLs in format "/l/?uddg=<encoded>".
    """
    external_links = ddg_result.get("links", {}).get("external", [])
    if not external_links:
        external_links = []

    collected: list[str] = []

    for link in external_links:
        href = link.get("href", "") if isinstance(link, dict) else str(link)
        if not href:
            continue

        # Handle DDG redirect URLs
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

        if "duckduckgo.com" in href:
            continue

        domain = urlparse(href).hostname or ""
        domain = domain.removeprefix("www.")
        if domain in TIER_3_DOMAINS:
            continue

        collected.append(href)
        if len(collected) >= max_urls:
            break

    return collected


def _print_summary_table(sources: list[dict]) -> None:
    """Print a formatted summary table of sources to stdout."""
    col_widths = {"#": 4, "Domain": 35, "Tier": 6, "Words": 8, "Status": 10}

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
            f"{str(src.get('index', '')):<{col_widths['#']}}"
            f"{domain:<{col_widths['Domain']}}"
            f"{str(tier):<{col_widths['Tier']}}"
            f"{str(words):<{col_widths['Words']}}"
            f"{status:<{col_widths['Status']}}"
        )

    print(separator)
    print(f"Total: {len(sources)} — {succeeded} succeeded, {failed} failed, {skipped} skipped")
    print()


def _fetch_and_save(
    urls: list[str],
    output_dir: Path,
    prefix: str,
    pass_label: str,
) -> list[dict]:
    """Fetch a list of URLs, save each as JSON, return manifest entries.

    Shared logic used by both cmd_survey and cmd_deepen.

    Args:
        urls: URLs to fetch.
        output_dir: Directory to write JSON files into.
        prefix: Filename prefix (e.g. "src" or "pass2").
        pass_label: Label for progress display (e.g. "pass2").

    Returns:
        List of lightweight manifest entries (no content field).
    """
    sources: list[dict] = []

    for idx, url in enumerate(urls, start=1):
        print(f"  [{pass_label} {idx}/{len(urls)}] Fetching {url} ...", end=" ", flush=True)
        result = fetch_with_retry(url)

        status = result["fetch_status"]
        content = _strip_trailing_sections(result["content"] or "")
        word_count = len(content.split()) if content else 0

        domain = urlparse(url).hostname or ""
        domain = domain.removeprefix("www.")
        tier = classify_domain(url)

        if status == "ok":
            print(f"ok ({word_count} words)")
        elif status == "skipped_tier3":
            print("skipped (tier 3)")
        else:
            print(f"failed — {result['error']}")

        # Write full source file
        filename = f"{prefix}_{idx:03d}.json"
        src_data = {
            "index": idx,
            "url": url,
            "domain": domain,
            "tier": tier,
            "word_count": word_count,
            "fetch_status": status,
            "error": result["error"],
            "content": content,
        }
        (output_dir / filename).write_text(
            json.dumps(src_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Lightweight manifest entry (no content)
        sources.append({
            "index": idx,
            "filename": filename,
            "url": url,
            "domain": domain,
            "tier": tier,
            "word_count": word_count,
            "fetch_status": status,
        })

    return sources


def cmd_survey(topic: str) -> None:
    """Pass 1: fetch Wikipedia + DDG results for a topic."""
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)
    print(f"Output directory: {output_dir}")

    # Clean previous run artifacts
    for old_file in output_dir.glob("src_*.json"):
        old_file.unlink()
    manifest_path = output_dir / "source_manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()

    # Get Wikipedia URL
    wikipedia_url = build_survey_urls(topic)[0]

    # Fetch DDG HTML and extract result URLs
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

    all_urls = [wikipedia_url] + ddg_urls
    sources = _fetch_and_save(all_urls, output_dir, "src", "survey")

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


def _collect_deep_dive_urls(manifest_path: Path) -> list[str]:
    """Read source_manifest.json and return deduplicated deep-dive URLs from recommended sources."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    result: list[str] = []

    for source in manifest.get("sources", []):
        if source.get("verdict") != "recommended":
            continue
        for url in source.get("deep_dive_urls", []):
            if url in seen:
                continue
            seen.add(url)
            if classify_domain(url) == 3:
                continue
            result.append(url)

    return result


def _get_fetched_urls(output_dir: Path) -> set[str]:
    """Return URLs already fetched in Pass 1 (src_*.json files)."""
    fetched: set[str] = set()
    for src_file in output_dir.glob("src_*.json"):
        try:
            data = json.loads(src_file.read_text(encoding="utf-8"))
            url = data.get("url")
            if url:
                fetched.add(url)
        except Exception:  # noqa: BLE001
            pass
    return fetched


def cmd_deepen(topic: str) -> None:
    """Pass 2: fetch targeted primary sources from evaluated manifest."""
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)

    manifest_path = output_dir / "source_manifest.json"
    if not manifest_path.exists():
        print(f"Error: source_manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    # Clean previous Pass 2 artifacts
    for old_file in output_dir.glob("pass2_*.json"):
        old_file.unlink()

    deep_dive_urls = _collect_deep_dive_urls(manifest_path)
    fetched_urls = _get_fetched_urls(output_dir)
    deep_dive_urls = [u for u in deep_dive_urls if u not in fetched_urls]

    # Budget guard: max 15 total files across both passes
    pass1_count = len(list(output_dir.glob("src_*.json")))
    pass2_budget = 15 - pass1_count

    if pass2_budget <= 0:
        print(f"Budget exhausted: {pass1_count} src_*.json files already exist (max 15 total). Skipping Pass 2.")
        return

    if not deep_dive_urls:
        print("No deep-dive URLs found in manifest -- skip Pass 2 or re-evaluate sources")
        return

    if len(deep_dive_urls) > pass2_budget:
        skipped_due_to_budget = deep_dive_urls[pass2_budget:]
        deep_dive_urls = deep_dive_urls[:pass2_budget]
        print(f"Budget: {pass2_budget} slots available. Skipping {len(skipped_due_to_budget)} URL(s):")
        for url in skipped_due_to_budget:
            print(f"  [budget-skip] {url}")

    pass2_sources = _fetch_and_save(deep_dive_urls, output_dir, "pass2", "pass2")

    _print_summary_table(pass2_sources)

    # Update manifest with pass2_sources
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["pass2_sources"] = pass2_sources
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Manifest: {manifest_path}")


def cmd_write(topic: str) -> None:
    """Pass 3: aggregate all source files into synthesis_input.md."""
    root = _get_project_root()
    output_dir = resolve_output_dir(root, topic)

    pass1, pass2 = load_source_files(output_dir)

    if not pass1 and not pass2:
        print(f"No source files found in {output_dir}. Run survey first.")
        raise ValueError(f"No source files found in {output_dir}. Run survey first.")

    content = build_synthesis_input(topic, pass1, pass2, output_dir)
    synthesis_path = write_synthesis_input(output_dir, content)

    prompt_path = root / ".claude" / "skills" / "researcher" / "prompts" / "synthesis.md"

    print(f"Synthesis input ready: {synthesis_path}")
    print(f"Pass 1 sources: {len(pass1)}  |  Pass 2 sources: {len(pass2)}")
    print(f"Synthesis prompt: {prompt_path}")
    print()
    print(
        "Aggregation complete. Read synthesis_input.md and the synthesis prompt, "
        "then produce Research.md and media_urls.md in the research/ directory."
    )


def main() -> None:
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(
        prog="researcher",
        description="Researcher skill — documentary video research pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    survey_parser = subparsers.add_parser("survey", help="Pass 1: fetch initial sources for a topic")
    survey_parser.add_argument("topic", help="Topic string (e.g. 'Jonestown Massacre')")

    deepen_parser = subparsers.add_parser("deepen", help="Pass 2: fetch targeted primary sources")
    deepen_parser.add_argument("topic", help="Topic string (same as used for survey)")

    write_parser = subparsers.add_parser("write", help="Pass 3: aggregate sources into synthesis_input.md")
    write_parser.add_argument("topic", help="Topic string (same as used for survey/deepen)")

    args = parser.parse_args()

    try:
        if args.command == "survey":
            cmd_survey(args.topic)
        elif args.command == "deepen":
            cmd_deepen(args.topic)
        elif args.command == "write":
            cmd_write(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
