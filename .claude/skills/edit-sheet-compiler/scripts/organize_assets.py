#!/usr/bin/env python3
"""Copy and rename assets into a flat project directory per an instruction file."""

import sys
import os
import json
import shutil
import argparse
from pathlib import Path


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def safe_copy(src, dst):
    """Copy file, creating parent dirs. Skip if dst already exists."""
    if os.path.exists(dst):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


def run(instructions_path):
    instructions = load_json(instructions_path)
    project_dir = instructions["project_dir"]
    assets_dir = os.path.join(project_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    results = {"copied": [], "failed": [], "global_copied": []}

    for item in instructions.get("copies", []):
        src = item["src"]
        project_name = item["project_name"]
        dst = os.path.join(assets_dir, project_name)

        if not os.path.exists(src):
            results["failed"].append({"src": src, "dst": project_name, "error": "Source not found"})
            continue

        try:
            if safe_copy(src, dst):
                results["copied"].append({"src": src, "dst": project_name})
            else:
                results["copied"].append({"src": src, "dst": project_name, "note": "already exists"})
        except Exception as e:
            results["failed"].append({"src": src, "dst": project_name, "error": str(e)})

    for item in instructions.get("global_copies", []):
        src = item["src"]
        global_dst = item["global_path"]
        project_name = item.get("project_name")

        if not os.path.exists(src):
            results["failed"].append({"src": src, "dst": global_dst, "error": "Source not found"})
            continue

        try:
            # Copy to global dir
            if safe_copy(src, global_dst):
                results["global_copied"].append({"src": src, "dst": global_dst})

            # Also copy to project dir if project_name provided
            if project_name:
                project_dst = os.path.join(assets_dir, project_name)
                safe_copy(src, project_dst)
        except Exception as e:
            results["failed"].append({"src": src, "dst": global_dst, "error": str(e)})

    print(json.dumps({
        "success": len(results["failed"]) == 0,
        "project_copies": len(results["copied"]),
        "global_copies": len(results["global_copied"]),
        "failures": len(results["failed"]),
        "details": results,
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--instructions", required=True, help="Path to instructions JSON")
    args = parser.parse_args()
    run(args.instructions)
