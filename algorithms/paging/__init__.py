"""Virtual Memory & Page Replacement Package."""

from algorithms.paging.base import StepRecord, PagingResult, BasePageReplacer
from algorithms.paging.replacers import (
    FIFOPageReplacer,
    LRUPageReplacer,
    OptimalPageReplacer,
    ClockPageReplacer,
    detect_belady_anomaly,
)

__all__ = [
    "StepRecord",
    "PagingResult",
    "BasePageReplacer",
    "FIFOPageReplacer",
    "LRUPageReplacer",
    "OptimalPageReplacer",
    "ClockPageReplacer",
    "detect_belady_anomaly",
]
