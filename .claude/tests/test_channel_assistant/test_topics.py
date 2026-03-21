"""Tests for channel_assistant.topics module."""

import pytest
from pathlib import Path


class TestLoadPastTopics:
    """Tests for _load_past_topics function."""

    def test_missing_file_returns_empty(self, tmp_path):
        from channel_assistant.topics import _load_past_topics

        result = _load_past_topics(tmp_path / "nonexistent.md")
        assert result == []

    def test_empty_file_returns_empty(self, tmp_path):
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text("", encoding="utf-8")
        result = _load_past_topics(path)
        assert result == []

    def test_extracts_bold_titles_canonical_format(self, tmp_path):
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text(
            "- **The Matamoros Murders** | 2026-01-01 | A cult killing spree\n"
            "- **Operation Paperclip** | 2025-11-15 | US gov Nazi recruitment\n",
            encoding="utf-8",
        )
        result = _load_past_topics(path)
        assert result == ["The Matamoros Murders", "Operation Paperclip"]

    def test_extracts_bold_titles_no_dash_prefix(self, tmp_path):
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text(
            "**Flight 980** | 2025-10-05 | Lost plane mystery\n",
            encoding="utf-8",
        )
        result = _load_past_topics(path)
        assert result == ["Flight 980"]

    def test_mixed_content_extracts_only_bold_titles(self, tmp_path):
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text(
            "# Past Topics\n"
            "\n"
            "Some intro text.\n"
            "\n"
            "- **The Matamoros Murders** | 2026-01-01 | summary\n"
            "- Regular list item without bold\n"
            "  - **Nested Item** | 2025-09-01 | something\n",
            encoding="utf-8",
        )
        result = _load_past_topics(path)
        assert "The Matamoros Murders" in result
        assert "Nested Item" in result
        # Should NOT include the plain list item
        assert len([r for r in result if r == "Regular list item without bold"]) == 0

    def test_handles_only_bold_prefix_format(self, tmp_path):
        """Lines starting with **Title** without a dash prefix."""
        from channel_assistant.topics import _load_past_topics

        path = tmp_path / "past_topics.md"
        path.write_text(
            "**Colonia Dignidad** | 2025-08-20 | Chilean torture colony\n"
            "normal line\n",
            encoding="utf-8",
        )
        result = _load_past_topics(path)
        assert "Colonia Dignidad" in result
        assert len(result) == 1


