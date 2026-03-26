#!/usr/bin/env python3
"""Estimate token usage for two-pass documentary video analysis."""

import sys
import json
import argparse
import math

PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":         {"input": 0.80, "output": 4.00},
}
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# 512px downscaled frames
TOKENS_PER_FRAME_TRIAGE = 800   # single mid-scene frame at 512px
TOKENS_PER_FRAME_FULL = 800     # full frames at 512px
OUTPUT_TOKENS_PER_BATCH = 400
FRAMES_PER_BATCH = 15


def estimate_triage(scene_count, model=DEFAULT_MODEL):
    """Estimate cost for triage pass (1 frame per scene)."""
    num_batches = math.ceil(scene_count / FRAMES_PER_BATCH)
    input_tokens = scene_count * TOKENS_PER_FRAME_TRIAGE + num_batches * 200
    output_tokens = num_batches * OUTPUT_TOKENS_PER_BATCH
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    cost = (input_tokens / 1e6) * pricing["input"] + (output_tokens / 1e6) * pricing["output"]

    return {
        "pass": "triage",
        "frames": scene_count,
        "batches": num_batches,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": round(cost, 4),
        "estimated_minutes": round(scene_count / (3 * 60), 1),
    }


def estimate_full(relevant_duration_sec, fps=2, model=DEFAULT_MODEL):
    """Estimate cost for full pass on relevant scenes only."""
    frame_count = int(relevant_duration_sec * fps)
    num_batches = math.ceil(frame_count / FRAMES_PER_BATCH)
    input_tokens = frame_count * TOKENS_PER_FRAME_FULL + num_batches * 200
    output_tokens = num_batches * OUTPUT_TOKENS_PER_BATCH
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    cost = (input_tokens / 1e6) * pricing["input"] + (output_tokens / 1e6) * pricing["output"]

    return {
        "pass": "full",
        "frames": frame_count,
        "batches": num_batches,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": round(cost, 4),
        "estimated_minutes": round(frame_count / (3 * 60), 1),
    }


def format_two_pass(video_name, duration_sec, scene_count, relevance_pct=15, model=DEFAULT_MODEL):
    """Format a two-pass estimate for user confirmation."""
    triage = estimate_triage(scene_count, model)

    # Estimate relevant duration assuming relevance_pct% of scenes are relevant
    relevant_duration = duration_sec * (relevance_pct / 100)
    full = estimate_full(relevant_duration, fps=2, model=model)

    total_tokens = triage["total_tokens"] + full["total_tokens"]
    total_cost = triage["cost_usd"] + full["cost_usd"]
    total_time = triage["estimated_minutes"] + full["estimated_minutes"]

    def fmt_tokens(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.0f}K"
        return str(n)

    lines = [
        "",
        "  TWO-PASS ANALYSIS ESTIMATE",
        "  " + "=" * 40,
        f"  Video       : {video_name}",
        f"  Duration    : {int(duration_sec//60)}m {int(duration_sec%60)}s",
        f"  Scenes      : {scene_count}",
        "",
        f"  Pass 1 (triage): {scene_count} frames → ~{fmt_tokens(triage['total_tokens'])} tokens",
        f"  Pass 2 (full):   ~{full['frames']} frames → ~{fmt_tokens(full['total_tokens'])} tokens",
        f"    (assuming ~{relevance_pct}% scene relevance)",
        "",
        f"  Total tokens: ~{fmt_tokens(total_tokens)}",
        f"  API cost:     ~${total_cost:.4f} ({model.split('-')[1].title()})",
        f"  Est. time:    ~{total_time:.1f} min",
        "",
    ]

    return "\n".join(lines), {"triage": triage, "full": full, "total_tokens": total_tokens, "total_cost_usd": total_cost}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-name", default="video")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--scenes", type=int, required=True)
    parser.add_argument("--relevance-pct", type=float, default=15)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text, data = format_two_pass(args.video_name, args.duration, args.scenes, args.relevance_pct, args.model)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(text)
