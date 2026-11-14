# OS-SIM: Operating System Simulation & System Monitoring Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Framework: Streamlit](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io/)

**OS-SIM** is a comprehensive educational and analytical platform that combines interactive Operating System algorithm visualizations (CPU scheduling, memory management, page replacement, and disk scheduling) with real-time Linux monitoring utilities powered by Bash scripts and Python integration.

---

## 🗂️ Project Structure

```text
OS-SIM/
├── app.py                     # Streamlit application entry point
├── requirements.txt           # Project dependencies
├── README.md                  # Project documentation
├── core/                      # Application core, config, and constants
├── algorithms/                # OS algorithm simulation engines
│   ├── cpu/                   # FCFS, SJF, SRTF, RR, Priority, MLFQ
│   ├── memory/                # First Fit, Best Fit, Worst Fit, Next Fit
│   ├── paging/                # FIFO, LRU, Optimal, Clock
│   └── disk/                  # FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
├── bash/                      # Native Linux system monitoring Bash scripts
│   ├── system_info.sh         # OS, kernel, and hardware metadata
│   ├── resource_monitor.sh    # CPU & RAM live utilization
│   ├── disk_monitor.sh        # Storage and partition usage
│   ├── process_monitor.sh     # Active processes inspection
│   └── health_check.sh        # Tooling and subsystem health checker
├── dashboard/                 # Streamlit UI pages and widgets
├── analytics/                 # Metrics, benchmark calculation, and comparison
├── database/                  # SQLite/JSON persistence for simulation history
├── tests/                     # Unit and integration test suite
└── data/                      # Sample inputs, logs, and stored simulation runs
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Linux environment (or WSL2 on Windows) for native Bash monitoring utilities

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Kush05Bhardwaj/OS-SIM.git
cd OS-SIM

# Create and activate virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Application
```bash
streamlit run app.py
```

---

## 🧩 Modules Overview

### 1. Algorithm Visualizer & Simulator
- **CPU Scheduling**: Interactive Gantt charts, waiting time, turnaround time, response time, and throughput comparison.
- **Memory Management**: Visual memory block allocation, fragmentation analysis (internal & external).
- **Paging & Virtual Memory**: Step-by-step page fault tracking, hit ratio calculations, and frame tables.
- **Disk Scheduling**: Head movement trajectory visualization and total cylinder travel calculations.

### 2. Linux System Monitoring Suite
- Real-time telemetry via modular Bash scripts returning structured JSON data.
- Python subprocess management with non-destructive guarantees, timeouts, and safe error parsing.
- Dashboard views comparing simulated algorithm behaviors against actual system metrics.

---

## 🧪 Testing

Execute the test suite using pytest:
```bash
pytest tests/ -v
```

---

## 📜 License
This project is open-source and licensed under the [MIT License](LICENSE).
