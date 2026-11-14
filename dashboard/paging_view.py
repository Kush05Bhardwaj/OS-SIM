"""
Interactive Virtual Memory & Page Replacement Visualizer
Renders step-by-step frame matrices, hit/fault pie charts, and Belady anomaly curves.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from algorithms.paging.replacers import (
    FIFOPageReplacer,
    LRUPageReplacer,
    OptimalPageReplacer,
    ClockPageReplacer,
    detect_belady_anomaly,
)

PAGING_PRESETS: Dict[str, List[int]] = {
    "Standard Textbook Sequence": [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1],
    "Belady's Anomaly Demo (FIFO)": [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5],
    "High Locality Loop": [1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 2, 3],
    "Sequential Scan": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
}


def render_paging_view():
    """Renders the virtual memory page replacement simulator."""
    st.title("📑 Virtual Memory & Page Replacement Simulator")
    st.markdown(
        "Trace physical frame allocation step-by-step, evaluate page hit vs. fault rates, "
        "and inspect Belady's Anomaly across FIFO, LRU, Optimal, and Clock algorithms."
    )

    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset_choice = st.selectbox("📋 Reference Sequence Preset", list(PAGING_PRESETS.keys()) + ["Custom"])
    with c2:
        algo_choice = st.selectbox(
            "⚙️ Page Replacement Algorithm",
            [
                "First-In First-Out (FIFO)",
                "Least Recently Used (LRU)",
                "Optimal (OPT / Belady's Min)",
                "Clock (Second Chance)",
            ],
            index=1,
        )
    with c3:
        num_frames = st.slider("Physical Frames", min_value=1, max_value=8, value=3)

    if preset_choice in PAGING_PRESETS:
        default_str = ", ".join(map(str, PAGING_PRESETS[preset_choice]))
    else:
        default_str = "1, 2, 3, 4, 1, 2, 5"

    ref_str_input = st.text_input(
        "Page Reference String (comma-separated integers)",
        value=default_str,
        help="Enter integers separated by commas or spaces.",
    )

    # Parse reference string
    clean_tokens = ref_str_input.replace(",", " ").split()
    reference_string: List[int] = []
    for t in clean_tokens:
        try:
            reference_string.append(int(t))
        except ValueError:
            continue

    if not reference_string:
        st.warning("Please provide at least one valid integer page reference.")
        return

    # Execute Selected Replacer
    if "FIFO" in algo_choice:
        replacer = FIFOPageReplacer()
    elif "LRU" in algo_choice:
        replacer = LRUPageReplacer()
    elif "Optimal" in algo_choice:
        replacer = OptimalPageReplacer()
    else:
        replacer = ClockPageReplacer()

    result = replacer.simulate(reference_string, num_frames=num_frames)

    # Top Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Requests", result.total_requests)
    m2.metric("Page Faults", result.page_faults, f"{result.fault_rate}% fault rate", delta_color="inverse")
    m3.metric("Page Hits", result.page_hits, f"{result.hit_rate}% hit rate")
    m4.metric("Physical Frames", num_frames)
    m5.metric("Algorithm", algo_choice.split()[0])

    st.divider()

    col_matrix, col_chart = st.columns([2.5, 1.2])

    with col_matrix:
        st.subheader("📊 Step-by-Step Frame Matrix Table")
        # Build table representation
        matrix_dict: Dict[str, List[Any]] = {"Step": [f"#{s.step}" for s in result.steps]}
        matrix_dict["Page Ref"] = [str(s.page) for s in result.steps]

        for f_idx in range(num_frames):
            matrix_dict[f"Frame {f_idx}"] = [
                str(s.frames[f_idx]) if s.frames[f_idx] is not None else "-"
                for s in result.steps
            ]

        matrix_dict["Result"] = ["🟢 HIT" if s.is_hit else f"🔴 FAULT ({s.victim_page} evicted)" if s.victim_page is not None else "🔴 FAULT (Empty)" for s in result.steps]

        matrix_df = pd.DataFrame(matrix_dict)
        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

    with col_chart:
        st.subheader("🎯 Hit vs. Fault Ratio")
        pie_fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Hits", "Faults"],
                    values=[result.page_hits, result.page_faults],
                    hole=0.55,
                    marker=dict(colors=["#10B981", "#EF4444"]),
                )
            ]
        )
        pie_fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        )
        st.plotly_chart(pie_fig, use_container_width=True)

    # Belady's Anomaly Inspector
    st.divider()
    st.subheader("🔬 Belady's Anomaly Curve Analyzer")
    st.caption("Inspect how page faults vary when increasing physical frames from 2 to 8.")

    analysis = detect_belady_anomaly(reference_string, min_frames=2, max_frames=8)
    frame_counts = list(analysis["frame_faults"].keys())
    fault_counts = list(analysis["frame_faults"].values())

    curve_fig = go.Figure()
    curve_fig.add_trace(
        go.Scatter(
            x=frame_counts,
            y=fault_counts,
            mode="lines+markers+text",
            text=fault_counts,
            textposition="top center",
            line=dict(color="#2563EB", width=3),
            marker=dict(size=9, color="#1E40AF"),
            name="FIFO Faults",
        )
    )

    if analysis["anomaly_detected"]:
        for pt in analysis["anomaly_points"]:
            curve_fig.add_annotation(
                x=pt["to_frames"],
                y=pt["faults_after"],
                text=f"⚠️ Belady Anomaly! ({pt['faults_before']} -> {pt['faults_after']} faults)",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#DC2626",
                font=dict(color="#DC2626", size=12),
            )
        st.warning(
            f"⚠️ **Belady's Anomaly Confirmed**: Page faults increased when adding more frames! "
            f"({analysis['anomaly_points'][0]['faults_before']} faults at {analysis['anomaly_points'][0]['from_frames']} frames ➔ "
            f"{analysis['anomaly_points'][0]['faults_after']} faults at {analysis['anomaly_points'][0]['to_frames']} frames)."
        )
    else:
        st.success("✅ Standard behavior observed: Faults monotonically decrease or stay flat as frames increase.")

    curve_fig.update_layout(
        title="<b>Page Faults vs. Physical Frame Allocation (FIFO)</b>",
        xaxis=dict(title="Physical Frames Allocated", dtick=1),
        yaxis=dict(title="Total Page Faults"),
        height=320,
        margin=dict(l=30, r=30, t=40, b=30),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(curve_fig, use_container_width=True)
