"""
Interactive Disk Scheduling & Head Trajectory Visualizer
Renders 2D seek trajectory curves, comparative seek charts, and step breakdowns.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from algorithms.disk.schedulers import (
    FCFSDiskScheduler,
    SSTFDiskScheduler,
    SCANDiskScheduler,
    CSCANDiskScheduler,
    LOOKDiskScheduler,
    CLOOKDiskScheduler,
)
from algorithms.disk.base import DiskScheduleResult
from core.logger import activity_logger

DISK_PRESETS: Dict[str, Dict[str, Any]] = {
    "Standard Textbook Sequence": {
        "requests": [98, 183, 37, 122, 14, 124, 65, 67],
        "initial_head": 53,
        "max_cylinder": 199,
        "direction": "RIGHT",
    },
    "Localized Sector Clusters": {
        "requests": [10, 12, 15, 11, 14, 180, 182, 185],
        "initial_head": 100,
        "max_cylinder": 199,
        "direction": "RIGHT",
    },
    "Worst-Case Alternating Edges": {
        "requests": [0, 199, 5, 195, 10, 190, 15, 185],
        "initial_head": 100,
        "max_cylinder": 199,
        "direction": "RIGHT",
    },
}

ALGO_COLORS = {
    "FCFS": "#2563EB",
    "SSTF": "#10B981",
    "SCAN": "#F59E0B",
    "C-SCAN": "#EF4444",
    "LOOK": "#8B5CF6",
    "C-LOOK": "#06B6D4",
}


def build_trajectory_figure(results: List[DiskScheduleResult], cylinder_max: int) -> go.Figure:
    """Renders 2D seek curve plotting Sequence Step vs. Cylinder Number."""
    fig = go.Figure()

    for res in results:
        algo_short = res.algorithm_name.split()[0].replace("(", "").replace(")", "")
        color = ALGO_COLORS.get(algo_short, "#2563EB")
        steps = list(range(len(res.seek_sequence)))

        fig.add_trace(
            go.Scatter(
                x=steps,
                y=res.seek_sequence,
                mode="lines+markers",
                name=f"{res.algorithm_name} ({res.total_head_movement} cyl)",
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
                hovertemplate="<b>Step:</b> %{x}<br><b>Cylinder:</b> %{y}<extra></extra>",
            )
        )

    fig.update_layout(
        title="<b>Disk Head Trajectory Curve (Step vs. Cylinder)</b>",
        xaxis=dict(title="Traversal Sequence Step", dtick=1, showgrid=True, gridcolor="#1e293b"),
        yaxis=dict(title="Cylinder Position", range=[0, cylinder_max + 5], showgrid=True, gridcolor="#1e293b"),
        height=380,
        margin=dict(l=30, r=30, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
    )
    return fig


def render_disk_view():
    """Renders the disk head visualizer dashboard."""
    st.title("Disk Head Scheduling & Trajectory")
    st.caption(
        "Evaluate seek arm efficiency, analyze 2D traversal curves, and compare FCFS, "
        "SSTF, SCAN, C-SCAN, LOOK, and C-LOOK across customizable disk geometries."
    )

    c1, c2, c3, c4 = st.columns([1.2, 1, 0.8, 0.8])
    with c1:
        preset_choice = st.selectbox("Preset Scenario", list(DISK_PRESETS.keys()) + ["Custom"])
    with c2:
        algo_choice = st.selectbox(
            "Scheduling Mode",
            [
                "Compare All 6 Schedulers",
                "First-Come, First-Served (FCFS)",
                "Shortest Seek Time First (SSTF)",
                "SCAN (Elevator)",
                "Circular SCAN (C-SCAN)",
                "LOOK",
                "C-LOOK",
            ],
            index=0,
        )
    with c3:
        direction_choice = st.selectbox("Head Direction", ["RIGHT", "LEFT"], index=0)
    with c4:
        cylinder_max = st.number_input("Max Cylinders", min_value=99, max_value=9999, value=199, step=100)

    # Preset defaults
    if preset_choice in DISK_PRESETS:
        preset_cfg = DISK_PRESETS[preset_choice]
        default_reqs = ", ".join(map(str, preset_cfg["requests"]))
        default_head = preset_cfg["initial_head"]
    else:
        default_reqs = "98, 183, 37, 122, 14, 124, 65, 67"
        default_head = 53

    col_reqs, col_head = st.columns([3, 1])
    with col_reqs:
        req_str_input = st.text_input("Cylinder Requests (comma-separated)", value=default_reqs)
    with col_head:
        initial_head = st.number_input("Initial Head Position", min_value=0, max_value=int(cylinder_max), value=int(default_head))

    # Parse requests
    tokens = req_str_input.replace(",", " ").split()
    requests: List[int] = []
    for t in tokens:
        try:
            val = int(t)
            if 0 <= val <= cylinder_max:
                requests.append(val)
        except ValueError:
            continue

    if not requests:
        st.warning("Please provide at least one valid cylinder request within disk bounds.")
        return

    # Schedulers
    schedulers_dict = {
        "FCFS": FCFSDiskScheduler(),
        "SSTF": SSTFDiskScheduler(),
        "SCAN": SCANDiskScheduler(),
        "C-SCAN": CSCANDiskScheduler(),
        "LOOK": LOOKDiskScheduler(),
        "C-LOOK": CLOOKDiskScheduler(),
    }

    results: List[DiskScheduleResult] = []

    if algo_choice == "Compare All 6 Schedulers":
        for s in schedulers_dict.values():
            results.append(s.schedule(requests, initial_head=initial_head, direction=direction_choice, cylinder_max=cylinder_max))
    else:
        for name, s in schedulers_dict.items():
            if name in algo_choice:
                results.append(s.schedule(requests, initial_head=initial_head, direction=direction_choice, cylinder_max=cylinder_max))
                break

    activity_logger.success("Disk", f"Simulated {len(requests)} cylinders with {algo_choice}")

    # Metrics Row
    if len(results) == 1:
        res = results[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Head Movement", f"{res.total_head_movement} cyl")
        m2.metric("Avg Seek Distance", f"{res.average_seek_distance} cyl/req")
        m3.metric("Total Requests Serviced", len(requests))
        m4.metric("Start Cylinder", initial_head)
    else:
        best_res = min(results, key=lambda r: r.total_head_movement)
        st.success(
            f" Optimal Disk Trajectory: **{best_res.algorithm_name}** with "
            f"**{best_res.total_head_movement} cylinders** total head movement "
            f"({best_res.average_seek_distance} cyl/request)."
        )

    # Trajectory Plot
    st.divider()
    traj_fig = build_trajectory_figure(results, cylinder_max)
    st.plotly_chart(traj_fig, use_container_width=True)

    # Comparison Leaderboard & Bar Chart (if multi mode)
    if len(results) > 1:
        st.subheader(" Disk Seek Comparison Leaderboard")
        comp_records = []
        for r in results:
            comp_records.append(
                {
                    "Algorithm": r.algorithm_name,
                    "Total Head Movement (Cylinders)": r.total_head_movement,
                    "Average Seek Distance (Cyl/Req)": r.average_seek_distance,
                    "Cylinders Traversed Relative to Best": f"+{r.total_head_movement - best_res.total_head_movement}",
                }
            )

        comp_df = pd.DataFrame(comp_records).sort_values(by="Total Head Movement (Cylinders)").reset_index(drop=True)

        col_tbl, col_bar = st.columns([1.5, 1.5])
        with col_tbl:
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

        with col_bar:
            bar_fig = go.Figure(
                go.Bar(
                    x=comp_df["Algorithm"],
                    y=comp_df["Total Head Movement (Cylinders)"],
                    marker_color=["#10B981" if idx == 0 else "#2563EB" for idx in range(len(comp_df))],
                    text=comp_df["Total Head Movement (Cylinders)"],
                    textposition="auto",
                )
            )
            bar_fig.update_layout(
                title="<b>Total Seek Distance (Lower is Better)</b>",
                xaxis=dict(tickangle=-25),
                yaxis=dict(title="Cylinders"),
                height=300,
                margin=dict(l=20, r=20, t=40, b=80),
                plot_bgcolor="#0f172a",
            )
            st.plotly_chart(bar_fig, use_container_width=True)

    # Traversal Order Trace Table
    st.divider()
    st.subheader(" Traversal Step-by-Step Trace")
    trace_cols = st.columns(len(results))
    for idx, r in enumerate(results):
        with trace_cols[idx % len(trace_cols)]:
            st.markdown(f"**{r.algorithm_name.split()[0]}** (`{r.total_head_movement} cyl`)")
            st.caption("  ".join(map(str, r.seek_sequence)))
