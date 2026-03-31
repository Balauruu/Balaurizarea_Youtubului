# Asset Analyzer V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the V1 PySceneDetect + Claude Vision asset analyzer with a local PE-Core CLIP embedding pipeline that indexes footage in minutes, matches shotlist queries via cosine similarity, and auto-generates project taxonomies for discovery.

**Architecture:** Six Python scripts sharing a common pool module. `ingest.py` decodes video via FFmpeg pipe, `embed.py` runs PE-Core on GPU, `search.py` and `discover.py` query cached embeddings, `evaluate.py` compares against ground truth, `promote.py` moves keepers to the global library. All scripts run in a dedicated `perception-models` conda env with PyTorch + CUDA. Claude orchestrates via SKILL.md — scripts do deterministic work, Claude does heuristic work (query refinement, taxonomy generation, review).

**Tech Stack:** Python 3.12, PyTorch 2.5.1 + CUDA 12.4, PE-Core-L14-336, scikit-learn (DBSCAN), NumPy, FFmpeg (NVDEC), tqdm

**Spec:** `docs/superpowers/specs/2026-03-31-asset-analyzer-v2-design.md`

**Existing scripts (unchanged, reused):**
- `export_clips.py` — clip extraction via FFmpeg (already works)
- `probe_video.py` — video metadata probing (already works)
- `data/catalog.py` — SQLite CRUD for `data/asset_catalog.db` (already works)

**Conda env Python path:** `C:/Users/iorda/miniconda3/envs/perception-models/python.exe`

**All new scripts go in:** `.claude/skills/asset-analyzer/scripts/`

**Test runner:** All tests run inside the conda env: `C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `.claude/skills/asset-analyzer/scripts/pool.py` | Create | Shared pool management: file hashing, pool paths, index CRUD |
| `.claude/skills/asset-analyzer/scripts/ingest.py` | Create | FFmpeg decode → frames in memory or to disk |
| `.claude/skills/asset-analyzer/scripts/embed.py` | Create | PE-Core embedding + pool-aware caching |
| `.claude/skills/asset-analyzer/scripts/search.py` | Create | Shotlist query matching + scene boundary detection |
| `.claude/skills/asset-analyzer/scripts/discover.py` | Create | Taxonomy classification + DBSCAN clustering |
| `.claude/skills/asset-analyzer/scripts/evaluate.py` | Create | Ground truth template generation + IoU evaluation + auto-calibration |
| `.claude/skills/asset-analyzer/scripts/promote.py` | Create | Project → global library promotion |
| `.claude/skills/asset-analyzer/scripts/test_pool.py` | Create | Unit tests for pool module |
| `.claude/skills/asset-analyzer/scripts/test_search.py` | Create | Unit tests for search logic (scene boundaries, scoring) |
| `.claude/skills/asset-analyzer/scripts/test_evaluate.py` | Create | Unit tests for IoU computation and calibration suggestions |
| `.claude/skills/asset-analyzer/references/taxonomy_global.yaml` | Create | Channel-derived global taxonomy |
| `.claude/skills/asset-analyzer/references/PE_CORE_USAGE.md` | Create | Model loading and inference reference |
| `.claude/skills/asset-analyzer/references/SCORING_GUIDE.md` | Create | Score interpretation guide |
| `.claude/skills/asset-analyzer/SKILL.md` | Create | V2 skill definition and workflow |
| `channel/visuals/VISUAL_STYLE_GUIDE.md` | Modify | Add `broll_environment` form, update `broll_atmospheric` variants |
| `.claude/skills/shot-planner/SKILL.md` | Modify | Add `broll_environment` to form values table |

---

## Task 0: Environment Setup

**Files:**
- No project files — conda env creation and dependency installation

- [ ] **Step 1: Create conda environment**

```bash
C:/Users/iorda/miniconda3/Scripts/conda.exe create -n perception-models python=3.12 -y
```

Expected: Environment created at `C:\Users\iorda\miniconda3\envs\perception-models`

- [ ] **Step 2: Install PyTorch + CUDA**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 xformers --index-url https://download.pytorch.org/whl/cu124
```

Expected: PyTorch installed with CUDA 12.4 support

- [ ] **Step 3: Install PE-Core**

```bash
git clone https://github.com/facebookresearch/perception_models.git C:\Users\iorda\repos\perception_models
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pip install -e C:\Users\iorda\repos\perception_models
```

Expected: PE-Core importable

- [ ] **Step 4: Install remaining dependencies**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pip install scikit-learn tqdm pillow numpy pyyaml pytest
```

- [ ] **Step 5: Verify GPU + PE-Core works**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
from perception_models import pe_core
model = pe_core.load_model('PE-Core-L14-336')
print(f'Model loaded, embedding dim: {model.visual.output_dim}')
"
```

Expected: CUDA available, RTX 4070 detected, model loads with 768-dim output.

**Note:** If PE-Core import fails, read the repo's README for Windows-specific instructions. Do NOT substitute a different model — escalate to the user.

- [ ] **Step 6: Commit environment docs**

```bash
git add -f .claude/skills/asset-analyzer/references/PE_CORE_USAGE.md
git commit -m "docs: add PE-Core usage reference for asset-analyzer V2"
```

---

## Task 1: Pool Management Module

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/pool.py`
- Test: `.claude/skills/asset-analyzer/scripts/test_pool.py`

This module handles file hashing, pool path resolution, and index CRUD. Every other script imports it.

- [ ] **Step 1: Write failing tests for file hashing**

```python
# .claude/skills/asset-analyzer/scripts/test_pool.py
import tempfile, os, json
import numpy as np
import pytest
from pool import file_hash, PoolIndex, get_pool_root

