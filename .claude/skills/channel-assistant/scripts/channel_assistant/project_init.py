"""Deterministic functions for project directory creation and metadata writing.

All functions use stdlib only (pathlib, re, datetime).
LLM reasoning (title variant generation, description writing) is performed
externally by Claude. This module handles: directory scaffold, metadata.md
write, and past_topics.md dedup loop closure.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _next_project_number(projects_dir: Path) -> int:
    """Return the next sequential project number.

    Scans *projects_dir* for directories matching the ``N. *`` pattern,
    finds the highest N, and returns N+1. Returns 1 if the directory is
    empty or does not exist.
    """
    if not projects_dir.exists():
        return 1
    pattern = re.compile(r"^(\d+)\.")
    numbers: list[int] = []
    for entry in projects_dir.iterdir():
        if entry.is_dir():
            m = pattern.match(entry.name)
            if m:
                numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


def _sanitize_dir_name(title: str) -> str:
    """Remove characters forbidden on Windows NTFS from a directory name.

    Forbidden characters: ``< > : " / \\ | ? *``
    Strips leading/trailing whitespace from the result.
    """
    return re.sub(r'[<>:"/\\|?*]', "", title).strip()


def _create_scaffold(project_dir: Path) -> None:
    """Create the three standard subdirectories inside *project_dir*.

    Creates ``research/``, ``assets/``, and ``script/`` using
    ``mkdir(parents=True, exist_ok=True)`` — safe to call on an existing
    directory.
    """
    for subdir in ("research", "assets", "script"):
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)


def _append_past_topic(path: Path, title: str, hook: str) -> None:
    """Append a new entry to *path* in the canonical past_topics.md format.

    Canonical format: ``- **Title** | YYYY-MM-DD | one-line summary``

    Creates the file if it does not exist.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"- **{title}** | {date_str} | {hook}\n"
    # Open in append mode; creates file if missing
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _write_metadata(
    path: Path,
    title: str,
    variants: list[dict],
    description: str,
    brief_markdown: str,
) -> None:
    """Write metadata.md to *path*.

    Schema:
    - H1 title + created date
    - Title Variants table (with RECOMMENDED label on flagged variant)
    - YouTube Description section
    - Topic Brief section (raw markdown copy)

    ``variants`` is a list of dicts with keys:
        ``title`` (str), ``hook_type`` (str), ``recommended`` (bool),
        ``notes`` (str, optional).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = [
        f"# {title}",
        "",
        f"*Created: {timestamp}*",
        "",
        "## Title Variants",
        "",
        "| # | Title | Hook Type | Notes |",
        "|---|-------|-----------|-------|",
    ]
    for i, v in enumerate(variants, start=1):
        notes = ""
        if v.get("recommended"):
            notes = "**RECOMMENDED**"
            if v.get("notes"):
                notes = f"{notes} — {v['notes']}"
        elif v.get("notes"):
            notes = v["notes"]
        lines.append(f"| {i} | {v['title']} | {v['hook_type']} | {notes} |")

    lines.extend([
        "",
        "## YouTube Description",
        "",
        description,
        "",
        "## Topic Brief",
        "",
        brief_markdown,
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_project(
    root: Path,
    title: str,
    hook: str,
    title_variants: list[dict],
    description: str,
    brief_markdown: str,
) -> Path:
    """Create project directory scaffold and write metadata.md.

    Steps:
    1. Scan ``projects/`` for the next sequential number.
    2. Sanitize *title* for filesystem safety (Windows NTFS).
    3. Create ``projects/N. Title/`` plus ``research/``, ``assets/``,
       ``script/`` subdirectories.
    4. Write ``metadata.md`` into the project directory.
    5. Append the selected topic to ``channel/past_topics.md``
       to close the dedup loop for future topic generation runs.

    Args:
        root: Project root directory (contains CLAUDE.md).
        title: Topic title, used verbatim in metadata.md and (sanitized)
               as the directory name.
        hook: One-line topic hook; appended to past_topics.md.
        title_variants: List of variant dicts — see ``_write_metadata``
                        for the dict schema.
        description: 2-3 sentence YouTube description.
        brief_markdown: Raw markdown of the selected topic brief from
                        ``topic_briefs.md``.

    Returns:
        The created project directory as a ``pathlib.Path``.

    Side effect:
        Appends the selected topic to
        ``channel/past_topics.md``.
    """
    # Warn about title variants that exceed the 70-char channel convention
    for v in title_variants:
        if len(v.get("title", "")) > 70:
            print(
                f"Warning: title variant exceeds 70 chars "
                f"({len(v['title'])} chars): {v['title']!r}",
                file=sys.stderr,
            )

    projects_dir = root / "projects"
    n = _next_project_number(projects_dir)
    safe_title = _sanitize_dir_name(title)
    project_dir = projects_dir / f"{n}. {safe_title}"

    # Create scaffold (also creates projects/ via parents=True)
    _create_scaffold(project_dir)

    # Write metadata.md
    metadata_path = project_dir / "metadata.md"
    _write_metadata(metadata_path, title, title_variants, description, brief_markdown)

    # Append to past_topics.md
    past_topics_path = root / "channel" / "past_topics.md"
    _append_past_topic(past_topics_path, title, hook)

    return project_dir


def load_project_inputs(root: Path, topic_number: int) -> dict:
    """Load context needed for project initialization.

    Reads the selected topic brief from ``strategy/topic_briefs.md``
    and extracts the Title Patterns section from
    ``strategy/competitors/analysis.md`` (if present).

    Args:
        root: Project root directory.
        topic_number: 1-based index of the selected topic brief.

    Returns:
        A dict with:
            ``"brief_markdown"`` — raw markdown of the selected brief
            section (from ``## N. Title`` through the next ``## N+1.`` or
            end-of-file).
            ``"title_patterns"`` — the Title Patterns section from
            ``analysis.md``, or an empty string if the file is absent.

    Raises:
        FileNotFoundError: if ``topic_briefs.md`` does not exist.
    """
    briefs_path = root / "strategy" / "topic_briefs.md"
    analysis_path = root / "strategy" / "competitors" / "analysis.md"

    if not briefs_path.exists():
        raise FileNotFoundError(
            f"Topic briefs not found: {briefs_path}. Run 'topics' first to generate topic_briefs.md"
        )

    # -----------------------------------------------------------------------
    # Extract brief section for the selected topic number
    # -----------------------------------------------------------------------
    text = briefs_path.read_text(encoding="utf-8")
    # Match "## N. " heading lines
    section_pattern = re.compile(r"^## \d+\.", re.MULTILINE)
    sections = list(section_pattern.finditer(text))

    brief_markdown = ""
    for idx, match in enumerate(sections):
        # Check if this section header starts with the requested number
        section_start = match.start()
        header_line = text[section_start:text.find("\n", section_start)]
        # e.g., "## 2. Topic Title"
        num_match = re.match(r"^## (\d+)\.", header_line)
        if num_match and int(num_match.group(1)) == topic_number:
            # Extract from this heading to the next section or end of file
            if idx + 1 < len(sections):
                section_end = sections[idx + 1].start()
            else:
                section_end = len(text)
            brief_markdown = text[section_start:section_end].strip()
            break

    if not brief_markdown:
        available = [
            int(re.match(r"^## (\d+)\.", text[m.start():text.find("\n", m.start())]).group(1))
            for m in sections
            if re.match(r"^## (\d+)\.", text[m.start():text.find("\n", m.start())])
        ]
        raise ValueError(
            f"Topic #{topic_number} not found in {briefs_path}. "
            f"Available: {available}"
        )

    # -----------------------------------------------------------------------
    # Extract Title Patterns section from analysis.md
    # -----------------------------------------------------------------------
    title_patterns = ""
    if analysis_path.exists():
        analysis_text = analysis_path.read_text(encoding="utf-8")
        patterns_match = re.search(
            r"(## Title Patterns\b.*?)(?=\n## |\Z)",
            analysis_text,
            re.DOTALL,
        )
        if patterns_match:
            title_patterns = patterns_match.group(1).strip()

    return {
        "brief_markdown": brief_markdown,
        "title_patterns": title_patterns,
    }
