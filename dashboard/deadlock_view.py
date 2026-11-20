"""
Interactive Deadlock Management Visualizer (Banker's Algorithm & Graph Detection).
"""

from typing import Dict, List, Tuple
import copy
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from algorithms.deadlock.base import DeadlockState
from algorithms.deadlock.banker import BankerAlgorithm
from algorithms.deadlock.detection import DeadlockDetector


PRESETS: Dict[str, Dict] = {
    "Silberschatz Textbook (Safe State)": {
        "processes": ["P0", "P1", "P2", "P3", "P4"],
        "resources": ["A", "B", "C"],
        "allocation": {
            "P0": {"A": 0, "B": 1, "C": 0},
            "P1": {"A": 2, "B": 0, "C": 0},
            "P2": {"A": 3, "B": 0, "C": 2},
            "P3": {"A": 2, "B": 1, "C": 1},
            "P4": {"A": 0, "B": 0, "C": 2},
        },
        "max_matrix": {
            "P0": {"A": 7, "B": 5, "C": 3},
            "P1": {"A": 3, "B": 2, "C": 2},
            "P2": {"A": 9, "B": 0, "C": 2},
            "P3": {"A": 2, "B": 2, "C": 2},
            "P4": {"A": 4, "B": 3, "C": 3},
        },
        "available": {"A": 3, "B": 3, "C": 2},
        "request": {
            "P0": {"A": 0, "B": 0, "C": 0},
            "P1": {"A": 1, "B": 0, "C": 2},
            "P2": {"A": 0, "B": 0, "C": 0},
            "P3": {"A": 0, "B": 0, "C": 0},
            "P4": {"A": 0, "B": 0, "C": 0},
        },
    },
    "Resource-Constrained (Unsafe / Deadlock)": {
        "processes": ["P0", "P1", "P2", "P3"],
        "resources": ["A", "B"],
        "allocation": {
            "P0": {"A": 2, "B": 0},
            "P1": {"A": 1, "B": 2},
            "P2": {"A": 0, "B": 1},
            "P3": {"A": 1, "B": 1},
        },
        "max_matrix": {
            "P0": {"A": 4, "B": 2},
            "P1": {"A": 3, "B": 3},
            "P2": {"A": 2, "B": 2},
            "P3": {"A": 2, "B": 2},
        },
        "available": {"A": 0, "B": 0},
        "request": {
            "P0": {"A": 1, "B": 1},
            "P1": {"A": 1, "B": 0},
            "P2": {"A": 1, "B": 0},
            "P3": {"A": 0, "B": 1},
        },
    },
    "Cyclic Dependency Deadlock (WFG)": {
        "processes": ["P0", "P1", "P2"],
        "resources": ["R0", "R1"],
        "allocation": {
            "P0": {"R0": 1, "R1": 0},
            "P1": {"R0": 0, "R1": 1},
            "P2": {"R0": 1, "R1": 1},
        },
        "max_matrix": {
            "P0": {"R0": 2, "R1": 2},
            "P1": {"R0": 2, "R1": 2},
            "P2": {"R0": 2, "R1": 2},
        },
        "available": {"R0": 0, "R1": 0},
        "request": {
            "P0": {"R0": 0, "R1": 1},
            "P1": {"R0": 1, "R1": 0},
            "P2": {"R0": 1, "R1": 1},
        },
    },
}


