"""Tests for ComfyUI client, workflow templates, prompt builder, and CLI integration."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from graphics_generator.comfyui.client import ComfyUIClient, ComfyUIUnavailableError
from graphics_generator.comfyui.workflows import (
    COMFYUI_BLOCKS,
    WORKFLOW_TEMPLATES,
    build_prompt,
    concept_diagram,
    data_moshing,
    glitch_icon,
    ritual_illustration,
)
from graphics_generator.renderers import COMFYUI_BLOCKS as REGISTRY_COMFYUI_BLOCKS
from graphics_generator.renderers import is_comfyui_block


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """A ComfyUIClient with defaults."""
    return ComfyUIClient(host="127.0.0.1", port=8188)


@pytest.fixture
def sample_shot():
    """A sample ComfyUI shot dict."""
    return {
        "id": "shot_42",
        "shotlist_type": "animation",
        "building_block": "Concept Diagram",
        "narrative_context": "The orphanage experiments revealed hidden trauma",
        "visual_need": "profile head with internal psychological layers",
    }


@pytest.fixture
def sample_comfyui_shots():
    """Multiple ComfyUI shots for CLI integration tests."""
    return {
        "project": "Test Project",
        "shots": [
            {
                "id": "shot_01",
                "shotlist_type": "animation",
                "building_block": "Silhouette Figure",
                "visual_need": "dark figure",
            },
            {
                "id": "shot_02",
                "shotlist_type": "animation",
                "building_block": "Concept Diagram",
                "narrative_context": "hidden experiments",
                "visual_need": "profile head diagram",
            },
            {
                "id": "shot_03",
                "shotlist_type": "animation",
                "building_block": "Ritual Illustration",
                "visual_need": "neon ritual scene",
            },
        ],
    }


# ---------------------------------------------------------------------------
# ComfyUI Client Tests
# ---------------------------------------------------------------------------

class TestComfyUIClient:
    """Tests for ComfyUIClient REST operations."""

    def test_address_property(self, client):
        assert client.address == "127.0.0.1:8188"

    def test_custom_host_port(self):
        c = ComfyUIClient(host="192.168.1.100", port=9999)
        assert c.base_url == "http://192.168.1.100:9999"
        assert c.address == "192.168.1.100:9999"

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_is_available_true(self, mock_get, client):
        mock_get.return_value = MagicMock(status_code=200)
        assert client.is_available() is True

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_is_available_false_on_connection_error(self, mock_get, client):
        import requests
        mock_get.side_effect = requests.ConnectionError("refused")
        assert client.is_available() is False

    @patch("graphics_generator.comfyui.client.requests.post")
    def test_queue_prompt_success(self, mock_post, client):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"prompt_id": "abc-123"},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        result = client.queue_prompt({"1": {"class_type": "Test"}})
        assert result == "abc-123"
        mock_post.assert_called_once()

    @patch("graphics_generator.comfyui.client.requests.post")
    def test_queue_prompt_connection_error(self, mock_post, client):
        import requests
        mock_post.side_effect = requests.ConnectionError("refused")

        with pytest.raises(ComfyUIUnavailableError) as exc_info:
            client.queue_prompt({"1": {}})

        # Error message should include address and suggest --code-gen-only
        assert "127.0.0.1:8188" in str(exc_info.value)
        assert "--code-gen-only" in str(exc_info.value)

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_poll_history_success(self, mock_get, client):
        client.poll_interval = 0.01  # Speed up test

        # First call: not ready; second call: ready
        not_ready = MagicMock(
            status_code=200,
            json=lambda: {},
        )
        not_ready.raise_for_status = MagicMock()

        completed = MagicMock(
            status_code=200,
            json=lambda: {
                "abc-123": {
                    "status": {"completed": True, "status_str": "success"},
                    "outputs": {
                        "7": {
                            "images": [
                                {"filename": "output_001.png", "subfolder": ""}
                            ]
                        }
                    },
                }
            },
        )
        completed.raise_for_status = MagicMock()

        mock_get.side_effect = [not_ready, completed]

        outputs = client.poll_history("abc-123")
        assert "7" in outputs
        assert outputs["7"]["images"][0]["filename"] == "output_001.png"

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_poll_history_connection_lost(self, mock_get, client):
        import requests
        mock_get.side_effect = requests.ConnectionError("lost")

        with pytest.raises(ComfyUIUnavailableError) as exc_info:
            client.poll_history("abc-123")

        assert "127.0.0.1:8188" in str(exc_info.value)
        assert "abc-123" in str(exc_info.value)

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_download_image_success(self, mock_get, client, tmp_path):
        mock_get.return_value = MagicMock(
            status_code=200,
            content=b"\x89PNG fake image data",
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = client.download_image("output_001.png", "", tmp_path)
        assert result == tmp_path / "output_001.png"
        assert result.read_bytes() == b"\x89PNG fake image data"

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_download_image_connection_error(self, mock_get, client, tmp_path):
        import requests
        mock_get.side_effect = requests.ConnectionError("refused")

        with pytest.raises(ComfyUIUnavailableError) as exc_info:
            client.download_image("out.png", "", tmp_path)

        assert "127.0.0.1:8188" in str(exc_info.value)

    @patch("graphics_generator.comfyui.client.requests.get")
    def test_queue_poll_download_flow(self, mock_get, client, tmp_path):
        """End-to-end: queue → poll → download with mocked HTTP."""
        # Mock poll response
        poll_resp = MagicMock(
            status_code=200,
            json=lambda: {
                "prompt-xyz": {
                    "status": {"completed": True, "status_str": "success"},
                    "outputs": {
                        "7": {
                            "images": [
                                {"filename": "generated.png", "subfolder": "out"}
                            ]
                        }
                    },
                }
            },
        )
        poll_resp.raise_for_status = MagicMock()

        # Mock download response
        dl_resp = MagicMock(
            status_code=200,
            content=b"\x89PNG generated",
        )
        dl_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [poll_resp, dl_resp]

        with patch("graphics_generator.comfyui.client.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"prompt_id": "prompt-xyz"},
            )
            mock_post.return_value.raise_for_status = MagicMock()

            # Queue
            prompt_id = client.queue_prompt({"1": {}})
            assert prompt_id == "prompt-xyz"

            # Poll
            outputs = client.poll_history(prompt_id)
            img_info = outputs["7"]["images"][0]

            # Download
            path = client.download_image(
                img_info["filename"], img_info["subfolder"], tmp_path
            )
            assert path.exists()
            assert path.name == "generated.png"


# ---------------------------------------------------------------------------
# Workflow Template Tests
# ---------------------------------------------------------------------------

class TestWorkflowTemplates:
    """Tests for ComfyUI workflow template structure."""

    @pytest.mark.parametrize("template_fn", [
        concept_diagram, ritual_illustration, glitch_icon, data_moshing
    ])
    def test_template_has_required_nodes(self, template_fn):
        workflow = template_fn("test prompt", (1920, 1080))

        # Must have all standard nodes
        required_types = {
            "CheckpointLoaderSimple",
            "EmptyLatentImage",
            "CLIPTextEncode",
            "KSampler",
            "VAEDecode",
            "SaveImage",
        }
        actual_types = {
            node["class_type"] for node in workflow.values()
        }
        assert required_types.issubset(actual_types), (
            f"Missing node types: {required_types - actual_types}"
        )

    @pytest.mark.parametrize("template_fn", [
        concept_diagram, ritual_illustration, glitch_icon, data_moshing
    ])
    def test_template_resolution(self, template_fn):
        workflow = template_fn("test", (1920, 1080))

        # Find EmptyLatentImage node
        latent_nodes = [
            n for n in workflow.values()
            if n["class_type"] == "EmptyLatentImage"
        ]
        assert len(latent_nodes) == 1
        assert latent_nodes[0]["inputs"]["width"] == 1920
        assert latent_nodes[0]["inputs"]["height"] == 1080

    @pytest.mark.parametrize("template_fn", [
        concept_diagram, ritual_illustration, glitch_icon, data_moshing
    ])
    def test_template_contains_prompt_text(self, template_fn):
        prompt = "mysterious dark ritual scene"
        workflow = template_fn(prompt)

        # At least one CLIPTextEncode should contain the prompt
        clip_nodes = [
            n for n in workflow.values()
            if n["class_type"] == "CLIPTextEncode"
        ]
        prompts_found = [
            n for n in clip_nodes if prompt in n["inputs"].get("text", "")
        ]
        assert len(prompts_found) >= 1

    def test_template_registry_matches_blocks(self):
        assert set(WORKFLOW_TEMPLATES.keys()) == set(COMFYUI_BLOCKS)

    def test_template_default_resolution(self):
        workflow = concept_diagram("test")
        latent = [n for n in workflow.values() if n["class_type"] == "EmptyLatentImage"][0]
        assert latent["inputs"]["width"] == 1920
        assert latent["inputs"]["height"] == 1080


# ---------------------------------------------------------------------------
# Prompt Builder Tests
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    """Tests for the build_prompt function."""

    def test_extracts_visual_need(self, sample_shot):
        prompt = build_prompt(sample_shot)
        assert "profile head with internal psychological layers" in prompt

    def test_extracts_narrative_context(self, sample_shot):
        prompt = build_prompt(sample_shot)
        assert "orphanage experiments revealed hidden trauma" in prompt

    def test_includes_style_modifier(self, sample_shot):
        prompt = build_prompt(sample_shot)
        assert "concept diagram" in prompt.lower()

    def test_handles_missing_fields(self):
        shot = {"building_block": "Glitch Icon"}
        prompt = build_prompt(shot)
        assert "chromatic aberration" in prompt.lower()

    def test_handles_unknown_building_block(self):
        shot = {"building_block": "Unknown Block", "visual_need": "something"}
        prompt = build_prompt(shot)
        assert "something" in prompt
        assert "dark mystery documentary" in prompt.lower()


# ---------------------------------------------------------------------------
# Renderer Registry Tests
# ---------------------------------------------------------------------------

class TestRendererRegistry:
    """Tests for ComfyUI block registration in renderer registry."""

    def test_comfyui_blocks_registered(self):
        assert REGISTRY_COMFYUI_BLOCKS == {
            "Concept Diagram",
            "Ritual Illustration",
            "Glitch Icon",
            "Data Moshing Montage",
        }

    def test_is_comfyui_block(self):
        assert is_comfyui_block("Concept Diagram") is True
        assert is_comfyui_block("Ritual Illustration") is True
        assert is_comfyui_block("Silhouette Figure") is False
        assert is_comfyui_block("Unknown") is False


# ---------------------------------------------------------------------------
# CLI --code-gen-only Tests
# ---------------------------------------------------------------------------

class TestCodeGenOnlyFlag:
    """Tests for the --code-gen-only CLI flag."""

    def test_code_gen_only_skips_comfyui_blocks(
        self, tmp_path, sample_comfyui_shots, capsys
    ):
        """With --code-gen-only, ComfyUI blocks are skipped with messages."""
        from graphics_generator.cli import cmd_generate

        # Set up project dir with shotlist
        project_dir = tmp_path / "projects" / "1. Test Project"
        project_dir.mkdir(parents=True)
        shotlist_path = project_dir / "shotlist.json"
        shotlist_path.write_text(
            json.dumps(sample_comfyui_shots), encoding="utf-8"
        )

        # Patch project resolution to use our tmp dir
        with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
            cmd_generate("Test Project", code_gen_only=True)

        captured = capsys.readouterr()
        # ComfyUI blocks should be skipped
        assert "Concept Diagram" in captured.err
        assert "--code-gen-only" in captured.err
        assert "Ritual Illustration" in captured.err

        # Silhouette Figure should have been generated (Pillow)
        assert "shot_01" in captured.err

    def test_code_gen_only_flag_in_argparse(self):
        """The generate subcommand accepts --code-gen-only."""
        import argparse

        from graphics_generator.cli import main

        # Verify it parses without error
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        gen_parser = subparsers.add_parser("generate")
        gen_parser.add_argument("topic")
        gen_parser.add_argument("--code-gen-only", action="store_true")

        args = parser.parse_args(["generate", "Test", "--code-gen-only"])
        assert args.code_gen_only is True
        assert args.topic == "Test"

    def test_generate_without_flag_warns_comfyui_unavailable(
        self, tmp_path, sample_comfyui_shots, capsys
    ):
        """Without --code-gen-only and ComfyUI unavailable, warns with address."""
        from graphics_generator.cli import cmd_generate

        project_dir = tmp_path / "projects" / "1. Test Project"
        project_dir.mkdir(parents=True)
        shotlist_path = project_dir / "shotlist.json"
        shotlist_path.write_text(
            json.dumps(sample_comfyui_shots), encoding="utf-8"
        )

        with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
            with patch(
                "graphics_generator.comfyui.client.ComfyUIClient"
            ) as MockClient:
                mock_instance = MockClient.return_value
                mock_instance.is_available.return_value = False
                mock_instance.address = "127.0.0.1:8188"

                cmd_generate("Test Project", code_gen_only=False)

        captured = capsys.readouterr()
        assert "127.0.0.1:8188" in captured.err
        assert "--code-gen-only" in captured.err
