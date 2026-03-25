"""Batch crawl source pages and extract scored images for media-scout Pass 1.

Usage:
    python crawl_images.py --input urls.json --output crawl_results.json

Input JSON: list of URL strings
    ["https://en.wikipedia.org/wiki/Topic", "https://example.com/article"]

Output JSON: dict keyed by URL with image metadata
    {
        "https://...": {
            "success": true,
            "images": [{"src": "...", "alt": "...", "score": 5, "desc": "..."}],
            "error": ""
        }
    }
"""
import asyncio
import argparse
import json
import sys
import os

os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def extract_images(urls: list[str]) -> dict:
    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=30000,
        image_score_threshold=3,
    )

    results = {}
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawl_results = await crawler.arun_many(urls, config=crawl_config)
        for result in crawl_results:
            url = result.url
            images = []
            if result.success and result.media and "images" in result.media:
                for img in result.media["images"]:
                    src = img.get("src", "")
                    if src and not src.startswith("data:"):
                        images.append({
                            "src": src,
                            "alt": img.get("alt", ""),
                            "score": img.get("score", 0),
                            "desc": img.get("desc", ""),
                        })
            error = ""
            if not result.success:
                error = str(getattr(result, "error_message", ""))[:200]
            results[url] = {"success": result.success, "images": images, "error": error}
            status = "OK" if result.success else "FAIL"
            print(f"{status}: {url} -> {len(images)} images")

    total = sum(len(v["images"]) for v in results.values())
    print(f"\nTotal pages: {len(results)}, Total images: {total}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Batch crawl pages and extract images")
    parser.add_argument("--input", required=True, help="JSON file with list of URLs")
    parser.add_argument("--output", required=True, help="Output JSON file for results")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        urls = json.load(f)

    if not urls:
        print("No URLs in input file")
        sys.exit(1)

    print(f"Crawling {len(urls)} URLs for image extraction...")
    results = asyncio.run(extract_images(urls))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
