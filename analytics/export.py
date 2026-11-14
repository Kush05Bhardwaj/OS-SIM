"""
Data Export & Reporting Utilities
Converts simulation benchmarks and telemetry logs into downloadable CSV and JSON formats.
"""

import json
from typing import List, Dict, Any
import pandas as pd


def export_simulation_runs_to_csv(runs: List[Dict[str, Any]]) -> str:
    """Exports simulation runs into flat CSV string format."""
    if not runs:
        return ""

    flattened = []
    for r in runs:
        entry = {
            "Run ID": r["run_id"],
            "Category": r["category"],
            "Algorithm": r["algorithm_name"],
            "Created At": r["created_at"],
        }
        # Flatten metrics
        metrics = r.get("metrics", {})
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                entry[f"Metric_{k}"] = v
        flattened.append(entry)

    df = pd.DataFrame(flattened)
    return df.to_csv(index=False)


def export_simulation_runs_to_json(runs: List[Dict[str, Any]]) -> str:
    """Exports simulation runs into pretty-printed JSON string format."""
    return json.dumps(runs, indent=2)


def export_telemetry_to_csv(snapshots: List[Dict[str, Any]]) -> str:
    """Exports telemetry snapshot records into flat CSV format."""
    if not snapshots:
        return ""
    df = pd.DataFrame(snapshots)
    return df.to_csv(index=False)


def export_telemetry_to_json(snapshots: List[Dict[str, Any]]) -> str:
    """Exports telemetry snapshot records into JSON format."""
    return json.dumps(snapshots, indent=2)