class TestCheckDuplicates:
    """Tests for check_duplicates function."""

    def test_empty_past_titles_returns_none(self):
        from channel_assistant.topics import check_duplicates

        result = check_duplicates("The Matamoros Murders", [])
        assert result is None

    def test_exact_match_returns_past_title(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders", "Operation Paperclip"]
        result = check_duplicates("The Matamoros Murders", past)
        assert result == "The Matamoros Murders"

    def test_case_insensitive_exact_match(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders"]
        result = check_duplicates("the matamoros murders", past)
        assert result == "The Matamoros Murders"

    def test_near_match_above_threshold_returns_match(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders"]
        # Very similar title should be flagged
        result = check_duplicates("The Matamoros Cult Murders", past, threshold=0.7)
        assert result == "The Matamoros Murders"

    def test_distinct_topic_returns_none(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders"]
        result = check_duplicates("Flight 980", past)
        assert result is None

    def test_default_threshold_distinct_returns_none(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders", "Operation Paperclip"]
        result = check_duplicates("Flight 980: The Lost Plane Mystery", past)
        assert result is None

    def test_returns_closest_matching_past_title(self):
        from channel_assistant.topics import check_duplicates

        past = ["The Matamoros Murders", "Operation Paperclip", "Flight 980"]
        # Should return the most-similar match
        result = check_duplicates("Operation Paperclip Secret", past, threshold=0.6)
        assert result == "Operation Paperclip"


class TestLoadTopicInputs:
    """Tests for load_topic_inputs function."""

    def test_missing_analysis_raises_file_not_found(self, tmp_path):
        from channel_assistant.topics import load_topic_inputs

        # Create channel.md and past_topics.md but NOT analysis.md
        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "competitors").mkdir(parents=True)
        (tmp_path / "context" / "channel" / "channel.md").write_text(
            "# Channel DNA", encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "past_topics.md").write_text(
            "", encoding="utf-8"
        )
        with pytest.raises(FileNotFoundError):
            load_topic_inputs(tmp_path)

    def test_missing_channel_dna_raises_file_not_found(self, tmp_path):
        from channel_assistant.topics import load_topic_inputs

        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "competitors").mkdir(parents=True)
        (tmp_path / "context" / "competitors" / "analysis.md").write_text(
            "# Analysis", encoding="utf-8"
        )
        # channel.md missing
        (tmp_path / "context" / "channel" / "past_topics.md").write_text(
            "", encoding="utf-8"
        )
        with pytest.raises(FileNotFoundError):
            load_topic_inputs(tmp_path)

    def test_missing_past_topics_returns_empty_list(self, tmp_path):
        from channel_assistant.topics import load_topic_inputs

        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "competitors").mkdir(parents=True)
        (tmp_path / "context" / "competitors" / "analysis.md").write_text(
            "# Analysis\nsome content", encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "channel.md").write_text(
            "# Channel DNA\nchannel content", encoding="utf-8"
        )
        # past_topics.md is missing

        inputs = load_topic_inputs(tmp_path)
        assert inputs["past_topics"] == []

    def test_returns_dict_with_expected_keys(self, tmp_path):
        from channel_assistant.topics import load_topic_inputs

        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "competitors").mkdir(parents=True)
        (tmp_path / "context" / "competitors" / "analysis.md").write_text(
            "# Analysis\nsome content", encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "channel.md").write_text(
            "# Channel DNA", encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "past_topics.md").write_text(
            "- **The Matamoros Murders** | 2026-01-01 | summary\n",
            encoding="utf-8",
        )

        inputs = load_topic_inputs(tmp_path)
        assert set(inputs.keys()) == {"analysis", "channel_dna", "past_topics", "trends", "content_gaps"}
        assert isinstance(inputs["analysis"], str)
        assert isinstance(inputs["channel_dna"], str)
        assert isinstance(inputs["past_topics"], list)
        assert inputs["past_topics"] == ["The Matamoros Murders"]
        assert isinstance(inputs["trends"], str)
        assert isinstance(inputs["content_gaps"], str)

    def test_reads_file_contents_correctly(self, tmp_path):
        from channel_assistant.topics import load_topic_inputs

        (tmp_path / "context" / "channel").mkdir(parents=True)
        (tmp_path / "context" / "competitors").mkdir(parents=True)
        analysis_text = "# Analysis\nCompetitor data here"
        dna_text = "# Channel DNA\nVoice: deadpan"
        (tmp_path / "context" / "competitors" / "analysis.md").write_text(
            analysis_text, encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "channel.md").write_text(
            dna_text, encoding="utf-8"
        )
        (tmp_path / "context" / "channel" / "past_topics.md").write_text(
            "", encoding="utf-8"
        )

        inputs = load_topic_inputs(tmp_path)
        assert inputs["analysis"] == analysis_text
        assert inputs["channel_dna"] == dna_text


class TestWriteTopicBriefs:
    """Tests for write_topic_briefs function."""

    @pytest.fixture
    def sample_brief(self):
        return {
            "title": "The Narcosatanist of Matamoros",
            "pillar": "Cults & Psychological Control",
            "hook": "A US college student was ritually murdered by a drug cult on the Mexico border.",
            "timeline": [
                "1986: Adolfo Constanzo forms cult in Mexico City",
                "1989: Mark Kilroy is abducted at the border",
                "1989: Cult compound raided, 15 bodies found",
                "1989: Constanzo killed by police",
            ],
            "scores": {
                "obscurity": 4,
                "complexity": 4,
                "shock_factor": 5,
                "verifiability": 5,
            },
            "justification": {
                "obscurity": "Known in true crime circles but not mainstream",
                "complexity": "Multi-layered: drug trafficking, Palo Mayombe, US-Mexico dynamics",
                "shock_factor": "Ritual murders including a US citizen at the border",
                "verifiability": "FBI records, Mexican police reports, US news archives",
            },
            "estimated_runtime_min": 35,
            "duplicate_of": None,
            "tags": ["UNDERSERVED CLUSTER: Cults & Psychological Control"],
        }

    def test_creates_output_directory_if_absent(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        output_path = tmp_path / "new_dir" / "subdir" / "topic_briefs.md"
        write_topic_briefs([sample_brief], output_path)
        assert output_path.exists()

    def test_writes_valid_markdown_header(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        output_path = tmp_path / "topic_briefs.md"
        write_topic_briefs([sample_brief], output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "# Topic Briefs" in content

    def test_writes_generation_timestamp(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        output_path = tmp_path / "topic_briefs.md"
        write_topic_briefs([sample_brief], output_path)
        content = output_path.read_text(encoding="utf-8")
        # Should contain some timestamp-like string
        assert "Generated" in content or "generated" in content

    def test_writes_all_schema_fields(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        output_path = tmp_path / "topic_briefs.md"
        write_topic_briefs([sample_brief], output_path)
        content = output_path.read_text(encoding="utf-8")

        assert "The Narcosatanist of Matamoros" in content
        assert "Cults & Psychological Control" in content
        # hook
        assert "US college student" in content
        # timeline entries
        assert "1986" in content
        assert "Adolfo Constanzo" in content
        # scores in O:X C:X S:X format
        assert "O:4" in content
        assert "C:4" in content
        assert "S:5" in content
        assert "V:5" in content
        # total score out of 20
        assert "/20" in content or "18/20" in content
        # runtime
        assert "35" in content
        # justification text
        assert "ritual murders" in content.lower() or "Ritual murders" in content

    def test_overwrites_on_subsequent_call(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        output_path = tmp_path / "topic_briefs.md"
        write_topic_briefs([sample_brief], output_path)
        first_content = output_path.read_text(encoding="utf-8")

        modified = dict(sample_brief)
        modified["title"] = "Completely Different Topic"
        write_topic_briefs([modified], output_path)
        second_content = output_path.read_text(encoding="utf-8")

        # Old title should be gone, new title present
        assert "The Narcosatanist of Matamoros" not in second_content
        assert "Completely Different Topic" in second_content

    def test_multiple_briefs_all_written(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        brief2 = dict(sample_brief)
        brief2["title"] = "Operation Paperclip"
        write_topic_briefs([sample_brief, brief2], output_path=tmp_path / "topic_briefs.md")
        content = (tmp_path / "topic_briefs.md").read_text(encoding="utf-8")
        assert "The Narcosatanist of Matamoros" in content
        assert "Operation Paperclip" in content

    def test_numbered_headings(self, tmp_path, sample_brief):
        from channel_assistant.topics import write_topic_briefs

        brief2 = dict(sample_brief)
        brief2["title"] = "Second Topic"
        write_topic_briefs(
            [sample_brief, brief2], output_path=tmp_path / "topic_briefs.md"
        )
        content = (tmp_path / "topic_briefs.md").read_text(encoding="utf-8")
        assert "## 1." in content or "## Topic 1" in content or "**1.**" in content
        assert "## 2." in content or "## Topic 2" in content or "**2.**" in content


class TestFormatChatCards:
    """Tests for format_chat_cards function."""

    @pytest.fixture
    def sample_brief(self):
        return {
            "title": "The Narcosatanist of Matamoros",
            "pillar": "Cults & Psychological Control",
            "hook": "A US college student was ritually murdered by a drug cult.",
            "timeline": ["1989: event A", "1989: event B"],
            "scores": {
                "obscurity": 4,
                "complexity": 4,
                "shock_factor": 5,
                "verifiability": 5,
            },
            "justification": {
                "obscurity": "Known in true crime circles",
                "complexity": "Multi-layered",
                "shock_factor": "Ritual murders",
                "verifiability": "FBI records",
            },
            "estimated_runtime_min": 35,
            "duplicate_of": None,
            "tags": [],
        }

    def test_returns_string(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert isinstance(result, str)

    def test_numbered_card(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert "[1]" in result

    def test_contains_title_and_hook(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert "The Narcosatanist of Matamoros" in result
        assert "A US college student" in result

    def test_contains_score_line(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert "O:4" in result
        assert "C:4" in result
        assert "S:5" in result
        assert "V:5" in result
        assert "18/20" in result

    def test_contains_runtime_and_pillar(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert "35min" in result or "35 min" in result
        assert "Cults" in result

    def test_duplicate_warning_shown_when_present(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        brief_with_dup = dict(sample_brief)
        brief_with_dup["duplicate_of"] = "The Matamoros Murders"
        result = format_chat_cards([brief_with_dup])
        assert "Similar to" in result or "Duplicate" in result or "duplicate" in result
        assert "The Matamoros Murders" in result

    def test_no_duplicate_warning_when_none(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        result = format_chat_cards([sample_brief])
        assert "Similar to" not in result

    def test_tag_shown_when_present(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        brief_with_tag = dict(sample_brief)
        brief_with_tag["tags"] = ["UNDERSERVED CLUSTER: Cults & Psychological Control"]
        result = format_chat_cards([brief_with_tag])
        assert "UNDERSERVED" in result

    def test_multiple_cards_numbered_sequentially(self, sample_brief):
        from channel_assistant.topics import format_chat_cards

        brief2 = dict(sample_brief)
        brief2["title"] = "Operation Paperclip"
        result = format_chat_cards([sample_brief, brief2])
        assert "[1]" in result
        assert "[2]" in result
        assert "Operation Paperclip" in result
