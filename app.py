"""
OS-SIM: Operating System Simulation & Real-time Linux Monitor
Main application entry point.
"""

import sys
import platform
import streamlit as st
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    APP_DESCRIPTION,
    UI_PAGE_TITLE,
    UI_PAGE_ICON,
    UI_LAYOUT,
    UI_INITIAL_SIDEBAR_STATE,
    ALGORITHM_CATEGORIES,
)
from dashboard.cpu_view import render_cpu_view
from dashboard.memory_view import render_memory_view
from dashboard.paging_view import render_paging_view
from dashboard.disk_view import render_disk_view

# Configure Streamlit page
st.set_page_config(
    page_title=UI_PAGE_TITLE,
    page_icon=UI_PAGE_ICON,
    layout=UI_LAYOUT,
    initial_sidebar_state=UI_INITIAL_SIDEBAR_STATE,
)

# Custom CSS for polished styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        border-radius: 8px;
        padding: 1rem;
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sidebar():
    """Renders application navigation and status in the sidebar."""
    st.sidebar.title(f"{UI_PAGE_ICON} {APP_NAME}")
    st.sidebar.caption(f"v{APP_VERSION} • Educational & Analytical Platform")
    st.sidebar.divider()

    navigation = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Overview",
            "⚡ CPU Scheduling",
            "🧠 Memory Management",
            "📑 Page Replacement",
            "💽 Disk Scheduling",
            "🖥️ Live System Monitor",
            "📊 Analytics & History",
        ],
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Environment Status")
    st.sidebar.text(f"OS: {platform.system()} {platform.release()}")
    st.sidebar.text(f"Python: {platform.python_version()}")

    is_linux = platform.system().lower() == "linux"
    st.sidebar.caption(
        "🟢 Linux Host (Native Bash Active)"
        if is_linux
        else "🟡 Windows / Non-Linux (Mock Telemetry Active)"
    )

    return navigation


def render_overview():
    """Renders the main dashboard welcome overview."""
    st.markdown(f"<div class='main-header'>{APP_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>{APP_TAGLINE}</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CPU Schedulers", "6 Algorithms", "FCFS, SJF, RR...")
    with col2:
        st.metric("Memory Fit Models", "4 Strategies", "First, Best, Worst...")
    with col3:
        st.metric("Page Replacement", "4 Algorithms", "LRU, Optimal, FIFO...")
    with col4:
        st.metric("Disk Schedulers", "6 Algorithms", "SCAN, SSTF, LOOK...")

    st.divider()

    st.subheader("📌 Platform Capabilities")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
            ### 🎓 Interactive OS Simulation Engines
            - **CPU Scheduling**: Interactive Gantt chart with millisecond precision, ready queue states, and turnaround/waiting metrics.
            - **Contiguous Memory**: First/Best/Worst/Next Fit with internal/external fragmentation indicators and dynamic compaction.
            - **Virtual Memory & Paging**: Step-by-step frame matrix visualizer, hit/fault ratio graphs, and Belady's Anomaly tests.
            - **Disk Head Scheduling**: Interactive 2D cylinder trajectory plots and seek travel comparisons.
            """
        )

    with c2:
        st.markdown(
            """
            ### 🖥️ Real-Time Linux System Telemetry
            - **Bash Utilities**: Modular shell scripts (`lscpu`, `free`, `df`, `ps`) reporting structured JSON.
            - **Python Subprocess Engine**: Safe, non-destructive execution with timeout handling and failure containment.
            - **Live Dashboard**: Real-time gauge meters, partition utilization bars, and interactive process table.
            - **Historical Persistence**: SQLite storage for tracking simulation benchmarks and historical trends.
            """
        )

    st.divider()
    st.subheader("📚 Available Algorithm Catalog")
    for category, algos in ALGORITHM_CATEGORIES.items():
        with st.expander(f"🔹 {category} ({len(algos)} variants)", expanded=False):
            st.write(", ".join(algos))


def render_placeholder(title: str, description: str):
    """Renders a structured placeholder for modules under active construction."""
    st.subheader(title)
    st.info(description)
    st.markdown(
        """
        > **Module Status**: Core architecture initialized. Implementation scheduled in upcoming sprint phase.
        """
    )


def main():
    selected_page = render_sidebar()

    if selected_page == "🏠 Overview":
        render_overview()
    elif selected_page == "⚡ CPU Scheduling":
        render_cpu_view()
    elif selected_page == "🧠 Memory Management":
        render_memory_view()
    elif selected_page == "📑 Page Replacement":
        render_paging_view()
    elif selected_page == "💽 Disk Scheduling":
        render_disk_view()
    elif selected_page == "🖥️ Live System Monitor":
        render_placeholder(
            "🖥️ Real-time Linux System Telemetry",
            "Real-time inspection of CPU utilization, RAM consumption, disk mounts, and active processes via Bash integration.",
        )
    elif selected_page == "📊 Analytics & History":
        render_placeholder(
            "📊 Simulation History & Comparative Benchmarks",
            "Query and export historical simulation outcomes and telemetry logs stored in SQLite.",
        )


if __name__ == "__main__":
    main()
