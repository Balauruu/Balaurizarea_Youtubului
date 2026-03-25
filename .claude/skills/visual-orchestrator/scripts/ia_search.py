"""Search Internet Archive for b-roll footage candidates."""
import os, sys
os.environ.setdefault('PYTHONUTF8', '1')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json

import internetarchive


def search_ia(query: str, collection: str | None = None, limit: int = 10) -> list[dict]:
    """Query Internet Archive for video items matching the search terms."""
    parts = [f"({query})", "mediatype:(movies)"]
    if collection:
        parts.append(f"collection:({collection})")
    full_query = " AND ".join(parts)

    results: list[dict] = []
    for item in internetarchive.search_items(full_query).iter_as_results():
        results.append({
            "identifier": item.get("identifier", ""),
            "title": item.get("title", ""),
            "description": (item.get("description") or "")[:300],
            "collection": item.get("collection", ""),
            "url": f"https://archive.org/details/{item.get('identifier', '')}",
        })
        if len(results) >= limit:
            break
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
