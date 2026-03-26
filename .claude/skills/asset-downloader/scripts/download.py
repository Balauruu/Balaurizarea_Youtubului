#!/usr/bin/env python3
"""Download video assets from YouTube and archive.org for a documentary project."""

import sys
import os
import json
import subprocess
import argparse
import time
import re
from datetime import datetime, timezone
from pathlib import Path

VOLUME_CAP_MB = 200 * 1024  # 200 GB
YT_DLP = "yt-dlp"
YOUTUBE_BATCH_SIZE = 10
YOUTUBE_BATCH_PAUSE = 15  # seconds between batches


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


def download_youtube(url, staging_dir):
    """Download a YouTube video. Returns (local_path, error)."""
    # Extract video ID for filename
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    vid_id = match.group(1) if match else "unknown"
    output_template = os.path.join(staging_dir, f"yt_{vid_id}.%(ext)s")

    cmd = [
        YT_DLP,
        "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "--merge-output-format", "mp4",
        "--restrict-filenames",
        "--sleep-interval", "3",
        "--max-sleep-interval", "8",
        "--sleep-requests", "1.5",
        "--no-overwrites",
        "-o", output_template,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Find the output file
    expected = os.path.join(staging_dir, f"yt_{vid_id}.mp4")
    if os.path.exists(expected):
        return expected, None

    # Check for error
    if result.returncode != 0:
        stderr = result.stderr[-500:] if result.stderr else "Unknown error"
        if "429" in stderr or "Too Many Requests" in stderr:
            return None, "HTTP 429 — rate limited"
        return None, stderr.strip()

    return None, "Output file not found after download"


def download_archive_org(url, staging_dir):
    """Download a video from archive.org. Returns (local_path, error)."""
    import requests

    # Extract item ID from URL
    match = re.search(r"archive\.org/details/([^/?#]+)", url)
    if not match:
        return None, f"Cannot parse archive.org item ID from: {url}"
    item_id = match.group(1)

    # Fetch item metadata
    try:
        meta_url = f"https://archive.org/metadata/{item_id}"
        resp = requests.get(meta_url, timeout=30)
        resp.raise_for_status()
        metadata = resp.json()
    except Exception as e:
        return None, f"Metadata fetch failed: {e}"

    # Find best video file: smallest MP4 with height <= 720
    files = metadata.get("files", [])
    video_files = []
    for f in files:
        name = f.get("name", "")
        fmt = f.get("format", "")
        if name.lower().endswith(".mp4") or "MPEG4" in fmt or "h.264" in fmt.lower():
            size = int(f.get("size", 0))
            height = int(f.get("height", 0)) if f.get("height") else 9999
            video_files.append({"name": name, "size": size, "height": height})

    if not video_files:
        return None, "No MP4/MPEG4 files found in item"

    # Filter to <= 720p, then pick smallest
    candidates = [v for v in video_files if v["height"] <= 720]
    if not candidates:
        # No resolution metadata — pick smallest MP4
        candidates = video_files
    candidates.sort(key=lambda v: v["size"])
    best = candidates[0]

    # Download
    download_url = f"https://archive.org/download/{item_id}/{best['name']}"
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", item_id)[:60]
    local_path = os.path.join(staging_dir, f"ia_{slug}.mp4")

    if os.path.exists(local_path):
        return local_path, None

    try:
        resp = requests.get(download_url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(local_path, "wb") as out:
            for chunk in resp.iter_content(chunk_size=8192):
                out.write(chunk)
    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        return None, f"Download failed: {e}"

    return local_path, None


def run(project_dir):
    staging_dir = os.path.join(project_dir, "assets", "staging")
    os.makedirs(staging_dir, exist_ok=True)
    manifest_path = os.path.join(project_dir, "visuals", "download_manifest.json")

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

    for entry in entries:
        dl_index += 1
        dl_id = f"DL-{dl_index:03d}"
        url = entry["source_url"]

        # Skip if already completed
        if url in existing:
            prev = existing[url]
            prev["id"] = dl_id
            results.append(prev)
            continue

        # Check volume cap
        if total_size_mb >= VOLUME_CAP_MB:
            results.append({
                "id": dl_id, **entry,
                "file_size_mb": None, "local_path": None,
                "status": "skipped", "error": "Volume cap reached",
            })
            continue

        # Download based on source
        if entry["source"] == "youtube":
            yt_batch_count += 1
            if yt_batch_count > YOUTUBE_BATCH_SIZE:
                yt_batch_count = 1
                print(f"  [Pausing {YOUTUBE_BATCH_PAUSE}s between YouTube batches]")
                time.sleep(YOUTUBE_BATCH_PAUSE)

            local_path, error = download_youtube(url, staging_dir)
        elif entry["source"] == "internet_archive":
            time.sleep(2)  # archive.org rate limit
            local_path, error = download_archive_org(url, staging_dir)
        else:
            local_path, error = None, f"Unknown source: {entry['source']}"

        if local_path and os.path.exists(local_path):
            # Validate
            size_mb = get_file_size_mb(local_path)
            if size_mb < 1:
                os.remove(local_path)
                local_path, error = None, "File too small (< 1MB)"
            elif not ffprobe_validate(local_path):
                os.remove(local_path)
                local_path, error = None, "ffprobe validation failed"
            else:
                total_size_mb += size_mb
                rel_path = os.path.relpath(local_path, project_dir).replace("\\", "/")
                # Get duration from ffprobe
                if entry["duration_sec"] is None:
                    try:
                        probe = subprocess.run(
                            ["ffprobe", "-v", "quiet", "-show_entries",
                             "format=duration", "-of", "json", local_path],
                            capture_output=True, text=True, timeout=15
                        )
                        dur = json.loads(probe.stdout).get("format", {}).get("duration")
                        entry["duration_sec"] = round(float(dur), 1) if dur else None
                    except Exception:
                        pass

                results.append({
                    "id": dl_id,
                    "source": entry["source"],
                    "source_url": url,
                    "title": entry["title"],
                    "duration_sec": entry["duration_sec"],
                    "score": entry["score"],
                    "file_size_mb": round(size_mb, 1),
                    "local_path": rel_path,
                    "status": "completed",
                    "shot_refs": entry["shot_refs"],
                    "context": entry["context"],
                })
                print(f"  OK  {dl_id} [{entry['source']}] {entry['title'][:60]} ({size_mb:.0f}MB)")
                continue

        # Failed
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
        print(f"  FAIL {dl_id} [{entry['source']}] {entry['title'][:60]}: {error}")

        # Stop on YouTube 429
        if entry["source"] == "youtube" and error and "429" in error:
            print("  [YouTube rate limit hit — stopping YouTube downloads]")
            # Mark remaining YouTube entries as failed
            for remaining in entries[dl_index:]:
                if remaining["source"] == "youtube":
                    dl_index += 1
                    results.append({
                        "id": f"DL-{dl_index:03d}",
                        **remaining,
                        "file_size_mb": None, "local_path": None,
                        "status": "failed",
                        "error": "Skipped due to YouTube 429 rate limit",
                    })

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

    print(f"\n{'='*60}")
    print(f"  Download Summary")
    print(f"{'='*60}")
    print(f"  Total: {len(results)} videos ({yt_count} YouTube, {ia_count} archive.org)")
    print(f"  Completed: {completed} ({total_size_mb:.0f} MB)")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Manifest: {manifest_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Path to project directory")
    args = parser.parse_args()

    if not os.path.isdir(args.project):
        print(f"Error: project directory not found: {args.project}", file=sys.stderr)
        sys.exit(1)

    run(args.project)
