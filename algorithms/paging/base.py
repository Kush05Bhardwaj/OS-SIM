"""
Virtual Memory & Page Replacement Base Models and Interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class StepRecord:
    """Represents the simulation state after processing a single page reference."""
    step: int
    page: int
    frames: List[Optional[int]]
    is_hit: bool
    victim_page: Optional[int] = None
    frame_index_modified: Optional[int] = None


@dataclass
class PagingResult:
    """Aggregated results and step-by-step trace of a page replacement simulation."""
    algorithm_name: str
    reference_string: List[int]
    num_frames: int
    steps: List[StepRecord]
    total_requests: int = 0
    page_faults: int = 0
    page_hits: int = 0
    fault_rate: float = 0.0
    hit_rate: float = 0.0

    def calculate_metrics(self) -> None:
        self.total_requests = len(self.reference_string)
        self.page_faults = sum(1 for s in self.steps if not s.is_hit)
        self.page_hits = self.total_requests - self.page_faults

        if self.total_requests > 0:
            self.fault_rate = round((self.page_faults / self.total_requests) * 100.0, 2)
            self.hit_rate = round((self.page_hits / self.total_requests) * 100.0, 2)


class BasePageReplacer(ABC):
    """Abstract base class for page replacement algorithms."""

    def __init__(self, name: str):
        self.name: str = name

    @abstractmethod
    def simulate(self, reference_string: List[int], num_frames: int) -> PagingResult:
        """Simulates page references on physical memory frames."""
        pass
