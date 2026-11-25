"""
Interactive CPU Scheduling Dashboard View
Enables interactive process configuration, animated simulation playback,
and multi-algorithm performance benchmarking in Streamlit.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd

from algorithms.cpu.base import Process, ScheduleResult, TimelineSlice
from algorithms.cpu.schedulers import (
    FCFSScheduler,
    SJFScheduler,
    SRTFScheduler,
    RoundRobinScheduler,
    PriorityScheduler,
    MLFQScheduler,
)
from algorithms.cpu.metrics import (
    extract_process_metrics_dataframe,
    compare_all_schedulers,
)
from dashboard.components.gantt import build_gantt_chart, build_comparison_barchart
from core.logger import activity_logger

PRESETS: Dict[str, List[Dict[str, Any]]] = {
    "Standard Mix": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
        {"pid": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1},
        {"pid": "P3", "arrival_time": 2, "burst_time": 8, "priority": 4},
        {"pid": "P4", "arrival_time": 3, "burst_time": 6, "priority": 3},
    ],
    "Convoy Effect (FCFS Bottleneck)": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 24, "priority": 1},
        {"pid": "P2", "arrival_time": 1, "burst_time": 3, "priority": 2},
        {"pid": "P3", "arrival_time": 2, "burst_time": 3, "priority": 3},
    ],
    "High Concurrency": [
        {"pid": "P1", "arrival_time": 0, "burst_time": 2, "priority": 3},
        {"pid": "P2", "arrival_time": 0, "burst_time": 4, "priority": 2},
        {"pid": "P3", "arrival_time": 0, "burst_time": 1, "priority": 1},
        {"pid": "P4", "arrival_time": 0, "burst_time": 3, "priority": 4},
        {"pid": "P5", "arrival_time": 0, "burst_time": 5, "priority": 5},
    ],
}


def render_cpu_view():
    """Renders the comprehensive CPU scheduling simulator dashboard."""
    st.title("CPU Scheduling Laboratory")
    st.caption(
        "Configure process arrival and burst parameters, inspect Gantt execution strips, "
        "step through CPU cycles, and benchmark algorithms against one another."
    )

    # Top level Configuration
    col_preset, col_algo = st.columns([1, 1])

    with col_preset:
        preset_choice = st.selectbox(
            "Scenario Preset",
            ["Custom Input"] + list(PRESETS.keys()),
            index=1,
            help="Choose a pre-configured OS workload scenario or input your own.",
        )

    with col_algo:
        algo_choice = st.selectbox(
            "Scheduling Algorithm",
            [
                "First-Come, First-Served (FCFS)",
                "Shortest Job First (SJF - Non-Preemptive)",
                "Shortest Remaining Time First (SRTF - Preemptive)",
                "Round Robin (RR)",
                "Priority Scheduling (Non-Preemptive)",
                "Priority Scheduling (Preemptive)",
                "Multi-Level Feedback Queue (MLFQ)",
            ],
            index=3,
        )

    # Dynamic Parameters
    rr_quantum = 2
    mlfq_q0 = 2
    mlfq_q1 = 4

    if "Round Robin" in algo_choice:
        rr_quantum = st.slider("Time Quantum (q)", min_value=1, max_value=10, value=2)
    elif "MLFQ" in algo_choice:
        c1, c2 = st.columns(2)
        with c1:
            mlfq_q0 = st.slider("Queue 0 Quantum (q0)", 1, 5, 2)
        with c2:
            mlfq_q1 = st.slider("Queue 1 Quantum (q1)", 2, 10, 4)

    # Load initial processes based on preset
    if "cpu_process_data" not in st.session_state or st.session_state.get("last_preset") != preset_choice:
        if preset_choice in PRESETS:
            st.session_state.cpu_process_data = pd.DataFrame(PRESETS[preset_choice])
        else:
            st.session_state.cpu_process_data = pd.DataFrame(
                [
                    {"pid": "P1", "arrival_time": 0, "burst_time": 4, "priority": 1},
                    {"pid": "P2", "arrival_time": 1, "burst_time": 2, "priority": 2},
                ]
            )
        st.session_state.last_preset = preset_choice

    st.subheader("Process Workload Configuration")
    edited_df = st.data_editor(
        st.session_state.cpu_process_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "pid": st.column_config.TextColumn("Process ID (PID)", required=True),
            "arrival_time": st.column_config.NumberColumn("Arrival Time", min_value=0, step=1, required=True),
            "burst_time": st.column_config.NumberColumn("Burst Time", min_value=1, step=1, required=True),
            "priority": st.column_config.NumberColumn("Priority (Lower = Higher)", min_value=0, step=1, required=True),
        },
        key="process_editor",
    )
    st.session_state.cpu_process_data = edited_df

    # Build Process objects
    processes: List[Process] = []
    for _, row in edited_df.iterrows():
        pid_str = str(row.get("pid", "")).strip()
        if not pid_str:
            continue
        try:
            at = int(row.get("arrival_time", 0))
            bt = int(row.get("burst_time", 1))
            pr = int(row.get("priority", 0))
            processes.append(Process(pid=pid_str, arrival_time=max(0, at), burst_time=max(1, bt), priority=pr))
        except (ValueError, TypeError):
            continue

    if not processes:
        st.warning("Please configure at least one valid process in the table above.")
        return

    # Execute Selected Algorithm
    if "FCFS" in algo_choice:
        scheduler = FCFSScheduler()
        res = scheduler.schedule(processes)
    elif "SJF" in algo_choice:
        scheduler = SJFScheduler()
        res = scheduler.schedule(processes)
    elif "SRTF" in algo_choice:
        scheduler = SRTFScheduler()
        res = scheduler.schedule(processes)
    elif "Round Robin" in algo_choice:
        scheduler = RoundRobinScheduler(quantum=rr_quantum)
        res = scheduler.schedule(processes, quantum=rr_quantum)
    elif "Priority Scheduling (Non-Preemptive)" in algo_choice:
        scheduler = PriorityScheduler(preemptive=False)
        res = scheduler.schedule(processes, preemptive=False)
    elif "Priority Scheduling (Preemptive)" in algo_choice:
        scheduler = PriorityScheduler(preemptive=True)
        res = scheduler.schedule(processes, preemptive=True)
    elif "MLFQ" in algo_choice:
        scheduler = MLFQScheduler(q0=mlfq_q0, q1=mlfq_q1)
        res = scheduler.schedule(processes)
    else:
        scheduler = FCFSScheduler()
        res = scheduler.schedule(processes)

    activity_logger.success("CPU", f"Simulated {len(processes)} processes with {res.algorithm_name}")

    # Render Tabs
    tab_timeline, tab_playback, tab_comparison = st.tabs(
        [
            "Execution Timeline & Metrics",
            "Cycle Step & Ready Queue",
            "Algorithm Leaderboard",
        ]
    )

    with tab_timeline:
        # Key Performance Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Avg Waiting Time", f"{res.avg_waiting_time} ms")
        m2.metric("Avg Turnaround", f"{res.avg_turnaround_time} ms")
        m3.metric("Avg Response Time", f"{res.avg_response_time} ms")
        m4.metric("CPU Utilization", f"{res.cpu_utilization}%")
        m5.metric("Throughput", f"{res.throughput} p/t")

        # Gantt Chart
        fig = build_gantt_chart(res)
        st.plotly_chart(fig, use_container_width=True)

        # Process Metrics Table
        st.subheader("Process Execution Statistics")
        proc_df = extract_process_metrics_dataframe(res)
        st.dataframe(proc_df, use_container_width=True, hide_index=True)

    with tab_playback:
        st.subheader("Simulation Cycle Inspector")
        total_time = res.total_time

        if total_time > 0:
            step_time = st.slider("Simulation Clock Tick", min_value=0, max_value=total_time, value=0)

            # Find active slice at step_time
            active_pid = "IDLE"
            for s in res.timeline:
                if s.start_time <= step_time < s.end_time:
                    active_pid = s.pid
                    break

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Clock Tick", f"t = {step_time}")
            with c2:
                st.metric("CPU State", "BUSY" if active_pid != "IDLE" else "IDLE")
            with c3:
                st.metric("Active Process", active_pid)

            st.divider()

            # Process state inspector at step_time
            status_records = []
            for p in res.processes:
                if step_time < p.arrival_time:
                    state = "Not Arrived"
                elif step_time >= p.completion_time:
                    state = "Terminated"
                elif p.pid == active_pid:
                    state = "Running (On CPU)"
                else:
                    state = "Ready (In Queue)"

                status_records.append(
                    {
                        "PID": p.pid,
                        "Arrival": p.arrival_time,
                        "Burst": p.burst_time,
                        "State at Tick": state,
                        "Completion Time": p.completion_time if step_time >= p.completion_time else "-",
                    }
                )

            st.dataframe(pd.DataFrame(status_records), use_container_width=True, hide_index=True)
        else:
            st.info("No timeline slices to inspect.")

    with tab_comparison:
        st.subheader("Algorithm Efficiency Comparison")
        st.caption(
            "Benchmark comparison across all 7 schedulers using the configured workload."
        )

        comp_df = compare_all_schedulers(processes, rr_quantum=rr_quantum, mlfq_q0=mlfq_q0, mlfq_q1=mlfq_q1)

        if not comp_df.empty:
            winner = comp_df.iloc[0]
            st.info(
                f"Optimal Strategy: **{winner['Algorithm']}** "
                f"(Avg Waiting: **{winner['Avg Waiting Time']} units**, "
                f"Avg Turnaround: **{winner['Avg Turnaround Time']} units**)"
            )

            barchart = build_comparison_barchart(comp_df)
            st.plotly_chart(barchart, use_container_width=True)

            st.dataframe(comp_df, use_container_width=True, hide_index=True)
