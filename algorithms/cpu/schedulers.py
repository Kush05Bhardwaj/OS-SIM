"""
Core CPU Scheduling Algorithms
Implementations of FCFS, SJF, SRTF, Round Robin, Priority, and MLFQ.
"""

from collections import deque
from typing import List, Optional, Dict, Any

from algorithms.cpu.base import Process, TimelineSlice, ScheduleResult, BaseScheduler


class FCFSScheduler(BaseScheduler):
    """First-Come, First-Served (FCFS) Non-Preemptive Scheduler."""

    def __init__(self):
        super().__init__("First-Come, First-Served (FCFS)")

    def schedule(self, processes: List[Process], **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        procs = [p.copy() for p in sorted(processes, key=lambda p: (p.arrival_time, p.pid))]
        current_time = 0
        timeline: List[TimelineSlice] = []
        idle_time = 0

        for p in procs:
            if current_time < p.arrival_time:
                gap = p.arrival_time - current_time
                timeline.append(TimelineSlice(current_time, p.arrival_time, "IDLE", "IDLE"))
                idle_time += gap
                current_time = p.arrival_time

            p.start_time = current_time
            current_time += p.burst_time
            p.completion_time = current_time
            p.remaining_time = 0
            timeline.append(TimelineSlice(p.start_time, p.completion_time, p.pid, "RUNNING"))

        res = ScheduleResult(
            algorithm_name=self.name,
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res


class SJFScheduler(BaseScheduler):
    """Shortest Job First (SJF) Non-Preemptive Scheduler."""

    def __init__(self):
        super().__init__("Shortest Job First (SJF - Non-Preemptive)")

    def schedule(self, processes: List[Process], **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        procs = [p.copy() for p in processes]
        uncompleted = list(procs)
        current_time = 0
        timeline: List[TimelineSlice] = []
        idle_time = 0

        while uncompleted:
            available = [p for p in uncompleted if p.arrival_time <= current_time]

            if not available:
                next_arr = min(p.arrival_time for p in uncompleted)
                timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                idle_time += (next_arr - current_time)
                current_time = next_arr
                continue

            # Pick shortest burst time; tie break by arrival time then PID
            best = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
            best.start_time = current_time
            current_time += best.burst_time
            best.completion_time = current_time
            best.remaining_time = 0

            timeline.append(TimelineSlice(best.start_time, best.completion_time, best.pid, "RUNNING"))
            uncompleted.remove(best)

        res = ScheduleResult(
            algorithm_name=self.name,
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res


class SRTFScheduler(BaseScheduler):
    """Shortest Remaining Time First (SRTF) Preemptive Scheduler."""

    def __init__(self):
        super().__init__("Shortest Remaining Time First (SRTF - Preemptive)")

    def schedule(self, processes: List[Process], **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        procs = [p.copy() for p in processes]
        current_time = 0
        completed = 0
        n = len(procs)
        timeline: List[TimelineSlice] = []
        idle_time = 0

        while completed < n:
            available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]

            if not available:
                unstarted = [p for p in procs if p.remaining_time > 0]
                next_arr = min(p.arrival_time for p in unstarted)
                timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                idle_time += (next_arr - current_time)
                current_time = next_arr
                continue

            best = min(available, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
            if best.start_time is None:
                best.start_time = current_time

            # Advance by 1 time unit
            timeline.append(TimelineSlice(current_time, current_time + 1, best.pid, "RUNNING"))
            best.remaining_time -= 1
            current_time += 1

            if best.remaining_time == 0:
                best.completion_time = current_time
                completed += 1

        res = ScheduleResult(
            algorithm_name=self.name,
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res


class RoundRobinScheduler(BaseScheduler):
    """Round Robin (RR) Preemptive Scheduler with configurable time quantum."""

    def __init__(self, quantum: int = 2):
        super().__init__(f"Round Robin (RR, q={quantum})")
        self.quantum = max(1, quantum)

    def schedule(self, processes: List[Process], quantum: Optional[int] = None, **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        q = quantum or self.quantum
        procs = [p.copy() for p in sorted(processes, key=lambda p: (p.arrival_time, p.pid))]
        queue: deque = deque()
        timeline: List[TimelineSlice] = []
        current_time = 0
        idle_time = 0

        unentered = list(procs)
        completed = 0
        n = len(procs)

        while completed < n:
            # Enqueue any processes that have arrived by current_time
            arrived = [p for p in unentered if p.arrival_time <= current_time]
            for p in arrived:
                queue.append(p)
                unentered.remove(p)

            if not queue:
                if unentered:
                    next_arr = min(p.arrival_time for p in unentered)
                    timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                    idle_time += (next_arr - current_time)
                    current_time = next_arr
                    continue
                else:
                    break

            current_proc = queue.popleft()
            if current_proc.start_time is None:
                current_proc.start_time = current_time

            exec_time = min(q, current_proc.remaining_time)
            timeline.append(TimelineSlice(current_time, current_time + exec_time, current_proc.pid, "RUNNING"))
            current_time += exec_time
            current_proc.remaining_time -= exec_time

            # Before re-enqueueing the current process, enqueue newly arrived processes during this slice
            newly_arrived = [p for p in unentered if p.arrival_time <= current_time]
            for p in newly_arrived:
                queue.append(p)
                unentered.remove(p)

            if current_proc.remaining_time > 0:
                queue.append(current_proc)
            else:
                current_proc.completion_time = current_time
                completed += 1

        res = ScheduleResult(
            algorithm_name=f"Round Robin (RR, q={q})",
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res


class PriorityScheduler(BaseScheduler):
    """Priority Scheduler supporting both Preemptive and Non-Preemptive variants."""

    def __init__(self, preemptive: bool = False):
        kind = "Preemptive" if preemptive else "Non-Preemptive"
        super().__init__(f"Priority Scheduling ({kind})")
        self.preemptive = preemptive

    def schedule(self, processes: List[Process], preemptive: Optional[bool] = None, **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        is_preempt = self.preemptive if preemptive is None else preemptive
        procs = [p.copy() for p in processes]
        current_time = 0
        timeline: List[TimelineSlice] = []
        idle_time = 0
        n = len(procs)

        if not is_preempt:
            uncompleted = list(procs)
            while uncompleted:
                available = [p for p in uncompleted if p.arrival_time <= current_time]
                if not available:
                    next_arr = min(p.arrival_time for p in uncompleted)
                    timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                    idle_time += (next_arr - current_time)
                    current_time = next_arr
                    continue

                best = min(available, key=lambda p: (p.priority, p.arrival_time, p.pid))
                best.start_time = current_time
                current_time += best.burst_time
                best.completion_time = current_time
                best.remaining_time = 0
                timeline.append(TimelineSlice(best.start_time, best.completion_time, best.pid, "RUNNING"))
                uncompleted.remove(best)
        else:
            completed = 0
            while completed < n:
                available = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]
                if not available:
                    unstarted = [p for p in procs if p.remaining_time > 0]
                    next_arr = min(p.arrival_time for p in unstarted)
                    timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                    idle_time += (next_arr - current_time)
                    current_time = next_arr
                    continue

                best = min(available, key=lambda p: (p.priority, p.remaining_time, p.arrival_time, p.pid))
                if best.start_time is None:
                    best.start_time = current_time

                timeline.append(TimelineSlice(current_time, current_time + 1, best.pid, "RUNNING"))
                best.remaining_time -= 1
                current_time += 1

                if best.remaining_time == 0:
                    best.completion_time = current_time
                    completed += 1

        res = ScheduleResult(
            algorithm_name=self.name,
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res


class MLFQScheduler(BaseScheduler):
    """
    Multi-Level Feedback Queue (MLFQ) Scheduler.
    3 Queues:
      Q0: RR with quantum q0 (highest priority)
      Q1: RR with quantum q1
      Q2: FCFS (lowest priority)
    With anti-starvation aging.
    """

    def __init__(self, q0: int = 2, q1: int = 4, aging_threshold: int = 20):
        super().__init__(f"Multi-Level Feedback Queue (MLFQ: q0={q0}, q1={q1})")
        self.q0 = max(1, q0)
        self.q1 = max(1, q1)
        self.aging_threshold = aging_threshold

    def schedule(self, processes: List[Process], **kwargs) -> ScheduleResult:
        if not processes:
            return ScheduleResult(self.name, [], [])

        procs = [p.copy() for p in sorted(processes, key=lambda p: (p.arrival_time, p.pid))]
        queue0: deque = deque()
        queue1: deque = deque()
        queue2: deque = deque()

        unentered = list(procs)
        wait_tracker: Dict[str, int] = {p.pid: 0 for p in procs}

        current_time = 0
        timeline: List[TimelineSlice] = []
        idle_time = 0
        completed = 0
        n = len(procs)

        while completed < n:
            # Enqueue arrivals into top queue (Q0)
            arrived = [p for p in unentered if p.arrival_time <= current_time]
            for p in arrived:
                queue0.append(p)
                unentered.remove(p)

            # Aging: promote waiting processes from lower queues if they waited >= aging_threshold
            if self.aging_threshold > 0:
                aged_from_q2 = [p for p in list(queue2) if (current_time - wait_tracker[p.pid]) >= self.aging_threshold]
                for p in aged_from_q2:
                    queue2.remove(p)
                    queue1.append(p)
                    wait_tracker[p.pid] = current_time

                aged_from_q1 = [p for p in list(queue1) if (current_time - wait_tracker[p.pid]) >= self.aging_threshold]
                for p in aged_from_q1:
                    queue1.remove(p)
                    queue0.append(p)
                    wait_tracker[p.pid] = current_time

            # Select queue to run
            target_q = None
            quantum = 1
            is_fcfs = False

            if queue0:
                target_q = queue0
                quantum = self.q0
            elif queue1:
                target_q = queue1
                quantum = self.q1
            elif queue2:
                target_q = queue2
                quantum = 999999
                is_fcfs = True
            else:
                if unentered:
                    next_arr = min(p.arrival_time for p in unentered)
                    timeline.append(TimelineSlice(current_time, next_arr, "IDLE", "IDLE"))
                    idle_time += (next_arr - current_time)
                    current_time = next_arr
                    continue
                else:
                    break

            proc = target_q.popleft()
            if proc.start_time is None:
                proc.start_time = current_time

            exec_time = min(quantum, proc.remaining_time)
            timeline.append(TimelineSlice(current_time, current_time + exec_time, proc.pid, "RUNNING"))
            current_time += exec_time
            proc.remaining_time -= exec_time

            # Check new arrivals before demoting
            newly_arrived = [p for p in unentered if p.arrival_time <= current_time]
            for p in newly_arrived:
                queue0.append(p)
                unentered.remove(p)

            if proc.remaining_time > 0:
                wait_tracker[proc.pid] = current_time
                # Demote to next queue if quantum exhausted
                if target_q is queue0:
                    queue1.append(proc)
                elif target_q is queue1:
                    queue2.append(proc)
                else:
                    queue2.append(proc)
            else:
                proc.completion_time = current_time
                completed += 1

        res = ScheduleResult(
            algorithm_name=self.name,
            timeline=self._compact_timeline(timeline),
            processes=procs,
            total_time=current_time,
            idle_time=idle_time,
        )
        res.calculate_metrics()
        return res
