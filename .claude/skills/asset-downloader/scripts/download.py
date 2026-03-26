#!/usr/bin/env python3
"""Download video assets from YouTube and archive.org for a documentary project."""

import sys
import os
import json
import subprocess
import argparse
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

VOLUME_CAP_MB = 200 * 1024  # 200 GB
YT_DLP = "yt-dlp"
YOUTUBE_BATCH_SIZE = 10
YOUTUBE_BATCH_PAUSE = 15  # seconds between batches
TARGET_FPS = 24
IA_PARALLEL_WORKERS = 5

# Patterns that indicate YouTube bot detection (beyond HTTP 429)
BOT_DETECTION_PATTERNS = [
    "429",
    "Too Many Requests",
    "Sign in to confirm",
    "not a bot",
    "confirm you're not a bot",
]


def log(msg):
    """Print with immediate flush so output is visible in real-time."""
    print(msg, flush=True)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ffprobe_validate(file_path):
    """Return True if ffprobe can read the file and it has a video stream."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=duration", "-of", "json", file_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False
        data = json.loads(result.stdout)
        return len(data.get("streams", [])) > 0
    except Exception:
        return False


def get_file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def get_video_fps(file_path):
    """Return the FPS of a video file, or None on failure."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "json", file_path],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None
        streams = json.loads(result.stdout).get("streams", [])
        if not streams:
            return None
        fps_str = streams[0].get("r_frame_rate", "0/1")
        num, den = fps_str.split("/")
        return round(float(num) / float(den), 3)
    except Exception:
        return None


def reencode_to_24fps(file_path):
    """Re-encode a video to 24fps. Returns (new_path, original_fps, error)."""
    fps = get_video_fps(file_path)
    if fps is None:
        return file_path, None, None
    if fps <= TARGET_FPS:
        return file_path, fps, None

    tmp_path = file_path + ".24fps.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-r", str(TARGET_FPS),
        "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast",
        "-c:a", "copy",
        tmp_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return file_path, fps, f"Re-encode failed: {result.stderr[-200:]}"

    # Replace original with re-encoded version
    os.remove(file_path)
    os.rename(tmp_path, file_path)
    return file_path, fps, None


def is_bot_detected(error_text):
    """Check if an error message indicates YouTube bot detection."""
    if not error_text:
        return False
    lower = error_text.lower()
    return any(p.lower() in lower for p in BOT_DETECTION_PATTERNS)


def detect_browser_for_cookies():
    """Auto-detect Brave browser cookies. Returns 'brave' or None."""
    brave_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Cookies"),
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Network\Cookies"),
    ]
    for cp in brave_paths:
        if os.path.exists(cp):
            return "brave"
    return None


def collect_urls(project_dir):
    """Collect all video URLs from media_leads.json and shotlist.json."""
    entries = []
    seen_urls = set()

    # YouTube URLs from media_leads.json
    media_leads_path = os.path.join(project_dir, "visuals", "media_leads.json")
    if os.path.exists(media_leads_path):
        ml = load_json(media_leads_path)
        for yt in ml.get("youtube_urls", []):
            url = yt.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            entries.append({
                "source": "youtube",
                "source_url": url,
                "title": yt.get("title", "Unknown"),
                "duration_sec": yt.get("duration_sec"),
                "score": yt.get("score"),
                "shot_refs": [],
                "context": yt.get("description", ""),
            })

    # Archive.org URLs from shotlist.json broll_leads
    shotlist_path = os.path.join(project_dir, "visuals", "shotlist.json")
    if os.path.exists(shotlist_path):
        sl = load_json(shotlist_path)
        for shot in sl.get("shots", []):
            for lead in shot.get("broll_leads", []):
                url = lead.get("url", "")
                if not url or url not in seen_urls:
                    if url:
                        seen_urls.add(url)
                        # Find all shot_refs for this URL
                        refs = [shot.get("id", "")]
                        entries.append({
                            "source": "internet_archive",
                            "source_url": url,
                            "title": lead.get("title", "Unknown"),
                            "duration_sec": None,
                            "score": None,
                            "shot_refs": refs,
                            "context": lead.get("match_reasoning", lead.get("description", "")),
                        })
                else:
                    # URL already collected — merge shot_ref
                    for e in entries:
                        if e["source_url"] == url:
                            shot_id = shot.get("id", "")
                            if shot_id and shot_id not in e["shot_refs"]:
                                e["shot_refs"].append(shot_id)
                            break

    return entries


