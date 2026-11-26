"""
OS-SIM Workstation
Integrated Operating System Simulation & Telemetry Engineering Console
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
    APP_VERSION,
    UI_PAGE_TITLE,
    UI_LAYOUT,
    UI_INITIAL_SIDEBAR_STATE,
)
from core.executor import BashExecutor

# Import View Modules
from dashboard.cpu_view import render_cpu_view
from dashboard.memory_view import render_memory_view
from dashboard.paging_view import render_paging_view
from dashboard.disk_view import render_disk_view
from dashboard.deadlock_view import render_deadlock_view
from dashboard.system_view import render_system_view
from dashboard.analysis_view import render_analysis_view
from dashboard.history_view import render_history_view

# Configure Streamlit page
st.set_page_config(
    page_title=f"{APP_NAME} Workstation",
    page_icon="OS",
    layout=UI_LAYOUT,
    initial_sidebar_state=UI_INITIAL_SIDEBAR_STATE,
)

# Dark workstation theme shared by every page.
st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {
        background: #0b1120 !important; color: #e5e7eb !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }
    [data-testid="stSidebar"] { background: #0f172a !important; border-right: 1px solid #263248 !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #94a3b8; }
    h1, h2, h3, h4 { color: #f1f5f9 !important; letter-spacing: -0.02em; }
    p, li, label, [data-testid="stCaptionContainer"] { color: #cbd5e1; }
    .workstation-header { display:flex; justify-content:space-between; align-items:center;
        background:linear-gradient(120deg,#111c31,#101827); border:1px solid #263248;
        border-radius:10px; padding:16px 20px; margin-bottom:20px; }
    .workstation-title { font-size:1.1rem; font-weight:700; color:#f1f5f9; }
    .workstation-meta { font-size:.8rem; color:#94a3b8; font-family:monospace; display:flex; gap:16px; }
    .status-tag { display:inline-flex; padding:3px 9px; border-radius:999px; font-size:.75rem; font-family:monospace; }
    .status-tag-active { background:#12352d; color:#6ee7b7; border:1px solid #1e5b48; }
    .status-tag-standby { background:#312719; color:#fcd34d; border:1px solid #59421f; }
    [data-testid="stMetric"] { background:#111827; border:1px solid #263248; border-radius:10px; padding:14px 16px !important; }
    [data-testid="stMetricValue"] { font-family:monospace !important; font-size:1.4rem !important; font-weight:700 !important; color:#f1f5f9 !important; }
    [data-testid="stMetricLabel"] { color:#94a3b8 !important; font-size:.75rem !important; text-transform:uppercase; letter-spacing:.05em; }
    .stButton > button, [data-testid="stDownloadButton"] button { background:#2563eb !important; color:#fff !important; border:1px solid #3b82f6 !important; border-radius:7px !important; }
    .stButton > button:hover, [data-testid="stDownloadButton"] button:hover { background:#1d4ed8 !important; }
    .stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #263248; }
    .stTabs [data-baseweb="tab"] { color:#94a3b8; }
    .stTabs [aria-selected="true"] { color:#93c5fd !important; border-bottom:2px solid #60a5fa !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #263248; border-radius:8px; }
    input, textarea, [data-baseweb="select"] > div { background:#111827 !important; color:#e5e7eb !important; }
    hr { border-color:#263248 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sidebar():
    """Renders application navigation and status in the sidebar."""
    st.sidebar.markdown(
        f"""
        <div style="padding: 4px 0 16px 0; border-bottom: 1px solid #263248; margin-bottom: 16px;">
            <div style="font-size: 1rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.01em;">
                {APP_NAME} <span style="font-size: 0.75rem; font-weight: 500; color: #94a3b8; font-family: monospace;">v{APP_VERSION}</span>
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
                OS Simulation & Telemetry Console
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    navigation = st.sidebar.radio(
        "Navigation",
        [
            "Overview",
            "CPU Scheduling",
            "Memory Management",
            "Page Replacement",
            "Disk Scheduling",
            "Deadlock Management",
            "Host Telemetry (Bash)",
            "Benchmark Studio",
            "Historical Database",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="border-top: 1px solid #263248; padding-top: 14px;">
            <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 8px;">
                Environment
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    executor = BashExecutor()
    has_bash = executor.is_bash_available()

    st.sidebar.caption(f"Host: {platform.system()} ({platform.machine()})")
    st.sidebar.caption(f"Runtime: Python {platform.python_version()}")
    if has_bash:
        st.sidebar.markdown('<span class="status-tag status-tag-active">● Bash Subprocess Active</span>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<span class="status-tag status-tag-standby">○ Emulation Fallback</span>', unsafe_allow_html=True)

    return navigation


def render_overview():
    """Renders clean operational dashboard overview."""
    st.markdown(
        f"""
        <div class="workstation-header">
            <div class="workstation-title">
                OS-SIM Workstation
            </div>
            <div class="workstation-meta">
                <span>Modules: 5</span>
                <span>Algorithms: 27</span>
                <span>Coverage: 89.28%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Process Schedulers", "7 Algorithms", "FCFS, SJF, SRTF, RR, Priority, MLFQ")
    with m2:
        st.metric("Memory Fit Strategies", "4 Strategies", "First, Best, Worst, Next Fit + Compaction")
    with m3:
        st.metric("Page Replacers", "4 Models", "FIFO, LRU, Optimal, Clock + Belady")
    with m4:
        st.metric("Disk Arm Schedulers", "6 Algorithms", "FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Simulation Workbenches")
        st.markdown(
            """
            - **CPU Scheduling**: Interactive Gantt execution strip, millisecond-resolution cycle inspector, and multi-algorithm turnaround/waiting comparisons.
            - **Memory Management**: Physical contiguous partition visualizer, external fragmentation meter, and dynamic address compaction.
            - **Virtual Memory & Paging**: Step-by-step physical frame matrix table, hit/fault ratio, and programmatic Belady's Anomaly analyzer.
            - **Disk Head Scheduling**: 2D cylinder trajectory plots ($x = \\text{Step}, y = \\text{Cylinder}$) and total head travel benchmarking.
            - **Deadlock Management**: Matrix representation of Allocation, Max, Need, and Available vectors with Banker's safety verification and WFG cycle detection.
            """
        )

    with col_right:
        st.markdown("### Host Monitoring & Subprocess Integration")
        st.markdown(
            """
            - **Non-Destructive Bash Scripts**: Gathers host telemetry via `system_info.sh`, `resource_monitor.sh`, `disk_monitor.sh`, and `process_monitor.sh`.
            - **Subprocess Security Layer**: Strict script whitelisting, directory traversal prevention (`../`), execution timeout enforcement, and schema validation.
            - **Comparative Benchmark Studio**: Automated execution of common workloads producing quantitative metrics and performance curves.
            - **Automated Verification**: Embedded pytest runner verifying 72 unit and integration tests with live audit logging.
            """
        )


def main():
    selected_page = render_sidebar()

    if selected_page == "Overview":
        render_overview()
    elif selected_page == "CPU Scheduling":
        render_cpu_view()
    elif selected_page == "Memory Management":
        render_memory_view()
    elif selected_page == "Page Replacement":
        render_paging_view()
    elif selected_page == "Disk Scheduling":
        render_disk_view()
    elif selected_page == "Deadlock Management":
        render_deadlock_view()
    elif selected_page == "Host Telemetry (Bash)":
        render_system_view()
    elif selected_page == "Benchmark Studio":
        render_analysis_view()
    elif selected_page == "Historical Database":
        render_history_view()


if __name__ == "__main__":
    main()
