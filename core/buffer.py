"""
Telemetry Buffer & In-Memory Cache
Thread-safe circular time-series buffer for real-time visualization and chart streaming.
"""

import threading
from datetime import datetime, timezone, timedelta
from collections import deque
from typing import List, Optional, Union, Dict, Any

import pandas as pd

from core.models import ResourceMetrics, TelemetrySnapshot


class TelemetryBuffer:
    """
    Fixed-capacity circular buffer storing system telemetry records.
    Thread-safe for background polling workers and Streamlit UI reads.
    """

    def __init__(self, capacity: int = 120):
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
        self.capacity: int = capacity
        self._buffer: deque = deque(maxlen=capacity)
        self._lock: threading.Lock = threading.Lock()

    def append(self, snapshot: Union[ResourceMetrics, TelemetrySnapshot, Dict[str, Any]]) -> None:
        """Appends a new telemetry snapshot thread-safely."""
        with self._lock:
            self._buffer.append(snapshot)

    def get_all(self) -> List[Any]:
        """Returns a snapshot copy of all items in the buffer."""
        with self._lock:
            return list(self._buffer)

    def get_recent(self, seconds: int = 60) -> List[Any]:
        """Filters snapshots captured within the last N seconds."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        with self._lock:
            recent = []
            for item in self._buffer:
                item_ts = getattr(item, "timestamp", None)
                if isinstance(item_ts, datetime) and item_ts >= cutoff:
                    recent.append(item)
                elif isinstance(item, dict) and "timestamp" in item:
                    ts = item["timestamp"]
                    if isinstance(ts, str):
                        try:
                            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except ValueError:
                            continue
                    if isinstance(ts, datetime) and ts >= cutoff:
                        recent.append(item)
            return recent

    def to_dataframe(self, seconds: Optional[int] = None) -> pd.DataFrame:
        """
        Converts buffered items into a Pandas DataFrame optimized for Plotly line charts.
        """
        items = self.get_recent(seconds) if seconds else self.get_all()

        if not items:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "cpu_usage_percent",
                    "memory_usage_percent",
                    "memory_used_mb",
                    "swap_usage_percent",
                ]
            )

        rows = []
        for item in items:
            if isinstance(item, TelemetrySnapshot):
                res = item.resources
                cpu = res.cpu.usage_percent if res else 0.0
                mem = res.memory.usage_percent if res else 0.0
                mem_mb = res.memory.used_mb if res else 0.0
                swap = res.swap.usage_percent if res else 0.0
                ts = item.timestamp
            elif isinstance(item, ResourceMetrics):
                cpu = item.cpu.usage_percent
                mem = item.memory.usage_percent
                mem_mb = item.memory.used_mb
                swap = item.swap.usage_percent
                ts = item.timestamp
            elif isinstance(item, dict):
                cpu = item.get("cpu", {}).get("usage_percent", 0.0)
                mem = item.get("memory", {}).get("usage_percent", 0.0)
                mem_mb = item.get("memory", {}).get("used_mb", 0.0)
                swap = item.get("swap", {}).get("usage_percent", 0.0)
                ts = item.get("timestamp", datetime.now(timezone.utc))
            else:
                continue

            rows.append(
                {
                    "timestamp": ts,
                    "cpu_usage_percent": float(cpu),
                    "memory_usage_percent": float(mem),
                    "memory_used_mb": float(mem_mb),
                    "swap_usage_percent": float(swap),
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values(by="timestamp")
        return df

    def clear(self) -> None:
        """Clears all elements in the buffer."""
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)
