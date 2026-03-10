"""Helper: save merged subagent analysis results to a JSON file.

Usage:
    python save_analysis.py <output_dir> '<json_array_string>'

The subagent analysis results (a JSON array) are passed as the second argument.
This avoids embedding large JSON in a -c string.
"""
import sys
import json
import os

output_dir = sys.argv[1]
analysis_json = sys.argv[2]

results = json.loads(analysis_json)
out_path = os.path.join(output_dir, "analysis_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"Saved {len(results)} frame analyses to {out_path}")