def build_wfg_figure(processes: List[str], edges: List[Tuple[str, str]], deadlocked: List[str]) -> go.Figure:
    """Builds a circular directed Wait-For Graph diagram with Plotly."""
    import math

    n = max(1, len(processes))
    positions = {}
    for i, p in enumerate(processes):
        angle = 2 * math.pi * i / n
        positions[p] = (math.cos(angle), math.sin(angle))

    fig = go.Figure()

    # Draw directed edges (arrows)
    for u, v in edges:
        x0, y0 = positions[u]
        x1, y1 = positions[v]
        fig.add_annotation(
            x=x1,
            y=y1,
            ax=x0,
            ay=y0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor="#EF4444" if (u in deadlocked and v in deadlocked) else "#6B7280",
            opacity=0.85,
        )

    # Draw nodes
    node_x = [positions[p][0] for p in processes]
    node_y = [positions[p][1] for p in processes]
    node_colors = ["#EF4444" if p in deadlocked else "#10B981" for p in processes]
    hover_texts = [f"<b>{p}</b>: {'DEADLOCKED' if p in deadlocked else 'SAFE'}" for p in processes]

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=processes,
            textposition="middle center",
            textfont=dict(color="#FFFFFF", size=13, family="sans-serif"),
            hoverinfo="text",
            hovertext=hover_texts,
            marker=dict(
                size=40,
                color=node_colors,
                line=dict(width=2, color="#111827"),
            ),
        )
    )

    fig.update_layout(
        title=dict(text="Wait-For Dependency Graph (WFG)", font=dict(size=14)),
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.4, 1.4]),
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#F9FAFB",
    )
    return fig


