import numpy as np
from pathlib import Path


def test_stub_model_embed_text_returns_correct_shape():
    from asset_manager.models import StubEmbeddingModel

    model = StubEmbeddingModel(dimensions=768)
    result = model.embed_text("dark corridor with flickering lights")
    assert isinstance(result, np.ndarray)
    assert result.shape == (768,)


def test_stub_model_embed_frames_returns_correct_shape():
    from asset_manager.models import StubEmbeddingModel

    model = StubEmbeddingModel(dimensions=768)
    # Stub doesn't need real files
    result = model.embed_frames([Path("fake1.jpg"), Path("fake2.jpg")])
    assert isinstance(result, np.ndarray)
    assert result.shape == (2, 768)


def test_stub_model_dimensions():
    from asset_manager.models import StubEmbeddingModel

    model = StubEmbeddingModel(dimensions=1536)
    assert model.dimensions() == 1536


def test_get_model_returns_stub():
    from asset_manager.models import get_model

    model = get_model("stub", dimensions=768)
    assert model.dimensions() == 768


def test_embedding_model_interface():
    """Verify that EmbeddingModel ABC defines required methods."""
    from asset_manager.models import EmbeddingModel
    import inspect

    assert inspect.isabstract(EmbeddingModel)
    methods = {name for name, _ in inspect.getmembers(EmbeddingModel, predicate=inspect.isfunction)}
    assert "embed_text" in methods
    assert "embed_frames" in methods
    assert "dimensions" in methods
