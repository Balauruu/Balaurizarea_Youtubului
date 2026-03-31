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

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex, file_hash, get_pool_root
from ingest import extract_frames

PE_PYTHON = "C:/Users/iorda/miniconda3/envs/perception-models/python.exe"


def load_model(device: str = "cuda"):
    """Load PE-Core-L14-336 and return (model, tokenizer, preprocess)."""
    import sys as _sys
    _sys.path.insert(0, "C:/Users/iorda/repos/perception_models")
    import core.vision_encoder.pe as pe
    import core.vision_encoder.transforms as transforms

    model = pe.CLIP.from_config("PE-Core-L14-336", pretrained=True)
    model = model.to(device).eval()

    tokenizer = transforms.get_text_tokenizer(model.context_length)
    preprocess = transforms.get_image_transform(model.image_size)

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
            emb = emb / emb.norm(dim=-1, keepdim=True)

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

    frames = extract_frames(video_path, fps=fps, size=size)
    if not frames:
        return {"status": "empty", "hash": fhash, "frames": 0}

    embeddings = embed_frames(model, preprocess, frames, batch_size=batch_size)
    timestamps = np.arange(len(frames), dtype=np.float64) / fps

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
    parser.add_argument("--pool", default="project", choices=["project", "global"])
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--health-check", action="store_true")
    args = parser.parse_args()

    pool_root = get_pool_root(args.pool, project_dir=os.path.abspath(args.project_dir))
    pool_index = PoolIndex(pool_root)

    if args.health_check:
        report = pool_index.health_check()
        print(json.dumps(report, indent=2))
        return

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

    new = sum(1 for r in results if r["status"] == "embedded")
    cached = sum(1 for r in results if r["status"] == "cached")
    print(f"\nDone: {new} embedded, {cached} cached (skipped), {len(videos)} total")


if __name__ == "__main__":
    main()
