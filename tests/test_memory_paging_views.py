"""
Smoke tests for Memory and Paging Dashboard Views.
"""

import pytest
import plotly.graph_objects as go
from algorithms.memory.base import MemoryPool
from dashboard.memory_view import render_memory_map_chart
from dashboard.paging_view import PAGING_PRESETS


def test_memory_map_chart_generation():
    pool = MemoryPool(total_size=500)
    pool.allocate("P1", 200)
    pool.allocate("P2", 100)

    fig = render_memory_map_chart(pool)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3  # P1, P2, and 1 remaining free block


def test_paging_presets():
    assert "Standard Textbook Sequence" in PAGING_PRESETS
    assert "Belady's Anomaly Demo (FIFO)" in PAGING_PRESETS
    assert len(PAGING_PRESETS["Standard Textbook Sequence"]) == 20
