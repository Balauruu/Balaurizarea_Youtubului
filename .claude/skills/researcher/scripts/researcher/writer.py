"""Source file aggregation into synthesis_input.md for the researcher skill.

Reads all src_*.json and pass2_*.json files from the output directory and
produces a flat markdown document (synthesis_input.md) for Claude to synthesize
into Research.md and media_urls.md.

Exported functions:
    load_source_files  — glob and read src/pass2 JSON files from output_dir
    build_synthesis_input — format sources into synthesis markdown string
    write_synthesis_input — write the markdown string to output_dir/synthesis_input.md
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def load_source_files(output_dir: Path) -> tuple[list[dict], list[dict]]:
    """Load all src_*.json and pass2_*.json source files from output_dir.

    Files are sorted by filename to ensure deterministic ordering.
    Files that fail to parse are silently skipped.

    Args:
        output_dir: Directory containing source JSON files.

    Returns:
        Tuple of (pass1_sources, pass2_sources) as lists of dicts.
        Each list is sorted by filename. Either may be empty.
    """
    pass1: list[dict] = []
    pass2: list[dict] = []

    for src_file in sorted(output_dir.glob("src_*.json")):
        try:
            data = json.loads(src_file.read_text(encoding="utf-8"))
            pass1.append(data)
        except Exception:  # noqa: BLE001
            pass

    for src_file in sorted(output_dir.glob("pass2_*.json")):
        try:
            data = json.loads(src_file.read_text(encoding="utf-8"))
            pass2.append(data)
        except Exception:  # noqa: BLE001
            pass

    return pass1, pass2


def build_synthesis_input(
    topic: str,
    pass1: list[dict],
    pass2: list[dict],
    output_dir: Path,
) -> str:
    """Format source lists into a flat markdown document for Claude synthesis.

    Sources with fetch_status != "ok" or empty content are listed in a
    "Skipped/failed sources" section at the top, not rendered as full sections.
    Sources with evaluation_notes are included if present.

    Args:
        topic: The research topic string.
        pass1: List of Pass 1 source dicts (from src_*.json).
        pass2: List of Pass 2 source dicts (from pass2_*.json).
        output_dir: The output directory path (included in header for Claude).

    Returns:
        Formatted markdown string.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_sources = [("Pass 1", s) for s in pass1] + [("Pass 2", s) for s in pass2]

    # Partition into good and skipped
    good: list[tuple[str, dict]] = []
    skipped: list[tuple[str, dict]] = []

    for pass_label, src in all_sources:
        if src.get("fetch_status") == "ok" and src.get("content", "").strip():
            good.append((pass_label, src))
        else:
            skipped.append((pass_label, src))

    total_sources = len(good)

    lines: list[str] = []

    # Header
    lines.append("# Synthesis Input")
    lines.append("")
    lines.append(f"**Topic:** {topic}")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Total sources (usable):** {total_sources}")
    lines.append(f"**Pass 1 sources:** {len(pass1)}")
    lines.append(f"**Pass 2 sources:** {len(pass2)}")
    lines.append(f"**Output directory:** {output_dir}")
    lines.append("")

    # Skipped/failed section
    if skipped:
        lines.append("## Skipped/failed sources")
        lines.append("")
        for pass_label, src in skipped:
            url = src.get("url", "(no url)")
            reason = src.get("error", "") or src.get("fetch_status", "empty")
            lines.append(f"- [{pass_label}] {url} — {reason}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Source sections
    lines.append("## Sources")
    lines.append("")

    for pass_label, src in good:
        url = src.get("url", "(no url)")
        domain = src.get("domain", "")
        tier = src.get("tier", "")
        word_count = src.get("word_count", 0)
        content = src.get("content", "")
        evaluation_notes = src.get("evaluation_notes", "")

        lines.append(f"### [{pass_label}] {domain}")
        lines.append("")
        lines.append(f"- **URL:** {url}")
        lines.append(f"- **Domain:** {domain}")
        lines.append(f"- **Tier:** {tier}")
        lines.append(f"- **Words:** {word_count}")
        if evaluation_notes:
            lines.append(f"- **Evaluation notes:** {evaluation_notes}")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def write_synthesis_input(output_dir: Path, content: str) -> Path:
    """Write synthesis_input.md to output_dir and return the path.

    Args:
        output_dir: Directory to write the file into.
        content: Markdown string to write.

    Returns:
        Path to the written synthesis_input.md file.
    """
    output_path = output_dir / "synthesis_input.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path