def test_file_hash_deterministic():
    """Same file content produces same hash."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(b"x" * 100_000)
        path = f.name
    try:
        h1 = file_hash(path)
        h2 = file_hash(path)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex
    finally:
        os.unlink(path)

def test_file_hash_differs_for_different_content():
    paths = []
    for content in [b"a" * 100_000, b"b" * 100_000]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(content)
            paths.append(f.name)
    try:
        assert file_hash(paths[0]) != file_hash(paths[1])
    finally:
        for p in paths:
            os.unlink(p)

def test_pool_root_project():
    root = get_pool_root("project", project_dir="/some/project")
    assert root.endswith(".broll-index")
    assert "some/project" in root.replace("\\", "/") or "some\\project" in root

def test_pool_root_global():
    root = get_pool_root("global")
    assert ".broll-index" in root
    assert "global" in root
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py -v
```

Expected: FAIL — `pool` module not found

- [ ] **Step 3: Implement pool.py**

```python
# .claude/skills/asset-analyzer/scripts/pool.py
"""Pool management for two-pool embedding index (project + global)."""

import hashlib
import json
import os
import shutil
from pathlib import Path

import numpy as np


def file_hash(path: str) -> str:
    """SHA-256 of first 64KB + file size. Fast, collision-resistant enough for dedup."""
    h = hashlib.sha256()
    size = os.path.getsize(path)
    h.update(size.to_bytes(8, "big"))
    with open(path, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()


def get_pool_root(pool: str, project_dir: str | None = None) -> str:
    """Return the root directory for a pool.

    - 'project': <project_dir>/.broll-index/
    - 'global':  ~/.broll-index/global/
    """
    if pool == "project":
        if not project_dir:
            raise ValueError("project_dir required for project pool")
        return os.path.join(project_dir, ".broll-index")
    elif pool == "global":
        return os.path.join(os.path.expanduser("~"), ".broll-index", "global")
    else:
        raise ValueError(f"Unknown pool: {pool!r}")


class PoolIndex:
    """Manages a pool's index.json and per-video embedding caches."""

    def __init__(self, pool_root: str):
        self.root = Path(pool_root)
        self.index_path = self.root / "index.json"
        self._index: dict | None = None

    def _load(self) -> dict:
        if self._index is None:
            if self.index_path.exists():
                self._index = json.loads(self.index_path.read_text(encoding="utf-8"))
            else:
                self._index = {}
        return self._index

    def _save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(self._load(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def has(self, fhash: str) -> bool:
        return fhash in self._load()

    def get(self, fhash: str) -> dict | None:
        return self._load().get(fhash)

    def put(
        self,
        fhash: str,
        embeddings: np.ndarray,
        timestamps: np.ndarray,
        meta: dict,
    ) -> None:
        """Store embeddings + timestamps + metadata for a video."""
        entry_dir = self.root / fhash
        entry_dir.mkdir(parents=True, exist_ok=True)

        np.save(str(entry_dir / "embeddings.npy"), embeddings.astype(np.float16))
        np.save(str(entry_dir / "timestamps.npy"), timestamps.astype(np.float64))
        (entry_dir / "meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        idx = self._load()
        idx[fhash] = {
            "source_path": meta.get("source_path", ""),
            "duration_sec": meta.get("duration_sec", 0),
            "frame_count": len(timestamps),
            "embed_date": meta.get("embed_date", ""),
        }
        self._save()

    def load_embeddings(self, fhash: str) -> tuple[np.ndarray, np.ndarray]:
        """Return (embeddings, timestamps) for a cached video."""
        entry_dir = self.root / fhash
        emb = np.load(str(entry_dir / "embeddings.npy"))
        ts = np.load(str(entry_dir / "timestamps.npy"))
        return emb, ts

    def load_all_embeddings(self) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        """Load all embeddings across the pool. Returns (embeddings, timestamps, frame_info).
        frame_info[i] = {"hash": ..., "source_path": ..., "frame_idx": ...}
        """
        all_emb, all_ts, all_info = [], [], []
        for fhash, entry in self._load().items():
            entry_dir = self.root / fhash
            if not (entry_dir / "embeddings.npy").exists():
                continue
            emb, ts = self.load_embeddings(fhash)
            for i in range(len(ts)):
                all_info.append({
                    "hash": fhash,
                    "source_path": entry.get("source_path", ""),
                    "frame_idx": i,
                })
            all_emb.append(emb)
            all_ts.append(ts)

        if not all_emb:
            return np.empty((0, 768), dtype=np.float16), np.empty(0), []

        return np.vstack(all_emb), np.concatenate(all_ts), all_info

    def remove(self, fhash: str) -> None:
        """Remove a video from the index and delete its cache."""
        idx = self._load()
        idx.pop(fhash, None)
        self._save()
        entry_dir = self.root / fhash
        if entry_dir.exists():
            shutil.rmtree(entry_dir)

    def list_entries(self) -> dict:
        """Return the full index."""
        return dict(self._load())

    def health_check(self) -> dict:
        """Report index health: total files, frames, dead references."""
        idx = self._load()
        total_files = len(idx)
        total_frames = sum(e.get("frame_count", 0) for e in idx.values())
        dead = []
        for fhash, entry in idx.items():
            src = entry.get("source_path", "")
            if src and not os.path.exists(src):
                dead.append({"hash": fhash, "path": src})
        return {
            "pool_root": str(self.root),
            "total_files": total_files,
            "total_frames": total_frames,
            "dead_references": dead,
        }
```

- [ ] **Step 4: Write remaining pool tests**

Add to `test_pool.py`:

```python
def test_pool_index_put_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(10, 768).astype(np.float16)
        ts = np.arange(10, dtype=np.float64)
        meta = {"source_path": "/fake/video.mp4", "duration_sec": 10.0, "embed_date": "2026-03-31"}

        idx.put("abc123", emb, ts, meta)

        assert idx.has("abc123")
        assert not idx.has("xyz999")

        loaded_emb, loaded_ts = idx.load_embeddings("abc123")
        assert loaded_emb.shape == (10, 768)
        assert loaded_ts.shape == (10,)
        np.testing.assert_array_almost_equal(loaded_emb, emb, decimal=2)

def test_pool_index_load_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        for name, n in [("aaa", 5), ("bbb", 3)]:
            emb = np.random.randn(n, 768).astype(np.float16)
            ts = np.arange(n, dtype=np.float64)
            idx.put(name, emb, ts, {"source_path": f"/fake/{name}.mp4"})

        all_emb, all_ts, info = idx.load_all_embeddings()
        assert all_emb.shape == (8, 768)
        assert len(all_ts) == 8
        assert len(info) == 8

def test_pool_index_remove():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("todelete", emb, ts, {})
        assert idx.has("todelete")
        idx.remove("todelete")
        assert not idx.has("todelete")

def test_health_check_detects_dead_refs():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("dead", emb, ts, {"source_path": "/nonexistent/video.mp4"})
        report = idx.health_check()
        assert report["total_files"] == 1
        assert len(report["dead_references"]) == 1
```

- [ ] **Step 5: Run all pool tests**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/pool.py .claude/skills/asset-analyzer/scripts/test_pool.py
git commit -m "feat: add pool management module for asset-analyzer V2"
```

---

## Task 2: Ingest Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/ingest.py`

Frame extraction via FFmpeg. Two modes: pipe raw bytes to stdout (for `embed.py`) or save frames to a directory (for Claude review). No PE-Core dependency — pure FFmpeg.

- [ ] **Step 1: Implement ingest.py**

```python
# .claude/skills/asset-analyzer/scripts/ingest.py
"""FFmpeg video decode → frames in memory or to disk."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _check_nvdec() -> bool:
    """Check if NVDEC hardware acceleration is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hwaccels"],
            capture_output=True, text=True, timeout=5,
        )
        return "cuda" in result.stdout.lower()
    except Exception:
        return False


def extract_frames(
    video_path: str,
    fps: int = 1,
    size: int = 336,
    use_hwaccel: bool = True,
) -> list[np.ndarray]:
    """Decode video to a list of RGB numpy arrays at the given fps and resolution.

    Returns list of np.ndarray with shape (size, size, 3), dtype uint8.
    """
    hwaccel_args = []
    if use_hwaccel and _check_nvdec():
        hwaccel_args = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]

    cmd = [
        "ffmpeg",
        *hwaccel_args,
        "-i", video_path,
        "-vf", f"fps={fps},scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "rgb24",
        "-f", "rawvideo",
        "-v", "error",
        "pipe:1",
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_bytes = proc.stdout.read()
    proc.wait()

    if proc.returncode != 0:
        err = proc.stderr.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg failed (exit {proc.returncode}): {err}")

    frame_size = size * size * 3
    n_frames = len(raw_bytes) // frame_size
    frames = []
    for i in range(n_frames):
        offset = i * frame_size
        frame = np.frombuffer(raw_bytes[offset:offset + frame_size], dtype=np.uint8)
        frame = frame.reshape(size, size, 3)
        frames.append(frame)

    return frames


def save_frames(
    video_path: str,
    output_dir: str,
    fps: int = 1,
    size: int = 336,
    start_sec: float | None = None,
    end_sec: float | None = None,
) -> list[str]:
    """Extract frames from video and save as JPEG files. Returns list of saved paths."""
    os.makedirs(output_dir, exist_ok=True)

    seek_args = []
    if start_sec is not None:
        seek_args += ["-ss", str(start_sec)]
    duration_args = []
    if start_sec is not None and end_sec is not None:
        duration_args += ["-t", str(end_sec - start_sec)]

    cmd = [
        "ffmpeg",
        *seek_args,
        "-i", video_path,
        *duration_args,
        "-vf", f"fps={fps},scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2",
        "-q:v", "2",
        "-v", "error",
        os.path.join(output_dir, "frame_%06d.jpg"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    saved = sorted(Path(output_dir).glob("frame_*.jpg"))
    return [str(p) for p in saved]


def main():
    parser = argparse.ArgumentParser(description="Extract frames from video via FFmpeg")
    parser.add_argument("--input", required=True, help="Path to video file")
    parser.add_argument("--fps", type=int, default=1, help="Frames per second to extract")
    parser.add_argument("--size", type=int, default=336, help="Output frame size (square)")
    parser.add_argument("--output-dir", help="Save frames to directory as JPEG")
    parser.add_argument("--start", type=float, help="Start time in seconds")
    parser.add_argument("--end", type=float, help="End time in seconds")
    parser.add_argument("--pipe", action="store_true", help="Pipe raw RGB to stdout")
    args = parser.parse_args()

    if args.output_dir:
        paths = save_frames(args.input, args.output_dir, args.fps, args.size, args.start, args.end)
        print(f"Saved {len(paths)} frames to {args.output_dir}")
    elif args.pipe:
        frames = extract_frames(args.input, args.fps, args.size)
        # Write raw bytes to stdout
        for frame in frames:
            sys.stdout.buffer.write(frame.tobytes())
    else:
        frames = extract_frames(args.input, args.fps, args.size)
        print(f"Extracted {len(frames)} frames ({args.size}x{args.size} RGB)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify with a real video**

Pick any short video from the Duplessis staging directory:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/ingest.py --input "projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/staging/<any_video>.mp4" --fps 1 --size 336 --output-dir .claude/scratch/test_frames
```

Expected: Frames saved to `.claude/scratch/test_frames/`, each 336x336 JPEG. Verify a couple look correct.

- [ ] **Step 3: Clean up test frames and commit**

```bash
rm -rf .claude/scratch/test_frames
git add .claude/skills/asset-analyzer/scripts/ingest.py
git commit -m "feat: add ingest.py — FFmpeg frame extraction for asset-analyzer V2"
```

---

## Task 3: Embed Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/embed.py`

Loads PE-Core, calls `ingest.py` for frames, embeds in batches, saves to pool cache. This is the GPU-heavy script.

- [ ] **Step 1: Implement embed.py**

```python
# .claude/skills/asset-analyzer/scripts/embed.py
"""Embed video frames using PE-Core-L14-336 and cache in pool index."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

# Add scripts dir to path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex, file_hash, get_pool_root
from ingest import extract_frames

# Resolve PE python env
PE_PYTHON = "C:/Users/iorda/miniconda3/envs/perception-models/python.exe"


def load_model(device: str = "cuda"):
    """Load PE-Core-L14-336 and return (model, tokenizer, preprocess)."""
    from perception_models import pe_core

    model = pe_core.load_model("PE-Core-L14-336")
    model = model.to(device).eval()

    tokenizer = pe_core.get_tokenizer("PE-Core-L14-336")
    preprocess = pe_core.get_preprocess("PE-Core-L14-336")

    return model, tokenizer, preprocess


def embed_frames(
    model,
    preprocess,
    frames: list[np.ndarray],
    batch_size: int = 64,
    device: str = "cuda",
) -> np.ndarray:
    """Embed a list of RGB numpy frames. Returns [N, 768] float16 array."""
    from PIL import Image

    all_embeddings = []
    for i in range(0, len(frames), batch_size):
        batch = frames[i : i + batch_size]
        images = [preprocess(Image.fromarray(f)) for f in batch]
        tensor = torch.stack(images).to(device)

        with torch.no_grad(), torch.amp.autocast("cuda"):
            emb = model.encode_image(tensor)
            emb = emb / emb.norm(dim=-1, keepdim=True)  # L2 normalize

        all_embeddings.append(emb.cpu().numpy().astype(np.float16))

    return np.vstack(all_embeddings)


def embed_video(
    video_path: str,
    pool_index: PoolIndex,
    model,
    preprocess,
    fps: int = 1,
    size: int = 336,
    batch_size: int = 64,
    force: bool = False,
) -> dict:
    """Embed a single video and cache in the pool. Returns summary dict."""
    fhash = file_hash(video_path)

    if pool_index.has(fhash) and not force:
        entry = pool_index.get(fhash)
        return {"status": "cached", "hash": fhash, "frames": entry.get("frame_count", 0)}

    # Extract frames
    frames = extract_frames(video_path, fps=fps, size=size)
    if not frames:
        return {"status": "empty", "hash": fhash, "frames": 0}

    # Embed
    embeddings = embed_frames(model, preprocess, frames, batch_size=batch_size)
    timestamps = np.arange(len(frames), dtype=np.float64) / fps

    # Get duration from probe
    duration = len(frames) / fps

    meta = {
        "source_path": os.path.abspath(video_path),
        "duration_sec": duration,
        "resolution": f"{size}x{size}",
        "fps_extracted": fps,
        "embed_date": datetime.now(timezone.utc).isoformat(),
        "file_hash": fhash,
    }

    pool_index.put(fhash, embeddings, timestamps, meta)

    return {"status": "embedded", "hash": fhash, "frames": len(frames)}


def main():
    parser = argparse.ArgumentParser(description="Embed videos with PE-Core into pool cache")
    parser.add_argument("--input-dir", help="Directory of videos to embed")
    parser.add_argument("--input", help="Single video file to embed")
    parser.add_argument("--pool", default="project", choices=["project", "global"],
                        help="Target pool (default: project)")
    parser.add_argument("--project-dir", default=".", help="Project directory (for project pool)")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for embedding")
    parser.add_argument("--force", action="store_true", help="Force re-embed cached videos")
    parser.add_argument("--health-check", action="store_true", help="Run health check on pool")
    args = parser.parse_args()

    pool_root = get_pool_root(args.pool, project_dir=os.path.abspath(args.project_dir))
    pool_index = PoolIndex(pool_root)

    if args.health_check:
        report = pool_index.health_check()
        print(json.dumps(report, indent=2))
        return

    # Collect video files
    video_exts = {".mp4", ".webm", ".mkv", ".avi", ".mov"}
    videos = []
    if args.input:
        videos = [args.input]
    elif args.input_dir:
        d = Path(args.input_dir)
        videos = sorted(str(p) for p in d.iterdir() if p.suffix.lower() in video_exts)
    else:
        parser.error("Provide --input or --input-dir")

    if not videos:
        print("No video files found.")
        return

    # Load model
    print("Loading PE-Core-L14-336...")
    model, tokenizer, preprocess = load_model()
    print(f"Model loaded. Processing {len(videos)} video(s)...")

    results = []
    for vpath in tqdm(videos, desc="Embedding"):
        result = embed_video(vpath, pool_index, model, preprocess,
                             batch_size=args.batch_size, force=args.force)
        result["file"] = os.path.basename(vpath)
        results.append(result)
        status = result["status"]
        frames = result["frames"]
        tqdm.write(f"  {result['file']}: {status} ({frames} frames)")

    # Summary
    new = sum(1 for r in results if r["status"] == "embedded")
    cached = sum(1 for r in results if r["status"] == "cached")
    print(f"\nDone: {new} embedded, {cached} cached (skipped), {len(videos)} total")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify with a real staging video**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/embed.py --input "projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/staging/<short_video>.mp4" --pool project --project-dir "projects/1. The Duplessis Orphans Quebec's Stolen Children"
```

Expected: Model loads, frames extracted, embeddings cached. Second run should show "cached".

- [ ] **Step 3: Verify cache skip works**

Run the same command again.

Expected: Output shows `cached (skipped)` — no model inference.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/embed.py
git commit -m "feat: add embed.py — PE-Core GPU embedding with pool caching"
```

---

## Task 4: Search Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/search.py`
- Test: `.claude/skills/asset-analyzer/scripts/test_search.py`

Loads cached embeddings from both pools, encodes text queries via PE-Core, finds matching segments using cosine similarity + scene boundary detection.

- [ ] **Step 1: Write failing tests for scene boundary detection and segment grouping**

```python
# .claude/skills/asset-analyzer/scripts/test_search.py
import numpy as np
import pytest
from search import detect_scene_boundaries, group_into_segments, score_queries

def test_detect_scene_boundaries_finds_cuts():
    """Sharp embedding changes should produce boundaries."""
    # 10 frames: 5 of type A, then 5 of type B (simulating a scene cut)
    emb = np.vstack([
        np.tile([1, 0, 0], (5, 1)),   # scene A
        np.tile([0, 1, 0], (5, 1)),   # scene B
    ]).astype(np.float32)
    ts = np.arange(10, dtype=np.float64)

    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
    # Should detect the cut between frame 4 and 5
    assert len(boundaries) >= 1
    assert any(abs(b - 4.5) < 1.5 for b in boundaries)

def test_detect_scene_boundaries_no_cuts():
    """Uniform embeddings should produce no boundaries."""
    emb = np.tile([1, 0, 0], (10, 1)).astype(np.float32)
    ts = np.arange(10, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
    assert len(boundaries) == 0

def test_group_into_segments():
    """Consecutive high-scoring frames within a scene should group into one segment."""
    scores = np.array([0.1, 0.3, 0.35, 0.28, 0.1, 0.1, 0.05, 0.32, 0.30, 0.1])
    ts = np.arange(10, dtype=np.float64)
    boundaries = [4.5]  # scene cut between frame 4 and 5
    threshold = 0.20

    segments = group_into_segments(scores, ts, boundaries, threshold)
    # Should find two segments: frames 1-3 and frames 7-8
    assert len(segments) == 2
    assert segments[0]["start_sec"] == 1.0
    assert segments[0]["end_sec"] == 3.0
    assert segments[1]["start_sec"] == 7.0

def test_score_queries():
    """Text query embeddings scored against frame embeddings via dot product."""
    frame_emb = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=np.float32)
    query_emb = np.array([
        [1, 0, 0],  # should match frame 0
        [0, 0, 1],  # should match frame 2
    ], dtype=np.float32)

    scores = score_queries(frame_emb, query_emb)
    assert scores.shape == (3, 2)
    assert scores[0, 0] > scores[1, 0]  # frame 0 best for query 0
    assert scores[2, 1] > scores[0, 1]  # frame 2 best for query 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_search.py -v
```

Expected: FAIL — `search` module not found

- [ ] **Step 3: Implement search.py**

```python
# .claude/skills/asset-analyzer/scripts/search.py
"""Shotlist query matching against cached embeddings from both pools."""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex, get_pool_root


def detect_scene_boundaries(
    embeddings: np.ndarray,
    timestamps: np.ndarray,
    percentile: int = 90,
) -> list[float]:
    """Detect scene boundaries from embedding deltas.

    Returns list of boundary timestamps (midpoints between cut frames).
    """
    if len(embeddings) < 2:
        return []

    # Cosine similarity between consecutive frames
    emb = embeddings.astype(np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-8)
    emb_norm = emb / norms

    sims = np.sum(emb_norm[:-1] * emb_norm[1:], axis=1)
    deltas = 1.0 - sims

    threshold = np.percentile(deltas, percentile)
    if threshold < 0.01:
        return []

    cut_indices = np.where(deltas > threshold)[0]
    boundaries = []
    for idx in cut_indices:
        # Boundary is midpoint between the two frames
        mid = (timestamps[idx] + timestamps[idx + 1]) / 2
        boundaries.append(float(mid))

    return boundaries


def score_queries(
    frame_embeddings: np.ndarray,
    query_embeddings: np.ndarray,
) -> np.ndarray:
    """Score frames against queries via dot product. Returns [N_frames, N_queries]."""
    fe = frame_embeddings.astype(np.float32)
    qe = query_embeddings.astype(np.float32)
    return fe @ qe.T


def group_into_segments(
    scores: np.ndarray,
    timestamps: np.ndarray,
    boundaries: list[float],
    threshold: float = 0.15,
) -> list[dict]:
    """Group consecutive above-threshold frames into segments, respecting scene boundaries.

    Returns list of segment dicts with start_sec, end_sec, peak_score, mean_score, best_frame_sec.
    """
    above = scores >= threshold
    segments = []
    current_start = None
    current_scores = []
    current_best_score = -1
    current_best_sec = 0

    for i, (is_above, ts_val) in enumerate(zip(above, timestamps)):
        # Check if we crossed a scene boundary
        crossed_boundary = False
        if current_start is not None:
            for b in boundaries:
                if timestamps[i - 1] < b <= ts_val:
                    crossed_boundary = True
                    break

        if crossed_boundary and current_start is not None:
            # Close current segment
            segments.append({
                "start_sec": float(current_start),
                "end_sec": float(timestamps[i - 1]),
                "peak_score": float(max(current_scores)),
                "mean_score": float(np.mean(current_scores)),
                "best_frame_sec": float(current_best_sec),
            })
            current_start = None
            current_scores = []
            current_best_score = -1

        if is_above:
            if current_start is None:
                current_start = ts_val
            current_scores.append(scores[i])
            if scores[i] > current_best_score:
                current_best_score = scores[i]
                current_best_sec = ts_val
        else:
            if current_start is not None:
                segments.append({
                    "start_sec": float(current_start),
                    "end_sec": float(timestamps[i - 1]),
                    "peak_score": float(max(current_scores)),
                    "mean_score": float(np.mean(current_scores)),
                    "best_frame_sec": float(current_best_sec),
                })
                current_start = None
                current_scores = []
                current_best_score = -1

    # Close trailing segment
    if current_start is not None:
        segments.append({
            "start_sec": float(current_start),
            "end_sec": float(timestamps[-1]),
            "peak_score": float(max(current_scores)),
            "mean_score": float(np.mean(current_scores)),
            "best_frame_sec": float(current_best_sec),
        })

    return segments


def encode_text_queries(model, tokenizer, queries: list[str], device: str = "cuda"):
    """Encode text queries using PE-Core. Returns [N, 768] float32 array."""
    import torch

    tokens = tokenizer(queries)
    if isinstance(tokens, dict):
        tokens = {k: v.to(device) for k, v in tokens.items()}
    else:
        tokens = tokens.to(device)

    with torch.no_grad(), torch.amp.autocast("cuda"):
        emb = model.encode_text(tokens)
        emb = emb / emb.norm(dim=-1, keepdim=True)

    return emb.cpu().numpy().astype(np.float32)


def search(
    queries: list[dict],
    project_dir: str,
    model=None,
    tokenizer=None,
    pool_only: str | None = None,
    boundary_percentile: int = 90,
) -> dict:
    """Run shotlist queries against both pools. Returns candidates.json structure.

    queries: list of {"shot_id": "S006", "text": "..."}
    """
    # Load embeddings from pools
    pools_searched = {}
    all_embeddings_list = []
    all_timestamps_list = []
    all_info_list = []

    for pool_name in ["project", "global"]:
        if pool_only and pool_name != pool_only:
            continue
        try:
            pool_root = get_pool_root(pool_name, project_dir=project_dir)
            idx = PoolIndex(pool_root)
            emb, ts, info = idx.load_all_embeddings()
            if len(emb) == 0:
                continue
            # Tag info with pool name
            for entry in info:
                entry["pool"] = pool_name
            all_embeddings_list.append(emb)
            all_timestamps_list.append(ts)
            all_info_list.extend(info)
            pools_searched[pool_name] = {
                "path": pool_root,
                "files": len(idx.list_entries()),
                "frames": len(emb),
            }
        except (ValueError, FileNotFoundError):
            continue

    if not all_embeddings_list:
        return {"pools_searched": {}, "query_results": [], "weak_queries": []}

    all_emb = np.vstack(all_embeddings_list)
    all_ts = np.concatenate(all_timestamps_list)

    # Detect scene boundaries per video
    scene_boundaries = {}
    # Group by source video
    video_frames = defaultdict(list)
    for i, info in enumerate(all_info_list):
        video_frames[info["source_path"]].append((i, all_ts[i]))

    for src, frame_list in video_frames.items():
        indices = [f[0] for f in sorted(frame_list, key=lambda x: x[1])]
        if len(indices) < 2:
            continue
        vid_emb = all_emb[indices]
        vid_ts = np.array([all_ts[i] for i in indices])
        bounds = detect_scene_boundaries(vid_emb, vid_ts, boundary_percentile)
        if bounds:
            scene_boundaries[src] = bounds

    # Encode queries
    query_texts = [q["text"] for q in queries]
    query_emb = encode_text_queries(model, tokenizer, query_texts)

    # Score
    scores = score_queries(all_emb, query_emb)  # [N_frames, N_queries]

    # Build results per query
    query_results = []
    weak_queries = []

    for qi, q in enumerate(queries):
        q_scores = scores[:, qi]
        peak = float(q_scores.max())

        if peak < 0.15:
            weak_queries.append(q["shot_id"])
            query_results.append({
                "shot_id": q["shot_id"],
                "query_text": q["text"],
                "refined_queries": [],
                "candidates": [],
            })
            continue

        # Group by video, find segments
        candidates = []
        for src, frame_list in video_frames.items():
            indices = [f[0] for f in sorted(frame_list, key=lambda x: x[1])]
            vid_scores = q_scores[indices]
            vid_ts = np.array([all_ts[i] for i in indices])
            vid_boundaries = scene_boundaries.get(src, [])
            pool = all_info_list[indices[0]]["pool"] if indices else "project"

            segments = group_into_segments(vid_scores, vid_ts, vid_boundaries, threshold=0.15)
            for seg in segments:
                seg["video"] = os.path.basename(src)
                seg["video_path"] = src
                seg["pool"] = pool
                candidates.append(seg)

        # Sort by peak score, take top candidates
        candidates.sort(key=lambda c: c["peak_score"], reverse=True)

        query_results.append({
            "shot_id": q["shot_id"],
            "query_text": q["text"],
            "refined_queries": [],
            "candidates": candidates[:10],
        })

        if peak < 0.20:
            weak_queries.append(q["shot_id"])

    return {
        "pools_searched": pools_searched,
        "query_results": query_results,
        "weak_queries": weak_queries,
        "scene_boundaries": {os.path.basename(k): v for k, v in scene_boundaries.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="Search cached embeddings with shotlist queries")
    parser.add_argument("--queries", help="Path to queries JSON file")
    parser.add_argument("--output", default="candidates.json", help="Output file")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--pool-only", choices=["project", "global"], help="Search only one pool")
    parser.add_argument("--boundary-percentile", type=int, default=90,
                        help="Percentile for scene boundary detection")
    args = parser.parse_args()

    with open(args.queries, encoding="utf-8") as f:
        queries = json.load(f)

    # Load model for text encoding
    from embed import load_model
    model, tokenizer, _ = load_model()

    results = search(
        queries=queries,
        project_dir=os.path.abspath(args.project_dir),
        model=model,
        tokenizer=tokenizer,
        pool_only=args.pool_only,
        boundary_percentile=args.boundary_percentile,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results written to {args.output}")
    print(f"  Pools searched: {list(results['pools_searched'].keys())}")
    print(f"  Queries: {len(results['query_results'])}")
    print(f"  Weak queries: {results['weak_queries']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run unit tests**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_search.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/search.py .claude/skills/asset-analyzer/scripts/test_search.py
git commit -m "feat: add search.py — shotlist query matching with scene boundary detection"
```

---

## Task 5: Discover Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/discover.py`

Classifies frames against taxonomy categories via zero-shot CLIP scoring, filters skip categories, clusters unknowns with DBSCAN.

- [ ] **Step 1: Implement discover.py**

```python
# .claude/skills/asset-analyzer/scripts/discover.py
"""Discovery mode: classify footage against taxonomy + DBSCAN clustering of unknowns."""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from sklearn.cluster import DBSCAN

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex, get_pool_root


def load_taxonomy(path: str) -> dict:
    """Load taxonomy YAML. Returns flat dict of {category_key: description_text}.
    Also returns a set of skip keys.
    """
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    categories = {}
    skip_keys = set()
    for group, entries in raw.items():
        if isinstance(entries, dict):
            for key, desc in entries.items():
                categories[key] = desc
                if group == "skip":
                    skip_keys.add(key)
    return categories, skip_keys


def merge_taxonomies(
    global_path: str,
    project_path: str | None = None,
) -> tuple[dict, set]:
    """Load and merge global + project taxonomies. Returns (categories, skip_keys)."""
    categories, skip_keys = load_taxonomy(global_path)

    if project_path and os.path.exists(project_path):
        with open(project_path, encoding="utf-8") as f:
            project_tax = json.load(f)
        # Project taxonomy is a flat dict of {key: description}
        if isinstance(project_tax, dict):
            # Handle {"project_specific": {...}} wrapper or flat dict
            if "project_specific" in project_tax:
                project_tax = project_tax["project_specific"]
            categories.update(project_tax)

    return categories, skip_keys


def classify_frames(
    frame_embeddings: np.ndarray,
    categories: dict,
    model,
    tokenizer,
    device: str = "cuda",
    confidence_threshold: float = 0.15,
) -> tuple[list[str], np.ndarray]:
    """Classify each frame against taxonomy categories via zero-shot scoring.

    Returns (primary_categories, max_scores) where:
    - primary_categories[i] = category key for frame i (or "__unknown__" if below threshold)
    - max_scores[i] = best category score for frame i
    """
    import torch

    cat_keys = list(categories.keys())
    cat_descs = list(categories.values())

    # Encode category descriptions
    tokens = tokenizer(cat_descs)
    if isinstance(tokens, dict):
        tokens = {k: v.to(device) for k, v in tokens.items()}
    else:
        tokens = tokens.to(device)

    with torch.no_grad(), torch.amp.autocast("cuda"):
        cat_emb = model.encode_text(tokens)
        cat_emb = cat_emb / cat_emb.norm(dim=-1, keepdim=True)

    cat_emb_np = cat_emb.cpu().numpy().astype(np.float32)

    # Score all frames against all categories
    fe = frame_embeddings.astype(np.float32)
    scores = fe @ cat_emb_np.T  # [N_frames, N_categories]

    max_indices = scores.argmax(axis=1)
    max_scores = scores.max(axis=1)

    primary = []
    for i in range(len(frame_embeddings)):
        if max_scores[i] < confidence_threshold:
            primary.append("__unknown__")
        else:
            primary.append(cat_keys[max_indices[i]])

    return primary, max_scores


def cluster_unknowns(
    embeddings: np.ndarray,
    eps: float = 0.3,
    min_samples: int = 3,
) -> np.ndarray:
    """DBSCAN cluster unknown-classified embeddings. Returns cluster labels (-1 = noise)."""
    if len(embeddings) < min_samples:
        return np.full(len(embeddings), -1)

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    return clustering.fit_predict(embeddings)


def discover(
    project_dir: str,
    pool: str,
    taxonomy_global_path: str,
    taxonomy_project_path: str | None = None,
    model=None,
    tokenizer=None,
    eps: float = 0.3,
    min_samples: int = 3,
    confidence_threshold: float = 0.15,
) -> dict:
    """Run discovery on a pool. Returns discovery.json structure."""
    pool_root = get_pool_root(pool, project_dir=project_dir)
    idx = PoolIndex(pool_root)
    all_emb, all_ts, all_info = idx.load_all_embeddings()

    if len(all_emb) == 0:
        return {"inventory": {}, "clusters": [], "noise_frames": 0}

    # Load and merge taxonomies
    categories, skip_keys = merge_taxonomies(taxonomy_global_path, taxonomy_project_path)

    # Classify
    primary_cats, max_scores = classify_frames(
        all_emb, categories, model, tokenizer,
        confidence_threshold=confidence_threshold,
    )

    # Build inventory (excluding skip and unknown)
    inventory = defaultdict(lambda: {"frame_count": 0, "total_seconds": 0, "videos": set()})

    unknown_indices = []
    for i, (cat, score) in enumerate(zip(primary_cats, max_scores)):
        if cat in skip_keys:
            continue
        if cat == "__unknown__":
            unknown_indices.append(i)
            continue
        inventory[cat]["frame_count"] += 1
        inventory[cat]["total_seconds"] += 1  # 1fps = 1 second per frame
        inventory[cat]["videos"].add(all_info[i]["source_path"])

    # Convert sets to lists for JSON
    inv_json = {}
    for cat, data in inventory.items():
        inv_json[cat] = {
            "frame_count": data["frame_count"],
            "total_minutes": round(data["total_seconds"] / 60, 2),
            "videos": [os.path.basename(v) for v in data["videos"]],
        }

    # Cluster unknowns
    clusters = []
    noise_frames = 0
    if unknown_indices:
        unknown_emb = all_emb[unknown_indices]
        labels = cluster_unknowns(unknown_emb, eps=eps, min_samples=min_samples)

        noise_frames = int(np.sum(labels == -1))

        for cluster_id in set(labels):
            if cluster_id == -1:
                continue
            mask = labels == cluster_id
            cluster_indices = np.array(unknown_indices)[mask]

            # Find centroid and representative frame
            cluster_emb = all_emb[cluster_indices]
            centroid = cluster_emb.mean(axis=0)
            dists = np.linalg.norm(cluster_emb - centroid, axis=1)
            rep_idx = cluster_indices[dists.argmin()]

            # Gather video sources and timestamp ranges
            video_ranges = defaultdict(list)
            for ci in cluster_indices:
                src = os.path.basename(all_info[ci]["source_path"])
                video_ranges[src].append(float(all_ts[ci]))

            ts_ranges = {}
            for src, times in video_ranges.items():
                times.sort()
                # Group consecutive timestamps into ranges
                ranges = []
                start = times[0]
                end = times[0]
                for t in times[1:]:
                    if t - end <= 2:  # within 2 seconds
                        end = t
                    else:
                        ranges.append([start, end])
                        start = t
                        end = t
                ranges.append([start, end])
                ts_ranges[src] = ranges

            clusters.append({
                "cluster_id": int(cluster_id),
                "frame_count": int(mask.sum()),
                "videos": list(video_ranges.keys()),
                "centroid_frame": {
                    "video": os.path.basename(all_info[rep_idx]["source_path"]),
                    "timestamp_sec": float(all_ts[rep_idx]),
                },
                "timestamp_ranges": ts_ranges,
            })

    return {
        "inventory": inv_json,
        "clusters": clusters,
        "noise_frames": noise_frames,
    }


def main():
    parser = argparse.ArgumentParser(description="Discover content in footage via taxonomy + clustering")
    parser.add_argument("--pool", default="project", choices=["project", "global"])
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--taxonomy-global", required=True, help="Path to global taxonomy YAML")
    parser.add_argument("--taxonomy-project", help="Path to project taxonomy JSON (auto-generated)")
    parser.add_argument("--output", default="discovery.json", help="Output file")
    parser.add_argument("--eps", type=float, default=0.3, help="DBSCAN eps parameter")
    parser.add_argument("--min-samples", type=int, default=3, help="DBSCAN min_samples")
    parser.add_argument("--confidence-threshold", type=float, default=0.15,
                        help="Min score to classify a frame (below = unknown)")
    args = parser.parse_args()

    from embed import load_model
    model, tokenizer, _ = load_model()

    results = discover(
        project_dir=os.path.abspath(args.project_dir),
        pool=args.pool,
        taxonomy_global_path=args.taxonomy_global,
        taxonomy_project_path=args.taxonomy_project,
        model=model,
        tokenizer=tokenizer,
        eps=args.eps,
        min_samples=args.min_samples,
        confidence_threshold=args.confidence_threshold,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Discovery written to {args.output}")
    print(f"  Categories: {len(results['inventory'])}")
    print(f"  Clusters: {len(results['clusters'])}")
    print(f"  Noise frames: {results['noise_frames']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify with embedded staging footage**

Requires Task 3 (embed) to have been run first:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/discover.py --pool project --project-dir "projects/1. The Duplessis Orphans Quebec's Stolen Children" --taxonomy-global .claude/skills/asset-analyzer/references/taxonomy_global.yaml --output .claude/scratch/discovery_test.json
```

Expected: JSON output with category inventory and clusters. Review output to see if categories make sense.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/discover.py
git commit -m "feat: add discover.py — taxonomy classification + DBSCAN clustering"
```

---

## Task 6: Evaluate Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/evaluate.py`
- Test: `.claude/skills/asset-analyzer/scripts/test_evaluate.py`

Ground truth template generation, IoU-based evaluation, and auto-calibration suggestions.

- [ ] **Step 1: Write failing tests for IoU and evaluation logic**

```python
# .claude/skills/asset-analyzer/scripts/test_evaluate.py
import pytest
from evaluate import compute_iou, evaluate_segments, suggest_calibration

def test_iou_full_overlap():
    assert compute_iou(10, 20, 10, 20) == 1.0

def test_iou_no_overlap():
    assert compute_iou(0, 5, 10, 15) == 0.0

def test_iou_partial_overlap():
    # overlap = 5-10 = 5, union = 0-15 = 15
    iou = compute_iou(0, 10, 5, 15)
    assert abs(iou - 5 / 15) < 0.01

def test_iou_contained():
    # gt inside pred: overlap = 5, union = 10
    iou = compute_iou(5, 10, 0, 10)
    assert abs(iou - 0.5) < 0.01

def test_evaluate_perfect_match():
    gt = [{"start_sec": 10, "end_sec": 20, "label": "test"}]
    pred = [{"start_sec": 10, "end_sec": 20}]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 1
    assert result["misses"] == 0
    assert result["false_positives"] == 0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0

def test_evaluate_complete_miss():
    gt = [{"start_sec": 10, "end_sec": 20, "label": "test"}]
    pred = [{"start_sec": 50, "end_sec": 60}]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 0
    assert result["misses"] == 1
    assert result["false_positives"] == 1

def test_evaluate_false_positive():
    gt = []
    pred = [{"start_sec": 10, "end_sec": 20}]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["false_positives"] == 1
    assert result["precision"] == 0.0

def test_suggest_calibration_low_recall():
    metrics = {"recall": 0.60, "precision": 0.90, "hits": 3, "misses": 2, "false_positives": 0}
    missed_details = [
        {"label": "test", "nearest_pred_score": 0.14},
        {"label": "test2", "nearest_pred_score": 0.13},
    ]
    suggestions = suggest_calibration(metrics, missed_details, current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    # Should suggest lowering thresholds
    assert any("threshold" in s["suggestion"].lower() for s in suggestions)

def test_suggest_calibration_good_metrics():
    metrics = {"recall": 0.90, "precision": 0.88, "hits": 9, "misses": 1, "false_positives": 1}
    suggestions = suggest_calibration(metrics, [], current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    # Should have no or minor suggestions
    assert len(suggestions) <= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_evaluate.py -v
```

Expected: FAIL — `evaluate` module not found

- [ ] **Step 3: Implement evaluate.py**

```python
# .claude/skills/asset-analyzer/scripts/evaluate.py
"""Ground truth evaluation and auto-calibration for asset-analyzer."""

import argparse
import glob
import json
import os
import subprocess
import sys


def compute_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    """Compute Intersection over Union for two time segments."""
    intersection_start = max(start_a, start_b)
    intersection_end = min(end_a, end_b)
    intersection = max(0, intersection_end - intersection_start)

    union = (end_a - start_a) + (end_b - start_b) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def evaluate_segments(
    ground_truth: list[dict],
    predictions: list[dict],
    iou_threshold: float = 0.5,
) -> dict:
    """Compare predicted segments against ground truth using IoU.

    Returns dict with hits, misses, false_positives, precision, recall, f1, boundary_accuracy.
    """
    gt_matched = set()
    pred_matched = set()
    boundary_offsets = []

    # Match each GT segment to best-overlapping prediction
    for gi, gt in enumerate(ground_truth):
        best_iou = 0
        best_pi = -1
        for pi, pred in enumerate(predictions):
            iou = compute_iou(gt["start_sec"], gt["end_sec"], pred["start_sec"], pred["end_sec"])
            if iou > best_iou:
                best_iou = iou
                best_pi = pi

        if best_iou >= iou_threshold:
            gt_matched.add(gi)
            pred_matched.add(best_pi)
            # Boundary accuracy
            pred = predictions[best_pi]
            boundary_offsets.append(abs(gt["start_sec"] - pred["start_sec"]))
            boundary_offsets.append(abs(gt["end_sec"] - pred["end_sec"]))

    hits = len(gt_matched)
    misses = len(ground_truth) - hits
    false_positives = len(predictions) - len(pred_matched)

    precision = hits / (hits + false_positives) if (hits + false_positives) > 0 else 0.0
    recall = hits / (hits + misses) if (hits + misses) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    boundary_acc = sum(boundary_offsets) / len(boundary_offsets) if boundary_offsets else 0.0

    return {
        "hits": hits,
        "misses": misses,
        "false_positives": false_positives,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "boundary_accuracy_sec": round(boundary_acc, 2),
    }


def suggest_calibration(
    metrics: dict,
    missed_details: list[dict],
    current_params: dict,
) -> list[dict]:
    """Suggest parameter adjustments based on evaluation results.

    missed_details: list of {"label": ..., "nearest_pred_score": ...} for each miss
    current_params: {"boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15}
    """
    suggestions = []

    # Low recall
    if metrics["recall"] < 0.80:
        # Check if misses are near the score threshold
        near_threshold = [
            m for m in missed_details
            if m.get("nearest_pred_score") and m["nearest_pred_score"] >= current_params["low_threshold"] * 0.7
        ]
        if near_threshold:
            new_low = round(min(m["nearest_pred_score"] for m in near_threshold) - 0.02, 2)
            suggestions.append({
                "symptom": f"{len(near_threshold)} misses scored near threshold ({current_params['low_threshold']})",
                "suggestion": f"Lower low_threshold from {current_params['low_threshold']} to {max(0.08, new_low)}",
                "param": "low_threshold",
                "current": current_params["low_threshold"],
                "suggested": max(0.08, new_low),
            })

        # Check if scene boundaries are too aggressive
        remaining_misses = len(missed_details) - len(near_threshold)
        if remaining_misses > 0 and current_params["boundary_percentile"] >= 88:
            new_pct = current_params["boundary_percentile"] - 5
            suggestions.append({
                "symptom": f"{remaining_misses} misses may be caused by aggressive scene boundary detection",
                "suggestion": f"Lower boundary_percentile from {current_params['boundary_percentile']} to {new_pct}",
                "param": "boundary_percentile",
                "current": current_params["boundary_percentile"],
                "suggested": new_pct,
            })

    # Low precision
    if metrics["precision"] < 0.75:
        new_high = round(current_params["high_threshold"] + 0.03, 2)
        suggestions.append({
            "symptom": f"Precision {metrics['precision']} below 0.75 — too many false positives",
            "suggestion": f"Raise high_threshold from {current_params['high_threshold']} to {new_high}",
            "param": "high_threshold",
            "current": current_params["high_threshold"],
            "suggested": new_high,
        })

    return suggestions


def generate_template(video_pattern: str, project_name: str = "") -> dict:
    """Generate ground truth template from video files."""
    video_paths = sorted(glob.glob(video_pattern))
    videos = []
    for vpath in video_paths:
        # Probe for duration
        duration = 0
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", vpath,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                fmt = json.loads(result.stdout).get("format", {})
                duration = float(fmt.get("duration", 0))
        except Exception:
            pass

        videos.append({
            "file": os.path.basename(vpath),
            "duration_sec": round(duration, 1),
            "segments": [],
        })

    return {
        "project": project_name,
        "videos": videos,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate asset-analyzer against ground truth")
    parser.add_argument("--generate-template", action="store_true", help="Generate ground truth template")
    parser.add_argument("--videos", help="Video glob pattern (for template generation)")
    parser.add_argument("--project-name", default="", help="Project name (for template)")
    parser.add_argument("--ground-truth", help="Path to ground truth JSON")
    parser.add_argument("--predictions", help="Path to predictions (video_analysis.json)")
    parser.add_argument("--output", default="eval_report.json", help="Output file")
    parser.add_argument("--iou-threshold", type=float, default=0.5, help="IoU threshold for hit/miss")
    args = parser.parse_args()

    if args.generate_template:
        if not args.videos:
            parser.error("--videos required for template generation")
        template = generate_template(args.videos, args.project_name)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        print(f"Template written to {args.output} ({len(template['videos'])} videos)")
        return

    if not args.ground_truth or not args.predictions:
        parser.error("--ground-truth and --predictions required for evaluation")

    with open(args.ground_truth, encoding="utf-8") as f:
        gt_data = json.load(f)
    with open(args.predictions, encoding="utf-8") as f:
        pred_data = json.load(f)

    # Match by filename
    all_metrics = []
    per_video = []
    all_missed_details = []

    for gt_video in gt_data["videos"]:
        fname = gt_video["file"]
        gt_segs = gt_video.get("segments", [])

        # Find matching predictions
        pred_segs = []
        if "videos" in pred_data:
            for pv in pred_data["videos"]:
                if os.path.basename(pv.get("source_file", "")) == fname:
                    pred_segs = pv.get("segments", [])
                    break

        metrics = evaluate_segments(gt_segs, pred_segs, args.iou_threshold)
        metrics["file"] = fname
        per_video.append(metrics)

        # Track missed details for calibration
        for gi, gt in enumerate(gt_segs):
            if gi not in {i for i in range(len(gt_segs))}:
                continue
            # Check if this GT was a miss
            best_iou = 0
            nearest_score = 0
            for pred in pred_segs:
                iou = compute_iou(gt["start_sec"], gt["end_sec"], pred["start_sec"], pred["end_sec"])
                if iou > best_iou:
                    best_iou = iou
                    nearest_score = pred.get("peak_score", 0)
            if best_iou < args.iou_threshold:
                all_missed_details.append({
                    "label": gt.get("label", ""),
                    "nearest_pred_score": nearest_score,
                })

    # Aggregate
    total_hits = sum(m["hits"] for m in per_video)
    total_misses = sum(m["misses"] for m in per_video)
    total_fp = sum(m["false_positives"] for m in per_video)

    precision = total_hits / (total_hits + total_fp) if (total_hits + total_fp) > 0 else 0
    recall = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    aggregate = {
        "hits": total_hits,
        "misses": total_misses,
        "false_positives": total_fp,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }

    # Auto-calibration suggestions
    current_params = {
        "boundary_percentile": 90,
        "high_threshold": 0.25,
        "low_threshold": 0.15,
    }
    suggestions = suggest_calibration(aggregate, all_missed_details, current_params)

    report = {
        "project": gt_data.get("project", ""),
        "iou_threshold": args.iou_threshold,
        "aggregate": aggregate,
        "per_video": per_video,
        "calibration_suggestions": suggestions,
        "current_params": current_params,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nEvaluation Report — {report['project']}")
    print(f"  Precision: {aggregate['precision']}")
    print(f"  Recall:    {aggregate['recall']}")
    print(f"  F1:        {aggregate['f1']}")
    if suggestions:
        print(f"\n  Calibration suggestions:")
        for s in suggestions:
            print(f"    - {s['suggestion']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run unit tests**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_evaluate.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/evaluate.py .claude/skills/asset-analyzer/scripts/test_evaluate.py
git commit -m "feat: add evaluate.py — IoU evaluation + auto-calibration suggestions"
```

---

## Task 7: Promote Script

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/promote.py`

Copies embeddings and metadata from the project pool to the global pool for selected clips.

- [ ] **Step 1: Implement promote.py**

```python
# .claude/skills/asset-analyzer/scripts/promote.py
"""Promote clips from project pool to global library."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex, get_pool_root


def promote_video(
    fhash: str,
    project_index: PoolIndex,
    global_index: PoolIndex,
) -> dict:
    """Copy a video's embeddings + metadata from project to global pool.

    Returns {"status": "promoted"|"already_exists"|"not_found", "hash": fhash}
    """
    if not project_index.has(fhash):
        return {"status": "not_found", "hash": fhash}

    if global_index.has(fhash):
        return {"status": "already_exists", "hash": fhash}

    # Load from project
    emb, ts = project_index.load_embeddings(fhash)
    entry = project_index.get(fhash)

    # Read full meta
    meta_path = project_index.root / fhash / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"source_path": entry.get("source_path", "")}

    # Write to global
    global_index.put(fhash, emb, ts, meta)

    return {"status": "promoted", "hash": fhash}


def main():
    parser = argparse.ArgumentParser(description="Promote clips from project to global library")
    parser.add_argument("--clips", nargs="+", help="Video filenames or hash:timecode specs to promote")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--all", action="store_true", help="Promote all project pool entries")
    args = parser.parse_args()

    project_root = get_pool_root("project", project_dir=os.path.abspath(args.project_dir))
    global_root = get_pool_root("global")

    project_idx = PoolIndex(project_root)
    global_idx = PoolIndex(global_root)

    entries = project_idx.list_entries()

    if args.all:
        hashes_to_promote = list(entries.keys())
    elif args.clips:
        # Match clip names to hashes
        hashes_to_promote = []
        for clip in args.clips:
            clip_base = clip.split(":")[0]  # strip timecode if present
            for fhash, entry in entries.items():
                src = os.path.basename(entry.get("source_path", ""))
                if clip_base in src:
                    hashes_to_promote.append(fhash)
                    break
            else:
                print(f"Warning: no match for '{clip}' in project pool")
    else:
        parser.error("Provide --clips or --all")
        return

    results = []
    for fhash in hashes_to_promote:
        result = promote_video(fhash, project_idx, global_idx)
        results.append(result)
        entry = entries.get(fhash, {})
        src = os.path.basename(entry.get("source_path", fhash))
        print(f"  {src}: {result['status']}")

    promoted = sum(1 for r in results if r["status"] == "promoted")
    existing = sum(1 for r in results if r["status"] == "already_exists")
    print(f"\nPromoted: {promoted}, Already in global: {existing}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/promote.py
git commit -m "feat: add promote.py — project to global library promotion"
```

---

## Task 8: Reference Files

**Files:**
- Create: `.claude/skills/asset-analyzer/references/taxonomy_global.yaml`
- Create: `.claude/skills/asset-analyzer/references/PE_CORE_USAGE.md`
- Create: `.claude/skills/asset-analyzer/references/SCORING_GUIDE.md`

- [ ] **Step 1: Write taxonomy_global.yaml**

```yaml
# Global taxonomy for video content classification.
# Derived from VISUAL_STYLE_GUIDE forms and variants.
# Grows over time as new patterns are discovered across projects.

atmospheric:
  atmospheric_institutional: "Institutional interior, ward, lobby, dim hallway"
  atmospheric_industrial: "Factory, machinery, smokestack, mechanical process"
  atmospheric_urban: "City texture, street, infrastructure, building at night"
  atmospheric_interior: "Generic indoor space, room, stairwell"

environment:
  environment_nature: "Forest, mountain, river, weather, landscape"
  environment_urban: "Cityscape, skyline, aerial city view"
  environment_rural: "Farmland, small town, open countryside"
  environment_water: "Ocean, lake, coastline, rain"

cartoon:
  cartoon_authority: "Authority figure, power dynamic, boss, ruler"
  cartoon_confinement: "Trap, cage, enclosure, locked room"
  cartoon_deception: "Trickery, disguise, hidden motive, con artist"
  cartoon_mechanical: "Machine, conveyor belt, labor, factory process"

archival_video:
  archival_news: "News broadcast, press footage, reporter on scene"
  archival_institutional: "Documentary footage of institution, hospital, school"

landscape:
  landscape_aerial: "Drone footage, aerial establishing shot, birds-eye view"
  landscape_rural: "Wide rural establishing shot, open field, countryside road"
  landscape_urban: "Wide urban establishing shot, city approach, downtown"

skip:
  talking_head: "Person speaking to camera, interview, talking head"
  title_graphic: "Title card, lower third, graphic overlay, channel logo"
  black_blank: "Black frame, blank screen, color bars, test pattern"
```

- [ ] **Step 2: Write PE_CORE_USAGE.md**

```markdown
# PE-Core-L14-336 Usage Reference

## Model Loading

```python
from perception_models import pe_core

model = pe_core.load_model("PE-Core-L14-336")
model = model.to("cuda").eval()

tokenizer = pe_core.get_tokenizer("PE-Core-L14-336")
preprocess = pe_core.get_preprocess("PE-Core-L14-336")
```

## Image Encoding

```python
from PIL import Image
import torch

img = preprocess(Image.open("frame.jpg"))
batch = img.unsqueeze(0).to("cuda")

with torch.no_grad(), torch.amp.autocast("cuda"):
    emb = model.encode_image(batch)          # [1, 768]
    emb = emb / emb.norm(dim=-1, keepdim=True)  # L2 normalize
```

## Text Encoding

```python
tokens = tokenizer(["a photo of a cathedral", "cartoon character"])
# tokens may be a dict or tensor depending on version
if isinstance(tokens, dict):
    tokens = {k: v.to("cuda") for k, v in tokens.items()}
else:
    tokens = tokens.to("cuda")

with torch.no_grad(), torch.amp.autocast("cuda"):
    emb = model.encode_text(tokens)
    emb = emb / emb.norm(dim=-1, keepdim=True)
```

## Cosine Similarity

After L2 normalization, cosine similarity = dot product:

```python
scores = image_emb @ text_emb.T  # [N_images, N_texts]
```

## Input Resolution

PE-Core-L14-336 expects 336x336 pixel input. The `preprocess` transform handles resizing and normalization.

## VRAM Usage

- Model weights: ~2 GB
- Batch of 64 frames at 336x336: ~1.5 GB
- Total peak: ~3.5 GB (well within 8 GB RTX 4070)

## Conda Environment

```
C:/Users/iorda/miniconda3/envs/perception-models/python.exe
```
```

- [ ] **Step 3: Write SCORING_GUIDE.md**

```markdown
# Score Interpretation Guide

## Cosine Similarity Ranges

CLIP-family models (including PE-Core) produce cosine similarities in roughly [-1, 1], but in practice text-image scores cluster in [0.05, 0.40].

| Score | Meaning | Action |
|-------|---------|--------|
| > 0.30 | Strong match — high visual-semantic alignment | Use directly |
| 0.25 – 0.30 | Good match — likely correct | Top 1 candidate per shot |
| 0.15 – 0.25 | Ambiguous — may or may not be relevant | Send top 3 to Claude review |
| < 0.15 | Weak/no match | Skip, or trigger query refinement |

## Content Type Effects

- **Live-action footage** tends to score higher (0.20–0.35 for good matches)
- **Cartoon/animated content** scores lower across the board (~0.15–0.28)
- **Abstract concepts** ("bureaucratic menace") score very low — rephrase to concrete visuals

## Query Refinement

When peak score < 0.20, the query is likely too abstract. Claude rephrases without viewing frames:
- Bad: "The psychological weight of institutional confinement"
- Good: "Empty corridor with rows of closed doors in dim lighting"

## Threshold Calibration

Starting thresholds (0.25/0.15) and boundary percentile (90th) are adjusted via the evaluation framework. After running `evaluate.py`, follow the calibration suggestions to tune for your footage mix.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/asset-analyzer/references/taxonomy_global.yaml .claude/skills/asset-analyzer/references/PE_CORE_USAGE.md .claude/skills/asset-analyzer/references/SCORING_GUIDE.md
git commit -m "docs: add reference files — taxonomy, PE-Core usage, scoring guide"
```

---

## Task 9: SKILL.md

**Files:**
- Create: `.claude/skills/asset-analyzer/SKILL.md`

The skill definition that Claude Code reads to orchestrate the pipeline.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: asset-analyzer
description: "Analyze and catalog video assets for documentary projects using PE-Core CLIP embeddings. Use when the user says 'analyze assets', 'analyze staging videos', 'discover footage', 'search footage for [topic]', 'find clips matching shotlist', 'evaluate asset selection', or any request to process downloaded video footage."
---

# Asset Analyzer V2

PE-Core CLIP embedding pipeline for video asset analysis. Embeds footage locally on GPU, matches against shotlist queries via cosine similarity, discovers content via auto-taxonomy, and evaluates selections against ground truth.

**Spec:** `docs/superpowers/specs/2026-03-31-asset-analyzer-v2-design.md`

## Modes

**Search mode** (default) — User references a project: "Analyze staging videos for Duplessis Orphans"
- Matches shotlist queries against embedded footage
- Searches both project and global pools
- Claude reviews top candidates adaptively (Sonnet subagent)

**Discovery mode** — "Discover what's in the Duplessis footage"
- Auto-generates project taxonomy from shotlist + script + research
- Classifies all frames against merged taxonomy (global + project)
- Clusters unknown frames via DBSCAN
- User browses and selects what to extract

**Evaluation mode** — "Evaluate asset selections for Duplessis"
- Compares skill selections against user-created ground truth
- Reports precision, recall, F1, boundary accuracy
- Suggests specific parameter adjustments

## Conda Environment

All scripts run via:
```
C:/Users/iorda/miniconda3/envs/perception-models/python.exe
```

## Search Workflow

### Step 1: Resolve context

1. Resolve project directory (case-insensitive substring match against `projects/`)
2. Read `visuals/download_manifest.json` — filter to video entries only (`.mp4`, `.webm`, `.mkv`)
3. Read `visuals/shotlist.json` — extract `search_query` fields from shots with `action: "curate"`

### Step 2: Embed staging videos

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/embed.py --input-dir "<project>/assets/staging" --pool project --project-dir "<project>"
```

Skips already-cached videos. First run ~15-20 min for 22h of footage, subsequent runs instant.

### Step 3: Build and run queries

Extract queries from shotlist — one per `curate` shot:
```json
[{"shot_id": "S006", "text": "Empty institutional corridor with dim lighting"}]
```

Write to `.claude/scratch/queries.json`, then:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/search.py --queries .claude/scratch/queries.json --project-dir "<project>" --output .claude/scratch/candidates.json
```

### Step 4: Refine weak queries

Read `candidates.json`. For queries in `weak_queries` (peak < 0.20), generate 2-3 alternative phrasings with concrete visual descriptions. Re-run search with refined queries.

Up to 3 refinement iterations. No vision needed — Claude sees only score reports.

### Step 5: Adaptive Claude review

Extract candidate frames to `.claude/scratch/frames/`:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/ingest.py --input "<video>" --output-dir .claude/scratch/frames --start <sec> --end <sec> --fps 1 --size 512
```

Send frames to Sonnet subagent (use `model: "sonnet"` in Agent tool):

| Score Range | Candidates Sent |
|-------------|-----------------|
| > 0.25 | Top 1 per shot |
| 0.15 – 0.25 | Top 3 per shot |
| < 0.15 | Skip — report to user |

Sonnet writes per-segment: description, mood, era, tags, scope, relevance.

### Step 6: Present for review

Present segment table:

| Video | Shot | Timestamps | Description | Score | Scope | Pool |
|-------|------|------------|-------------|-------|-------|------|

User approves/rejects, adjusts timestamps or scope.

### Step 7: Extract + Catalog

For each approved segment, use existing `export_clips.py`:

```bash
python .claude/skills/asset-analyzer/scripts/export_clips.py --input "<source>" --output "<dest>" --clips '[{"start": "<s>", "end": "<e>", "label": "<name>"}]'
```

Catalog in SQLite:
```python
from data.catalog import get_connection, insert_clip
conn = get_connection()
insert_clip(conn, path=clip_path, source_type="youtube", scope=scope,
            source_url=url, project=project_name, category=category,
            description=desc, mood=mood, era=era, tags=tags,
            duration_sec=duration)
```

**Output paths:**
- `scope: "project"` → `projects/N/assets/{category}/`
- `scope: "global"` → `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/`

## Discovery Workflow

### Step 1: Embed (same as search, skips if cached)

### Step 2: Generate project taxonomy

Read `shotlist.json`, `script/Script.md`, and research docs. Generate 5-15 project-specific categories with CLIP-friendly descriptions. Write to `.claude/scratch/project_taxonomy.json`:

```json
{
  "project_specific": {
    "quebec_institutional": "Quebec orphanage exterior, Catholic institution, grey stone building",
    "religious_ceremony": "Catholic mass, nuns in habit, church interior, crucifix"
  }
}
```

### Step 3: Run discovery

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/discover.py --pool project --project-dir "<project>" --taxonomy-global .claude/skills/asset-analyzer/references/taxonomy_global.yaml --taxonomy-project .claude/scratch/project_taxonomy.json --output .claude/scratch/discovery.json
```

### Step 4: Present results

Show category inventory (minutes per category) + unknown clusters with representative frames.

For unknown clusters, extract 1 representative frame per cluster and view it (Sonnet subagent) to propose a name.

### Step 5: User selects what to extract

### Step 6: Extract + Catalog (same as search)

### Step 7: Taxonomy growth

If user approves unknown cluster names, append them to `references/taxonomy_global.yaml` with a date comment:

```yaml
# Added 2026-04-15 from "The Duplessis Orphans" project
  atmospheric_religious: "Church interior, chapel, stained glass, religious iconography"
```

## Evaluation Workflow

### Step 1: Generate ground truth template

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/evaluate.py --generate-template --videos "<project>/assets/staging/*.mp4" --project-name "<name>" --output "<project>/visuals/ground_truth.json"
```

Give template to user. They fill in segments in DaVinci Resolve.

### Step 2: Run evaluation

After user completes ground truth:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/evaluate.py --ground-truth "<project>/visuals/ground_truth.json" --predictions "<project>/visuals/video_analysis.json" --output "<project>/visuals/eval_report.json"
```

### Step 3: Review and apply calibration

Present metrics and calibration suggestions. Apply approved parameter changes for the next run.

## Project Lifecycle

When a new project is initialized (channel-assistant `init_project()`):

1. Check if `./.broll-index/` exists from a previous project
2. If yes: prompt user to promote keepers via `promote.py`
3. After promotion: delete `./.broll-index/`

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 2 (embed) | Embedding summary (videos, frames, time) | Continue |
| Step 4 (refine) | Weak queries + proposed alternatives | Approve alternatives |
| Step 6 (present) | Segment table with scores | Approve/reject segments |
| Step 7 (cleanup) | Extraction complete | Delete staging files or keep |

## Model Routing

- **Haiku:** Not used in V2 (CLIP handles triage locally)
- **Sonnet:** Claude review of candidate frames (Step 5)
- **Opus:** Orchestration only — query refinement, taxonomy generation, presentation
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/asset-analyzer/SKILL.md
git commit -m "feat: add V2 SKILL.md for asset-analyzer — PE-Core CLIP pipeline"
```

---

## Task 10: Upstream Changes

**Files:**
- Modify: `channel/visuals/VISUAL_STYLE_GUIDE.md`
- Modify: `.claude/skills/shot-planner/SKILL.md`

- [ ] **Step 1: Update VISUAL_STYLE_GUIDE.md**

Add `broll_environment` form and update `broll_atmospheric` variants.

In the "Curated B-Roll Forms" table, after the `broll_cartoon` row, add:

```markdown
| `broll_environment` | Wide establishing or scenic footage — geographic and environmental context | nature, urban, rural, water |
```

Update the `broll_atmospheric` row's example variants from:
```
institutional_corridor, industrial, nature, urban_decay
```
to:
```
institutional, industrial, urban, interior
```

In the "Atmospheric B-Roll" section under "Visual Asset Types", add after it:

```markdown
### Environment B-Roll
Wide establishing and scenic footage that orients the viewer geographically. Nature, cityscapes, rural landscapes, bodies of water.

**When to use:** When the narration moves to a new location or needs a geographic anchor — establishing shots, transitions between settings, or scene-setting before specific content.

**Shot planner guidance:**
- Use `action: "curate"` with form `broll_environment`
- Preferred for `atmospheric` and `transitional` visual registers
- Distinct from `broll_atmospheric`: environment shots establish location, atmospheric shots establish mood
- Source the same way as atmospheric — archive.org footage with aged, documentary quality
```

- [ ] **Step 2: Update shot-planner SKILL.md**

In the Form Values table, add after `broll_atmospheric`:

```markdown
| `broll_environment` | curate | Wide establishing/scenic footage — nature, cityscapes, rural landscapes, water |
```

Update `broll_atmospheric` variant examples from `institutional_corridor, industrial, nature, urban_decay` to `institutional, industrial, urban, interior`.

- [ ] **Step 3: Commit**

```bash
git add "channel/visuals/VISUAL_STYLE_GUIDE.md" ".claude/skills/shot-planner/SKILL.md"
git commit -m "feat: add broll_environment form, update broll_atmospheric variants"
```

---

## Task 11: Integration Verification

End-to-end smoke test on real footage.

- [ ] **Step 1: Embed a staging video**

Pick one short video from Duplessis staging:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/embed.py --input "<short_video>.mp4" --pool project --project-dir "projects/1. The Duplessis Orphans Quebec's Stolen Children"
```

Verify: cache files created in `.broll-index/`, embedding count matches expected frame count.

- [ ] **Step 2: Search with a test query**

```bash
echo '[{"shot_id": "TEST01", "text": "institutional building exterior grey stone"}]' > .claude/scratch/test_queries.json
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/search.py --queries .claude/scratch/test_queries.json --project-dir "projects/1. The Duplessis Orphans Quebec's Stolen Children" --output .claude/scratch/test_candidates.json
```

Verify: `candidates.json` has results with scores, scene boundaries detected.

- [ ] **Step 3: Run discovery**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/discover.py --pool project --project-dir "projects/1. The Duplessis Orphans Quebec's Stolen Children" --taxonomy-global .claude/skills/asset-analyzer/references/taxonomy_global.yaml --output .claude/scratch/test_discovery.json
```

Verify: category inventory populated, clusters found (or noise if too few frames).

- [ ] **Step 4: Generate evaluation template**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/evaluate.py --generate-template --videos "projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/staging/*.mp4" --project-name "The Duplessis Orphans" --output .claude/scratch/test_ground_truth.json
```

Verify: template has all video filenames and durations, empty segments arrays.

- [ ] **Step 5: Clean up scratch files**

```bash
rm -f .claude/scratch/test_*.json .claude/scratch/queries.json
```

- [ ] **Step 6: Run all unit tests**

```bash
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py test_search.py test_evaluate.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "test: integration verification of asset-analyzer V2 pipeline"
```
