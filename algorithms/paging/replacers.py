"""
Page Replacement Algorithm Implementations: FIFO, LRU, Optimal, Clock.
Includes Belady's Anomaly detection utility.
"""

from collections import deque
from typing import List, Optional, Dict, Any

from algorithms.paging.base import StepRecord, PagingResult, BasePageReplacer


class FIFOPageReplacer(BasePageReplacer):
    """First-In, First-Out (FIFO) Page Replacement Algorithm."""

    def __init__(self):
        super().__init__("First-In First-Out (FIFO)")

    def simulate(self, reference_string: List[int], num_frames: int) -> PagingResult:
        if num_frames <= 0:
            raise ValueError("Number of frames must be >= 1.")

        frames: List[Optional[int]] = [None] * num_frames
        fifo_queue: deque = deque()
        steps: List[StepRecord] = []

        for step_idx, page in enumerate(reference_string):
            if page in frames:
                # Page Hit
                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=True,
                    )
                )
            else:
                # Page Fault
                victim = None
                mod_idx = None

                if None in frames:
                    # Place in first available empty frame
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    fifo_queue.append((page, empty_idx))
                    mod_idx = empty_idx
                else:
                    # Evict oldest from FIFO queue
                    victim, victim_idx = fifo_queue.popleft()
                    frames[victim_idx] = page
                    fifo_queue.append((page, victim_idx))
                    mod_idx = victim_idx

                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=False,
                        victim_page=victim,
                        frame_index_modified=mod_idx,
                    )
                )

        res = PagingResult(self.name, reference_string, num_frames, steps)
        res.calculate_metrics()
        return res


class LRUPageReplacer(BasePageReplacer):
    """Least Recently Used (LRU) Page Replacement Algorithm."""

    def __init__(self):
        super().__init__("Least Recently Used (LRU)")

    def simulate(self, reference_string: List[int], num_frames: int) -> PagingResult:
        if num_frames <= 0:
            raise ValueError("Number of frames must be >= 1.")

        frames: List[Optional[int]] = [None] * num_frames
        last_accessed: Dict[int, int] = {}
        steps: List[StepRecord] = []

        for step_idx, page in enumerate(reference_string):
            last_accessed[page] = step_idx

            if page in frames:
                # Page Hit
                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=True,
                    )
                )
            else:
                # Page Fault
                victim = None
                mod_idx = None

                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    mod_idx = empty_idx
                else:
                    # Evict page in frames with minimum last_accessed time
                    victim = min(
                        [p for p in frames if p is not None],
                        key=lambda p: last_accessed.get(p, -1),
                    )
                    victim_idx = frames.index(victim)
                    frames[victim_idx] = page
                    mod_idx = victim_idx

                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=False,
                        victim_page=victim,
                        frame_index_modified=mod_idx,
                    )
                )

        res = PagingResult(self.name, reference_string, num_frames, steps)
        res.calculate_metrics()
        return res


class OptimalPageReplacer(BasePageReplacer):
    """Optimal (OPT / Belady's Min) Page Replacement Algorithm."""

    def __init__(self):
        super().__init__("Optimal (OPT / Belady's Min)")

    def simulate(self, reference_string: List[int], num_frames: int) -> PagingResult:
        if num_frames <= 0:
            raise ValueError("Number of frames must be >= 1.")

        frames: List[Optional[int]] = [None] * num_frames
        steps: List[StepRecord] = []
        n = len(reference_string)

        for step_idx, page in enumerate(reference_string):
            if page in frames:
                # Page Hit
                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=True,
                    )
                )
            else:
                # Page Fault
                victim = None
                mod_idx = None

                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    mod_idx = empty_idx
                else:
                    # Look ahead to find page not used for longest time into the future
                    future_refs = reference_string[step_idx + 1 :]
                    victim_candidate = None
                    furthest_next_use = -1

                    for f_page in frames:
                        if f_page is None:
                            continue
                        if f_page not in future_refs:
                            # Not used again in the future! Immediate best candidate
                            victim_candidate = f_page
                            break
                        else:
                            next_use_idx = future_refs.index(f_page)
                            if next_use_idx > furthest_next_use:
                                furthest_next_use = next_use_idx
                                victim_candidate = f_page

                    victim = victim_candidate
                    victim_idx = frames.index(victim)
                    frames[victim_idx] = page
                    mod_idx = victim_idx

                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=False,
                        victim_page=victim,
                        frame_index_modified=mod_idx,
                    )
                )

        res = PagingResult(self.name, reference_string, num_frames, steps)
        res.calculate_metrics()
        return res


class ClockPageReplacer(BasePageReplacer):
    """Clock (Second Chance) Page Replacement Algorithm."""

    def __init__(self):
        super().__init__("Clock (Second Chance)")

    def simulate(self, reference_string: List[int], num_frames: int) -> PagingResult:
        if num_frames <= 0:
            raise ValueError("Number of frames must be >= 1.")

        frames: List[Optional[int]] = [None] * num_frames
        use_bits: List[int] = [0] * num_frames
        pointer: int = 0
        steps: List[StepRecord] = []

        for step_idx, page in enumerate(reference_string):
            if page in frames:
                # Page Hit - set reference bit to 1
                hit_idx = frames.index(page)
                use_bits[hit_idx] = 1
                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=True,
                    )
                )
            else:
                # Page Fault
                victim = None
                mod_idx = None

                if None in frames:
                    empty_idx = frames.index(None)
                    frames[empty_idx] = page
                    use_bits[empty_idx] = 1
                    mod_idx = empty_idx
                else:
                    # Scan clock hand until bit 0 is found
                    while True:
                        if use_bits[pointer] == 0:
                            # Replace this frame
                            victim = frames[pointer]
                            frames[pointer] = page
                            use_bits[pointer] = 1
                            mod_idx = pointer
                            pointer = (pointer + 1) % num_frames
                            break
                        else:
                            # Second chance: reset bit to 0 and advance pointer
                            use_bits[pointer] = 0
                            pointer = (pointer + 1) % num_frames

                steps.append(
                    StepRecord(
                        step=step_idx + 1,
                        page=page,
                        frames=list(frames),
                        is_hit=False,
                        victim_page=victim,
                        frame_index_modified=mod_idx,
                    )
                )

        res = PagingResult(self.name, reference_string, num_frames, steps)
        res.calculate_metrics()
        return res


def detect_belady_anomaly(
    reference_string: List[int],
    min_frames: int = 2,
    max_frames: int = 6,
) -> Dict[str, Any]:
    """
    Evaluates FIFO page replacement across increasing frame capacities to detect
    instances where increasing physical frames causes an INCREASE in page faults.
    """
    fifo = FIFOPageReplacer()
    frame_faults: Dict[int, int] = {}
    anomaly_detected = False
    anomaly_points = []

    prev_faults = None
    for f in range(min_frames, max_frames + 1):
        res = fifo.simulate(reference_string, f)
        frame_faults[f] = res.page_faults
        if prev_faults is not None and res.page_faults > prev_faults:
            anomaly_detected = True
            anomaly_points.append({"from_frames": f - 1, "to_frames": f, "faults_before": prev_faults, "faults_after": res.page_faults})
        prev_faults = res.page_faults

    return {
        "anomaly_detected": anomaly_detected,
        "frame_faults": frame_faults,
        "anomaly_points": anomaly_points,
    }
