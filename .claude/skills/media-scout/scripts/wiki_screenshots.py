"""Take Wikipedia viewport screenshots and convert to JPEG for documentary B-roll.

Usage:
    python wiki_screenshots.py --input pages.json --output-dir path/to/documents

Input JSON: list of [url, filename] pairs
    [
        ["https://en.wikipedia.org/wiki/Topic", "wiki-topic-en.jpg"],
        ["https://fr.wikipedia.org/wiki/Sujet", "wiki-sujet-fr.jpg"]
    ]

Output: JPEG screenshots (quality 85) in the specified directory.
Skips files that already exist and are > 10KB. Discards captures < 10KB (blank).
"""
import asyncio
import argparse
import base64
import io
import json
import sys
import os

os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Lazy-import Pillow only if needed (for PNG -> JPEG conversion)
_PIL_AVAILABLE = None


def _ensure_pillow():
    global _PIL_AVAILABLE
    if _PIL_AVAILABLE is None:
        try:
            from PIL import Image  # noqa: F401
            _PIL_AVAILABLE = True
        except ImportError:
            _PIL_AVAILABLE = False
    return _PIL_AVAILABLE


def _convert_png_to_jpeg(png_bytes: bytes, quality: int = 85) -> bytes:
    """Convert PNG bytes to JPEG bytes. Falls back to saving PNG if Pillow unavailable."""
    if not _ensure_pillow():
        print("WARNING: Pillow not installed, saving as PNG (larger files)")
        return png_bytes

    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


async def take_screenshots(pages: list[list[str]], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    browser_config = BrowserConfig(
        headless=True, viewport_width=1280, viewport_height=900
    )

    results = {"saved": [], "skipped": [], "failed": []}

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url, filename in pages:
            dest = output_dir / filename
            if dest.exists() and dest.stat().st_size > 10240:
                print(f"SKIP (exists): {filename}")
                results["skipped"].append(filename)
                continue

            try:
                crawl_config = CrawlerRunConfig(
                    wait_until="networkidle",
                    page_timeout=30000,
                    screenshot=True,
                    screenshot_wait_for=1.0,
                )
                result = await crawler.arun(url=url, config=crawl_config)

                if not result.screenshot:
                    print(f"FAIL (no screenshot): {filename}")
                    results["failed"].append({"file": filename, "reason": "no screenshot"})
                    continue

                png_data = base64.b64decode(result.screenshot)
                if len(png_data) < 10240:
                    print(f"DISCARD (too small): {filename}")
                    results["failed"].append({"file": filename, "reason": "too small"})
                    continue

                # Convert to JPEG if filename ends with .jpg/.jpeg
                if filename.lower().endswith((".jpg", ".jpeg")):
                    data = _convert_png_to_jpeg(png_data)
                else:
                    data = png_data

                dest.write_bytes(data)
                size_kb = len(data) // 1024
                print(f"OK ({size_kb}KB): {filename}")
                results["saved"].append(filename)

            except Exception as e:
                print(f"ERROR: {filename} - {e}")
                results["failed"].append({"file": filename, "reason": str(e)[:200]})

    print(f"\nSaved: {len(results['saved'])}, Skipped: {len(results['skipped'])}, Failed: {len(results['failed'])}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Take Wikipedia viewport screenshots")
    parser.add_argument("--input", required=True, help="JSON file with [[url, filename], ...] pairs")
    parser.add_argument("--output-dir", required=True, help="Directory to save screenshots")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        pages = json.load(f)

    if not pages:
        print("No pages in input file")
        sys.exit(1)

    print(f"Taking {len(pages)} screenshots...")
    output_dir = Path(args.output_dir)
    results = asyncio.run(take_screenshots(pages, output_dir))

    # Write results summary next to input for reference
    summary_path = Path(args.input).with_suffix(".results.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
