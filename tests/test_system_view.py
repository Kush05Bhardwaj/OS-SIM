"""
Smoke tests for Live System Monitoring View.
"""

import pytest
import plotly.graph_objects as go
from dashboard.system_view import create_gauge


def test_create_gauge():
    fig = create_gauge("CPU Load", 55.4, max_val=100.0)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    indicator = fig.data[0]
    assert indicator.value == 55.4
