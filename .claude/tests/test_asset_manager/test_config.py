from pathlib import Path


def test_default_config_has_required_fields():
    from asset_manager.config import AssetManagerConfig

    cfg = AssetManagerConfig()
    assert cfg.video_library_path == Path("D:/VideoLibrary")
    assert cfg.lancedb_path == Path("D:/VideoLibrary/index")
    assert cfg.model_name == "Qwen/Qwen3-VL-Embedding-8B"
    assert cfg.embedding_dim == 768
    assert cfg.quantization == "gptq-int4"
    assert cfg.max_quality == "720p"
    assert cfg.scene_detect_threshold == 27.0
    assert cfg.scene_detect_method == "content"
    assert cfg.index_batch_size == 1


def test_config_override():
    from asset_manager.config import AssetManagerConfig

    cfg = AssetManagerConfig(
        video_library_path=Path("E:/MyLibrary"),
        embedding_dim=1536,
    )
    assert cfg.video_library_path == Path("E:/MyLibrary")
    assert cfg.lancedb_path == Path("E:/MyLibrary/index")
    assert cfg.embedding_dim == 1536


def test_config_channels_json_path():
    from asset_manager.config import AssetManagerConfig

    cfg = AssetManagerConfig()
    assert cfg.channels_json_path == Path("D:/VideoLibrary/channels.json")


def test_config_channels_dir():
    from asset_manager.config import AssetManagerConfig

    cfg = AssetManagerConfig()
    assert cfg.channels_dir == Path("D:/VideoLibrary/channels")
