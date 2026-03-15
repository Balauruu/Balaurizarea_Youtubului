"""Tests for graphics_generator renderers — each produces valid 1920×1080 PNG.

Uses tmp_path fixture for output. Validates file exists, is valid PNG, and correct dimensions.
"""
from pathlib import Path

import pytest
from PIL import Image

from graphics_generator.renderers.silhouette import render as render_silhouette
from graphics_generator.renderers.icon import render as render_icon
from graphics_generator.renderers.texture import render as render_texture
from graphics_generator.renderers.glitch import render as render_glitch
from graphics_generator.renderers.noise import render as render_noise
from graphics_generator.renderers.code_screen import render as render_code_screen
from graphics_generator.renderers.profile_card import render as render_profile_card
from graphics_generator.renderers import RENDERER_REGISTRY


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_shot() -> dict:
    """Minimal shot dict for renderer testing."""
    return {
        "id": "S042",
        "chapter": 3,
        "chapter_title": "The Truth",
        "narrative_context": "Revealing the conspiracy.",
        "visual_need": "Dark figure emerging from shadows.",
        "building_block": "Silhouette Figure",
        "shotlist_type": "animation",
    }


def _assert_valid_png(path: Path, expected_w: int = 1920, expected_h: int = 1080) -> None:
    """Assert the file exists, is valid PNG, and has correct dimensions."""
    assert path.exists(), f"File not found: {path}"
    assert path.stat().st_size > 0, f"File is empty: {path}"

    img = Image.open(str(path))
    assert img.format == "PNG", f"Expected PNG, got {img.format}"
    assert img.size == (expected_w, expected_h), f"Expected {expected_w}x{expected_h}, got {img.size}"
    assert img.mode == "RGBA", f"Expected RGBA mode, got {img.mode}"


# ---------------------------------------------------------------------------
# Individual renderer tests
# ---------------------------------------------------------------------------

class TestSilhouetteRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_silhouette(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_silhouette(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "silhouette_figure" in result.name

    def test_with_label(self, sample_shot: dict, tmp_path: Path) -> None:
        sample_shot["text_content"] = "FAITH HEALER"
        result = render_silhouette(sample_shot, tmp_path)
        _assert_valid_png(result)


class TestIconRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        sample_shot["building_block"] = "Symbolic Icon"
        result = render_icon(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_icon(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "symbolic_icon" in result.name


class TestTextureRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_texture(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_texture(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "abstract_texture" in result.name


class TestGlitchRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_glitch(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_glitch(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "glitch_stinger" in result.name


class TestNoiseRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_noise(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_noise(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "static_noise" in result.name


class TestCodeScreenRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_code_screen(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_code_screen(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "code_screen" in result.name


class TestProfileCardRenderer:
    def test_produces_valid_png(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_profile_card(sample_shot, tmp_path)
        _assert_valid_png(result)

    def test_filename_includes_shot_id(self, sample_shot: dict, tmp_path: Path) -> None:
        result = render_profile_card(sample_shot, tmp_path)
        assert "S042" in result.name
        assert "profile_card" in result.name

    def test_with_names(self, sample_shot: dict, tmp_path: Path) -> None:
        sample_shot["names"] = ["Alice", "Bob", "Charlie"]
        result = render_profile_card(sample_shot, tmp_path)
        _assert_valid_png(result)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestRendererRegistry:
    def test_all_code_gen_blocks_registered(self) -> None:
        """All 7 Pillow building blocks must be in the registry."""
        expected = {
            "Silhouette Figure",
            "Symbolic Icon",
            "Abstract Texture",
            "Glitch Stinger",
            "Static Noise / Corruption",
            "Retro Code Screen",
            "Character Profile Card",
        }
        assert expected.issubset(set(RENDERER_REGISTRY.keys()))

    def test_comfyui_blocks_not_registered(self) -> None:
        """ComfyUI blocks should not be in the Pillow registry."""
        comfyui_blocks = {
            "Concept Diagram",
            "Ritual Illustration",
            "Glitch Icon",
            "Data Moshing Montage",
            "Location Map",
        }
        for bb in comfyui_blocks:
            assert bb not in RENDERER_REGISTRY

    def test_all_registered_renderers_callable(self) -> None:
        """Every registry value must be callable."""
        for name, renderer in RENDERER_REGISTRY.items():
            assert callable(renderer), f"Renderer for '{name}' is not callable"
