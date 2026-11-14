"""
Base data models and abstract scheduler interface for CPU Scheduling simulations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TimelineSlice:
    """Represents a discrete time interval executed on the CPU."""
    start_time: int
    end_time: int
    pid: str
    state: str = "RUNNING"  # "RUNNING" or "IDLE"

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time


@dataclass
class Process:
    """Represents a process control block in the simulation."""
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0  # Lower number = higher priority
    remaining_time: int = field(init=False)
    start_time: Optional[int] = None
    completion_time: int = 0
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: int = 0

    def __post_init__(self):
        self.remaining_time = self.burst_time

    def copy(self) -> "Process":
        """Creates an independent copy of the process for simulation."""
        p = Process(
            pid=self.pid,
            arrival_time=self.arrival_time,
            burst_time=self.burst_time,
            priority=self.priority,
        )
        p.remaining_time = self.remaining_time
        p.start_time = self.start_time
        p.completion_time = self.completion_time
        p.waiting_time = self.waiting_time
        p.turnaround_time = self.turnaround_time
        p.response_time = self.response_time
        return p


@dataclass
class ScheduleResult:
    """Encapsulates the complete execution trace and computed metrics."""
    algorithm_name: str
    timeline: List[TimelineSlice]
    processes: List[Process]
    total_time: int = 0
    idle_time: int = 0
    avg_waiting_time: float = 0.0
    avg_turnaround_time: float = 0.0
    avg_response_time: float = 0.0
    cpu_utilization: float = 0.0
    throughput: float = 0.0

    def calculate_metrics(self) -> None:
        """Calculates standard OS scheduling benchmark metrics."""
        if not self.processes:
            return

        total_wt = 0
        total_tat = 0
        total_rt = 0

        for p in self.processes:
            # Turnaround Time = Completion Time - Arrival Time
            p.turnaround_time = max(0, p.completion_time - p.arrival_time)
            # Waiting Time = Turnaround Time - Burst Time
            p.waiting_time = max(0, p.turnaround_time - p.burst_time)
            # Response Time = First Start Time - Arrival Time
            if p.start_time is not None:
                p.response_time = max(0, p.start_time - p.arrival_time)
            else:
                p.response_time = p.waiting_time

            total_wt += p.waiting_time
            total_tat += p.turnaround_time
            total_rt += p.response_time

        n = len(self.processes)
        self.avg_waiting_time = round(total_wt / n, 2)
        self.avg_turnaround_time = round(total_tat / n, 2)
        self.avg_response_time = round(total_rt / n, 2)

        if self.total_time > 0:
            busy_time = self.total_time - self.idle_time
            self.cpu_utilization = round((busy_time / self.total_time) * 100.0, 2)
            self.throughput = round(n / self.total_time, 4)
        else:
            self.cpu_utilization = 0.0
            self.throughput = 0.0


class BaseScheduler(ABC):
    """Abstract base class for all CPU scheduling algorithms."""

    def __init__(self, name: str):
        self.name: str = name

    @abstractmethod
    def schedule(self, processes: List[Process], **kwargs) -> ScheduleResult:
        """Executes scheduling on the given process list."""
        pass

    def _compact_timeline(self, raw_timeline: List[TimelineSlice]) -> List[TimelineSlice]:
        """Merges contiguous slices belonging to the same PID."""
        if not raw_timeline:
            return []

        compacted: List[TimelineSlice] = []
        current = raw_timeline[0]

        for s in raw_timeline[1:]:
            if s.pid == current.pid and s.state == current.state and s.start_time == current.end_time:
                current = TimelineSlice(current.start_time, s.end_time, current.pid, current.state)
            else:
                compacted.append(current)
                current = s
        compacted.append(current)
        return compacted
