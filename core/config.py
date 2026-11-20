"""
OS-SIM Configuration & Constants
Centralized settings for simulation parameters, paths, and application metadata.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Base Directory Resolution
BASE_DIR: Path = Path(__file__).resolve().parent.parent
BASH_DIR: Path = BASE_DIR / "bash"
DATA_DIR: Path = BASE_DIR / "data"

# Application Metadata
APP_NAME: str = "OS-SIM"
APP_TAGLINE: str = "Operating System Simulator & Real-time Linux Monitor"
APP_VERSION: str = "0.1.0"
APP_DESCRIPTION: str = (
    "A dual-purpose platform combining interactive OS algorithm simulations "
    "(CPU scheduling, memory management, page replacement, disk scheduling, deadlock management) "
    "with live Linux system monitoring utilities."
)

# Supported Algorithms & Categories
ALGORITHM_CATEGORIES: Dict[str, List[str]] = {
    "CPU Scheduling": [
        "First-Come, First-Served (FCFS)",
        "Shortest Job First (SJF - Non-Preemptive)",
        "Shortest Remaining Time First (SRTF - Preemptive)",
        "Round Robin (RR)",
        "Priority Scheduling (Preemptive & Non-Preemptive)",
        "Multi-Level Feedback Queue (MLFQ)",
    ],
    "Memory Allocation": [
        "First Fit",
        "Best Fit",
        "Worst Fit",
        "Next Fit",
    ],
    "Page Replacement": [
        "First-In First-Out (FIFO)",
        "Least Recently Used (LRU)",
        "Optimal (OPT)",
        "Clock (Second Chance)",
    ],
    "Disk Scheduling": [
        "FCFS",
        "SSTF (Shortest Seek Time First)",
        "SCAN (Elevator)",
        "C-SCAN (Circular SCAN)",
        "LOOK",
        "C-LOOK",
    ],
    "Deadlock Management": [
        "Banker's Algorithm (Safety & Avoidance)",
        "Resource-Request Evaluation",
        "Wait-For Graph Cycle Detection",
    ],
}

# Bash Execution Settings
BASH_DEFAULT_TIMEOUT: int = 10  # in seconds
BASH_ALLOWED_SCRIPTS: List[str] = [
    "system_info.sh",
    "resource_monitor.sh",
    "disk_monitor.sh",
    "process_monitor.sh",
    "health_check.sh",
]

# UI / Streamlit Configuration
UI_PAGE_TITLE: str = f"{APP_NAME} | OS Simulator"
UI_PAGE_ICON: str = "⚡"
UI_LAYOUT: str = "wide"
UI_INITIAL_SIDEBAR_STATE: str = "expanded"


@dataclass
class AppConfig:
    """Runtime configuration object."""
    app_name: str = APP_NAME
    version: str = APP_VERSION
    base_dir: Path = BASE_DIR
    bash_dir: Path = BASH_DIR
    data_dir: Path = DATA_DIR
    debug_mode: bool = False
    default_timeout: int = BASH_DEFAULT_TIMEOUT


config = AppConfig()
