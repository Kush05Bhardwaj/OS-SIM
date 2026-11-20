"""
Unit and integration tests for Deadlock Management (Banker's Algorithm & Deadlock Detection).
"""

import pytest

from algorithms.deadlock.base import DeadlockState
from algorithms.deadlock.banker import BankerAlgorithm
from algorithms.deadlock.detection import DeadlockDetector


def get_silberschatz_state() -> DeadlockState:
    """Standard 5-process, 3-resource safe textbook scenario."""
    processes = ["P0", "P1", "P2", "P3", "P4"]
    resources = ["A", "B", "C"]
    allocation = {
        "P0": {"A": 0, "B": 1, "C": 0},
        "P1": {"A": 2, "B": 0, "C": 0},
        "P2": {"A": 3, "B": 0, "C": 2},
        "P3": {"A": 2, "B": 1, "C": 1},
        "P4": {"A": 0, "B": 0, "C": 2},
    }
    max_matrix = {
        "P0": {"A": 7, "B": 5, "C": 3},
        "P1": {"A": 3, "B": 2, "C": 2},
        "P2": {"A": 9, "B": 0, "C": 2},
        "P3": {"A": 2, "B": 2, "C": 2},
        "P4": {"A": 4, "B": 3, "C": 3},
    }
    available = {"A": 3, "B": 3, "C": 2}

    return DeadlockState(
        processes=processes,
        resources=resources,
        allocation=allocation,
        max_matrix=max_matrix,
        available=available,
    )


def test_banker_safety_silberschatz_safe():
    state = get_silberschatz_state()
    banker = BankerAlgorithm(state)

    need = banker.get_need_matrix()
    assert need["P0"] == {"A": 7, "B": 4, "C": 3}
    assert need["P1"] == {"A": 1, "B": 2, "C": 2}
    assert need["P3"] == {"A": 0, "B": 1, "C": 1}

    result = banker.check_safety()
    assert result.is_safe is True
    assert len(result.safe_sequence) == 5
    assert len(result.steps) == 5
    assert result.safe_sequence[0] in ["P1", "P3"]
    assert len(result.unresolved_processes) == 0


def test_banker_safety_unsafe_scenario():
    state = get_silberschatz_state()
    # Starve available resources so no process can run
    state.available = {"A": 0, "B": 0, "C": 0}
    banker = BankerAlgorithm(state)

    result = banker.check_safety()
    assert result.is_safe is False
    assert len(result.safe_sequence) == 0
    assert len(result.unresolved_processes) == 5
    assert "UNSAFE state" in result.message


def test_banker_request_granted():
    state = get_silberschatz_state()
    banker = BankerAlgorithm(state)

    # P1 requests [1, 0, 2]
    req = {"A": 1, "B": 0, "C": 2}
    result = banker.request_resources("P1", req)

    assert result.granted is True
    assert "GRANTED" in result.reason
    assert banker.state.available["A"] == 2
    assert banker.state.available["B"] == 3
    assert banker.state.available["C"] == 0
    assert banker.state.allocation["P1"]["A"] == 3
    assert banker.state.allocation["P1"]["C"] == 2


def test_banker_request_exceeds_need():
    state = get_silberschatz_state()
    banker = BankerAlgorithm(state)

    # P1 max need for A is 1; request 4
    req = {"A": 4, "B": 0, "C": 0}
    result = banker.request_resources("P1", req)

    assert result.granted is False
    assert "exceeded its maximum claim" in result.reason


def test_banker_request_insufficient_available():
    state = get_silberschatz_state()
    banker = BankerAlgorithm(state)

    # Available has A=3; P0 needs 7, requests 5
    req = {"A": 5, "B": 0, "C": 0}
    result = banker.request_resources("P0", req)

    assert result.granted is False
    assert "Insufficient available resources" in result.reason


