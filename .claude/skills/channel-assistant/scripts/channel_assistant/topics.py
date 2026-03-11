"""Deterministic helper functions for the topic generation workflow.

All functions use stdlib only (pathlib, re, difflib, datetime).
LLM reasoning (topic ideation, scoring) is performed externally by Claude.
This module handles: loading inputs, duplicate checking, writing output files.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_section(content: str, header: str) -> str:
    """Extract text between '## Header' and next '## ' heading or EOF.

    Returns empty string if header not found.
    """
    pattern = re.compile(
        r"^## " + re.escape(header) + r"\s*\n(.*?)(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def _load_past_topics(path: Path) -> list[str]:
    """Read past_topics.md and return a list of title strings.

    Canonical line format: ``- **Title** | YYYY-MM-DD | one-line summary``
    Also handles: ``**Title** | ...`` (no leading dash).

    Returns an empty list if the file is missing or empty.
    """
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []

    titles: list[str] = []
    # Match **Title** anywhere in a line (handles both "- **T**" and "**T**" prefixes)
    pattern = re.compile(r"\*\*(.+?)\*\*")
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            titles.append(match.group(1))

    return titles


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_duplicates(
    candidate_title: str,
    past_titles: list[str],
    threshold: float = 0.85,
) -> str | None:
    """Return the past title that is a near-duplicate of *candidate_title*, or None.

    Comparison is case-insensitive. Uses SequenceMatcher ratio.
    Returns the *best* match above *threshold*, or None if no match.
    """
    if not past_titles:
        return None

    candidate_lower = candidate_title.lower()
    best_ratio = 0.0
    best_match: str | None = None

    for past in past_titles:
        ratio = SequenceMatcher(None, candidate_lower, past.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = past

    if best_ratio >= threshold:
        return best_match
    return None


def load_topic_inputs(root: Path) -> dict:
    """Load all inputs needed for the topic generation workflow.

    Returns:
        {
            "analysis": str,           # contents of context/competitors/analysis.md
            "channel_dna": str,        # contents of context/channel/channel.md
            "past_topics": list[str],  # titles from context/channel/past_topics.md
            "trends": str,             # ## Trending Topics section from analysis.md (empty if absent)
            "content_gaps": str,       # ## Content Gaps section from analysis.md (empty if absent)
        }

    Raises FileNotFoundError for missing analysis.md or channel.md.
    Returns empty list for missing past_topics.md.
    Returns empty strings for trends/content_gaps if trends has not been run yet.
    """
    analysis_path = root / "context" / "competitors" / "analysis.md"
    channel_dna_path = root / "context" / "channel" / "channel.md"
    past_topics_path = root / "context" / "channel" / "past_topics.md"

    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_path}")
    if not channel_dna_path.exists():
        raise FileNotFoundError(f"Channel DNA file not found: {channel_dna_path}")

    analysis = analysis_path.read_text(encoding="utf-8")
    channel_dna = channel_dna_path.read_text(encoding="utf-8")
    past_topics = _load_past_topics(past_topics_path)

    # Extract trend sections from analysis.md (empty strings if not yet present)
    trends_section = _extract_section(analysis, "Trending Topics")
    gaps_section = _extract_section(analysis, "Content Gaps")

    return {
        "analysis": analysis,
        "channel_dna": channel_dna,
        "past_topics": past_topics,
        "trends": trends_section,
        "content_gaps": gaps_section,
    }


def write_topic_briefs(briefs: list[dict], output_path: Path) -> None:
    """Write a list of topic brief dicts to a markdown file.

    Creates parent directories as needed. Overwrites on each call.

    Brief dict schema::

        {
            "title": str,
            "pillar": str,
            "hook": str,
            "timeline": list[str],
            "scores": {"obscurity": int, "complexity": int,
                       "shock_factor": int, "verifiability": int},
            "justification": {"obscurity": str, "complexity": str,
                              "shock_factor": str, "verifiability": str},
            "estimated_runtime_min": int,
            "duplicate_of": str | None,
            "tags": list[str],
        }
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# Topic Briefs",
        "",
        f"*Generated: {timestamp}*",
        "",
    ]

    for i, brief in enumerate(briefs, start=1):
        scores = brief["scores"]
        o = scores["obscurity"]
        c = scores["complexity"]
        s = scores["shock_factor"]
        v = scores["verifiability"]
        total = o + c + s + v
        score_line = f"O:{o} C:{c} S:{s} V:{v} = {total}/20"

        lines.append(f"## {i}. {brief['title']}")
        lines.append("")
        lines.append(f"**Pillar:** {brief['pillar']}")
        lines.append("")
        lines.append(f"**Score:** {score_line}  |  ~{brief['estimated_runtime_min']}min")
        lines.append("")
        lines.append(f"**Hook:** {brief['hook']}")
        lines.append("")

        # Timeline
        lines.append("**Timeline:**")
        for entry in brief["timeline"]:
            lines.append(f"- {entry}")
        lines.append("")

        # Scoring justification
        lines.append("**Scoring Justification:**")
        justification = brief.get("justification", {})
        lines.append(f"- Obscurity ({o}/5): {justification.get('obscurity', '')}")
        lines.append(f"- Complexity ({c}/5): {justification.get('complexity', '')}")
        lines.append(f"- Shock Factor ({s}/5): {justification.get('shock_factor', '')}")
        lines.append(f"- Verifiability ({v}/5): {justification.get('verifiability', '')}")
        lines.append("")

        # Optional tags
        tags = brief.get("tags", [])
        if tags:
            lines.append(f"**Tags:** {' | '.join(tags)}")
            lines.append("")

        # Duplicate warning
        if brief.get("duplicate_of"):
            lines.append(f"> **Warning:** Similar to past topic: *{brief['duplicate_of']}*")
            lines.append("")

        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def format_chat_cards(briefs: list[dict]) -> str:
    """Return a compact multi-line string with numbered topic cards.

    Format per card::

        [N] Title -- hook (1 line)
            O:X C:X S:X V:X = N/20 | ~Xmin | Pillar
            [UNDERSERVED CLUSTER: ...] (optional)
            [Similar to: Past Title] (optional)
    """
    cards: list[str] = []

    for i, brief in enumerate(briefs, start=1):
        scores = brief["scores"]
        o = scores["obscurity"]
        c = scores["complexity"]
        s = scores["shock_factor"]
        v = scores["verifiability"]
        total = o + c + s + v
        score_line = f"O:{o} C:{c} S:{s} V:{v} = {total}/20"

        runtime = brief["estimated_runtime_min"]
        pillar = brief["pillar"]

        card_lines = [
            f"[{i}] {brief['title']} -- {brief['hook']}",
            f"    {score_line} | ~{runtime}min | {pillar}",
        ]

        # Optional tags (e.g., UNDERSERVED CLUSTER)
        for tag in brief.get("tags", []):
            card_lines.append(f"    [{tag}]")

        # Duplicate warning
        if brief.get("duplicate_of"):
            card_lines.append(f"    [Similar to: {brief['duplicate_of']}]")

        cards.append("\n".join(card_lines))

    return "\n\n".join(cards)
