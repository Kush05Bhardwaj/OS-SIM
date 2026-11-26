"""
Plotly Gantt Chart & Comparative Metrics Visualizer
"""

from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import pandas as pd

from algorithms.cpu.base import ScheduleResult, TimelineSlice

# Professional color palette for CPU process blocks
PALETTE = [
    "#2563EB",  # Blue
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#EF4444",  # Red
    "#8B5CF6",  # Violet
    "#EC4899",  # Pink
    "#06B6D4",  # Cyan
    "#84CC16",  # Lime
    "#6366F1",  # Indigo
    "#14B8A6",  # Teal
]


def build_gantt_chart(result: ScheduleResult) -> go.Figure:
    """
    Renders an interactive Plotly horizontal Gantt chart from simulation timeline slices.
    """
    fig = go.Figure()

    if not result or not result.timeline:
        fig.add_annotation(
            text="No simulation trace available. Configure processes to run.",
            showarrow=False,
            font=dict(size=14, color="#94a3b8"),
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=200,
        )
        return fig

    # Assign distinct colors to distinct PIDs
    unique_pids = [p.pid for p in sorted(result.processes, key=lambda x: x.pid)]
    color_map: Dict[str, str] = {}
    for idx, pid in enumerate(unique_pids):
        color_map[pid] = PALETTE[idx % len(PALETTE)]
    color_map["IDLE"] = "#334155"

    # Add each slice as a horizontal bar
    # Tracking legend items so each PID appears once in the legend
    seen_in_legend = set()

    for s in result.timeline:
        is_idle = s.pid == "IDLE" or s.state == "IDLE"
        color = color_map.get(s.pid, "#64748b")
        show_legend = s.pid not in seen_in_legend and not is_idle
        if show_legend:
            seen_in_legend.add(s.pid)

        fig.add_trace(
            go.Bar(
                name=s.pid if not is_idle else "CPU Idle",
                y=["CPU Execution"],
                x=[s.duration],
                base=[s.start_time],
                orientation="h",
                marker=dict(
                    color=color,
                    line=dict(color="#e2e8f0" if not is_idle else "#64748b", width=1.5),
                ),
                text=f"<b>{s.pid}</b>" if not is_idle else "IDLE",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="#f8fafc" if not is_idle else "#cbd5e1", size=12),
                customdata=[[s.pid, s.end_time, s.duration]],
                hovertemplate=(
                    "<b>Process:</b> %{customdata[0]}<br>"
                    "<b>Window:</b> [%{base}, %{customdata[1]}]<br>"
                    "<b>Duration:</b> %{customdata[2]} time units<extra></extra>"
                ),
                showlegend=show_legend,
            )
        )

    max_time = result.total_time
    tick_step = max(1, max_time // 20)

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=f"<b>CPU Execution Timeline: {result.algorithm_name}</b>",
            font=dict(size=16, color="#e2e8f0"),
        ),
        xaxis=dict(
            title="Simulation Time Units",
            dtick=tick_step,
            range=[0, max(max_time + 1, 10)],
            showgrid=True,
            gridcolor="#1e293b",
            zeroline=True,
            zerolinecolor="#64748b",
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
            showgrid=False,
        ),
        height=240,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
        ),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
    )

    return fig


def build_comparison_barchart(comparison_df: pd.DataFrame) -> go.Figure:
    """
    Renders grouped bar chart comparing Average Waiting Time and Turnaround Time across algorithms.
    """
    fig = go.Figure()

    if comparison_df is None or comparison_df.empty:
        return fig

    fig.add_trace(
        go.Bar(
            name="Avg Waiting Time",
            x=comparison_df["Algorithm"],
            y=comparison_df["Avg Waiting Time"],
            marker_color="#2563EB",
            text=comparison_df["Avg Waiting Time"],
            textposition="auto",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Avg Turnaround Time",
            x=comparison_df["Algorithm"],
            y=comparison_df["Avg Turnaround Time"],
            marker_color="#F59E0B",
            text=comparison_df["Avg Turnaround Time"],
            textposition="auto",
        )
    )

    fig.update_layout(
        barmode="group",
        title=dict(
            text="<b>Multi-Algorithm Efficiency Leaderboard</b>",
            font=dict(size=16, color="#e2e8f0"),
        ),
        xaxis=dict(
            title="Algorithm",
            tickangle=-25,
            showgrid=False,
        ),
        yaxis=dict(
            title="Time Units (Lower is Better)",
            showgrid=True,
            gridcolor="#1e293b",
        ),
        height=420,
        margin=dict(l=40, r=40, t=50, b=100),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
    )

    return fig
