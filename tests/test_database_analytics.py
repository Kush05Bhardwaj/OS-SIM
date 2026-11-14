"""
Unit tests for SQLite database manager and analytics export utilities.
"""

import json
import pytest
from database.db_manager import DatabaseManager
from analytics.export import (
    export_simulation_runs_to_csv,
    export_simulation_runs_to_json,
    export_telemetry_to_csv,
    export_telemetry_to_json,
)


@pytest.fixture
def mem_db():
    return DatabaseManager(db_path=":memory:")


def test_save_and_get_simulation_run(mem_db):
    run_id = mem_db.save_simulation_run(
        category="CPU Scheduling",
        algorithm_name="FCFS",
        input_params={"processes": 3},
        metrics={"avg_wt": 2.5, "avg_tat": 5.5},
    )
    assert run_id.startswith("RUN-")

    runs = mem_db.get_simulation_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == run_id
    assert runs[0]["category"] == "CPU Scheduling"
    assert runs[0]["algorithm_name"] == "FCFS"
    assert runs[0]["metrics"]["avg_wt"] == 2.5


def test_save_and_get_telemetry_snapshot(mem_db):
    snap_id = mem_db.save_telemetry_snapshot(
        {
            "timestamp": "2026-11-14T10:00:00Z",
            "cpu": {"usage_percent": 35.5},
            "memory": {"usage_percent": 60.0, "used_mb": 4096.0},
            "swap": {"usage_percent": 10.0},
        }
    )
    assert snap_id > 0

    snaps = mem_db.get_telemetry_snapshots()
    assert len(snaps) == 1
    assert snaps[0]["cpu_percent"] == 35.5
    assert snaps[0]["memory_percent"] == 60.0


def test_clear_all_database(mem_db):
    mem_db.save_simulation_run("CPU", "SJF", {}, {})
    mem_db.save_telemetry_snapshot({"cpu": {"usage_percent": 10}})
    assert len(mem_db.get_simulation_runs()) == 1
    assert len(mem_db.get_telemetry_snapshots()) == 1

    mem_db.clear_all()
    assert len(mem_db.get_simulation_runs()) == 0
    assert len(mem_db.get_telemetry_snapshots()) == 0


def test_exports():
    runs = [
        {
            "run_id": "RUN-01",
            "category": "CPU",
            "algorithm_name": "FCFS",
            "input_params": {},
            "metrics": {"avg_wt": 2.0},
            "created_at": "2026-11-14T10:00:00Z",
        }
    ]
    csv_str = export_simulation_runs_to_csv(runs)
    assert "RUN-01" in csv_str
    assert "FCFS" in csv_str

    json_str = export_simulation_runs_to_json(runs)
    parsed = json.loads(json_str)
    assert len(parsed) == 1
    assert parsed[0]["run_id"] == "RUN-01"

    snaps = [{"timestamp": "2026-11-14T10:00:00Z", "cpu_percent": 25.0}]
    t_csv = export_telemetry_to_csv(snaps)
    assert "25.0" in t_csv

    t_json = export_telemetry_to_json(snaps)
    assert "25.0" in t_json
