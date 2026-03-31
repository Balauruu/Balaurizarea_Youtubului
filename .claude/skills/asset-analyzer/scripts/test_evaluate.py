import pytest
from evaluate import compute_iou, evaluate_segments, suggest_calibration

def test_iou_full_overlap():
    assert compute_iou(10, 20, 10, 20) == 1.0

def test_iou_no_overlap():
    assert compute_iou(0, 5, 10, 15) == 0.0

def test_iou_partial_overlap():
    iou = compute_iou(0, 10, 5, 15)
    assert abs(iou - 5 / 15) < 0.01

def test_iou_contained():
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
    assert any("threshold" in s["suggestion"].lower() for s in suggestions)

def test_suggest_calibration_good_metrics():
    metrics = {"recall": 0.90, "precision": 0.88, "hits": 9, "misses": 1, "false_positives": 1}
    suggestions = suggest_calibration(metrics, [], current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    assert len(suggestions) <= 1
