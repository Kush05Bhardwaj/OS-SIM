# OS-SIM System Architecture Documentation

Welcome to the **OS-SIM** technical architecture guide. This document details the software architecture, modular components, algorithmic foundations, telemetry dataflow, and deployment topology.

---

## 1. High-Level Architectural Blueprint

OS-SIM uses a decoupled, modular design divided into three primary tiers:

```mermaid
flowchart TD
    subgraph Client ["Client Tier (Browser)"]
        Browser["User Browser (Port 8501)"]
    end

    subgraph Presentation ["Presentation & Dashboard Tier (Streamlit)"]
        App["app.py (Navigation & Entry)"]
        CPUView["dashboard/cpu_view.py"]
        MemView["dashboard/memory_view.py"]
        PageView["dashboard/paging_view.py"]
        DiskView["dashboard/disk_view.py"]
        DeadlockView["dashboard/deadlock_view.py"]
        LiveView["dashboard/system_view.py"]
        HistoryView["dashboard/history_view.py"]
        GanttComp["dashboard/components/gantt.py"]
    end

    subgraph Logic ["Simulation & Algorithmic Engines"]
        CPUSched["algorithms/cpu/ (FCFS, SJF, SRTF, RR, Priority, MLFQ)"]
        MemAlloc["algorithms/memory/ (First, Best, Worst, Next Fit)"]
        PageRepl["algorithms/paging/ (FIFO, LRU, Optimal, Clock)"]
        DiskSched["algorithms/disk/ (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)"]
        DeadlockMgmt["algorithms/deadlock/ (Banker's Avoidance, WFG Detection)"]
    end

    subgraph Telemetry ["Linux Telemetry & Integration Tier"]
        BashExec["core/executor.py (BashExecutor)"]
        BashScripts["bash/*.sh (system_info, resource, disk, process, health)"]
        PydanticModels["core/models.py (Pydantic Schemas)"]
        CircBuffer["core/buffer.py (TelemetryBuffer)"]
    end

    subgraph Storage ["Persistence & Analytics Tier"]
        DBManager["database/db_manager.py (SQLite)"]
        ExportUtil["analytics/export.py (CSV & JSON)"]
        DBFile["data/os_sim.db"]
    end

    Browser <--> Presentation
    App --> CPUView & MemView & PageView & DiskView & DeadlockView & LiveView & HistoryView
    CPUView --> CPUSched & GanttComp
    MemView --> MemAlloc
    PageView --> PageRepl
    DiskView --> DiskSched
    DeadlockView --> DeadlockMgmt
    LiveView --> BashExec --> BashScripts
    BashExec --> PydanticModels --> CircBuffer
    HistoryView --> DBManager --> DBFile
    HistoryView --> ExportUtil
```

---

## 2. Linux Telemetry & Subprocess Dataflow

The host monitoring subsystem provides non-destructive telemetry with strict security sandboxing:

```mermaid
sequenceDiagram
    autonumber
    participant UI as Live Monitoring View
    participant Exec as BashExecutor
    participant Sub as subprocess.run()
    participant Sh as bash/*.sh
    participant Proc as /proc filesystem
    participant Buf as TelemetryBuffer

    UI->>Exec: execute("resource_monitor.sh", timeout=10)
    Exec->>Exec: Whitelist check & path traversal prevention
    alt Linux / WSL / Git-Bash available
        Exec->>Sub: Spawn bash script
        Sub->>Sh: Run script
        Sh->>Proc: Read /proc/stat & /proc/meminfo
        Proc-->>Sh: Raw telemetry
        Sh-->>Sub: Structured JSON stdout (exit code 0)
        Sub-->>Exec: CompletedProcess(returncode=0)
        Exec->>Exec: Parse JSON & validate
    else Native Windows / Non-Linux Fallback
        Exec->>Exec: Generate live telemetry via psutil
    end
    Exec-->>UI: ExecutionResult(success=True, parsed_data)
    UI->>Buf: append(ResourceMetrics)
    Buf-->>UI: to_dataframe() for Plotly streaming line chart
```

---

## 3. Algorithmic Modules

### CPU Scheduling Engine
- **Process State Machine**: Supports arrival queues, preemption slices, and completion bookkeeping.
- **Algorithms**: FCFS, SJF (Non-preemptive), SRTF (Preemptive), Round Robin ($q$), Priority (Preemptive & Non-preemptive), and 3-queue MLFQ with anti-starvation aging.

### Contiguous Memory Allocation Engine
- **Variable Partitioning**: Dynamic allocation supporting First Fit, Best Fit, Worst Fit, and Next Fit.
- **Adjacent Coalescing**: Automatically combines free memory partitions on deallocation.
- **Dynamic Compaction**: Consolidates fragmented holes into one contiguous high-address block.

### Virtual Memory & Page Replacement
- **Frame Matrices**: Traces exact physical frame states across each step of the reference string.
- **Algorithms**: FIFO, LRU, Optimal (forward lookahead), and Clock (second-chance reference bits).
- **Belady's Anomaly Detection**: Automated frame-scaling analysis.

### Disk Scheduling Engine
- **Traversals**: FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK with customizable boundary limits and directional sweeps.

### Deadlock Management Engine
- **Deadlock Avoidance**: Dijkstra's Banker's Algorithm with multiple resource instances, Need matrix evaluation ($Need = Max - Allocation$), safety verification, and interactive dynamic resource-request safety checks.
- **Deadlock Detection**: Multi-instance matrix reduction algorithm and Wait-For Graph (WFG) directed cycle detection.

---

## 4. Deployment Topology

```mermaid
flowchart LR
    subgraph Host ["Host System / Cloud Server"]
        Docker["Docker Engine"]
        
        subgraph Container ["Container: os-sim-app"]
            Streamlit["Streamlit Web Server (app.py)"]
            PyRuntime["Python 3.12 Runtime"]
            Coreutils["Linux Utilities (lscpu, free, df, ps, awk)"]
            LocalDB["/app/data/os_sim.db"]
        end
        
        Volume["Host Mount: ./data"]
    end

    User["Web Browser"] -->|Port 8501| Streamlit
    Streamlit --> PyRuntime
    PyRuntime --> Coreutils
    PyRuntime --> LocalDB
    LocalDB <--> Volume
```
