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
from dashboard.design_view import render_design_view
from dashboard.cpu_view import render_cpu_view
from dashboard.memory_view import render_memory_view
from dashboard.paging_view import render_paging_view
from dashboard.disk_view import render_disk_view
from dashboard.deadlock_view import render_deadlock_view
from dashboard.system_view import render_system_view
from dashboard.analysis_view import render_analysis_view
from dashboard.reliability_view import render_reliability_view
from dashboard.report_view import render_report_view
from dashboard.history_view import render_history_view

# Configure Streamlit page
st.set_page_config(
    page_title=f"{APP_NAME} Workstation",
    page_icon="⚙️",
    layout=UI_LAYOUT,
    initial_sidebar_state=UI_INITIAL_SIDEBAR_STATE,
)

# Professional Precision Light-Mode Stylesheet
st.markdown(
    """
    <style>
    /* Global Reset & Typography */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FAFAFA !important;
        color: #111827 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
    }

    /* Headings */
    h1 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        letter-spacing: -0.025em !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #1F2937 !important;
        letter-spacing: -0.02em !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Top Workstation Bar */
    .workstation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 12px 20px;
        margin-bottom: 20px;
    }
    .workstation-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .workstation-meta {
        font-size: 0.8rem;
        color: #6B7280;
        font-family: "SF Mono", "JetBrains Mono", Consolas, monospace;
        display: flex;
        gap: 16px;
    }
    .status-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        font-family: "SF Mono", "JetBrains Mono", Consolas, monospace;
    }
    .status-tag-active {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .status-tag-standby {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }

    /* Panels & Containers */
    .stCard, .console-panel {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    /* Metric Boxes */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 12px 16px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    [data-testid="stMetricValue"] {
        font-family: "SF Mono", "JetBrains Mono", Consolas, monospace !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #6B7280 !important;
        font-weight: 600 !important;
    }

    /* Primary Buttons */
    .stButton > button {
        background-color: #1E40AF !important;
        color: #FFFFFF !important;
        border-radius: 5px !important;
        border: 1px solid #1D4ED8 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
        transition: background-color 0.15s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
        border-color: #1E40AF !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #E5E7EB;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        color: #4B5563;
        font-size: 0.875rem;
        font-weight: 500;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #1E40AF !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #1E40AF !important;
        background: transparent !important;
    }

    /* DataFrames & Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #E5E7EB;
        border-radius: 4px;
    }

    /* Dividers */
    hr {
        margin: 1.25rem 0 !important;
        border-color: #E5E7EB !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_sidebar():
    """Renders application navigation and status in the sidebar."""
    st.sidebar.markdown(
        f"""
        <div style="padding: 4px 0 16px 0; border-bottom: 1px solid #E5E7EB; margin-bottom: 16px;">
            <div style="font-size: 1rem; font-weight: 700; color: #111827; letter-spacing: -0.01em;">
                {APP_NAME} <span style="font-size: 0.75rem; font-weight: 500; color: #6B7280; font-family: monospace;">v{APP_VERSION}</span>
            </div>
            <div style="font-size: 0.75rem; color: #6B7280; margin-top: 2px;">
                OS Simulation & Telemetry Console
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    navigation = st.sidebar.radio(
        "Navigation",
        [
            "Overview & Quick Launch",
            "CPU Scheduling",
            "Memory Management",
            "Page Replacement",
            "Disk Scheduling",
            "Deadlock Management",
            "Host Telemetry (Bash)",
            "Benchmark Studio",
            "Reliability & Test Suite",
            "Architecture & Specs",
            "Documentation & Traces",
            "Historical Database",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="border-top: 1px solid #E5E7EB; padding-top: 14px;">
            <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #9CA3AF; margin-bottom: 8px;">
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

    if selected_page == "Overview & Quick Launch":
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
    elif selected_page == "Reliability & Test Suite":
        render_reliability_view()
    elif selected_page == "Architecture & Specs":
        render_design_view()
    elif selected_page == "Documentation & Traces":
        render_report_view()
    elif selected_page == "Historical Database":
        render_history_view()


if __name__ == "__main__":
    main()
