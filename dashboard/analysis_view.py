"""
Phase 3: Comparative Analysis & Benchmarking Studio View
Evaluates standard OS workloads across all implemented algorithms,
producing comparative metrics tables, labelled Plotly visual charts,
and in-depth technical observations.
"""

from typing import List, Dict, Any
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.config import DATA_DIR
from core.logger import activity_logger
from algorithms.cpu.base import Process
from algorithms.cpu.schedulers import (
    FCFSScheduler,
    SJFScheduler,
    SRTFScheduler,
    RoundRobinScheduler,
    PriorityScheduler,
    MLFQScheduler,
)
from algorithms.cpu.metrics import compare_all_schedulers
from algorithms.disk.schedulers import (
    FCFSDiskScheduler,
    SSTFDiskScheduler,
    SCANDiskScheduler,
    CSCANDiskScheduler,
    LOOKDiskScheduler,
    CLOOKDiskScheduler,
)
from algorithms.paging.replacers import (
    FIFOPageReplacer,
    LRUPageReplacer,
    OptimalPageReplacer,
    ClockPageReplacer,
)


def load_sample_inputs() -> Dict[str, Any]:
    """Load pre-configured standard datasets from sample_inputs.json."""
    sample_file = DATA_DIR / "sample_inputs.json"
    if sample_file.exists():
        try:
            with open(sample_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def render_analysis_view():
    """Renders the comprehensive Comparative Analysis Studio."""
    st.title("Comparative Benchmark Studio")
    st.caption(
        "Quantitative cross-algorithmic evaluation on standardized OS benchmark workloads. "
        "Produces comparative metrics tables, trajectory curves, and analytical trade-off evaluations."
    )

    sample_inputs = load_sample_inputs()

    tab_cpu, tab_disk, tab_paging, tab_insights = st.tabs(
        [
            "CPU Scheduling",
            "Disk Arm Trajectory",
            "Page Replacement",
            "Technical Observations",
        ]
    )

    # -------------------------------------------------------------
    # TAB 1: CPU SCHEDULING BENCHMARK
    # -------------------------------------------------------------
    with tab_cpu:
        st.subheader("CPU Scheduling Multi-Algorithm Benchmark")
        st.caption("Executes 7 distinct scheduling strategies against identical workloads.")

        cpu_presets = sample_inputs.get("cpu_scheduling", {})
        selected_workload = st.selectbox(
            "Select Standard Workload",
            list(cpu_presets.keys()) if cpu_presets else ["standard_workload"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        raw_procs = cpu_presets.get(
            selected_workload,
            [
                {"pid": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
                {"pid": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1},
                {"pid": "P3", "arrival_time": 2, "burst_time": 8, "priority": 4},
                {"pid": "P4", "arrival_time": 3, "burst_time": 6, "priority": 3},
            ],
        )

        processes = [Process(**p) for p in raw_procs]
        df_inputs = pd.DataFrame(raw_procs)

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("**Workload Process Table:**")
            st.dataframe(df_inputs, use_container_width=True, hide_index=True)

        comp_df = compare_all_schedulers(processes, rr_quantum=2, mlfq_q0=2, mlfq_q1=4)

        with c2:
            st.markdown("**Comparative Performance Metrics:**")
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

        # Plotly comparison
        fig_cpu = go.Figure()
        fig_cpu.add_trace(
            go.Bar(
                name="Avg Waiting Time",
                x=comp_df["Algorithm"],
                y=comp_df["Avg Waiting Time"],
                marker_color="#2563EB",
                text=comp_df["Avg Waiting Time"],
                textposition="auto",
            )
        )
        fig_cpu.add_trace(
            go.Bar(
                name="Avg Turnaround Time",
                x=comp_df["Algorithm"],
                y=comp_df["Avg Turnaround Time"],
                marker_color="#F59E0B",
                text=comp_df["Avg Turnaround Time"],
                textposition="auto",
            )
        )
        fig_cpu.update_layout(
            barmode="group",
            title="<b>CPU Schedulers: Waiting Time vs. Turnaround Time (Lower is Better)</b>",
            xaxis=dict(title="Scheduling Algorithm", tickangle=-20),
            yaxis=dict(title="Time Units"),
            height=380,
            margin=dict(l=30, r=30, t=50, b=80),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

        st.markdown(
            f"""
            > **Observation on `{selected_workload}`**:
            > - **Optimal Waiting Time**: `{comp_df.iloc[0]['Algorithm']}` achieved the lowest waiting time of `{comp_df.iloc[0]['Avg Waiting Time']}` units.
            > - **Turnaround Time Ratio**: Preemptive algorithms (SRTF/RR) avoid process starvation under mixed burst conditions compared to pure FCFS.
            """
        )

    # -------------------------------------------------------------
    # TAB 2: DISK SCHEDULING BENCHMARK
    # -------------------------------------------------------------
    with tab_disk:
        st.subheader("Disk Scheduling Head Movement Benchmark")
        st.caption("Compares total seek cylinder travel across 6 disk scheduling algorithms.")

        disk_presets = sample_inputs.get("disk_scheduling", {})
        disk_choice = st.selectbox(
            "Select Disk Request Scenario",
            list(disk_presets.keys()) if disk_presets else ["standard_cylinders"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        d_config = disk_presets.get(
            disk_choice,
            {
                "requests": [98, 183, 37, 122, 14, 124, 65, 67],
                "initial_head": 53,
                "max_cylinder": 199,
                "direction": "RIGHT",
            },
        )

        reqs = d_config["requests"]
        init_h = d_config["initial_head"]
        max_c = d_config["max_cylinder"]
        dir_val = d_config["direction"]

        disk_schedulers = [
            ("FCFS", FCFSDiskScheduler().schedule(reqs, init_h)),
            ("SSTF", SSTFDiskScheduler().schedule(reqs, init_h)),
            ("SCAN", SCANDiskScheduler().schedule(reqs, init_h, direction=dir_val, max_cylinder=max_c)),
            ("C-SCAN", CSCANDiskScheduler().schedule(reqs, init_h, direction=dir_val, max_cylinder=max_c)),
            ("LOOK", LOOKDiskScheduler().schedule(reqs, init_h, direction=dir_val)),
            ("C-LOOK", CLOOKDiskScheduler().schedule(reqs, init_h, direction=dir_val)),
        ]

        disk_records = []
        for name, res in disk_schedulers:
            disk_records.append(
                {
                    "Algorithm": name,
                    "Total Head Movement (Cylinders)": res.total_head_movement,
                    "Average Seek Length": round(res.total_head_movement / max(1, len(reqs)), 2),
                    "Traversal Sequence": " ➔ ".join(map(str, res.seek_sequence[:8])) + ("..." if len(res.seek_sequence) > 8 else ""),
                }
            )

        df_disk = pd.DataFrame(disk_records).sort_values("Total Head Movement (Cylinders)")

        c_d1, c_d2 = st.columns([1.2, 1.8])
        with c_d1:
            st.markdown(f"**Workload Parameters:** Initial Head = `{init_h}`, Requests = `{reqs}`")
            st.dataframe(df_disk[["Algorithm", "Total Head Movement (Cylinders)", "Average Seek Length"]], use_container_width=True, hide_index=True)

        with c_d2:
            fig_disk = go.Figure()
            fig_disk.add_trace(
                go.Bar(
                    x=df_disk["Algorithm"],
                    y=df_disk["Total Head Movement (Cylinders)"],
                    marker_color=["#10B981" if idx == 0 else "#2563EB" for idx in range(len(df_disk))],
                    text=df_disk["Total Head Movement (Cylinders)"],
                    textposition="auto",
                )
            )
            fig_disk.update_layout(
                title="<b>Total Seek Cylinders Traveled (Lower is Better)</b>",
                xaxis=dict(title="Algorithm"),
                yaxis=dict(title="Total Head Movement (Cylinders)"),
                height=320,
                margin=dict(l=30, r=30, t=50, b=40),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
            )
            st.plotly_chart(fig_disk, use_container_width=True)

        best_disk = df_disk.iloc[0]
        st.info(f"🏆 **Winner**: **{best_disk['Algorithm']}** incurred the minimal mechanical head movement of **{best_disk['Total Head Movement (Cylinders)']} cylinders**.")

    # -------------------------------------------------------------
    # TAB 3: PAGE REPLACEMENT BENCHMARK
    # -------------------------------------------------------------
    with tab_paging:
        st.subheader("Virtual Memory Page Replacement Benchmark")
        st.caption("Compares Page Faults and Hit Ratios across FIFO, LRU, Optimal, and Clock.")

        paging_presets = sample_inputs.get("page_replacement", {})
        paging_choice = st.selectbox(
            "Select Page Reference Stream",
            list(paging_presets.keys()) if paging_presets else ["standard_textbook_trace"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

        p_ref = paging_presets.get(paging_choice, [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1])
        frame_slider = st.slider("Benchmark Frame Count", min_value=2, max_value=6, value=3)

        res_fifo = FIFOPageReplacer().simulate(p_ref, num_frames=frame_slider)
        res_lru = LRUPageReplacer().simulate(p_ref, num_frames=frame_slider)
        res_opt = OptimalPageReplacer().simulate(p_ref, num_frames=frame_slider)
        res_clock = ClockPageReplacer().simulate(p_ref, num_frames=frame_slider)

        paging_records = [
            {"Algorithm": "FIFO", "Page Faults": res_fifo.page_faults, "Page Hits": res_fifo.page_hits, "Fault Rate (%)": res_fifo.fault_rate, "Hit Rate (%)": res_fifo.hit_rate},
            {"Algorithm": "LRU", "Page Faults": res_lru.page_faults, "Page Hits": res_lru.page_hits, "Fault Rate (%)": res_lru.fault_rate, "Hit Rate (%)": res_lru.hit_rate},
            {"Algorithm": "Optimal (OPT)", "Page Faults": res_opt.page_faults, "Page Hits": res_opt.page_hits, "Fault Rate (%)": res_opt.fault_rate, "Hit Rate (%)": res_opt.hit_rate},
            {"Algorithm": "Clock (2nd Chance)", "Page Faults": res_clock.page_faults, "Page Hits": res_clock.page_hits, "Fault Rate (%)": res_clock.fault_rate, "Hit Rate (%)": res_clock.hit_rate},
        ]

        df_paging = pd.DataFrame(paging_records).sort_values("Page Faults")

        cp1, cp2 = st.columns([1.2, 1.8])
        with cp1:
            st.markdown(f"**Reference Stream ({len(p_ref)} refs, {frame_slider} frames):**")
            st.code(", ".join(map(str, p_ref)))
            st.dataframe(df_paging, use_container_width=True, hide_index=True)

        with cp2:
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(name="Hits", x=df_paging["Algorithm"], y=df_paging["Page Hits"], marker_color="#10B981"))
            fig_p.add_trace(go.Bar(name="Faults", x=df_paging["Algorithm"], y=df_paging["Page Faults"], marker_color="#EF4444"))
            fig_p.update_layout(
                barmode="stack",
                title="<b>Page Hits vs. Page Faults Breakdown</b>",
                xaxis=dict(title="Algorithm"),
                yaxis=dict(title="Total Memory Accesses"),
                height=320,
                margin=dict(l=30, r=30, t=50, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
            )
            st.plotly_chart(fig_p, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 4: TECHNICAL OBSERVATIONS & INSIGHTS
    # -------------------------------------------------------------
    with tab_insights:
        st.subheader("🔬 Synthesized Technical Observations & Algorithmic Trade-offs")
        st.markdown(
            """
            ### 1. Process Scheduling Trade-offs
            - **SJF / SRTF Optimality**: Mathematically provable to yield the minimum average waiting time by prioritizing shorter burst tasks. However, it requires future CPU burst knowledge, which real operating systems approximate using exponential smoothing.
            - **FCFS Convoy Effect**: In the presence of a single compute-bound (long burst) job at $t=0$, short I/O-bound processes are blocked in the ready queue, driving CPU utilization down and average turnaround time up.
            - **Round Robin vs. Quantum Selection**: A small time quantum approximates processor sharing at the expense of high context-switching overhead. A large quantum degenerates into FCFS. MLFQ resolves this dynamically by demoting CPU-heavy processes and promoting I/O-heavy ones.

            ### 2. Disk Arm Trajectory & Mechanical Wear
            - **SSTF Starvation Risk**: While SSTF provides short average seek distances, requests at the physical disk perimeters suffer from starvation under continuous middle-cylinder request streams.
            - **SCAN & C-SCAN Fairness**: SCAN (Elevator) provides bounded wait times by sweeping unidirectionally. C-SCAN further enforces uniform waiting time across inner and outer cylinders by seeking back without serving intermediate requests.

            ### 3. Virtual Memory & Belady's Anomaly
            - **Stack Algorithms (LRU & OPT)**: Guaranteed never to exhibit Belady's Anomaly because the set of pages in an $n$-frame pool is strictly a subset of the pages in an $(n+1)$-frame pool.
            - **FIFO Vulnerability**: FIFO is susceptible to Belady's Anomaly (demonstrated on reference string `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5`), where allocating 4 frames produces 10 page faults compared to only 9 faults with 3 frames!
            - **Clock Algorithm Practicability**: Operates with $O(1)$ amortized overhead using a circular buffer and single reference bit, closely approximating LRU efficiency without expensive linked-list timestamp shuffling.
            """
        )

        st.divider()
        st.download_button(
            "📥 Export CPU Benchmark Data (CSV)",
            comp_df.to_csv(index=False),
            file_name="cpu_benchmark_results.csv",
            mime="text/csv",
        )
