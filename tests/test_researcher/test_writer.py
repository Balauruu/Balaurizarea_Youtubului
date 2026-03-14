"""Tests for researcher.writer — source file aggregation into synthesis_input.md.

All tests use tmp_path fixtures with fake JSON source files.
No network access, no crawl4ai required.
"""
import json
from pathlib import Path

import pytest

from researcher.writer import build_synthesis_input, load_source_files, write_synthesis_input


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_src(dir_path: Path, filename: str, data: dict) -> Path:
    """Write a fake source JSON file to dir_path."""
    p = dir_path / filename
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _make_src(
    index: int,
    url: str = "https://en.wikipedia.org/wiki/Test",
    domain: str = "en.wikipedia.org",
    tier: int = 1,
    word_count: int = 500,
    fetch_status: str = "ok",
    error: str = "",
    content: str = "This is the source content.",
) -> dict:
    return {
        "index": index,
        "url": url,
        "domain": domain,
        "tier": tier,
        "word_count": word_count,
        "fetch_status": fetch_status,
        "error": error,
        "content": content,
    }


# ---------------------------------------------------------------------------
# load_source_files tests
# ---------------------------------------------------------------------------

def test_load_source_files_reads_both_passes(tmp_path: Path) -> None:
    """Given a dir with 2 src_*.json and 1 pass2_*.json, returns (pass1=[2], pass2=[1])."""
    _write_src(tmp_path, "src_001.json", _make_src(1, url="https://a.com"))
    _write_src(tmp_path, "src_002.json", _make_src(2, url="https://b.com"))
    _write_src(tmp_path, "pass2_001.json", _make_src(1, url="https://c.com"))

    pass1, pass2 = load_source_files(tmp_path)

    assert len(pass1) == 2
    assert len(pass2) == 1
    # Sorted by filename — src_001.json first
    assert pass1[0]["url"] == "https://a.com"
    assert pass1[1]["url"] == "https://b.com"
    assert pass2[0]["url"] == "https://c.com"


def test_load_source_files_no_pass2(tmp_path: Path) -> None:
    """Given only src_*.json files, returns (pass1=[items], pass2=[]) without error."""
    _write_src(tmp_path, "src_001.json", _make_src(1))
    _write_src(tmp_path, "src_002.json", _make_src(2))

    pass1, pass2 = load_source_files(tmp_path)

    assert len(pass1) == 2
    assert pass2 == []


def test_load_source_files_empty_dir(tmp_path: Path) -> None:
    """Given empty directory, returns ([], [])."""
    pass1, pass2 = load_source_files(tmp_path)

    assert pass1 == []
    assert pass2 == []


# ---------------------------------------------------------------------------
# build_synthesis_input tests
# ---------------------------------------------------------------------------

def test_build_synthesis_input_basic(tmp_path: Path) -> None:
    """Output string contains header, topic, source count, and source details."""
    pass1 = [_make_src(1, url="https://en.wikipedia.org/wiki/Test", domain="en.wikipedia.org", tier=1, word_count=300, content="Content here.")]
    pass2 = [_make_src(1, url="https://example.com/article", domain="example.com", tier=2, word_count=150, content="More content.")]

    output = build_synthesis_input("Test Topic", pass1, pass2, tmp_path)

    assert "# Synthesis Input" in output
    assert "Test Topic" in output
    # Source count — total 2 sources
    assert "2" in output
    # Source details
    assert "https://en.wikipedia.org/wiki/Test" in output
    assert "en.wikipedia.org" in output
    assert "Content here." in output
    assert "https://example.com/article" in output
    assert "More content." in output


def test_build_synthesis_input_skips_failed(tmp_path: Path) -> None:
    """Failed source appears in skipped section at top, not as full source entry."""
    failed_src = _make_src(
        1,
        url="https://bad.example.com/404",
        fetch_status="failed",
        error="HTTP 404",
        content="",
        word_count=0,
    )
    good_src = _make_src(2, url="https://good.example.com/ok", content="Good content.")

    output = build_synthesis_input("Test Topic", [failed_src, good_src], [], tmp_path)

    # Failed source listed in skipped section
    assert "https://bad.example.com/404" in output
    # Full content section only for good source
    assert "Good content." in output
    # Verify the failed URL appears before or in a "skipped" indicator
    skipped_idx = output.lower().find("skip")
    failed_url_idx = output.find("https://bad.example.com/404")
    assert skipped_idx != -1, "Expected 'skipped' indicator in output"
    # Failed source should not have its own full section with content
    # (it has empty content so this is implicitly true, but ensure it's in skipped list)
    assert failed_url_idx < output.find("Good content."), "Failed URL should appear before the good content"


def test_build_synthesis_input_includes_output_dir(tmp_path: Path) -> None:
    """Output string contains '**Output directory:**' with the provided path."""
    pass1 = [_make_src(1)]
    output = build_synthesis_input("Topic", pass1, [], tmp_path)

    assert "**Output directory:**" in output
    assert str(tmp_path) in output


# ---------------------------------------------------------------------------
# write_synthesis_input tests
# ---------------------------------------------------------------------------

def test_write_synthesis_input_creates_file(tmp_path: Path) -> None:
    """Writes synthesis_input.md to output_dir and returns the path."""
    content = "# Synthesis Input\n\nTest content here.\n"

    result_path = write_synthesis_input(tmp_path, content)

    assert result_path == tmp_path / "synthesis_input.md"
    assert result_path.exists()
    assert result_path.read_text(encoding="utf-8") == content
