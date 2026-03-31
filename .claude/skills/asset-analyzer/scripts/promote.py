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
    """Copy a video's embeddings + metadata from project to global pool."""
    if not project_index.has(fhash):
        return {"status": "not_found", "hash": fhash}

    if global_index.has(fhash):
        return {"status": "already_exists", "hash": fhash}

    emb, ts = project_index.load_embeddings(fhash)
    entry = project_index.get(fhash)

    meta_path = project_index.root / fhash / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"source_path": entry.get("source_path", "")}

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
        hashes_to_promote = []
        for clip in args.clips:
            clip_base = clip.split(":")[0]
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
