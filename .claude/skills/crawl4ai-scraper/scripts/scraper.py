import argparse
import asyncio
import sys

async def main():
    parser = argparse.ArgumentParser(description="Scrape a URL and output clean Markdown using crawl4ai.")
    parser.add_argument("url", help="The URL to scrape")
    args = parser.parse_args()

    url = args.url

    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            if result.success:
                print(result.markdown)
            else:
                print(f"Error scraping {url}: {result.error_message}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
