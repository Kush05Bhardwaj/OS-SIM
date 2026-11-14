"""
Disk Scheduling Base Models and Interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DiskScheduleResult:
    """Encapsulates the cylinder traversal sequence and seek metrics."""
    algorithm_name: str
    initial_head: int
    direction: str  # "RIGHT" (toward higher cylinders) or "LEFT" (toward cylinder 0)
    seek_sequence: List[int]
    step_movements: List[int] = field(default_factory=list)
    total_head_movement: int = 0
    average_seek_distance: float = 0.0
    cylinder_max: int = 199

    def calculate_metrics(self) -> None:
        """Calculates step movements and total cylinder travel."""
        if len(self.seek_sequence) <= 1:
            self.step_movements = []
            self.total_head_movement = 0
            self.average_seek_distance = 0.0
            return

        self.step_movements = []
        total = 0
        for i in range(len(self.seek_sequence) - 1):
            diff = abs(self.seek_sequence[i + 1] - self.seek_sequence[i])
            self.step_movements.append(diff)
            total += diff

        self.total_head_movement = total
        # Average seek distance per serviced request (excluding initial jump if count > 0)
        num_requests = len(self.seek_sequence) - 1
        self.average_seek_distance = round(total / num_requests, 2) if num_requests > 0 else 0.0


class BaseDiskScheduler(ABC):
    """Abstract base class for disk arm scheduling algorithms."""

    def __init__(self, name: str):
        self.name: str = name

    @abstractmethod
    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        """Schedules cylinder requests and returns seek trajectory result."""
        pass
