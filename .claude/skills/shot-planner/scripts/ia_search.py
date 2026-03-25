"""Search Internet Archive for b-roll footage candidates.

Two-step process: search for identifiers, then fetch full metadata.
Results are cached to data/ia_cache.json to avoid redundant API calls.
"""
import os, sys
os.environ.setdefault('PYTHONUTF8', '1')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import time
from pathlib import Path

import internetarchive

CACHE_PATH = Path(__file__).resolve().parents[4] / "data" / "ia_cache.json"


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _fetch_metadata(identifier: str, cache: dict) -> dict | None:
    """Fetch full metadata for an IA item, using cache when available."""
    if identifier in cache:
        return cache[identifier]

    try:
        item = internetarchive.get_item(identifier)
        md = item.metadata
        entry = {
            "identifier": identifier,
            "title": md.get("title", ""),
            "description": (md.get("description") or "")[:500],
            "collection": md.get("collection", ""),
            "creator": md.get("creator", ""),
            "date": md.get("date", ""),
            "url": f"https://archive.org/details/{identifier}",
        }
        cache[identifier] = entry
        return entry
    except Exception as e:
        print(f"  Warning: failed to fetch metadata for {identifier}: {e}", file=sys.stderr)
        return None


def search_ia(query: str, collection: str | None = None, limit: int = 10) -> list[dict]:
    """Query Internet Archive for video items, returning full metadata."""
    parts = [f"({query})", "mediatype:(movies)"]
    if collection:
        parts.append(f"collection:({collection})")
    full_query = " AND ".join(parts)

    cache = _load_cache()
    identifiers: list[str] = []

    for item in internetarchive.search_items(full_query).iter_as_results():
        identifier = item.get("identifier", "")
        if identifier:
            identifiers.append(identifier)
        if len(identifiers) >= limit:
            break

    # Step 2: fetch full metadata for each identifier
    results: list[dict] = []
    for identifier in identifiers:
        entry = _fetch_metadata(identifier, cache)
        if entry and entry.get("title"):  # skip items with no title
            results.append(entry)
        time.sleep(0.3)  # gentle rate limiting

    _save_cache(cache)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Internet Archive for b-roll footage.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--collection", default=None, help="Filter to a specific IA collection (e.g. prelinger)")
    parser.add_argument("--limit", type=int, default=10, help="Max results to return (default 10)")
    args = parser.parse_args()

    results = search_ia(args.query, collection=args.collection, limit=args.limit)
    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
