"""
Disk Arm Scheduling Algorithms: FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK.
"""

from typing import List, Optional, Dict, Any
from algorithms.disk.base import DiskScheduleResult, BaseDiskScheduler


class FCFSDiskScheduler(BaseDiskScheduler):
    """First-Come, First-Served Disk Scheduling."""

    def __init__(self):
        super().__init__("First-Come, First-Served (FCFS)")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        seek_sequence = [initial_head] + list(requests)
        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res


class SSTFDiskScheduler(BaseDiskScheduler):
    """Shortest Seek Time First (SSTF) Disk Scheduling."""

    def __init__(self):
        super().__init__("Shortest Seek Time First (SSTF)")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        if not requests:
            res = DiskScheduleResult(self.name, initial_head, direction, [initial_head], cylinder_max=cylinder_max)
            res.calculate_metrics()
            return res

        pending = list(requests)
        current = initial_head
        seek_sequence = [current]

        while pending:
            closest = min(pending, key=lambda c: (abs(c - current), c))
            seek_sequence.append(closest)
            pending.remove(closest)
            current = closest

        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res


class SCANDiskScheduler(BaseDiskScheduler):
    """SCAN (Elevator) Disk Scheduling."""

    def __init__(self):
        super().__init__("SCAN (Elevator)")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        if not requests:
            res = DiskScheduleResult(self.name, initial_head, direction, [initial_head], cylinder_max=cylinder_max)
            res.calculate_metrics()
            return res

        dir_upper = direction.upper()
        left = sorted([r for r in requests if r < initial_head])
        right = sorted([r for r in requests if r >= initial_head])

        seek_sequence = [initial_head]

        if dir_upper == "RIGHT":
            # Go right up to cylinder_max, then reverse down
            seek_sequence.extend(right)
            if left:
                # Travel all the way to extreme right boundary if there are requests on the left
                if cylinder_max not in seek_sequence:
                    seek_sequence.append(cylinder_max)
                seek_sequence.extend(reversed(left))
        else:
            # Go left down to 0, then reverse right
            seek_sequence.extend(reversed(left))
            if right:
                if 0 not in seek_sequence:
                    seek_sequence.append(0)
                seek_sequence.extend(right)

        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res


class CSCANDiskScheduler(BaseDiskScheduler):
    """Circular SCAN (C-SCAN) Disk Scheduling."""

    def __init__(self):
        super().__init__("Circular SCAN (C-SCAN)")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        if not requests:
            res = DiskScheduleResult(self.name, initial_head, direction, [initial_head], cylinder_max=cylinder_max)
            res.calculate_metrics()
            return res

        dir_upper = direction.upper()
        left = sorted([r for r in requests if r < initial_head])
        right = sorted([r for r in requests if r >= initial_head])

        seek_sequence = [initial_head]

        if dir_upper == "RIGHT":
            seek_sequence.extend(right)
            if left:
                # Reach upper boundary, jump to 0, then service left in increasing order
                if cylinder_max not in seek_sequence:
                    seek_sequence.append(cylinder_max)
                if 0 not in seek_sequence:
                    seek_sequence.append(0)
                seek_sequence.extend(left)
        else:
            seek_sequence.extend(reversed(left))
            if right:
                if 0 not in seek_sequence:
                    seek_sequence.append(0)
                if cylinder_max not in seek_sequence:
                    seek_sequence.append(cylinder_max)
                seek_sequence.extend(reversed(right))

        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res


class LOOKDiskScheduler(BaseDiskScheduler):
    """LOOK Disk Scheduling (Reverses without travelling to disk ends)."""

    def __init__(self):
        super().__init__("LOOK")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        if not requests:
            res = DiskScheduleResult(self.name, initial_head, direction, [initial_head], cylinder_max=cylinder_max)
            res.calculate_metrics()
            return res

        dir_upper = direction.upper()
        left = sorted([r for r in requests if r < initial_head])
        right = sorted([r for r in requests if r >= initial_head])

        seek_sequence = [initial_head]

        if dir_upper == "RIGHT":
            seek_sequence.extend(right)
            seek_sequence.extend(reversed(left))
        else:
            seek_sequence.extend(reversed(left))
            seek_sequence.extend(right)

        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res


class CLOOKDiskScheduler(BaseDiskScheduler):
    """Circular LOOK (C-LOOK) Disk Scheduling."""

    def __init__(self):
        super().__init__("C-LOOK")

    def schedule(
        self,
        requests: List[int],
        initial_head: int = 50,
        direction: str = "RIGHT",
        cylinder_max: int = 199,
    ) -> DiskScheduleResult:
        if not requests:
            res = DiskScheduleResult(self.name, initial_head, direction, [initial_head], cylinder_max=cylinder_max)
            res.calculate_metrics()
            return res

        dir_upper = direction.upper()
        left = sorted([r for r in requests if r < initial_head])
        right = sorted([r for r in requests if r >= initial_head])

        seek_sequence = [initial_head]

        if dir_upper == "RIGHT":
            seek_sequence.extend(right)
            seek_sequence.extend(left)
        else:
            seek_sequence.extend(reversed(left))
            seek_sequence.extend(reversed(right))

        res = DiskScheduleResult(
            algorithm_name=self.name,
            initial_head=initial_head,
            direction=direction,
            seek_sequence=seek_sequence,
            cylinder_max=cylinder_max,
        )
        res.calculate_metrics()
        return res
