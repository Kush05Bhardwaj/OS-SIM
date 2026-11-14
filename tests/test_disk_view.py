"""
Smoke tests for Disk Scheduling Dashboard View.
"""

import pytest
import plotly.graph_objects as go
from algorithms.disk.schedulers import FCFSDiskScheduler, SSTFDiskScheduler
from dashboard.disk_view import build_trajectory_figure, DISK_PRESETS


def test_disk_presets():
    assert "Standard Textbook Sequence" in DISK_PRESETS
    assert "Localized Sector Clusters" in DISK_PRESETS
    cfg = DISK_PRESETS["Standard Textbook Sequence"]
    assert cfg["initial_head"] == 53
    assert len(cfg["requests"]) == 8


def test_build_trajectory_figure():
    scheduler1 = FCFSDiskScheduler()
    res1 = scheduler1.schedule([10, 20, 30], initial_head=0)
    scheduler2 = SSTFDiskScheduler()
    res2 = scheduler2.schedule([10, 20, 30], initial_head=0)

    fig = build_trajectory_figure([res1, res2], cylinder_max=199)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
