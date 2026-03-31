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


def load_taxonomy(path: str) -> tuple[dict, set]:
    """Load taxonomy YAML. Returns (categories dict, skip_keys set)."""
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
    """Load and merge global + project taxonomies."""
    categories, skip_keys = load_taxonomy(global_path)

    if project_path and os.path.exists(project_path):
        with open(project_path, encoding="utf-8") as f:
            project_tax = json.load(f)
        if isinstance(project_tax, dict):
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
    """Classify each frame against taxonomy categories via zero-shot scoring."""
    import torch

    cat_keys = list(categories.keys())
    cat_descs = list(categories.values())

    tokens = tokenizer(cat_descs)
    if isinstance(tokens, dict):
        tokens = {k: v.to(device) for k, v in tokens.items()}
    else:
        tokens = tokens.to(device)

    with torch.no_grad(), torch.amp.autocast("cuda"):
        cat_emb = model.encode_text(tokens)
        cat_emb = cat_emb / cat_emb.norm(dim=-1, keepdim=True)

    cat_emb_np = cat_emb.cpu().numpy().astype(np.float32)

    fe = frame_embeddings.astype(np.float32)
    scores = fe @ cat_emb_np.T

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
    """DBSCAN cluster unknown-classified embeddings."""
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

    categories, skip_keys = merge_taxonomies(taxonomy_global_path, taxonomy_project_path)

    primary_cats, max_scores = classify_frames(
        all_emb, categories, model, tokenizer,
        confidence_threshold=confidence_threshold,
    )

    inventory = defaultdict(lambda: {"frame_count": 0, "total_seconds": 0, "videos": set()})

    unknown_indices = []
    for i, (cat, score) in enumerate(zip(primary_cats, max_scores)):
        if cat in skip_keys:
            continue
        if cat == "__unknown__":
            unknown_indices.append(i)
            continue
        inventory[cat]["frame_count"] += 1
        inventory[cat]["total_seconds"] += 1
        inventory[cat]["videos"].add(all_info[i]["source_path"])

    inv_json = {}
    for cat, data in inventory.items():
        inv_json[cat] = {
            "frame_count": data["frame_count"],
            "total_minutes": round(data["total_seconds"] / 60, 2),
            "videos": [os.path.basename(v) for v in data["videos"]],
        }

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

            cluster_emb = all_emb[cluster_indices]
            centroid = cluster_emb.mean(axis=0)
            dists = np.linalg.norm(cluster_emb - centroid, axis=1)
            rep_idx = cluster_indices[dists.argmin()]

            video_ranges = defaultdict(list)
            for ci in cluster_indices:
                src = os.path.basename(all_info[ci]["source_path"])
                video_ranges[src].append(float(all_ts[ci]))

            ts_ranges = {}
            for src, times in video_ranges.items():
                times.sort()
                ranges = []
                start = times[0]
                end = times[0]
                for t in times[1:]:
                    if t - end <= 2:
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
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--taxonomy-global", required=True)
    parser.add_argument("--taxonomy-project")
    parser.add_argument("--output", default="discovery.json")
    parser.add_argument("--eps", type=float, default=0.3)
    parser.add_argument("--min-samples", type=int, default=3)
    parser.add_argument("--confidence-threshold", type=float, default=0.15)
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