def test_banker_request_leads_to_unsafe_state():
    state = get_silberschatz_state()
    banker = BankerAlgorithm(state)

    # P4 requests [3, 3, 0].
    # Need for P4 is [4, 3, 1], Available is [3, 3, 2].
    # Request <= Need and Request <= Available.
    # However, granting this leaves Available [0, 0, 2], which cannot satisfy
    # any process's need (all require at least A>=1 or B>=1).
    req = {"A": 3, "B": 3, "C": 0}
    result = banker.request_resources("P4", req)

    assert result.granted is False
    assert "UNSAFE state" in result.reason
    # Verify rollback: state should remain untouched
    assert banker.state.available["A"] == 3
    assert banker.state.available["B"] == 3
    assert banker.state.allocation["P4"]["A"] == 0


def test_banker_invalid_state_validation():
    state = get_silberschatz_state()
    # Allocation > Max
    state.allocation["P0"]["A"] = 10
    state.max_matrix["P0"]["A"] = 5

    with pytest.raises(ValueError, match="exceeds Max"):
        BankerAlgorithm(state)

    # Negative available
    state = get_silberschatz_state()
    state.available["A"] = -1
    with pytest.raises(ValueError, match="cannot be negative"):
        BankerAlgorithm(state)


def test_deadlock_detection_matrices_no_deadlock():
    processes = ["P0", "P1", "P2"]
    resources = ["A", "B"]
    allocation = {
        "P0": {"A": 1, "B": 0},
        "P1": {"A": 0, "B": 1},
        "P2": {"A": 0, "B": 0},
    }
    request = {
        "P0": {"A": 0, "B": 1},
        "P1": {"A": 0, "B": 0},
        "P2": {"A": 0, "B": 0},
    }
    available = {"A": 0, "B": 1}

    detector = DeadlockDetector(processes, resources, allocation, request, available)
    res = detector.detect_matrix()

    assert res.has_deadlock is False
    assert len(res.deadlocked_processes) == 0
    assert len(res.safe_processes) == 3


def test_deadlock_detection_matrices_with_deadlock():
    processes = ["P0", "P1", "P2"]
    resources = ["A", "B"]
    allocation = {
        "P0": {"A": 1, "B": 0},
        "P1": {"A": 0, "B": 1},
        "P2": {"A": 1, "B": 1},
    }
    request = {
        "P0": {"A": 0, "B": 1},  # P0 holds A, waits for B (held by P1)
        "P1": {"A": 1, "B": 0},  # P1 holds B, waits for A (held by P0)
        "P2": {"A": 2, "B": 2},  # P2 needs 2 of A and B, neither available
    }
    available = {"A": 0, "B": 0}

    detector = DeadlockDetector(processes, resources, allocation, request, available)
    res = detector.detect_matrix()

    assert res.has_deadlock is True
    assert "P0" in res.deadlocked_processes
    assert "P1" in res.deadlocked_processes
    assert "P2" in res.deadlocked_processes
    assert len(res.cycles) > 0


def test_find_cycles_in_graph():
    # Cyclic: P1 -> P2 -> P3 -> P1
    edges = [("P1", "P2"), ("P2", "P3"), ("P3", "P1"), ("P4", "P1")]
    cycles = DeadlockDetector.find_cycles_in_graph(edges)

    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle == ["P1", "P2", "P3", "P1"]

    # Acyclic
    acyclic_edges = [("P1", "P2"), ("P2", "P3"), ("P1", "P3")]
    no_cycles = DeadlockDetector.find_cycles_in_graph(acyclic_edges)
    assert len(no_cycles) == 0


def test_deadlock_dashboard_helpers():
    from dashboard.deadlock_view import PRESETS, build_wfg_figure

    assert "Silberschatz Textbook (Safe State)" in PRESETS
    assert "Resource-Constrained (Unsafe / Deadlock)" in PRESETS
    assert "Cyclic Dependency Deadlock (WFG)" in PRESETS

    fig = build_wfg_figure(
        processes=["P0", "P1", "P2"],
        edges=[("P0", "P1"), ("P1", "P0")],
        deadlocked=["P0", "P1"],
    )
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter"

