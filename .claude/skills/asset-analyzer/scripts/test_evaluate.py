import pytest
from evaluate import compute_iou, evaluate_segments, suggest_calibration, generate_template

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


def test_iou_zero_length_segment():
    """Segment with start == end has zero area, IoU = 0."""
    assert compute_iou(5, 5, 0, 10) == 0.0


def test_iou_negative_segment():
    """Segment with start > end returns 0."""
    assert compute_iou(10, 5, 0, 15) == 0.0


def test_iou_touching_segments():
    """Adjacent segments [0,5] and [5,10] have IoU = 0 (no overlap)."""
    assert compute_iou(0, 5, 5, 10) == 0.0


def test_evaluate_multiple_gt_one_pred():
    """One prediction can only match one GT segment (greedy)."""
    gt = [
        {"start_sec": 10, "end_sec": 20, "label": "a"},
        {"start_sec": 12, "end_sec": 18, "label": "b"},
    ]
    pred = [{"start_sec": 10, "end_sec": 20}]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 1
    assert result["misses"] == 1


def test_evaluate_one_gt_multiple_pred():
    """Multiple predictions, only one matches GT, rest are FP."""
    gt = [{"start_sec": 10, "end_sec": 20, "label": "a"}]
    pred = [
        {"start_sec": 10, "end_sec": 20},
        {"start_sec": 50, "end_sec": 60},
        {"start_sec": 70, "end_sec": 80},
    ]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 1
    assert result["false_positives"] == 2


def test_evaluate_empty_both():
    """No GT + no predictions returns zeroed metrics."""
    result = evaluate_segments([], [], iou_threshold=0.5)
    assert result["hits"] == 0
    assert result["misses"] == 0
    assert result["false_positives"] == 0
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0


def test_suggest_calibration_low_precision():
    """Precision < 0.75 suggests raising high_threshold."""
    metrics = {"recall": 0.90, "precision": 0.60, "hits": 6, "misses": 0, "false_positives": 4}
    suggestions = suggest_calibration(metrics, [], current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    assert any(s["param"] == "high_threshold" for s in suggestions)


def test_suggest_calibration_both_low():
    """Both low recall and low precision produce multiple suggestions."""
    metrics = {"recall": 0.50, "precision": 0.50, "hits": 2, "misses": 2, "false_positives": 2}
    missed = [
        {"label": "test", "nearest_pred_score": 0.13},
        {"label": "test2", "nearest_pred_score": 0.14},
    ]
    suggestions = suggest_calibration(metrics, missed, current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    assert len(suggestions) >= 2


def test_generate_template_no_videos():
    """Empty glob pattern returns template with empty videos list."""
    template = generate_template("/nonexistent/path/*.mp4", "Test Project")
    assert template["project"] == "Test Project"
    assert template["videos"] == []
