"""
Unit tests for CPU Scheduling algorithms (FCFS, SJF, SRTF, RR, Priority, MLFQ).
"""

import pytest
from algorithms.cpu.base import Process, TimelineSlice, ScheduleResult
from algorithms.cpu.schedulers import (
    FCFSScheduler,
    SJFScheduler,
    SRTFScheduler,
    RoundRobinScheduler,
    PriorityScheduler,
    MLFQScheduler,
)


def test_fcfs_basic():
    # P1: AT=0, BT=4; P2: AT=1, BT=3; P3: AT=2, BT=1
    procs = [
        Process("P1", arrival_time=0, burst_time=4),
        Process("P2", arrival_time=1, burst_time=3),
        Process("P3", arrival_time=2, burst_time=1),
    ]
    scheduler = FCFSScheduler()
    res = scheduler.schedule(procs)

    assert res.total_time == 8
    assert res.idle_time == 0

    p_map = {p.pid: p for p in res.processes}
    assert p_map["P1"].completion_time == 4
    assert p_map["P2"].completion_time == 7
    assert p_map["P3"].completion_time == 8

    assert p_map["P1"].waiting_time == 0
    assert p_map["P2"].waiting_time == 3
    assert p_map["P3"].waiting_time == 5

    assert res.avg_waiting_time == 2.67
    assert res.avg_turnaround_time == 5.33


def test_sjf_non_preemptive():
    # P1(0, 7), P2(2, 4), P3(4, 1), P4(5, 4)
    procs = [
        Process("P1", 0, 7),
        Process("P2", 2, 4),
        Process("P3", 4, 1),
        Process("P4", 5, 4),
    ]
    scheduler = SJFScheduler()
    res = scheduler.schedule(procs)

    p_map = {p.pid: p for p in res.processes}
    assert p_map["P1"].completion_time == 7
    assert p_map["P3"].completion_time == 8
    assert p_map["P2"].completion_time == 12
    assert p_map["P4"].completion_time == 16


def test_srtf_preemptive():
    # P1(0, 8), P2(1, 4), P3(2, 9), P4(3, 5)
    procs = [
        Process("P1", 0, 8),
        Process("P2", 1, 4),
        Process("P3", 2, 9),
        Process("P4", 3, 5),
    ]
    scheduler = SRTFScheduler()
    res = scheduler.schedule(procs)

    p_map = {p.pid: p for p in res.processes}
    assert p_map["P2"].completion_time == 5
    assert res.total_time == 26


def test_round_robin():
    # Quantum = 2
    procs = [
        Process("P1", 0, 5),
        Process("P2", 1, 3),
        Process("P3", 2, 1),
    ]
    scheduler = RoundRobinScheduler(quantum=2)
    res = scheduler.schedule(procs)

    p_map = {p.pid: p for p in res.processes}
    assert p_map["P3"].completion_time == 5
    assert p_map["P2"].completion_time == 8
    assert p_map["P1"].completion_time == 9
    assert res.total_time == 9


def test_priority_non_preemptive():
    # Lower number = higher priority
    procs = [
        Process("P1", arrival_time=0, burst_time=4, priority=3),
        Process("P2", arrival_time=1, burst_time=3, priority=1),
        Process("P3", arrival_time=2, burst_time=2, priority=2),
    ]
    scheduler = PriorityScheduler(preemptive=False)
    res = scheduler.schedule(procs)

    p_map = {p.pid: p for p in res.processes}
    # P1 runs 0-4
    assert p_map["P1"].completion_time == 4
    # P2 (priority 1) runs next: 4-7
    assert p_map["P2"].completion_time == 7
    # P3 (priority 2) runs next: 7-9
    assert p_map["P3"].completion_time == 9


def test_priority_preemptive():
    procs = [
        Process("P1", arrival_time=0, burst_time=8, priority=3),
        Process("P2", arrival_time=2, burst_time=2, priority=1),
    ]
    scheduler = PriorityScheduler(preemptive=True)
    res = scheduler.schedule(procs)

    p_map = {p.pid: p for p in res.processes}
    # P1 starts at 0, preempted at 2 by P2, P2 runs 2-4, P1 finishes 4-10
    assert p_map["P2"].completion_time == 4
    assert p_map["P1"].completion_time == 10


def test_mlfq_scheduling():
    procs = [
        Process("P1", arrival_time=0, burst_time=10),
        Process("P2", arrival_time=1, burst_time=4),
    ]
    scheduler = MLFQScheduler(q0=2, q1=4)
    res = scheduler.schedule(procs)

    assert res.total_time == 14
    p_map = {p.pid: p for p in res.processes}
    assert p_map["P1"].completion_time > 0
    assert p_map["P2"].completion_time > 0


def test_idle_gaps_in_schedule():
    procs = [
        Process("P1", arrival_time=0, burst_time=2),
        Process("P2", arrival_time=5, burst_time=2),
    ]
    scheduler = FCFSScheduler()
    res = scheduler.schedule(procs)

    assert res.total_time == 7
    assert res.idle_time == 3
    assert any(s.pid == "IDLE" for s in res.timeline)


def test_empty_process_list():
    scheduler = FCFSScheduler()
    res = scheduler.schedule([])
    assert len(res.timeline) == 0
    assert res.total_time == 0
