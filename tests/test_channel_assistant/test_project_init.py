"""Tests for channel_assistant.project_init module."""

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def make_variants(recommended_idx=4):
    """Return a list of 5 title variant dicts with one recommended."""
    variants = []
    hook_types = ["question", "statement", "revelation", "curiosity gap", "declaration"]
    for i in range(5):
        variants.append({
            "title": f"Title Variant {i + 1}: The Test Case",
            "hook_type": hook_types[i],
            "recommended": (i == recommended_idx),
            "notes": "Best pattern fit" if i == recommended_idx else "",
        })
    return variants


# ---------------------------------------------------------------------------
# Tests for _next_project_number
# ---------------------------------------------------------------------------


class TestNextProjectNumber:
    """Tests for _next_project_number internal helper."""

    def test_empty_dir_returns_1(self, tmp_path):
        from channel_assistant.project_init import _next_project_number

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        assert _next_project_number(projects_dir) == 1

    def test_nonexistent_dir_returns_1(self, tmp_path):
        from channel_assistant.project_init import _next_project_number

        result = _next_project_number(tmp_path / "nonexistent")
        assert result == 1

    def test_increments_past_existing(self, tmp_path):
        from channel_assistant.project_init import _next_project_number

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "1. First Title").mkdir()
        (projects_dir / "2. Second Title").mkdir()
        assert _next_project_number(projects_dir) == 3

    def test_uses_max_not_count(self, tmp_path):
        """If dirs are 1 and 3, next should be 4 (max+1), not 3 (count+1)."""
        from channel_assistant.project_init import _next_project_number

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "1. First Title").mkdir()
        (projects_dir / "3. Third Title").mkdir()
        assert _next_project_number(projects_dir) == 4

    def test_ignores_non_numeric_dirs(self, tmp_path):
        from channel_assistant.project_init import _next_project_number

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "1. Real Project").mkdir()
        (projects_dir / "some-other-dir").mkdir()
        (projects_dir / "README").mkdir()
        assert _next_project_number(projects_dir) == 2

    def test_ignores_files(self, tmp_path):
        from channel_assistant.project_init import _next_project_number

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "1. Real Project").mkdir()
        (projects_dir / "2. note.txt").write_text("not a dir", encoding="utf-8")
        # "2. note.txt" is a file, not a dir — must be ignored
        assert _next_project_number(projects_dir) == 2


# ---------------------------------------------------------------------------
# Tests for _sanitize_dir_name
# ---------------------------------------------------------------------------


class TestSanitizeDirName:
    """Tests for _sanitize_dir_name internal helper."""

    def test_clean_title_unchanged(self):
        from channel_assistant.project_init import _sanitize_dir_name

        assert _sanitize_dir_name("Clean Title") == "Clean Title"

    def test_strips_colon(self):
        from channel_assistant.project_init import _sanitize_dir_name

        result = _sanitize_dir_name("Title: The Subtitle")
        assert ":" not in result

    def test_strips_all_forbidden_chars(self):
        from channel_assistant.project_init import _sanitize_dir_name

        # Windows NTFS forbidden: < > : " / \ | ? *
        result = _sanitize_dir_name('Title: The "Bad" One?')
        assert ":" not in result
        assert '"' not in result
        assert "?" not in result

    def test_full_forbidden_set(self):
        from channel_assistant.project_init import _sanitize_dir_name

        title = 'Bad<>:"/\\|?*Title'
        result = _sanitize_dir_name(title)
        for ch in '<>:"/\\|?*':
            assert ch not in result

    def test_strips_leading_trailing_whitespace(self):
        from channel_assistant.project_init import _sanitize_dir_name

        result = _sanitize_dir_name("  Clean Title  ")
        assert result == "Clean Title"

    def test_removes_chars_not_just_replaces(self):
        """Characters should be removed, not replaced with underscores or dashes."""
        from channel_assistant.project_init import _sanitize_dir_name

        result = _sanitize_dir_name("Title: Subtitle")
        # Should be "Title Subtitle" (colon removed, space preserved)
        assert result == "Title Subtitle"


# ---------------------------------------------------------------------------
# Tests for _create_scaffold
# ---------------------------------------------------------------------------


