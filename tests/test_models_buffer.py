"""
Unit tests for Pydantic telemetry models and TelemetryBuffer.
"""

import time
from datetime import datetime, timezone, timedelta
import pytest
import pandas as pd

from core.models import (
    SystemInfo,
    CpuMetrics,
    MemoryMetrics,
    SwapMetrics,
    ResourceMetrics,
    DiskPartition,
    DiskSnapshot,
    ProcessInfo,
    ProcessSnapshot,
    HealthCheckSnapshot,
    TelemetrySnapshot,
)
from core.buffer import TelemetryBuffer


def test_system_info_defaults_and_validation():
    info = SystemInfo(
        hostname="test-box",
        os_name="Ubuntu 22.04",
        cpu_cores=8,
        uptime_seconds=3600.5,
    )
    assert info.hostname == "test-box"
    assert info.cpu_cores == 8
    assert info.uptime_seconds == 3600.5
    assert isinstance(info.timestamp, datetime)

    # Missing optional fields receive defaults
    raw = {"hostname": "box"}
    parsed = SystemInfo.model_validate(raw)
    assert parsed.os_name == "Linux"
    assert parsed.cpu_cores == 1


def test_resource_metrics_validation():
    data = {
        "timestamp": "2026-11-14T10:00:00Z",
        "cpu": {"usage_percent": 45.2, "load_1m": 1.2, "load_5m": 0.8, "load_15m": 0.5},
        "memory": {"total_mb": 16000, "used_mb": 8000, "free_mb": 8000, "usage_percent": 50.0},
        "swap": {"total_mb": 4000, "used_mb": 500, "free_mb": 3500, "usage_percent": 12.5},
    }
    metrics = ResourceMetrics.model_validate(data)
    assert metrics.cpu.usage_percent == 45.2
    assert metrics.memory.total_mb == 16000.0
    assert metrics.swap.used_mb == 500.0
    assert metrics.timestamp.year == 2026


def test_disk_partition_and_snapshot():
    p1 = DiskPartition(filesystem="/dev/sda1", mountpoint="/", total_gb=100.0, used_gb=40.0, available_gb=60.0, usage_percent=40.0)
    snap = DiskSnapshot(partitions=[p1])
    assert len(snap.partitions) == 1
    assert snap.partitions[0].mountpoint == "/"


def test_process_snapshot():
    proc = ProcessInfo(pid=123, user="root", name="systemd", cpu_percent=0.1, memory_percent=0.2, status="S")
    snap = ProcessSnapshot(limit=5, sort_by="cpu", processes=[proc])
    assert len(snap.processes) == 1
    assert snap.processes[0].pid == 123


def test_telemetry_snapshot_flattening():
    snap = TelemetrySnapshot(
        system=SystemInfo(hostname="flat-host", uptime_seconds=100.0),
        resources=ResourceMetrics(
            cpu=CpuMetrics(usage_percent=25.0),
            memory=MemoryMetrics(used_mb=4096.0, usage_percent=50.0),
            swap=SwapMetrics(usage_percent=5.0),
        )
    )
    flat = snap.to_flat_dict()
    assert flat["hostname"] == "flat-host"
    assert flat["cpu_percent"] == 25.0
    assert flat["memory_percent"] == 50.0
    assert flat["memory_used_mb"] == 4096.0


def test_telemetry_buffer_capacity_and_eviction():
    buf = TelemetryBuffer(capacity=3)
    assert len(buf) == 0

    m1 = ResourceMetrics(cpu=CpuMetrics(usage_percent=10.0))
    m2 = ResourceMetrics(cpu=CpuMetrics(usage_percent=20.0))
    m3 = ResourceMetrics(cpu=CpuMetrics(usage_percent=30.0))
    m4 = ResourceMetrics(cpu=CpuMetrics(usage_percent=40.0))

    buf.append(m1)
    buf.append(m2)
    buf.append(m3)
    assert len(buf) == 3

    # Adding 4th item should evict m1
    buf.append(m4)
    assert len(buf) == 3
    items = buf.get_all()
    assert items[0].cpu.usage_percent == 20.0
    assert items[2].cpu.usage_percent == 40.0


def test_telemetry_buffer_to_dataframe():
    buf = TelemetryBuffer(capacity=10)
    now = datetime.now(timezone.utc)

    for i in range(5):
        buf.append(
            ResourceMetrics(
                timestamp=now + timedelta(seconds=i),
                cpu=CpuMetrics(usage_percent=10.0 * i),
                memory=MemoryMetrics(usage_percent=20.0, used_mb=1024.0 * i),
                swap=SwapMetrics(usage_percent=0.0),
            )
        )

    df = buf.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "cpu_usage_percent" in df.columns
    assert "memory_usage_percent" in df.columns
    assert "memory_used_mb" in df.columns
    assert df["cpu_usage_percent"].iloc[-1] == 40.0


def test_telemetry_buffer_clear():
    buf = TelemetryBuffer(capacity=5)
    buf.append(ResourceMetrics())
    assert len(buf) == 1
    buf.clear()
    assert len(buf) == 0
