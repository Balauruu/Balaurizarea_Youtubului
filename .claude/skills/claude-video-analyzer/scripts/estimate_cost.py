#!/usr/bin/env python3
"""
Estimate token usage and cost before running video analysis.
Prints a human-readable confirmation prompt for the user to approve.
"""

import sys
import json
import argparse
import math

# Claude subscription context: no per-token billing, but estimate relative "weight"
# For API users: current vision pricing (per 1M tokens)
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":         {"input": 0.80, "output": 4.00},
}
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Token costs per image (approximate, based on standard 1024px image)
# Claude vision: ~1000-1600 tokens per image depending on resolution
TOKENS_PER_FRAME = {
    "low":    800,   # <512px
    "medium": 1100,  # 512-1024px (most common after ffmpeg extraction)
    "high":   1600,  # >1024px or complex scenes
}

# Extraction rates per mode
MODE_FPS = {
    "quick":     1,
    "standard":  2,
    "detailed":  5,
    "technical": None,   # full frame count
    "keyframes": None,   # estimated ~0.3x scene changes
}

# Output tokens per batch (approximate response length)
OUTPUT_TOKENS_PER_BATCH = 400
FRAMES_PER_BATCH = 15


def estimate(duration_sec, declared_fps, mode, resolution_w, resolution_h, model=DEFAULT_MODEL):
    # Determine image size tier
    max_dim = max(resolution_w or 0, resolution_h or 0)
    if max_dim < 512:
        size_tier = "low"
    elif max_dim <= 1024:
        size_tier = "medium"
    else:
        size_tier = "high"

    tokens_per_frame = TOKENS_PER_FRAME[size_tier]

    # Estimate frame count
    mode_fps = MODE_FPS.get(mode)
    if mode_fps is not None:
        estimated_frames = int(duration_sec * mode_fps)
    elif mode == "technical":
        estimated_frames = int(duration_sec * declared_fps)
    elif mode == "keyframes":
        # Keyframes: roughly 1 per 3-5 seconds of content (varies wildly)
        estimated_frames = max(1, int(duration_sec / 4))
    else:
        estimated_frames = int(duration_sec * 2)

    # Batch count
    num_batches = math.ceil(estimated_frames / FRAMES_PER_BATCH)

    # Token math
    input_tokens = estimated_frames * tokens_per_frame
    # Add text prompt tokens per batch (~200 tokens system + context)
    input_tokens += num_batches * 200
    output_tokens = num_batches * OUTPUT_TOKENS_PER_BATCH

    total_tokens = input_tokens + output_tokens

    # Cost (API users only)
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    # Time estimate (rough: ~3 frames/sec processing rate)
    estimated_minutes = round(estimated_frames / (3 * 60), 1)

    return {
        "mode": mode,
        "duration_sec": duration_sec,
        "resolution": f"{resolution_w}×{resolution_h}",
        "size_tier": size_tier,
        "estimated_frames": estimated_frames,
        "tokens_per_frame": tokens_per_frame,
        "num_batches": num_batches,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "api_cost_usd": round(total_cost, 4),
        "estimated_minutes": estimated_minutes,
        "model": model,
    }


def format_confirmation(probe_data, mode, model=DEFAULT_MODEL):
    duration = probe_data.get("duration_sec", 0)
    w = probe_data.get("width", 1280)
    h = probe_data.get("height", 720)
    fps = probe_data.get("declared_fps", 30)
    filename = probe_data.get("file", "video")

    est = estimate(duration, fps, mode, w, h, model)

    # Format tokens nicely
    def fmt_tokens(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.0f}K"
        return str(n)

    lines = [
        "",
        "┌─────────────────────────────────────────────┐",
        "│           VIDEO ANALYSIS ESTIMATE            │",
        "└─────────────────────────────────────────────┘",
        "",
        f"  File        : {filename}",
        f"  Duration    : {probe_data.get('duration_human', f'{duration:.0f}s')}",
        f"  Resolution  : {w}×{h}",
        f"  Mode        : {mode}",
        "",
        f"  Frames      : ~{est['estimated_frames']:,}",
        f"  Batches     : {est['num_batches']}",
        f"  Input tokens: ~{fmt_tokens(est['input_tokens'])}",
        f"  Output tokens: ~{fmt_tokens(est['output_tokens'])}",
        f"  Total tokens: ~{fmt_tokens(est['total_tokens'])}",
        "",
    ]

    # Subscription vs API messaging
    lines += [
        "  ─────────────────────────────────────────",
        "  💳 Subscription (Claude Code): No extra cost",
        f"     but will consume significant usage quota",
        f"  💰 API billing (if applicable):",
        f"     ~${est['api_cost_usd']:.4f} USD ({model.split('-')[1].title()})",
        "  ─────────────────────────────────────────",
        "",
        f"  ⏱  Estimated time: ~{est['estimated_minutes']} min",
        "",
    ]

    # Recommendations
    if est["estimated_frames"] > 500:
        lines.append("  ⚠️  Large job. Consider using 'quick' mode or")
        lines.append("      limiting to a time range (--start / --end)")
        lines.append("")
    elif est["estimated_frames"] > 200:
        lines.append("  ℹ️  Medium job. Should complete without issues.")
        lines.append("")
    else:
        lines.append("  ✅ Small job. Fast and efficient.")
        lines.append("")

    lines += [
        "  Proceed with analysis? [yes / no / change mode]",
        "",
    ]

    return "\n".join(lines), est


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", required=True, help="Path to probe JSON or inline JSON string")
    parser.add_argument("--mode", default="standard")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    # Load probe data
    if args.probe.startswith("{"):
        probe_data = json.loads(args.probe)
    else:
        with open(args.probe) as f:
            probe_data = json.load(f)

    text, est_data = format_confirmation(probe_data, args.mode, args.model)

    if args.json:
        print(json.dumps(est_data, indent=2))
    else:
        print(text)
        # Also write JSON for programmatic use
        import tempfile, os
        est_path = os.path.join(tempfile.gettempdir(), "video_estimate.json")
        with open(est_path, "w") as f:
            json.dump(est_data, f, indent=2)
        print(f"  [Estimate saved to {est_path}]")