class TestCreateScaffold:
    """Tests for _create_scaffold internal helper."""

    def test_creates_research_dir(self, tmp_path):
        from channel_assistant.project_init import _create_scaffold

        project_dir = tmp_path / "1. Test Project"
        project_dir.mkdir()
        _create_scaffold(project_dir)
        assert (project_dir / "research").is_dir()

    def test_creates_assets_dir(self, tmp_path):
        from channel_assistant.project_init import _create_scaffold

        project_dir = tmp_path / "1. Test Project"
        project_dir.mkdir()
        _create_scaffold(project_dir)
        assert (project_dir / "assets").is_dir()

    def test_creates_script_dir(self, tmp_path):
        from channel_assistant.project_init import _create_scaffold

        project_dir = tmp_path / "1. Test Project"
        project_dir.mkdir()
        _create_scaffold(project_dir)
        assert (project_dir / "script").is_dir()

    def test_idempotent_when_dirs_exist(self, tmp_path):
        from channel_assistant.project_init import _create_scaffold

        project_dir = tmp_path / "1. Test Project"
        project_dir.mkdir()
        _create_scaffold(project_dir)
        # Should not raise on second call
        _create_scaffold(project_dir)
        assert (project_dir / "research").is_dir()


# ---------------------------------------------------------------------------
# Tests for _append_past_topic
# ---------------------------------------------------------------------------


class TestAppendPastTopic:
    """Tests for _append_past_topic internal helper."""

    def test_appends_canonical_format(self, tmp_path):
        from channel_assistant.project_init import _append_past_topic

        path = tmp_path / "past_topics.md"
        path.write_text("", encoding="utf-8")
        _append_past_topic(path, "My Test Title", "A short hook sentence")
        content = path.read_text(encoding="utf-8")
        assert "**My Test Title**" in content
        assert "A short hook sentence" in content

    def test_appends_date_in_format(self, tmp_path):
        from channel_assistant.project_init import _append_past_topic
        import re

        path = tmp_path / "past_topics.md"
        path.write_text("", encoding="utf-8")
        _append_past_topic(path, "Test", "hook")
        content = path.read_text(encoding="utf-8")
        # Should contain YYYY-MM-DD format
        assert re.search(r"\d{4}-\d{2}-\d{2}", content)

    def test_appends_to_existing_content(self, tmp_path):
        from channel_assistant.project_init import _append_past_topic

        path = tmp_path / "past_topics.md"
        path.write_text(
            "- **Existing Topic** | 2025-01-01 | Existing hook\n",
            encoding="utf-8",
        )
        _append_past_topic(path, "New Topic", "New hook")
        content = path.read_text(encoding="utf-8")
        assert "Existing Topic" in content
        assert "New Topic" in content

    def test_creates_file_if_missing(self, tmp_path):
        from channel_assistant.project_init import _append_past_topic

        path = tmp_path / "past_topics.md"
        assert not path.exists()
        _append_past_topic(path, "New Topic", "New hook")
        assert path.exists()

    def test_round_trips_through_load_past_topics(self, tmp_path):
        """Entry written by _append_past_topic must be read back by _load_past_topics."""
        from channel_assistant.project_init import _append_past_topic
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text("", encoding="utf-8")
        _append_past_topic(path, "The Dark Cult of Rome", "A secret society that killed senators")
        titles = _load_past_topics(path)
        assert "The Dark Cult of Rome" in titles

    def test_multiple_appends_all_readable(self, tmp_path):
        from channel_assistant.project_init import _append_past_topic
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text("", encoding="utf-8")
        _append_past_topic(path, "First Topic", "First hook")
        _append_past_topic(path, "Second Topic", "Second hook")
        titles = _load_past_topics(path)
        assert "First Topic" in titles
        assert "Second Topic" in titles


# ---------------------------------------------------------------------------
# Tests for _write_metadata
# ---------------------------------------------------------------------------


