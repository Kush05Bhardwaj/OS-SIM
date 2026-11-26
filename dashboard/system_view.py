"""
Real-Time System Monitoring Dashboard View
Gathers and visualizes live host metrics via BashExecutor or cross-platform fallback.
"""

from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.executor import BashExecutor
from core.models import ResourceMetrics, TelemetrySnapshot
from core.buffer import TelemetryBuffer


def create_gauge(title: str, value: float, max_val: float = 100.0, color: str = "#2563EB") -> go.Figure:
    """Creates a sleek semi-circular gauge chart."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": f"<b>{title}</b>", "font": {"size": 14, "color": "#e2e8f0"}},
            number={"suffix": "%", "font": {"size": 22, "color": "#e2e8f0"}},
            gauge={
                "axis": {"range": [0, max_val], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": color},
                "bgcolor": "#1e293b",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 60], "color": "#12352d"},
                    {"range": [60, 85], "color": "#49391a"},
                    {"range": [85, 100], "color": "#4a2529"},
                ],
                "threshold": {
                    "line": {"color": "#DC2626", "width": 3},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )
    fig.update_layout(
        height=190,
        margin=dict(l=15, r=15, t=30, b=15),
        paper_bgcolor="#0f172a",
    )
    return fig


def render_system_view():
    """Renders the real-time Linux telemetry dashboard."""
    st.title("Host Telemetry & Subprocess Monitor")
    st.caption(
        "Live host telemetry gathered via non-destructive POSIX shell scripts and safe Python subprocess execution. "
        "Provides real-time gauges, time-series streaming metrics, partition meters, and process inspection."
    )

    if "telemetry_buffer" not in st.session_state:
        st.session_state.telemetry_buffer = TelemetryBuffer(capacity=60)
    if "bash_executor" not in st.session_state:
        st.session_state.bash_executor = BashExecutor()

    executor: BashExecutor = st.session_state.bash_executor
    buffer: TelemetryBuffer = st.session_state.telemetry_buffer

    # Controls Header
    col_refresh, col_mode = st.columns([1, 2])
    with col_refresh:
        refresh_clicked = st.button("Poll Metrics", use_container_width=True)
    with col_mode:
        is_live = executor.is_bash_available()
        if is_live:
            st.markdown('<span class="status-tag status-tag-active" style="margin-top: 6px;">● Native/Git Bash Subprocess Active</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-tag status-tag-standby" style="margin-top: 6px;">○ Cross-Platform psutil Fallback</span>', unsafe_allow_html=True)

    # Collect data
    sys_res = executor.execute("system_info.sh")
    res_res = executor.execute("resource_monitor.sh")
    disk_res = executor.execute("disk_monitor.sh")

    # Process controls
    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        proc_limit = st.selectbox("Process Limit", [10, 20, 30], index=0)
    with col_p2:
        proc_sort = st.selectbox("Sort Processes By", ["cpu", "memory"], index=0)

    proc_res = executor.execute("process_monitor.sh", args=[str(proc_limit), proc_sort])
    health_res = executor.execute("health_check.sh")

    sys_data = sys_res.data
    res_data = res_res.data
    disk_data = disk_res.data
    proc_data = proc_res.data
    health_data = health_res.data

    # Append to circular buffer
    if res_data and "cpu" in res_data:
        try:
            rm = ResourceMetrics.model_validate(res_data)
            buffer.append(rm)
        except Exception:
            buffer.append(res_data)

    # System Info Header Banner
    with st.container():
        st.subheader("Host Specifications")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Hostname", sys_data.get("hostname", "unknown"))
        i2.metric("Operating System", sys_data.get("os_name", "Linux"))
        i3.metric("Kernel Release", sys_data.get("kernel_release", "unknown"))
        i4.metric("Uptime", sys_data.get("uptime_human", "unknown"))

    st.divider()

    # Gauges Row
    st.subheader("Resource Utilization")
    cpu_info = res_data.get("cpu", {})
    mem_info = res_data.get("memory", {})
    swap_info = res_data.get("swap", {})

    cpu_val = float(cpu_info.get("usage_percent", 0.0))
    mem_val = float(mem_info.get("usage_percent", 0.0))
    swap_val = float(swap_info.get("usage_percent", 0.0))

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(create_gauge("CPU Load", cpu_val, color="#2563EB"), use_container_width=True)
        st.caption(f"1m: `{cpu_info.get('load_1m', 0.0)}` | 5m: `{cpu_info.get('load_5m', 0.0)}` | 15m: `{cpu_info.get('load_15m', 0.0)}`")
    with g2:
        st.plotly_chart(create_gauge("Memory (RAM)", mem_val, color="#10B981"), use_container_width=True)
        st.caption(f"Used: `{mem_info.get('used_mb', 0)} MB` / Total: `{mem_info.get('total_mb', 0)} MB`")
    with g3:
        st.plotly_chart(create_gauge("Swap Space", swap_val, color="#F59E0B"), use_container_width=True)
        st.caption(f"Used: `{swap_info.get('used_mb', 0)} MB` / Total: `{swap_info.get('total_mb', 0)} MB`")

    # Time-Series Real-Time Trendline
    st.divider()
    st.subheader("Telemetry Time-Series (Last 60s)")
    df_history = buffer.to_dataframe()

    if not df_history.empty and len(df_history) >= 1:
        trend_fig = go.Figure()
        trend_fig.add_trace(
            go.Scatter(
                x=df_history["timestamp"],
                y=df_history["cpu_usage_percent"],
                mode="lines+markers",
                name="CPU Utilization (%)",
                line=dict(color="#2563EB", width=2.5),
            )
        )
        trend_fig.add_trace(
            go.Scatter(
                x=df_history["timestamp"],
                y=df_history["memory_usage_percent"],
                mode="lines+markers",
                name="Memory Utilization (%)",
                line=dict(color="#10B981", width=2.5),
            )
        )
        trend_fig.update_layout(
            height=280,
            margin=dict(l=30, r=30, t=30, b=30),
            yaxis=dict(title="Utilization (%)", range=[0, 100]),
            xaxis=dict(title="Time"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#0f172a",
            paper_bgcolor="#0f172a",
        )
        st.plotly_chart(trend_fig, use_container_width=True)
    else:
        st.info("Collecting initial time-series history...")

    # Disk Storage Partitions
    st.divider()
    st.subheader("Storage Partitions")
    partitions = disk_data.get("partitions", [])
    if partitions:
        d_cols = st.columns(min(len(partitions), 3))
        for idx, p in enumerate(partitions):
            with d_cols[idx % len(d_cols)]:
                p_used = p.get("used_gb", 0.0)
                p_total = p.get("total_gb", 0.0)
                p_pct = float(p.get("usage_percent", 0.0))
                st.markdown(f"**Mount:** `{p.get('mountpoint', '/')}` (`{p.get('filesystem', '')}`)")
                st.progress(min(max(p_pct / 100.0, 0.0), 1.0))
                st.caption(f"{p_used} GB / {p_total} GB ({p_pct}%)")
    else:
        st.info("No partition metrics detected.")

    # Active Process Table
    st.divider()
    st.subheader("Active Process Table")
    procs = proc_data.get("processes", [])
    if procs:
        proc_df = pd.DataFrame(procs)
        search_term = st.text_input("Filter by Process Name / User", "")
        if search_term:
            proc_df = proc_df[
                proc_df["name"].str.contains(search_term, case=False, na=False)
                | proc_df["user"].str.contains(search_term, case=False, na=False)
            ]
        st.dataframe(proc_df, use_container_width=True, hide_index=True)
    else:
        st.info("No active process records.")

    # Health Check Expander
    with st.expander("Subsystem Health & Diagnostics", expanded=False):
        st.json(health_data)
