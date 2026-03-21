import numpy as np
from pathlib import Path
from datetime import datetime, timezone


def test_store_init_creates_table(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    assert store.table_name == "scenes"


def test_store_add_and_count(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    scenes = [
        {
            "id": "test_abc123_001",
            "embedding": np.random.rand(768).astype(np.float32),
            "video_path": "channels/test/video.mp4",
            "video_id": "abc123",
            "start_sec": 0.0,
            "end_sec": 12.5,
            "duration": 12.5,
            "channel": "test",
            "title": "Test Video",
            "license": "PD",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    store.add_scenes(scenes)
    assert store.count() == 1


def test_store_search_returns_ranked_results(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    # Add two scenes with known embeddings
    vec_a = np.zeros(768, dtype=np.float32)
    vec_a[0] = 1.0  # points in one direction
    vec_b = np.zeros(768, dtype=np.float32)
    vec_b[1] = 1.0  # points in another direction

    store.add_scenes([
        {
            "id": "ch_v1_001",
            "embedding": vec_a,
            "video_path": "channels/ch/v1.mp4",
            "video_id": "v1",
            "start_sec": 0.0,
            "end_sec": 10.0,
            "duration": 10.0,
            "channel": "ch",
            "title": "Video 1",
            "license": "PD",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "ch_v1_002",
            "embedding": vec_b,
            "video_path": "channels/ch/v1.mp4",
            "video_id": "v1",
            "start_sec": 10.0,
            "end_sec": 20.0,
            "duration": 10.0,
            "channel": "ch",
            "title": "Video 1",
            "license": "PD",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
    ])

    # Search with query close to vec_a
    results = store.search(vec_a, top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "ch_v1_001"  # closest match


def test_store_search_with_channel_filter(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    vec = np.random.rand(768).astype(np.float32)

    store.add_scenes([
        {
            "id": "ch1_v1_001",
            "embedding": vec,
            "video_path": "channels/ch1/v1.mp4",
            "video_id": "v1",
            "start_sec": 0.0,
            "end_sec": 10.0,
            "duration": 10.0,
            "channel": "ch1",
            "title": "V1",
            "license": "PD",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "ch2_v2_001",
            "embedding": vec,
            "video_path": "channels/ch2/v2.mp4",
            "video_id": "v2",
            "start_sec": 0.0,
            "end_sec": 10.0,
            "duration": 10.0,
            "channel": "ch2",
            "title": "V2",
            "license": "CC-BY",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        },
    ])

    results = store.search(vec, top_k=10, channel_filter="ch1")
    assert len(results) == 1
    assert results[0]["channel"] == "ch1"


def test_store_has_video(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    vec = np.random.rand(768).astype(np.float32)
    store.add_scenes([
        {
            "id": "ch_abc_001",
            "embedding": vec,
            "video_path": "channels/ch/abc.mp4",
            "video_id": "abc",
            "start_sec": 0.0,
            "end_sec": 5.0,
            "duration": 5.0,
            "channel": "ch",
            "title": "ABC",
            "license": "PD",
            "description": "",
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
    ])
    assert store.has_video("abc") is True
    assert store.has_video("xyz") is False


def test_store_status(tmp_path):
    from asset_manager.store import SceneStore

    store = SceneStore(tmp_path / "index")
    status = store.status()
    assert status["total_scenes"] == 0
    assert isinstance(status["index_size_mb"], float)
