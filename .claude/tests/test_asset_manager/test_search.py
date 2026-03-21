import numpy as np
from pathlib import Path
from datetime import datetime, timezone


def _make_store_with_scenes(tmp_path):
    """Helper: create a store with two scenes."""
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    vec_a = np.zeros(768, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b = np.zeros(768, dtype=np.float32)
    vec_b[1] = 1.0

    store.add_scenes([
        {
            "id": "ch_v1_001", "embedding": vec_a,
            "video_path": "channels/ch/v1.mp4", "video_id": "v1",
            "start_sec": 0.0, "end_sec": 10.0, "duration": 10.0,
            "channel": "ch", "title": "Video 1", "license": "PD",
            "description": "", "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "ch_v1_002", "embedding": vec_b,
            "video_path": "channels/ch/v1.mp4", "video_id": "v1",
            "start_sec": 10.0, "end_sec": 20.0, "duration": 10.0,
            "channel": "ch", "title": "Video 1", "license": "PD",
            "description": "", "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
    ])
    return store


def test_search_clips_returns_formatted_results(tmp_path):
    from asset_manager.search import search_clips
    from asset_manager.models import StubEmbeddingModel

    store = _make_store_with_scenes(tmp_path)
    model = StubEmbeddingModel(dimensions=768)
    results = search_clips(
        query="test query",
        model=model,
        store=store,
        top_k=5,
    )
    assert isinstance(results, list)
    assert len(results) <= 5
    # Each result must have these keys
    required = {"video_path", "start_sec", "end_sec", "score", "channel", "license", "title"}
    for r in results:
        assert required.issubset(r.keys())


def test_search_clips_respects_top_k(tmp_path):
    from asset_manager.search import search_clips
    from asset_manager.models import StubEmbeddingModel

    store = _make_store_with_scenes(tmp_path)
    model = StubEmbeddingModel(dimensions=768)
    results = search_clips(query="test", model=model, store=store, top_k=1)
    assert len(results) == 1
