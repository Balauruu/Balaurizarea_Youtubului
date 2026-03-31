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
    """Compare predicted segments against ground truth using IoU."""
    gt_matched = set()
    pred_matched = set()
    boundary_offsets = []

    for gi, gt in enumerate(ground_truth):
        best_iou = 0
        best_pi = -1
        for pi, pred in enumerate(predictions):
            if pi in pred_matched:
                continue
            iou = compute_iou(gt["start_sec"], gt["end_sec"], pred["start_sec"], pred["end_sec"])
            if iou > best_iou:
                best_iou = iou
                best_pi = pi

        if best_iou >= iou_threshold:
            gt_matched.add(gi)
            pred_matched.add(best_pi)
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
    """Suggest parameter adjustments based on evaluation results."""
    suggestions = []

    if metrics["recall"] < 0.80:
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
    parser.add_argument("--generate-template", action="store_true")
    parser.add_argument("--videos", help="Video glob pattern")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--ground-truth", help="Path to ground truth JSON")
    parser.add_argument("--predictions", help="Path to predictions JSON")
    parser.add_argument("--output", default="eval_report.json")
    parser.add_argument("--iou-threshold", type=float, default=0.5)
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

    all_metrics = []
    per_video = []
    all_missed_details = []

    for gt_video in gt_data["videos"]:
        fname = gt_video["file"]
        gt_segs = gt_video.get("segments", [])

        pred_segs = []
        if "videos" in pred_data:
            for pv in pred_data["videos"]:
                if os.path.basename(pv.get("source_file", "")) == fname:
                    pred_segs = pv.get("segments", [])
                    break

        metrics = evaluate_segments(gt_segs, pred_segs, args.iou_threshold)
        metrics["file"] = fname
        per_video.append(metrics)

        for gi, gt in enumerate(gt_segs):
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

    total_hits = sum(m["hits"] for m in per_video)
    total_misses = sum(m["misses"] for m in per_video)
    total_fp = sum(m["false_positives"] for m in per_video)

    precision = total_hits / (total_hits + total_fp) if (total_hits + total_fp) > 0 else 0
    recall = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    aggregate = {
        "hits": total_hits, "misses": total_misses, "false_positives": total_fp,
        "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
    }

    current_params = {"boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15}
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
