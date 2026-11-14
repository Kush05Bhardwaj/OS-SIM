"""
Unit tests for CPU Gantt chart generator and comparative metrics evaluation.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from algorithms.cpu.base import Process
from algorithms.cpu.schedulers import FCFSScheduler
from algorithms.cpu.metrics import extract_process_metrics_dataframe, compare_all_schedulers
from dashboard.components.gantt import build_gantt_chart, build_comparison_barchart


@pytest.fixture
def sample_processes():
    return [
        Process("P1", arrival_time=0, burst_time=4, priority=2),
        Process("P2", arrival_time=1, burst_time=3, priority=1),
        Process("P3", arrival_time=2, burst_time=1, priority=3),
    ]


def test_extract_process_metrics_dataframe(sample_processes):
    scheduler = FCFSScheduler()
    res = scheduler.schedule(sample_processes)

    df = extract_process_metrics_dataframe(res)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "Process ID" in df.columns
    assert "Turnaround Time (TAT)" in df.columns
    assert "Waiting Time (WT)" in df.columns
    assert "Response Time (RT)" in df.columns


def test_compare_all_schedulers(sample_processes):
    df = compare_all_schedulers(sample_processes, rr_quantum=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 7  # FCFS, SJF, SRTF, RR, Priority (Non-P & P), MLFQ
    assert "Algorithm" in df.columns
    assert "Avg Waiting Time" in df.columns
    assert "CPU Utilization (%)" in df.columns
    assert "Throughput (proc/unit)" in df.columns


def test_build_gantt_chart(sample_processes):
    scheduler = FCFSScheduler()
    res = scheduler.schedule(sample_processes)

    fig = build_gantt_chart(res)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3  # 3 slices

    # Empty result test
    empty_fig = build_gantt_chart(None)
    assert isinstance(empty_fig, go.Figure)


def test_build_comparison_barchart(sample_processes):
    comp_df = compare_all_schedulers(sample_processes)
    fig = build_comparison_barchart(comp_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # Avg WT and Avg TAT traces

    empty_fig = build_comparison_barchart(pd.DataFrame())
    assert isinstance(empty_fig, go.Figure)
