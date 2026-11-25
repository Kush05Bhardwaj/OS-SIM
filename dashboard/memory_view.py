"""
Interactive Contiguous Memory Management Visualizer
Visualizes dynamic memory partitions, allocation strategies, fragmentation, and compaction.
"""

from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from algorithms.memory.base import MemoryPool, MemoryBlock
from core.logger import activity_logger

PALETTE = [
    "#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
    "#EC4899", "#06B6D4", "#84CC16", "#6366F1", "#14B8A6"
]


def render_memory_map_chart(pool: MemoryPool) -> go.Figure:
    """Renders physical memory as a linear horizontal bar of address spaces."""
    fig = go.Figure()

    if not pool.blocks:
        return fig

    allocated_pids = sorted(list({b.pid for b in pool.blocks if b.is_allocated and b.pid}))
    color_map = {pid: PALETTE[i % len(PALETTE)] for i, pid in enumerate(allocated_pids)}

    for b in pool.blocks:
        is_alloc = b.is_allocated
        color = color_map.get(b.pid, "#3B82F6") if is_alloc else "#E5E7EB"
        label = f"<b>{b.pid}</b><br>{b.size} KB" if is_alloc else f"FREE<br>{b.size} KB"

        fig.add_trace(
            go.Bar(
                name=b.pid if is_alloc else "Free Space",
                y=["Physical Memory"],
                x=[b.size],
                base=[b.start_address],
                orientation="h",
                marker=dict(
                    color=color,
                    line=dict(color="#111827" if is_alloc else "#9CA3AF", width=1.5),
                ),
                text=label,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="#FFFFFF" if is_alloc else "#4B5563", size=11),
                customdata=[[b.pid or "Free", b.start_address, b.end_address, b.size]],
                hovertemplate=(
                    "<b>Block:</b> %{customdata[0]}<br>"
                    "<b>Address Range:</b> [%{customdata[1]}, %{customdata[2]}]<br>"
                    "<b>Size:</b> %{customdata[3]} KB<extra></extra>"
                ),
                showlegend=is_alloc,
            )
        )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text="<b>Physical Memory Partition Layout (Address 0 to End)</b>",
            font=dict(size=16, color="#1F2937"),
        ),
        xaxis=dict(
            title="Physical Address (KB)",
            range=[0, pool.total_size],
            showgrid=True,
            gridcolor="#F3F4F6",
        ),
        yaxis=dict(showticklabels=False),
        height=200,
        margin=dict(l=20, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


def render_memory_view():
    """Renders the memory management dashboard."""
    st.title("Physical Memory Manager")
    st.caption(
        "Dynamic contiguous partition allocation, real-time fragmentation monitoring, "
        "adjacent hole coalescing, and address compaction."
    )

    if "memory_pool" not in st.session_state:
        st.session_state.memory_pool = MemoryPool(total_size=1024)

    pool: MemoryPool = st.session_state.memory_pool

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Pool", f"{pool.total_size} KB")
    m2.metric("Allocated", f"{pool.total_allocated_memory} KB", f"{(pool.total_allocated_memory / pool.total_size)*100:.1f}%")
    m3.metric("Free Memory", f"{pool.total_free_memory} KB", f"{pool.free_blocks_count} hole(s)")
    m4.metric("Free Partitions", f"{pool.free_blocks_count} Block(s)")

    st.divider()

    # Memory Visual Map
    fig = render_memory_map_chart(pool)
    st.plotly_chart(fig, use_container_width=True)

    # Interactive Allocation & Actions Form
    col_alloc, col_dealloc, col_actions = st.columns([1.5, 1.2, 1])

    with col_alloc:
        st.subheader("Allocate Partition")
        with st.form("alloc_form", clear_on_submit=True):
            pid_input = st.text_input("Process ID", value=f"P{len(pool.blocks)}")
            size_input = st.number_input("Requested Size (KB)", min_value=1, max_value=pool.total_size, value=150, step=10)
            strat_input = st.selectbox("Allocation Strategy", ["First Fit", "Best Fit", "Worst Fit", "Next Fit"])
            submit_alloc = st.form_submit_button("Allocate Memory", use_container_width=True)

            if submit_alloc:
                strat_key = strat_input.lower().replace(" ", "_")
                res = pool.allocate(pid_input.strip(), int(size_input), strategy=strat_key)
                if res.success:
                    activity_logger.success("Memory", f"Allocated {size_input} KB to {pid_input} ({strat_input})")
                    st.success(f"Allocated {size_input} KB to {pid_input} at address {res.allocated_block.start_address}.")
                    st.rerun()
                else:
                    activity_logger.warning("Memory", f"Allocation failed for {pid_input} ({size_input} KB): {res.error_message}")
                    st.error(f"Allocation Failed: {res.error_message}")

    with col_dealloc:
        st.subheader("Deallocate Partition")
        allocated_pids = [b.pid for b in pool.blocks if b.is_allocated and b.pid]
        if allocated_pids:
            with st.form("dealloc_form"):
                target_pid = st.selectbox("Select Process to Free", allocated_pids)
                submit_dealloc = st.form_submit_button("Free Memory & Coalesce", use_container_width=True)
                if submit_dealloc:
                    if pool.deallocate(target_pid):
                        activity_logger.success("Memory", f"Deallocated partition for {target_pid} and coalesced")
                        st.success(f"Released partition for {target_pid} and coalesced adjacent free holes.")
                        st.rerun()
        else:
            st.info("No processes currently allocated.")

    with col_actions:
        st.subheader("Memory Operations")
        if st.button("Compact Memory", use_container_width=True, help="Shift active blocks to low addresses and consolidate free space."):
            pool.compact()
            activity_logger.info("Memory", "Triggered dynamic memory compaction")
            st.success("Memory compacted into single continuous free block.")
            st.rerun()

        if st.button("Reset Memory Pool", use_container_width=True):
            pool.reset()
            activity_logger.info("Memory", "Reset physical memory pool")
            st.info("Memory pool reset.")
            st.rerun()

    # Partition Table
    st.divider()
    st.subheader("Partition Table Inspector")
    table_data = []
    for idx, b in enumerate(pool.blocks):
        table_data.append(
            {
                "Block #": idx + 1,
                "Start Address": b.start_address,
                "End Address": b.end_address,
                "Size (KB)": b.size,
                "Status": "ALLOCATED" if b.is_allocated else "FREE",
                "PID": b.pid if b.is_allocated else "-",
            }
        )
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
