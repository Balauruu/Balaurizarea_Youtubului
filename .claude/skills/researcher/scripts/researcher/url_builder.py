"""Project directory resolution and URL construction for the researcher skill.

Provides:
- _get_project_root: Walk up from __file__ to find CLAUDE.md project root marker.
- find_project_dir: Case-insensitive substring match against projects/ subdirectories.
- resolve_output_dir: Return/create output directory (project research/ or scratch).
- make_ddg_url: Build a DuckDuckGo HTML endpoint URL for a query string.
- build_survey_urls: Return initial URL list for a topic (Wikipedia only; DDG handled in cli.py).
"""
import urllib.parse
from pathlib import Path


def _get_project_root() -> Path:
    """Walk up from this file looking for CLAUDE.md as the project root marker.

    Returns:
        Project root Path. Falls back to cwd if CLAUDE.md not found.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def find_project_dir(root: Path, topic: str) -> Path | None:
    """Find a projects/ subdirectory by case-insensitive substring match.

    Args:
        root: Project root directory (must contain projects/).
        topic: Search string to match against directory names.

    Returns:
        Matching Path if exactly one directory matches, None if no match.

    Raises:
        ValueError: When multiple directories match (lists all matching names).
    """
    projects_dir = root / "projects"
    if not projects_dir.is_dir():
        return None

    query = topic.lower()
    matches = [
        d for d in projects_dir.iterdir()
        if d.is_dir() and query in d.name.lower()
    ]

    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]

    names = ", ".join(f'"{m.name}"' for m in sorted(matches))
    raise ValueError(
        f"Multiple project directories match '{topic}': {names}. "
        "Please use a more specific topic string."
    )


def resolve_output_dir(root: Path, topic: str) -> Path:
    """Return the output directory for a survey run, creating it if needed.

    If a matching project directory exists, returns projects/N. Title/research/.
    If no match, returns .claude/scratch/researcher/ (standalone mode).

    Args:
        root: Project root directory.
        topic: Topic string used to find the project directory.

    Returns:
        Path to the output directory (guaranteed to exist after this call).
    """
    project_dir = find_project_dir(root, topic)
    if project_dir is not None:
        output_dir = project_dir / "research"
    else:
        output_dir = root / ".claude" / "scratch" / "researcher"

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def make_ddg_url(query: str) -> str:
    """Build a DuckDuckGo HTML endpoint URL for a search query.

    Uses the static HTML endpoint (no JS required) for crawl4ai compatibility.

    Args:
        query: Search query string.

    Returns:
        URL-encoded DuckDuckGo HTML search URL.
    """
    encoded = urllib.parse.quote_plus(query)
    return f"https://html.duckduckgo.com/html/?q={encoded}"


def build_survey_urls(topic: str) -> list[str]:
    """Build initial URL list for a survey run.

    Returns Wikipedia page URL only. DDG URL expansion is handled in
    cmd_survey after link extraction.

    Args:
        topic: Topic string (e.g. "Jonestown Massacre").

    Returns:
        List of URLs to fetch in survey pass (Wikipedia URL only).
    """
    wiki_query = urllib.parse.quote(topic.replace(" ", "_"))
    wikipedia_url = f"https://en.wikipedia.org/wiki/{wiki_query}"
    return [wikipedia_url]