def download_youtube(url, staging_dir, score=None, cookies_browser=None, cookies_file=None):
    """Download a YouTube video. Returns (local_path, error)."""
    # Extract video ID for filename
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    vid_id = match.group(1) if match else "unknown"
    output_template = os.path.join(staging_dir, f"yt_{vid_id}.%(ext)s")

    # Score 1 = tier 1 (primary source) — keep audio. All others = video only.
    if score == 1:
        fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"
    else:
        fmt = "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]"

    cmd = [
        YT_DLP,
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--restrict-filenames",
        "--concurrent-fragments", "4",
        "--http-chunk-size", "10M",
        "--sleep-interval", "3",
        "--max-sleep-interval", "8",
        "--no-overwrites",
        "-o", output_template,
    ]

    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    elif cookies_browser:
        cmd.extend(["--cookies-from-browser", cookies_browser])

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Find the output file
    expected = os.path.join(staging_dir, f"yt_{vid_id}.mp4")
    if os.path.exists(expected):
        return expected, None

    # Check for error
    if result.returncode != 0:
        stderr = result.stderr[-500:] if result.stderr else "Unknown error"
        if is_bot_detected(stderr):
            return None, "YouTube bot detection — sign-in required"
        return None, stderr.strip()

    return None, "Output file not found after download"


def download_archive_org(url, staging_dir):
    """Download a video from archive.org using yt-dlp. Returns (local_path, error)."""
    # Extract item ID from URL for filename
    match = re.search(r"archive\.org/details/([^/?#]+)", url)
    if not match:
        return None, f"Cannot parse archive.org item ID from: {url}"
    item_id = match.group(1)

    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", item_id)[:60]
    local_path = os.path.join(staging_dir, f"ia_{slug}.mp4")

    if os.path.exists(local_path):
        return local_path, None

    # Use yt-dlp which natively supports archive.org
    output_template = os.path.join(staging_dir, f"ia_{slug}.%(ext)s")
    cmd = [
        YT_DLP,
        "-f", "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--restrict-filenames",
        "--no-overwrites",
        "-o", output_template,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if os.path.exists(local_path):
        return local_path, None

    # yt-dlp might have saved with a different extension, check for any match
    for f in os.listdir(staging_dir):
        if f.startswith(f"ia_{slug}.") and not f.endswith(".part"):
            found_path = os.path.join(staging_dir, f)
            if found_path != local_path and os.path.exists(found_path):
                # Rename to expected .mp4 path
                os.rename(found_path, local_path)
                return local_path, None

    if result.returncode != 0:
        stderr = result.stderr[-500:] if result.stderr else "Unknown error"
        return None, stderr.strip()

    return None, "Output file not found after download"


def process_downloaded_file(entry, dl_id, local_path, project_dir, reencode_fps):
    """Validate and optionally re-encode a downloaded file. Returns result dict or None on failure."""
    size_mb = get_file_size_mb(local_path)
    if size_mb < 1:
        os.remove(local_path)
        return None, "File too small (< 1MB)"
    if not ffprobe_validate(local_path):
        os.remove(local_path)
        return None, "ffprobe validation failed"

    original_fps = None
    if reencode_fps:
        local_path, original_fps, reencode_err = reencode_to_24fps(local_path)
        if reencode_err:
            log(f"  WARN {dl_id} re-encode failed, keeping original: {reencode_err}")
        elif original_fps and original_fps > TARGET_FPS:
            size_mb = get_file_size_mb(local_path)
            log(f"  RE-ENCODED {dl_id} {original_fps}fps → {TARGET_FPS}fps")
    else:
        original_fps = get_video_fps(local_path)

    # Get duration from ffprobe if not already known
    duration_sec = entry["duration_sec"]
    if duration_sec is None:
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries",
                 "format=duration", "-of", "json", local_path],
                capture_output=True, text=True, timeout=15
            )
            dur = json.loads(probe.stdout).get("format", {}).get("duration")
            duration_sec = round(float(dur), 1) if dur else None
        except Exception:
            pass

    rel_path = os.path.relpath(local_path, project_dir).replace("\\", "/")
    result = {
        "id": dl_id,
        "source": entry["source"],
        "source_url": entry["source_url"],
        "title": entry["title"],
        "duration_sec": duration_sec,
        "score": entry["score"],
        "file_size_mb": round(size_mb, 1),
        "local_path": rel_path,
        "status": "completed",
        "shot_refs": entry["shot_refs"],
        "context": entry["context"],
        "original_fps": original_fps,
        "fps": TARGET_FPS if (reencode_fps and original_fps and original_fps > TARGET_FPS) else original_fps,
    }
    return result, None


