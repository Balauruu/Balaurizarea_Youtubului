"""Tests for visual_orchestrator.schema — shotlist.json schema validator.

Each test modifies the valid fixture minimally to trigger exactly one error class.
"""
import copy

import pytest

from visual_orchestrator.schema import validate_shotlist


# ---------------------------------------------------------------------------
# Minimal valid shotlist fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_shotlist() -> dict:
    """Return a minimal valid shotlist with 3 shots — enough for sequencing tests."""
    return {
        "project": "Test Project",
        "guide_source": "Test Guide",
        "generated": "2026-03-15T00:00:00Z",
        "shots": [
            {
                "id": "S001",
                "chapter": 1,
                "chapter_title": "The Beginning",
                "narrative_context": "Opening scene establishing the setting.",
                "visual_need": "Wide establishing shot of location.",
                "building_block": "Archival Footage",
                "shotlist_type": "archival_video",
                "text_content": None,
            },
            {
                "id": "S002",
                "chapter": 1,
                "chapter_title": "The Beginning",
                "narrative_context": "Key testimony from a witness.",
                "visual_need": "Quote card with testimony text.",
                "building_block": "Quote Card",
                "shotlist_type": "text_overlay",
                "text_content": "They put them in cardboard boxes.",
            },
            {
                "id": "S003",
                "chapter": 2,
                "chapter_title": "The Investigation",
                "narrative_context": "Geographical context for events.",
                "visual_need": "Map showing location of events.",
                "building_block": "Animated Map",
                "shotlist_type": "map",
                "text_content": None,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_shotlist_passes(valid_shotlist: dict) -> None:
    """A well-formed shotlist produces zero errors."""
    errors = validate_shotlist(valid_shotlist)
    assert errors == []


# ---------------------------------------------------------------------------
# Top-level structure errors
# ---------------------------------------------------------------------------

def test_missing_top_level_key(valid_shotlist: dict) -> None:
    """Removing a required top-level key is caught."""
    del valid_shotlist["project"]
    errors = validate_shotlist(valid_shotlist)
    assert any("Missing required top-level key: 'project'" in e for e in errors)


# ---------------------------------------------------------------------------
# Per-shot field errors
# ---------------------------------------------------------------------------

def test_missing_shot_field(valid_shotlist: dict) -> None:
    """Removing a required shot field is caught with shot ID context."""
    del valid_shotlist["shots"][0]["building_block"]
    errors = validate_shotlist(valid_shotlist)
    assert any("S001" in e and "building_block" in e for e in errors)


def test_invalid_shotlist_type(valid_shotlist: dict) -> None:
    """An invalid shotlist_type enum value is caught."""
    valid_shotlist["shots"][0]["shotlist_type"] = "hologram"
    errors = validate_shotlist(valid_shotlist)
    assert any("invalid shotlist_type 'hologram'" in e for e in errors)


def test_invalid_id_format(valid_shotlist: dict) -> None:
    """A malformed shot ID like 'shot1' (not S001 pattern) is caught."""
    valid_shotlist["shots"][0]["id"] = "shot1"
    errors = validate_shotlist(valid_shotlist)
    assert any("invalid ID format 'shot1'" in e for e in errors)


# ---------------------------------------------------------------------------
# text_content rules (R002)
# ---------------------------------------------------------------------------

def test_text_overlay_without_text_content(valid_shotlist: dict) -> None:
    """text_overlay shot with empty text_content is caught."""
    valid_shotlist["shots"][1]["text_content"] = None
    errors = validate_shotlist(valid_shotlist)
    assert any("text_overlay" in e and "text_content" in e and "S002" in e for e in errors)


def test_non_text_overlay_with_text_content(valid_shotlist: dict) -> None:
    """Non-text_overlay shot with populated text_content is caught."""
    valid_shotlist["shots"][0]["text_content"] = "Should not be here"
    errors = validate_shotlist(valid_shotlist)
    assert any("text_content" in e and "S001" in e for e in errors)


# ---------------------------------------------------------------------------
# Sequencing constraints
# ---------------------------------------------------------------------------

def test_back_to_back_glitch_shots(valid_shotlist: dict) -> None:
    """Two consecutive glitch building blocks are caught."""
    valid_shotlist["shots"][0]["building_block"] = "Glitch Stinger"
    valid_shotlist["shots"][0]["shotlist_type"] = "animation"
    valid_shotlist["shots"][0]["text_content"] = None
    valid_shotlist["shots"][1]["building_block"] = "Static Noise / Corruption"
    valid_shotlist["shots"][1]["shotlist_type"] = "animation"
    valid_shotlist["shots"][1]["text_content"] = None
    errors = validate_shotlist(valid_shotlist)
    assert any("back-to-back glitch" in e for e in errors)


def test_more_than_3_consecutive_text_overlay(valid_shotlist: dict) -> None:
    """4 consecutive text_overlay shots are caught."""
    # Build 4 consecutive text_overlay shots
    shots = []
    for i in range(1, 5):
        shots.append({
            "id": f"S{i:03d}",
            "chapter": 1,
            "chapter_title": "Chapter",
            "narrative_context": f"Context {i}",
            "visual_need": f"Need {i}",
            "building_block": "Quote Card",
            "shotlist_type": "text_overlay",
            "text_content": f"Text {i}",
        })
    # Add a non-text_overlay at the end to close the run for the validator
    shots.append({
        "id": "S005",
        "chapter": 1,
        "chapter_title": "Chapter",
        "narrative_context": "Context 5",
        "visual_need": "Need 5",
        "building_block": "Archival Footage",
        "shotlist_type": "archival_video",
        "text_content": None,
    })
    valid_shotlist["shots"] = shots
    errors = validate_shotlist(valid_shotlist)
    assert any("consecutive text_overlay" in e for e in errors)


def test_more_than_3_consecutive_silhouette_figure(valid_shotlist: dict) -> None:
    """4 consecutive Silhouette Figure animation shots are caught."""
    shots = []
    for i in range(1, 5):
        shots.append({
            "id": f"S{i:03d}",
            "chapter": 1,
            "chapter_title": "Chapter",
            "narrative_context": f"Context {i}",
            "visual_need": f"Need {i}",
            "building_block": "Silhouette Figure",
            "shotlist_type": "animation",
            "text_content": None,
        })
    # Add a different shot to close the run
    shots.append({
        "id": "S005",
        "chapter": 1,
        "chapter_title": "Chapter",
        "narrative_context": "Context 5",
        "visual_need": "Need 5",
        "building_block": "Archival Footage",
        "shotlist_type": "archival_video",
        "text_content": None,
    })
    valid_shotlist["shots"] = shots
    errors = validate_shotlist(valid_shotlist)
    assert any("consecutive Silhouette Figure" in e for e in errors)