def render_deadlock_view() -> None:
    """Renders the Deadlock Management dashboard page."""
    st.header("🔒 Deadlock Management & Avoidance")
    st.markdown(
        "Explore **Dijkstra's Banker's Algorithm** for deadlock avoidance and **Resource Allocation Graph (RAG) / Wait-For Graph (WFG)** cycle detection."
    )

    # Preset selection
    st.sidebar.subheader("⚙️ Scenario Selection")
    chosen_preset = st.sidebar.selectbox("Load Scenario Preset", list(PRESETS.keys()), index=0)

    cfg = copy.deepcopy(PRESETS[chosen_preset])
    processes = cfg["processes"]
    resources = cfg["resources"]

    state = DeadlockState(
        processes=processes,
        resources=resources,
        allocation=cfg["allocation"],
        max_matrix=cfg["max_matrix"],
        available=cfg["available"],
    )

    tab_banker, tab_detect = st.tabs(["🛡️ Banker's Algorithm (Avoidance)", "🔍 Deadlock Detection & Graph"])

    with tab_banker:
        st.subheader("📊 System Matrices & Available Resources")

        col_avail, col_alloc, col_max, col_need = st.columns(4)

        with col_avail:
            st.markdown("**Available Vector**")
            df_avail = pd.DataFrame([state.available])
            st.dataframe(df_avail, use_container_width=True)

        with col_alloc:
            st.markdown("**Allocation Matrix**")
            df_alloc = pd.DataFrame.from_dict(state.allocation, orient="index")
            st.dataframe(df_alloc, use_container_width=True)

        with col_max:
            st.markdown("**Max Claim Matrix**")
            df_max = pd.DataFrame.from_dict(state.max_matrix, orient="index")
            st.dataframe(df_max, use_container_width=True)

        with col_need:
            st.markdown("**Need Matrix** *(Max - Alloc)*")
            df_need = pd.DataFrame.from_dict(state.get_need_matrix(), orient="index")
            st.dataframe(df_need, use_container_width=True)

        st.divider()

        banker = BankerAlgorithm(state)
        safety_result = banker.check_safety()

        st.subheader("🚦 Safety Verification")
        if safety_result.is_safe:
            seq_display = " ➔ ".join([f"**{p}**" for p in safety_result.safe_sequence])
            st.success(f"✅ **SAFE STATE**: System is safe from deadlock! Safe execution sequence: {seq_display}")
        else:
            st.error(f"❌ **UNSAFE STATE**: {safety_result.message}")

        with st.expander("📝 View Step-by-Step Safety Algorithm Execution Trace", expanded=True):
            if safety_result.steps:
                trace_rows = []
                for s in safety_result.steps:
                    trace_rows.append(
                        {
                            "Step": s.step_number,
                            "Process": s.process_id,
                            "Work Before": str(s.work_before),
                            "Need": str(s.need),
                            "Allocation Released": str(s.allocation),
                            "Work After": str(s.work_after),
                        }
                    )
                st.dataframe(pd.DataFrame(trace_rows), use_container_width=True)
            else:
                st.warning("No process could satisfy its needs with the initial Available resources.")

        st.divider()
        st.subheader("🎯 Interactive Resource-Request Evaluation")
        st.markdown(
            "Simulate a dynamic request from a running process to test whether the OS would grant it or force it to wait."
        )

        c_req_p, c_req_vals = st.columns([1, 2])
        with c_req_p:
            req_process = st.selectbox("Requesting Process", processes, index=1 if len(processes) > 1 else 0)

        with c_req_vals:
            req_inputs = {}
            col_res = st.columns(len(resources))
            for i, r in enumerate(resources):
                with col_res[i]:
                    max_allowable = state.get_need_matrix()[req_process].get(r, 0)
                    req_inputs[r] = st.number_input(
                        f"Req {r} (Max Need: {max_allowable})",
                        min_value=0,
                        max_value=max(10, max_allowable),
                        value=min(1, max_allowable),
                        key=f"req_{r}",
                    )

        if st.button("Evaluate Resource Request", type="primary"):
            req_res = banker.request_resources(req_process, req_inputs)
            if req_res.granted:
                st.success(f"🎉 **Request GRANTED**: {req_res.reason}")
                if req_res.safety_result:
                    st.info(f"Safe sequence post-allocation: <{', '.join(req_res.safety_result.safe_sequence)}>")
            else:
                st.error(f"🚫 **Request REJECTED**: {req_res.reason}")

    with tab_detect:
        st.subheader("🔍 Matrix Deadlock Detection & Wait-For Dependency Graph")
        st.markdown(
            "Identifies deadlocks in systems without advance resource claims by evaluating pending request matrices and cycle detection."
        )

        col_det_alloc, col_det_req, col_det_avail = st.columns(3)
        with col_det_alloc:
            st.markdown("**Current Allocation**")
            st.dataframe(pd.DataFrame.from_dict(cfg["allocation"], orient="index"), use_container_width=True)

        with col_det_req:
            st.markdown("**Pending Requests**")
            st.dataframe(pd.DataFrame.from_dict(cfg["request"], orient="index"), use_container_width=True)

        with col_det_avail:
            st.markdown("**Available Resources**")
            st.dataframe(pd.DataFrame([cfg["available"]]), use_container_width=True)

        detector = DeadlockDetector(
            processes=processes,
            resources=resources,
            allocation=cfg["allocation"],
            request=cfg["request"],
            available=cfg["available"],
        )
        det_result = detector.detect_matrix()

        st.divider()
        if det_result.has_deadlock:
            deadlocked_str = ", ".join([f"**{p}**" for p in det_result.deadlocked_processes])
            st.error(f"🚨 **DEADLOCK DETECTED!** Deadlocked processes: {deadlocked_str}")
            if det_result.cycles:
                cycles_str = " | ".join([" ➔ ".join(c) for c in det_result.cycles])
                st.warning(f"🔄 **Culprit Dependency Cycle(s)**: {cycles_str}")
        else:
            st.success("✅ **NO DEADLOCK DETECTED**: All processes can successfully complete.")

        c_graph, c_info = st.columns([1.4, 1])
        with c_graph:
            fig_wfg = build_wfg_figure(processes, det_result.wait_for_edges, det_result.deadlocked_processes)
            st.plotly_chart(fig_wfg, use_container_width=True)

        with c_info:
            st.markdown("**Wait-For Dependency Edges ($P_i \\to P_j$)**")
            if det_result.wait_for_edges:
                edge_df = pd.DataFrame(det_result.wait_for_edges, columns=["Waiting Process", "Holding Process"])
                st.dataframe(edge_df, use_container_width=True)
            else:
                st.info("No active wait-for dependencies.")

            st.markdown("**Resolution Order / Steps**")
            if det_result.steps:
                det_trace = [
                    {"Step": s.step_number, "Resolved Process": s.process_id, "New Work": str(s.work_after)}
                    for s in det_result.steps
                ]
                st.dataframe(pd.DataFrame(det_trace), use_container_width=True)
            else:
                st.write("No processes could be resolved.")
