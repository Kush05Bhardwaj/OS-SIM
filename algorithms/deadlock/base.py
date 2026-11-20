"""
Base data models and contracts for Deadlock Management (Avoidance & Detection).
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class DeadlockState(BaseModel):
    """
    State representation of system processes and resources.
    """
    processes: List[str] = Field(..., description="List of process identifiers (e.g. ['P0', 'P1'])")
    resources: List[str] = Field(..., description="List of resource identifiers (e.g. ['A', 'B', 'C'])")
    allocation: Dict[str, Dict[str, int]] = Field(..., description="Allocation matrix {process: {resource: count}}")
    max_matrix: Dict[str, Dict[str, int]] = Field(..., description="Maximum claim matrix {process: {resource: count}}")
    available: Dict[str, int] = Field(..., description="Available instances {resource: count}")

    def get_need_matrix(self) -> Dict[str, Dict[str, int]]:
        """Compute Need = Max - Allocation."""
        need: Dict[str, Dict[str, int]] = {}
        for p in self.processes:
            need[p] = {}
            for r in self.resources:
                alloc = self.allocation.get(p, {}).get(r, 0)
                max_val = self.max_matrix.get(p, {}).get(r, 0)
                need[p][r] = max(0, max_val - alloc)
        return need


class SafetyStep(BaseModel):
    """
    Individual step in Banker's safety evaluation sequence.
    """
    step_number: int
    process_id: str
    work_before: Dict[str, int]
    need: Dict[str, int]
    allocation: Dict[str, int]
    work_after: Dict[str, int]
    satisfied: bool
    explanation: str


class SafetyResult(BaseModel):
    """
    Overall result of Banker's safety algorithm check.
    """
    is_safe: bool
    safe_sequence: List[str] = Field(default_factory=list)
    steps: List[SafetyStep] = Field(default_factory=list)
    unresolved_processes: List[str] = Field(default_factory=list)
    message: str


class ResourceRequestResult(BaseModel):
    """
    Outcome of evaluating a resource allocation request from a process.
    """
    granted: bool
    process_id: str
    request: Dict[str, int]
    reason: str
    safety_result: Optional[SafetyResult] = None
    state_after: Optional[DeadlockState] = None


class DetectionStep(BaseModel):
    """
    Step trace in Deadlock Detection algorithm.
    """
    step_number: int
    process_id: str
    work_before: Dict[str, int]
    request: Dict[str, int]
    allocation: Dict[str, int]
    work_after: Dict[str, int]
    finished: bool


class DetectionResult(BaseModel):
    """
    Outcome of deadlock detection algorithm (Matrix & Graph Cycle analysis).
    """
    has_deadlock: bool
    deadlocked_processes: List[str] = Field(default_factory=list)
    safe_processes: List[str] = Field(default_factory=list)
    cycles: List[List[str]] = Field(default_factory=list)
    wait_for_edges: List[Tuple[str, str]] = Field(default_factory=list)
    steps: List[DetectionStep] = Field(default_factory=list)
    message: str
