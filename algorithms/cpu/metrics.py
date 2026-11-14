"""
CPU Scheduling Metrics & Comparative Evaluation Engine
"""

from typing import List, Dict, Any, Optional
import pandas as pd

from algorithms.cpu.base import Process, ScheduleResult
from algorithms.cpu.schedulers import (
    FCFSScheduler,
    SJFScheduler,
    SRTFScheduler,
    RoundRobinScheduler,
    PriorityScheduler,
    MLFQScheduler,
)


def extract_process_metrics_dataframe(result: ScheduleResult) -> pd.DataFrame:
    """
    Extracts individual process scheduling statistics into a formatted DataFrame.
    """
    if not result or not result.processes:
        return pd.DataFrame()

    data = []
    for p in sorted(result.processes, key=lambda x: x.pid):
        data.append(
            {
                "Process ID": p.pid,
                "Arrival Time": p.arrival_time,
                "Burst Time": p.burst_time,
                "Priority": p.priority,
                "Start Time": p.start_time if p.start_time is not None else 0,
                "Completion Time": p.completion_time,
                "Turnaround Time (TAT)": p.turnaround_time,
                "Waiting Time (WT)": p.waiting_time,
                "Response Time (RT)": p.response_time,
            }
        )

    return pd.DataFrame(data)


def compare_all_schedulers(
    processes: List[Process],
    rr_quantum: int = 2,
    mlfq_q0: int = 2,
    mlfq_q1: int = 4,
) -> pd.DataFrame:
    """
    Executes all 6 schedulers on the same process dataset and compiles a comparative benchmark leaderboard.
    """
    if not processes:
        return pd.DataFrame()

    schedulers = [
        FCFSScheduler(),
        SJFScheduler(),
        SRTFScheduler(),
        RoundRobinScheduler(quantum=rr_quantum),
        PriorityScheduler(preemptive=False),
        PriorityScheduler(preemptive=True),
        MLFQScheduler(q0=mlfq_q0, q1=mlfq_q1),
    ]

    records = []
    for s in schedulers:
        # Pass deep copied processes to ensure algorithmic purity
        procs_copy = [p.copy() for p in processes]
        res = s.schedule(procs_copy)

        records.append(
            {
                "Algorithm": res.algorithm_name,
                "Avg Waiting Time": res.avg_waiting_time,
                "Avg Turnaround Time": res.avg_turnaround_time,
                "Avg Response Time": res.avg_response_time,
                "CPU Utilization (%)": res.cpu_utilization,
                "Throughput (proc/unit)": res.throughput,
                "Total Duration": res.total_time,
            }
        )

    df = pd.DataFrame(records)
    # Sort leaderboard by lowest average waiting time
    df = df.sort_values(by=["Avg Waiting Time", "Avg Turnaround Time"]).reset_index(drop=True)
    return df
