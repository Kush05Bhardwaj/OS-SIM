"""
Smoke and logic tests for the CPU Dashboard View.
"""

import pytest
import pandas as pd
from dashboard.cpu_view import PRESETS
from algorithms.cpu.base import Process
from algorithms.cpu.schedulers import FCFSScheduler


def test_presets_structure():
    assert "Standard Mix" in PRESETS
    assert "Convoy Effect (FCFS Bottleneck)" in PRESETS
    assert "High Concurrency" in PRESETS

    for name, procs in PRESETS.items():
        assert len(procs) >= 2
        for p in procs:
            assert "pid" in p
            assert "arrival_time" in p
            assert "burst_time" in p
            assert p["burst_time"] > 0
            assert p["arrival_time"] >= 0


def test_preset_conversion_and_execution():
    standard = PRESETS["Standard Mix"]
    procs = [
        Process(
            pid=p["pid"],
            arrival_time=p["arrival_time"],
            burst_time=p["burst_time"],
            priority=p.get("priority", 0),
        )
        for p in standard
    ]
    scheduler = FCFSScheduler()
    res = scheduler.schedule(procs)

    assert res.total_time == sum(p["burst_time"] for p in standard)
    assert len(res.processes) == len(standard)
