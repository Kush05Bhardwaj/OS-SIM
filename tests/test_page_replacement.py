"""
Unit tests for Page Replacement algorithms (FIFO, LRU, Optimal, Clock) and Belady's Anomaly detection.
"""

import pytest
from algorithms.paging.replacers import (
    FIFOPageReplacer,
    LRUPageReplacer,
    OptimalPageReplacer,
    ClockPageReplacer,
    detect_belady_anomaly,
)

# Classic Silberschatz textbook reference string
TEXTBOOK_REFS = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]


def test_fifo_textbook_trace():
    replacer = FIFOPageReplacer()
    res = replacer.simulate(TEXTBOOK_REFS, num_frames=3)

    assert res.total_requests == 20
    assert res.page_faults == 15
    assert res.page_hits == 5
    assert res.fault_rate == 75.0
    assert res.hit_rate == 25.0
    assert len(res.steps) == 20


def test_lru_textbook_trace():
    replacer = LRUPageReplacer()
    res = replacer.simulate(TEXTBOOK_REFS, num_frames=3)

    assert res.total_requests == 20
    assert res.page_faults == 12
    assert res.page_hits == 8
    assert res.fault_rate == 60.0
    assert res.hit_rate == 40.0


def test_optimal_textbook_trace():
    replacer = OptimalPageReplacer()
    res = replacer.simulate(TEXTBOOK_REFS, num_frames=3)

    assert res.total_requests == 20
    assert res.page_faults == 9
    assert res.page_hits == 11
    assert res.fault_rate == 45.0
    assert res.hit_rate == 55.0


def test_clock_page_replacement():
    replacer = ClockPageReplacer()
    res = replacer.simulate(TEXTBOOK_REFS, num_frames=3)

    assert res.total_requests == 20
    assert res.page_faults > 0
    assert res.page_faults + res.page_hits == 20
    assert round(res.fault_rate + res.hit_rate, 1) == 100.0


def test_belady_anomaly_detection():
    # Classic Belady reference string: [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    belady_refs = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    analysis = detect_belady_anomaly(belady_refs, min_frames=3, max_frames=4)

    assert analysis["anomaly_detected"] is True
    assert analysis["frame_faults"][3] == 9
    assert analysis["frame_faults"][4] == 10
    assert len(analysis["anomaly_points"]) == 1
    assert analysis["anomaly_points"][0]["faults_before"] == 9
    assert analysis["anomaly_points"][0]["faults_after"] == 10


def test_invalid_frame_count():
    replacer = FIFOPageReplacer()
    with pytest.raises(ValueError):
        replacer.simulate([1, 2, 3], num_frames=0)
