# crawl4ai-scraper

## Description
Provides the ability to scrape any valid URL directly into clean Markdown format. Useful for web data acquisition, reading articles, documentation, or retrieving textual content from any web page. This skill uses the deterministic Python `crawl4ai` asynchronous library under the hood.

## Instructions
1. This skill relies on the native execution of a Python script. Do not try to make LLM API calls inside the execution.
2. To scrape a URL, use the `Bash` or shell execution tool to run the python scraper script.
3. The scraper will output clean markdown directly to standard output. Capture this output.
4. If an error is returned, analyze the output to determine if the URL was invalid, blocked, or unavailable.

## Usage
Run the script natively from the project root:

```bash
python .claude/skills/crawl4ai-scraper/scripts/scraper.py <URL>
```

**Example:**
```bash
python .claude/skills/crawl4ai-scraper/scripts/scraper.py "https://example.com/article"
```

## Dependencies
- Requires Python
- Requires `crawl4ai` library (already managed by environment)

## Outputs
- Clean, raw Markdown of the main content extracted from the provided URL, returned directly to standard output.