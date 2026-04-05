"""Shotlist query matching against cached embeddings from both pools."""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SCORE_NO_MATCH = 0.15    # Below this, skip entirely
SCORE_WEAK_QUERY = 0.20  # Below this, flag for refinement


def fmt_ts(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

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

    emb = embeddings.astype(np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-8)
    emb_norm = emb / norms

    sims = np.sum(emb_norm[:-1] * emb_norm[1:], axis=1)
    deltas = 1.0 - sims

    threshold = np.percentile(deltas, percentile)
    if threshold < 0.01:
        return []

    cut_indices = np.where(deltas >= threshold)[0]
    boundaries = []
    for idx in cut_indices:
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
    """Group consecutive above-threshold frames into segments, respecting scene boundaries."""
    above = scores >= threshold
    segments = []
    current_start = None
    current_scores = []
    current_best_score = -1
    current_best_sec = 0

    for i, (is_above, ts_val) in enumerate(zip(above, timestamps)):
        crossed_boundary = False
        if current_start is not None:
            for b in boundaries:
                if timestamps[i - 1] < b <= ts_val:
                    crossed_boundary = True
                    break

        if crossed_boundary and current_start is not None:
            segments.append({
                "start_sec": float(current_start),
                "end_sec": float(timestamps[i - 1]),
                "start_ts": fmt_ts(current_start),
                "end_ts": fmt_ts(timestamps[i - 1]),
                "peak_score": float(max(current_scores)),
                "mean_score": float(np.mean(current_scores)),
                "best_frame_sec": float(current_best_sec),
                "best_frame_ts": fmt_ts(current_best_sec),
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
                    "start_ts": fmt_ts(current_start),
                    "end_ts": fmt_ts(timestamps[i - 1]),
                    "peak_score": float(max(current_scores)),
                    "mean_score": float(np.mean(current_scores)),
                    "best_frame_sec": float(current_best_sec),
                    "best_frame_ts": fmt_ts(current_best_sec),
                })
                current_start = None
                current_scores = []
                current_best_score = -1

    if current_start is not None:
        segments.append({
            "start_sec": float(current_start),
            "end_sec": float(timestamps[-1]),
            "start_ts": fmt_ts(current_start),
            "end_ts": fmt_ts(timestamps[-1]),
            "peak_score": float(max(current_scores)),
            "mean_score": float(np.mean(current_scores)),
            "best_frame_sec": float(current_best_sec),
            "best_frame_ts": fmt_ts(current_best_sec),
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
    segment_threshold: float = 0.15,
) -> dict:
    """Run shotlist queries against both pools. Returns candidates.json structure."""
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

    scene_boundaries = {}
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

    query_texts = [q["text"] for q in queries]
    query_emb = encode_text_queries(model, tokenizer, query_texts)

    scores = score_queries(all_emb, query_emb)

    query_results = []
    weak_queries = []

    for qi, q in enumerate(queries):
        q_scores = scores[:, qi]
        peak = float(q_scores.max())

        if peak < SCORE_NO_MATCH:
            weak_queries.append(q["shot_id"])
            query_results.append({
                "shot_id": q["shot_id"],
                "query_text": q["text"],
                "refined_queries": [],
                "candidates": [],
            })
            continue

        candidates = []
        for src, frame_list in video_frames.items():
            indices = [f[0] for f in sorted(frame_list, key=lambda x: x[1])]
            vid_scores = q_scores[indices]
            vid_ts = np.array([all_ts[i] for i in indices])
            vid_boundaries = scene_boundaries.get(src, [])
            pool = all_info_list[indices[0]]["pool"] if indices else "project"

            segments = group_into_segments(vid_scores, vid_ts, vid_boundaries, threshold=segment_threshold)
            for seg in segments:
                seg["video"] = os.path.basename(src)
                seg["video_path"] = src
                seg["pool"] = pool
                candidates.append(seg)

        candidates.sort(key=lambda c: c["peak_score"], reverse=True)

        query_results.append({
            "shot_id": q["shot_id"],
            "query_text": q["text"],
            "refined_queries": [],
            "candidates": candidates[:10],
        })

        if peak < SCORE_WEAK_QUERY:
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
    parser.add_argument("--output", default="candidates.json")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--pool-only", choices=["project", "global"])
    parser.add_argument("--boundary-percentile", type=int, default=90)
    parser.add_argument("--segment-threshold", type=float, default=0.15)
    args = parser.parse_args()

    with open(args.queries, encoding="utf-8") as f:
        queries = json.load(f)

    from embed import load_model
    model, tokenizer, _ = load_model()

    results = search(
        queries=queries,
        project_dir=os.path.abspath(args.project_dir),
        model=model,
        tokenizer=tokenizer,
        pool_only=args.pool_only,
        boundary_percentile=args.boundary_percentile,
        segment_threshold=args.segment_threshold,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results written to {args.output}")
    print(f"  Pools searched: {list(results['pools_searched'].keys())}")
    print(f"  Queries: {len(results['query_results'])}")
    print(f"  Weak queries: {results['weak_queries']}")


if __name__ == "__main__":
    main()