def download_ia_worker(entry, dl_id, staging_dir, project_dir, reencode_fps):
    """Worker function for parallel archive.org downloads.
    Returns (dl_id, result_dict).
    """
    local_path, error = download_archive_org(entry["source_url"], staging_dir)

    if local_path and os.path.exists(local_path):
        result, proc_error = process_downloaded_file(
            entry, dl_id, local_path, project_dir, reencode_fps
        )
        if result:
            return dl_id, result
        else:
            error = proc_error

    return dl_id, {
        "id": dl_id,
        "source": entry["source"],
        "source_url": entry["source_url"],
        "title": entry["title"],
        "duration_sec": entry["duration_sec"],
        "score": entry["score"],
        "file_size_mb": None,
        "local_path": None,
        "status": "failed",
        "shot_refs": entry["shot_refs"],
        "context": entry["context"],
        "error": error or "Unknown error",
    }


def run(project_dir, reencode_fps=True, cookies_browser=None, cookies_file=None):
    staging_dir = os.path.join(project_dir, "assets", "staging")
    os.makedirs(staging_dir, exist_ok=True)
    manifest_path = os.path.join(project_dir, "visuals", "download_manifest.json")

    # Cookie auth: file takes precedence over browser extraction
    if cookies_file:
        log(f"  [Using cookies file: {cookies_file}]")
        cookies_browser = None  # file overrides browser
    elif cookies_browser is False:
        cookies_browser = None
        log("  [Cookies disabled — downloading without authentication]")
    elif cookies_browser is None:
        cookies_browser = detect_browser_for_cookies()
        if cookies_browser:
            log(f"  [Using cookies from {cookies_browser} browser]")
        else:
            log("  [No browser cookies found — downloading without authentication]")
    else:
        log(f"  [Using cookies from {cookies_browser} browser]")

    # Load existing manifest for resume
    existing = {}
    if os.path.exists(manifest_path):
        prev = load_json(manifest_path)
        for v in prev.get("videos", []):
            if v.get("status") == "completed":
                lp = v.get("local_path")
                if lp:
                    full = os.path.join(project_dir, lp)
                    if os.path.exists(full):
                        existing[v["source_url"]] = v

    entries = collect_urls(project_dir)
    results = []
    total_size_mb = sum(v.get("file_size_mb", 0) for v in existing.values())
    dl_index = 0
    yt_batch_count = 0
    yt_bot_detected = False

    # Separate YouTube and archive.org entries
    yt_entries = []
    ia_entries = []
    for entry in entries:
        dl_index += 1
        dl_id = f"DL-{dl_index:03d}"
        entry["_dl_id"] = dl_id

        if entry["source_url"] in existing:
            prev = existing[entry["source_url"]]
            prev["id"] = dl_id
            results.append(prev)
            continue

        if total_size_mb >= VOLUME_CAP_MB:
            results.append({
                "id": dl_id, **{k: v for k, v in entry.items() if k != "_dl_id"},
                "file_size_mb": None, "local_path": None,
                "status": "skipped", "error": "Volume cap reached",
            })
            continue

        if entry["source"] == "youtube":
            yt_entries.append((dl_id, entry))
        elif entry["source"] == "internet_archive":
            ia_entries.append((dl_id, entry))

    # Start archive.org downloads in background (independent of YouTube)
    ia_results = {}
    ia_thread = None
    if ia_entries:
        log(f"\n  --- Archive.org downloads ({len(ia_entries)} videos, {IA_PARALLEL_WORKERS} parallel) ---")

        def _run_ia_downloads():
            with ThreadPoolExecutor(max_workers=IA_PARALLEL_WORKERS) as executor:
                futures = {}
                for dl_id, entry in ia_entries:
                    future = executor.submit(
                        download_ia_worker,
                        entry, dl_id, staging_dir, project_dir, reencode_fps
                    )
                    futures[future] = (dl_id, entry)
                for future in as_completed(futures):
                    dl_id, result = future.result()
                    ia_results[dl_id] = result
                    if result["status"] == "completed":
                        log(f"  OK  {dl_id} [internet_archive] {result['title'][:60]} ({result['file_size_mb']:.0f}MB)")
                    else:
                        log(f"  FAIL {dl_id} [internet_archive] {result['title'][:60]}: {result.get('error', '?')}")

        ia_thread = threading.Thread(target=_run_ia_downloads, daemon=True)
        ia_thread.start()

    # YouTube downloads (sequential with rate limiting) — runs while IA downloads proceed
    if yt_entries:
        log(f"\n  --- YouTube downloads ({len(yt_entries)} videos) ---")

    for dl_id, entry in yt_entries:
        url = entry["source_url"]

        if yt_bot_detected:
            results.append({
                "id": dl_id,
                "source": entry["source"],
                "source_url": url,
                "title": entry["title"],
                "duration_sec": entry["duration_sec"],
                "score": entry["score"],
                "file_size_mb": None,
                "local_path": None,
                "status": "failed",
                "shot_refs": entry["shot_refs"],
                "context": entry["context"],
                "error": "Skipped — YouTube bot detection triggered on earlier download",
            })
            continue

        yt_batch_count += 1
        if yt_batch_count > YOUTUBE_BATCH_SIZE:
            yt_batch_count = 1
            log(f"  [Pausing {YOUTUBE_BATCH_PAUSE}s between YouTube batches]")
            time.sleep(YOUTUBE_BATCH_PAUSE)

        local_path, error = download_youtube(url, staging_dir, score=entry["score"],
                                              cookies_browser=cookies_browser,
                                              cookies_file=cookies_file)

        if local_path and os.path.exists(local_path):
            result, proc_error = process_downloaded_file(
                entry, dl_id, local_path, project_dir, reencode_fps
            )
            if result:
                total_size_mb += result["file_size_mb"]
                results.append(result)
                log(f"  OK  {dl_id} [youtube] {entry['title'][:60]} ({result['file_size_mb']:.0f}MB)")
                continue
            else:
                error = proc_error

        results.append({
            "id": dl_id,
            "source": entry["source"],
            "source_url": url,
            "title": entry["title"],
            "duration_sec": entry["duration_sec"],
            "score": entry["score"],
            "file_size_mb": None,
            "local_path": None,
            "status": "failed",
            "shot_refs": entry["shot_refs"],
            "context": entry["context"],
            "error": error or "Unknown error",
        })
        log(f"  FAIL {dl_id} [youtube] {entry['title'][:60]}: {error}")

        if is_bot_detected(error):
            log("  [YouTube bot detection — skipping remaining YouTube downloads]")
            yt_bot_detected = True

    # Wait for archive.org downloads to finish
    if ia_thread:
        ia_thread.join()
        for dl_id, entry in ia_entries:
            if dl_id in ia_results:
                if ia_results[dl_id]["status"] == "completed":
                    total_size_mb += ia_results[dl_id]["file_size_mb"]
                results.append(ia_results[dl_id])

    # Sort results by DL-ID to maintain order
    results.sort(key=lambda r: r["id"])

    # Build manifest
    project_name = Path(project_dir).name
    # Strip leading number + dot
    match = re.match(r"\d+\.\s*(.*)", project_name)
    project_name = match.group(1) if match else project_name

    manifest = {
        "project": project_name,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_size_mb": round(total_size_mb, 1),
        "videos": results,
    }

    save_json(manifest_path, manifest)

    # Summary
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    yt_count = sum(1 for r in results if r["source"] == "youtube")
    ia_count = sum(1 for r in results if r["source"] == "internet_archive")

    log(f"\n{'='*60}")
    log(f"  Download Summary")
    log(f"{'='*60}")
    log(f"  Total: {len(results)} videos ({yt_count} YouTube, {ia_count} archive.org)")
    log(f"  Completed: {completed} ({total_size_mb:.0f} MB)")
    log(f"  Failed: {failed}")
    log(f"  Skipped: {skipped}")
    log(f"  Manifest: {manifest_path}")
    log(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Path to project directory")
    parser.add_argument("--no-reencode", action="store_true",
                        help="Skip 24fps re-encoding (default: re-encode videos above 24fps)")
    parser.add_argument("--cookies", default=None,
                        help="Path to a Netscape-format cookies.txt file for YouTube authentication")
    parser.add_argument("--cookies-from-browser", default=None,
                        help="Browser to extract cookies from (chrome, firefox, edge, brave, opera). "
                             "Default: auto-detect. Use --no-cookies to disable.")
    parser.add_argument("--no-cookies", action="store_true",
                        help="Disable browser cookie extraction (download without authentication)")
    args = parser.parse_args()

    if not os.path.isdir(args.project):
        log(f"Error: project directory not found: {args.project}")
        sys.exit(1)

    if args.no_cookies:
        cookies = False  # False = explicitly disabled, None = auto-detect
    else:
        cookies = args.cookies_from_browser  # None = auto-detect, or explicit browser name

    run(args.project, reencode_fps=not args.no_reencode, cookies_browser=cookies,
        cookies_file=args.cookies)
