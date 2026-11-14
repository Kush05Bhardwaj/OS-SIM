# OS-SIM: Operating System Simulation & Real-Time Linux Telemetry Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10 | 3.11 | 3.12](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://www.python.org/)
[![Framework: Streamlit](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io/)
[![CI: Passing](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)
[![Coverage: 88%](https://img.shields.io/badge/Coverage-88%25-success.svg)](.coveragerc)

**OS-SIM** is a comprehensive educational and analytical platform combining interactive Operating System algorithm simulations (CPU scheduling, memory management, page replacement, and disk scheduling) with real-time Linux host monitoring utilities powered by Bash scripts and Python subprocess integration.

---

## 🗂️ Project Structure

```text
OS-SIM/
├── app.py                     # Streamlit application entry point & navigation
├── Dockerfile                 # Multi-stage container deployment
├── docker-compose.yml         # Single-command Docker compose configuration
├── requirements.txt           # Project dependencies
├── README.md                  # Comprehensive documentation
├── core/                      # Application settings, executor, models, buffer
│   ├── config.py              # Application settings and whitelists
│   ├── executor.py            # BashExecutor with timeout and fallbacks
│   ├── models.py              # Pydantic v2 telemetry schemas
│   └── buffer.py              # Thread-safe circular time-series buffer
├── algorithms/                # Core simulation engines
│   ├── cpu/                   # FCFS, SJF, SRTF, RR, Priority, MLFQ, Metrics
│   ├── memory/                # First Fit, Best Fit, Worst Fit, Next Fit, Compaction
│   ├── paging/                # FIFO, LRU, Optimal, Clock, Belady Detector
│   └── disk/                  # FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
├── bash/                      # Native Linux monitoring shell scripts
│   ├── system_info.sh         # OS, kernel, and hardware metadata
│   ├── resource_monitor.sh    # CPU, RAM, and Swap live metrics
│   ├── disk_monitor.sh        # Storage and partition usage
│   ├── process_monitor.sh     # Active processes inspection
│   └── health_check.sh        # Tooling and subsystem health checker
├── dashboard/                 # Streamlit UI pages and widgets
│   ├── cpu_view.py            # CPU Gantt charts, cycle playback, leaderboards
│   ├── memory_view.py         # Partition memory maps and compaction visualizer
│   ├── paging_view.py         # Frame matrix tables & Belady anomaly curve
│   ├── disk_view.py           # 2D seek trajectory curves and distance charts
│   ├── system_view.py         # Live CPU/RAM gauges and time-series line plot
│   └── history_view.py        # SQLite history browser and CSV/JSON exporter
├── database/                  # SQLite storage manager
├── analytics/                 # CSV and JSON report export utilities
├── tests/                     # Comprehensive test suite (61 tests, > 85% coverage)
└── docs/                      # Architectural documentation & diagrams
```

---

## 🚀 Quickstart Guide

### Option A: Local Python Environment
```bash
# Clone the repository
git clone https://github.com/Kush05Bhardwaj/OS-SIM.git
cd OS-SIM

# Create and activate virtual environment (Python 3.10+)
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Launch the Streamlit application
streamlit run app.py
```

### Option B: Docker Container Deployment
```bash
# Build and run with Docker Compose
docker compose up --build

# Access the application in your browser:
# http://localhost:8501
```

---

## 🧪 Testing & Code Coverage

Execute the 61-test automated suite and generate coverage reports:
```bash
pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing
```

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).
