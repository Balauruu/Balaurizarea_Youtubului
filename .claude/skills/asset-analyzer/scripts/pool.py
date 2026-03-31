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
