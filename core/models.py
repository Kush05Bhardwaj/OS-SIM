"""
Telemetry Data Models
Pydantic v2 schemas for Linux subsystem metrics and system snapshots.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class BaseTelemetryModel(BaseModel):
    """Base model with common configurations and serialization helpers."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore"
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO-8601 UTC timestamp of collection"
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        if isinstance(v, str):
            try:
                # Handle standard ISO strings
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now(timezone.utc)
        elif isinstance(v, datetime):
            return v
        return datetime.now(timezone.utc)


class SystemInfo(BaseTelemetryModel):
    """Host operating system and hardware metadata."""
    hostname: str = Field(default="unknown")
    os_name: str = Field(default="Linux")
    kernel_release: str = Field(default="unknown")
    architecture: str = Field(default="x86_64")
    cpu_model: str = Field(default="Generic CPU")
    cpu_cores: int = Field(default=1, ge=1)
    uptime_seconds: float = Field(default=0.0, ge=0.0)
    uptime_human: str = Field(default="unknown")


class CpuMetrics(BaseModel):
    """CPU usage percentage and system load averages."""
    usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    load_1m: float = Field(default=0.0, ge=0.0)
    load_5m: float = Field(default=0.0, ge=0.0)
    load_15m: float = Field(default=0.0, ge=0.0)


class MemoryMetrics(BaseModel):
    """Physical memory allocation and usage statistics in Megabytes."""
    total_mb: float = Field(default=0.0, ge=0.0)
    used_mb: float = Field(default=0.0, ge=0.0)
    free_mb: float = Field(default=0.0, ge=0.0)
    available_mb: float = Field(default=0.0, ge=0.0)
    usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class SwapMetrics(BaseModel):
    """Virtual swap space utilization in Megabytes."""
    total_mb: float = Field(default=0.0, ge=0.0)
    used_mb: float = Field(default=0.0, ge=0.0)
    free_mb: float = Field(default=0.0, ge=0.0)
    usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class ResourceMetrics(BaseTelemetryModel):
    """Combined live CPU, RAM, and Swap resource metrics."""
    cpu: CpuMetrics = Field(default_factory=CpuMetrics)
    memory: MemoryMetrics = Field(default_factory=MemoryMetrics)
    swap: SwapMetrics = Field(default_factory=SwapMetrics)


class DiskPartition(BaseModel):
    """Single filesystem partition storage metrics."""
    filesystem: str = Field(default="unknown")
    mountpoint: str = Field(default="/")
    total_gb: float = Field(default=0.0, ge=0.0)
    used_gb: float = Field(default=0.0, ge=0.0)
    available_gb: float = Field(default=0.0, ge=0.0)
    usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class DiskSnapshot(BaseTelemetryModel):
    """Collection of mounted disk partition metrics."""
    partitions: List[DiskPartition] = Field(default_factory=list)


class ProcessInfo(BaseModel):
    """Running process snapshot entry."""
    pid: int = Field(ge=0)
    user: str = Field(default="unknown")
    name: str = Field(default="unknown")
    cpu_percent: float = Field(default=0.0, ge=0.0)
    memory_percent: float = Field(default=0.0, ge=0.0)
    status: str = Field(default="R")


class ProcessSnapshot(BaseTelemetryModel):
    """Active process table snapshot with sorting criteria."""
    limit: int = Field(default=10, ge=1)
    sort_by: str = Field(default="cpu")
    processes: List[ProcessInfo] = Field(default_factory=list)


class HealthCheckSnapshot(BaseTelemetryModel):
    """Host dependency and procfs availability check."""
    subsystem: str = Field(default="unknown")
    all_healthy: bool = Field(default=False)
    commands: Dict[str, bool] = Field(default_factory=dict)
    procfs: Dict[str, bool] = Field(default_factory=dict)


class TelemetrySnapshot(BaseTelemetryModel):
    """Aggregated full system telemetry snapshot."""
    system: Optional[SystemInfo] = None
    resources: Optional[ResourceMetrics] = None
    disks: Optional[DiskSnapshot] = None
    processes: Optional[ProcessSnapshot] = None
    health: Optional[HealthCheckSnapshot] = None

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flattens key metrics for logging or table view."""
        flat = {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.resources.cpu.usage_percent if self.resources else 0.0,
            "memory_percent": self.resources.memory.usage_percent if self.resources else 0.0,
            "memory_used_mb": self.resources.memory.used_mb if self.resources else 0.0,
            "swap_percent": self.resources.swap.usage_percent if self.resources else 0.0,
        }
        if self.system:
            flat["hostname"] = self.system.hostname
            flat["uptime_seconds"] = self.system.uptime_seconds
        return flat
