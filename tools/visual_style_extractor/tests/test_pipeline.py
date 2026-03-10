import json
import pytest
from unittest.mock import patch, MagicMock
from visual_style_extractor.pipeline import run_stages_0_to_4, PipelineConfig


def test_pipeline_config_from_url():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc123")
    assert config.is_youtube
    assert config.source == "https://youtube.com/watch?v=abc123"


def test_pipeline_config_from_dir(tmp_path):
    config = PipelineConfig(source=str(tmp_path))
    assert not config.is_youtube


def test_pipeline_config_custom_threshold():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc", adaptive_threshold=2.5)
    assert config.adaptive_threshold == 2.5


def test_pipeline_config_default_output_dir():
    config = PipelineConfig(source="https://youtube.com/watch?v=abc")
    assert config.output_dir is None  # Will be set during acquisition
