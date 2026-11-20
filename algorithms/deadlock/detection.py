"""
Deadlock Detection algorithms:
1. Multiple-instance matrix reduction algorithm.
2. Resource Allocation Graph (RAG) / Wait-For Graph (WFG) cycle detection.
"""

from typing import Dict, List, Set, Tuple
import copy

from algorithms.deadlock.base import (
    DetectionStep,
    DetectionResult,
)


class DeadlockDetector:
    """
    Implements multi-resource matrix reduction deadlock detection
    and Wait-For Graph (WFG) cycle detection.
    """

    def __init__(
        self,
        processes: List[str],
        resources: List[str],
        allocation: Dict[str, Dict[str, int]],
        request: Dict[str, Dict[str, int]],
        available: Dict[str, int],
    ):
        self.processes = processes
        self.resources = resources
        self.allocation = copy.deepcopy(allocation)
        self.request = copy.deepcopy(request)
        self.available = copy.deepcopy(available)

    def detect_matrix(self) -> DetectionResult:
        """
        Multi-resource instance deadlock detection algorithm (Silberschatz):
        Work = Available
        Finish[i] = (Allocation[i] == 0)
        Find i where Finish[i] == False and Request[i] <= Work.
        If found: Work += Allocation[i], Finish[i] = True.
        Processes with Finish == False at the end are deadlocked.
        """
        work: Dict[str, int] = copy.deepcopy(self.available)
        finish: Dict[str, bool] = {}

        for p in self.processes:
            p_alloc = self.allocation.get(p, {})
            has_allocation = any(p_alloc.get(r, 0) > 0 for r in self.resources)
            finish[p] = not has_allocation

        steps: List[DetectionStep] = []
        step_counter = 1

        while True:
            found = False
            for p in self.processes:
                if not finish[p]:
                    p_req = self.request.get(p, {})
                    can_satisfy = all(p_req.get(r, 0) <= work.get(r, 0) for r in self.resources)

                    if can_satisfy:
                        p_alloc = self.allocation.get(p, {})
                        work_before = copy.deepcopy(work)

                        for r in self.resources:
                            work[r] = work.get(r, 0) + p_alloc.get(r, 0)

                        finish[p] = True
                        found = True

                        steps.append(
                            DetectionStep(
                                step_number=step_counter,
                                process_id=p,
                                work_before=work_before,
                                request=copy.deepcopy(p_req),
                                allocation=copy.deepcopy(p_alloc),
                                work_after=copy.deepcopy(work),
                                finished=True,
                            )
                        )
                        step_counter += 1
                        break

            if not found:
                break

        deadlocked = [p for p in self.processes if not finish[p]]
        safe = [p for p in self.processes if finish[p]]
        has_deadlock = len(deadlocked) > 0

        # Also extract Wait-For Graph edges and cycles
        wfg_edges = self.extract_wait_for_graph()
        cycles = self.find_cycles_in_graph(wfg_edges)

        if has_deadlock:
            msg = (
                f"DEADLOCK DETECTED! Deadlocked processes: {', '.join(deadlocked)}. "
                f"Available resources cannot satisfy remaining pending requests."
            )
        else:
            msg = "NO DEADLOCK DETECTED. All processes can successfully complete."

        return DetectionResult(
            has_deadlock=has_deadlock,
            deadlocked_processes=deadlocked,
            safe_processes=safe,
            cycles=cycles,
            wait_for_edges=wfg_edges,
            steps=steps,
            message=msg,
        )

    def extract_wait_for_graph(self) -> List[Tuple[str, str]]:
        """
        Constructs Wait-For Graph (WFG) directed edges:
        Pi -> Pj exists if Pi requests resource Rk and Pj currently holds an allocation of Rk.
        """
        edges: Set[Tuple[str, str]] = set()

        for p_req_id in self.processes:
            p_req_map = self.request.get(p_req_id, {})
            for r in self.resources:
                if p_req_map.get(r, 0) > 0:
                    # Resource r is requested by p_req_id.
                    # Find all processes holding resource r:
                    for p_holder_id in self.processes:
                        if p_holder_id != p_req_id:
                            p_holder_alloc = self.allocation.get(p_holder_id, {}).get(r, 0)
                            if p_holder_alloc > 0:
                                edges.add((p_req_id, p_holder_id))

        return sorted(list(edges))

    @staticmethod
    def find_cycles_in_graph(edges: List[Tuple[str, str]]) -> List[List[str]]:
        """
        Identifies simple directed cycles in a graph represented by edges (u, v).
        Uses Depth-First Search cycle detection.
        """
        adj: Dict[str, List[str]] = {}
        all_nodes: Set[str] = set()

        for u, v in edges:
            all_nodes.add(u)
            all_nodes.add(v)
            if u not in adj:
                adj[u] = []
            adj[u].append(v)

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: List[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle found! Extract subpath from neighbor to end of rec_stack
                    idx = rec_stack.index(neighbor)
                    cycle_path = rec_stack[idx:] + [neighbor]
                    # Normalize cycle path to avoid duplicates
                    # Rotate such that min element is first
                    nodes_in_cycle = cycle_path[:-1]
                    min_idx = nodes_in_cycle.index(min(nodes_in_cycle))
                    canonical = nodes_in_cycle[min_idx:] + nodes_in_cycle[:min_idx] + [nodes_in_cycle[min_idx]]
                    if canonical not in cycles:
                        cycles.append(canonical)

            rec_stack.pop()

        for n in sorted(list(all_nodes)):
            if n not in visited:
                dfs(n)

        return cycles