class TestWriteMetadata:
    """Tests for _write_metadata internal helper."""

    @pytest.fixture
    def variants(self):
        return make_variants(recommended_idx=4)

    def test_creates_metadata_file(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Test Title", variants, "A great description.", "## Brief content")
        assert path.exists()

    def test_title_in_header(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "My Topic Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        assert "My Topic Title" in content

    def test_variants_all_written(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        for i in range(1, 6):
            assert f"Title Variant {i}" in content

    def test_recommended_label_present(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        assert "RECOMMENDED" in content

    def test_description_written(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "A compelling description sentence.", "brief")
        content = path.read_text(encoding="utf-8")
        assert "A compelling description sentence." in content

    def test_brief_markdown_written(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        brief_md = "## 1. Test Topic\n\n**Hook:** The hook text here"
        _write_metadata(path, "Title", variants, "description", brief_md)
        content = path.read_text(encoding="utf-8")
        assert "The hook text here" in content

    def test_section_headers_present(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        assert "## Title Variants" in content
        assert "## YouTube Description" in content
        assert "## Topic Brief" in content

    def test_table_headers_present(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        assert "| # |" in content or "| # | Title" in content

    def test_hook_types_in_table(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        assert "question" in content
        assert "statement" in content

    def test_created_date_in_header(self, tmp_path, variants):
        from channel_assistant.project_init import _write_metadata
        import re

        path = tmp_path / "metadata.md"
        _write_metadata(path, "Title", variants, "description", "brief")
        content = path.read_text(encoding="utf-8")
        # Created date in YYYY-MM-DD format
        assert re.search(r"\d{4}-\d{2}-\d{2}", content)


# ---------------------------------------------------------------------------
# Tests for init_project (public API)
# ---------------------------------------------------------------------------


class TestInitProject:
    """Tests for init_project public function."""

    @pytest.fixture
    def variants(self):
        return make_variants()

    @pytest.fixture
    def root(self, tmp_path):
        """Set up a minimal project root with past_topics.md."""
        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "channel" / "past_topics.md").write_text(
            "", encoding="utf-8"
        )
        return tmp_path

    def test_creates_numbered_directory(self, root, variants):
        from channel_assistant.project_init import init_project

        project_dir = init_project(
            root=root,
            title="Test Topic",
            hook="A compelling hook",
            title_variants=variants,
            description="Test description.",
            brief_markdown="## Brief",
        )
        assert project_dir.is_dir()
        assert project_dir.name.startswith("1.")

    def test_increments_past_existing(self, root, variants):
        from channel_assistant.project_init import init_project

        # Create a pre-existing project
        (root / "projects").mkdir()
        (root / "projects" / "1. Existing Project").mkdir()

        project_dir = init_project(
            root=root,
            title="New Topic",
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        assert project_dir.name.startswith("2.")

    def test_scaffold_subdirs_exist(self, root, variants):
        from channel_assistant.project_init import init_project

        project_dir = init_project(
            root=root,
            title="Test Topic",
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        assert (project_dir / "research").is_dir()
        assert (project_dir / "assets").is_dir()
        assert (project_dir / "script").is_dir()

    def test_metadata_file_created(self, root, variants):
        from channel_assistant.project_init import init_project

        project_dir = init_project(
            root=root,
            title="Test Topic",
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        assert (project_dir / "metadata.md").is_file()

    def test_appends_past_topic(self, root, variants):
        from channel_assistant.project_init import init_project
        from channel_assistant.topics import _load_past_topics

        init_project(
            root=root,
            title="The Dark Experiment",
            hook="Scientists crossed a line",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        past_topics_path = root / "context" / "channel" / "past_topics.md"
        titles = _load_past_topics(past_topics_path)
        assert "The Dark Experiment" in titles

    def test_sanitizes_forbidden_chars(self, root, variants):
        from channel_assistant.project_init import init_project

        project_dir = init_project(
            root=root,
            title='Title: The "Bad" One?',
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        for ch in '<>:"/\\|?*':
            assert ch not in project_dir.name

    def test_returns_project_dir_path(self, root, variants):
        from channel_assistant.project_init import init_project

        result = init_project(
            root=root,
            title="Test Topic",
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        assert isinstance(result, Path)
        assert result.is_dir()

    def test_title_length_check_warns_not_fails(self, root, variants, capsys):
        """A variant with >70 chars should log a warning but not raise."""
        from channel_assistant.project_init import init_project

        long_variants = list(variants)
        long_variants[0] = {
            "title": "A" * 75,  # 75 chars, exceeds 70-char limit
            "hook_type": "question",
            "recommended": False,
            "notes": "",
        }

        # Should not raise
        project_dir = init_project(
            root=root,
            title="Test Topic",
            hook="hook",
            title_variants=long_variants,
            description="desc",
            brief_markdown="brief",
        )
        assert project_dir.is_dir()
        # Warning should be printed somewhere (stdout or stderr)
        captured = capsys.readouterr()
        assert "70" in captured.out or "70" in captured.err or "Warning" in captured.out or "warning" in captured.out.lower()

    def test_creates_projects_dir_if_missing(self, root, variants):
        """projects/ doesn't exist — init_project must create it."""
        from channel_assistant.project_init import init_project

        assert not (root / "projects").exists()
        project_dir = init_project(
            root=root,
            title="First Project",
            hook="hook",
            title_variants=variants,
            description="desc",
            brief_markdown="brief",
        )
        assert (root / "projects").is_dir()
        assert project_dir.is_dir()


# ---------------------------------------------------------------------------
# Tests for load_project_inputs (public API)
# ---------------------------------------------------------------------------


class TestLoadProjectInputs:
    """Tests for load_project_inputs public function."""

    def _make_topic_briefs(self, tmp_path, n_topics=3):
        """Write a topic_briefs.md with n numbered topic sections."""
        briefs_dir = tmp_path / "context" / "topics"
        briefs_dir.mkdir(parents=True)
        lines = ["# Topic Briefs", "", "*Generated: 2026-03-11 10:00 UTC*", ""]
        for i in range(1, n_topics + 1):
            lines.extend([
                f"## {i}. Topic Number {i}",
                "",
                f"**Hook:** Hook for topic {i}",
                "",
                "---",
                "",
            ])
        (briefs_dir / "topic_briefs.md").write_text("\n".join(lines), encoding="utf-8")

    def test_raises_file_not_found_when_briefs_missing(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        with pytest.raises(FileNotFoundError):
            load_project_inputs(tmp_path, topic_number=1)

    def test_returns_dict_with_expected_keys(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path)
        result = load_project_inputs(tmp_path, topic_number=1)
        assert "brief_markdown" in result
        assert "title_patterns" in result

    def test_brief_markdown_contains_topic_content(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path, n_topics=3)
        result = load_project_inputs(tmp_path, topic_number=2)
        assert "Topic Number 2" in result["brief_markdown"]

    def test_brief_markdown_does_not_contain_other_topic(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path, n_topics=3)
        result = load_project_inputs(tmp_path, topic_number=1)
        # Should extract only topic 1's section, not topic 2 or 3
        assert "Topic Number 2" not in result["brief_markdown"]
        assert "Topic Number 3" not in result["brief_markdown"]

    def test_title_patterns_is_string(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path)
        result = load_project_inputs(tmp_path, topic_number=1)
        assert isinstance(result["title_patterns"], str)

    def test_title_patterns_from_analysis_when_present(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path)
        # Create analysis.md with Title Patterns section
        analysis_dir = tmp_path / "context" / "competitors"
        analysis_dir.mkdir(parents=True)
        analysis_content = (
            "# Competitor Analysis Report\n\n"
            "## Channel Stats\n\nSome stats\n\n"
            "## Title Patterns\n\nPattern 1: 'The X That Y'\nPattern 2: 'How X Became Y'\n\n"
        )
        (analysis_dir / "analysis.md").write_text(analysis_content, encoding="utf-8")

        result = load_project_inputs(tmp_path, topic_number=1)
        assert "Pattern 1" in result["title_patterns"] or "Title Patterns" in result["title_patterns"]

    def test_title_patterns_empty_when_analysis_missing(self, tmp_path):
        from channel_assistant.project_init import load_project_inputs

        self._make_topic_briefs(tmp_path)
        # No analysis.md — title_patterns should still work (return empty string)
        result = load_project_inputs(tmp_path, topic_number=1)
        assert isinstance(result["title_patterns"], str)
