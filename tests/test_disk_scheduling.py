"""
Unit tests for Disk Scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK).
"""

import pytest
from algorithms.disk.schedulers import (
    FCFSDiskScheduler,
    SSTFDiskScheduler,
    SCANDiskScheduler,
    CSCANDiskScheduler,
    LOOKDiskScheduler,
    CLOOKDiskScheduler,
)

# Classic Silberschatz textbook cylinder requests
TEXTBOOK_REQUESTS = [98, 183, 37, 122, 14, 124, 65, 67]
INITIAL_HEAD = 53
CYLINDER_MAX = 199


def test_fcfs_disk():
    scheduler = FCFSDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 98, 183, 37, 122, 14, 124, 65, 67]
    assert res.total_head_movement == 640


def test_sstf_disk():
    scheduler = SSTFDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 65, 67, 37, 14, 98, 122, 124, 183]
    assert res.total_head_movement == 236


def test_scan_disk():
    scheduler = SCANDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, direction="RIGHT", cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 65, 67, 98, 122, 124, 183, 199, 37, 14]
    assert res.total_head_movement == 331


def test_cscan_disk():
    scheduler = CSCANDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, direction="RIGHT", cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 65, 67, 98, 122, 124, 183, 199, 0, 14, 37]
    assert res.total_head_movement == 382


def test_look_disk():
    scheduler = LOOKDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, direction="RIGHT", cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 65, 67, 98, 122, 124, 183, 37, 14]
    assert res.total_head_movement == 299


def test_clook_disk():
    scheduler = CLOOKDiskScheduler()
    res = scheduler.schedule(TEXTBOOK_REQUESTS, initial_head=INITIAL_HEAD, direction="RIGHT", cylinder_max=CYLINDER_MAX)

    assert res.seek_sequence == [53, 65, 67, 98, 122, 124, 183, 14, 37]
    assert res.total_head_movement == 322


def test_empty_requests():
    scheduler = FCFSDiskScheduler()
    res = scheduler.schedule([], initial_head=50)
    assert res.total_head_movement == 0
    assert res.seek_sequence == [50]
