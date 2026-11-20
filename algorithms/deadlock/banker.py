"""
Dijkstra's Banker's Algorithm for Deadlock Avoidance.
Supports multi-resource safety checks and dynamic resource request evaluation.
"""

from typing import Dict, List, Optional
import copy

from algorithms.deadlock.base import (
    DeadlockState,
    SafetyStep,
    SafetyResult,
    ResourceRequestResult,
)


class BankerAlgorithm:
    """
    Implements Dijkstra's Banker's Algorithm for Deadlock Avoidance.
    """

    def __init__(self, state: DeadlockState):
        self.state = copy.deepcopy(state)
        self._validate_state()

    def _validate_state(self) -> None:
        """Ensure matrices and dimensions are logically consistent."""
        for p in self.state.processes:
            if p not in self.state.allocation:
                raise ValueError(f"Process {p} missing from allocation matrix.")
            if p not in self.state.max_matrix:
                raise ValueError(f"Process {p} missing from max matrix.")

            for r in self.state.resources:
                alloc = self.state.allocation[p].get(r, 0)
                max_val = self.state.max_matrix[p].get(r, 0)
                if alloc < 0 or max_val < 0:
                    raise ValueError(f"Resource values for {p}, {r} cannot be negative.")
                if alloc > max_val:
                    raise ValueError(f"Allocation ({alloc}) exceeds Max ({max_val}) for {p}, {r}.")

        for r in self.state.resources:
            avail = self.state.available.get(r, 0)
            if avail < 0:
                raise ValueError(f"Available count for resource {r} cannot be negative.")

    def get_need_matrix(self) -> Dict[str, Dict[str, int]]:
        """Return Need = Max - Allocation."""
        return self.state.get_need_matrix()

    def check_safety(self) -> SafetyResult:
        """
        Executes Banker's Safety Algorithm to verify if system is in a safe state.
        Returns safety result including safe execution sequence and step trace.
        """
        work: Dict[str, int] = copy.deepcopy(self.state.available)
        finish: Dict[str, bool] = {p: False for p in self.state.processes}
        need_matrix = self.get_need_matrix()

        safe_seq: List[str] = []
        steps: List[SafetyStep] = []
        step_counter = 1

        while len(safe_seq) < len(self.state.processes):
            found_candidate = False

            for p in self.state.processes:
                if not finish[p]:
                    # Check if Need[p] <= Work
                    p_need = need_matrix[p]
                    can_allocate = all(p_need.get(r, 0) <= work.get(r, 0) for r in self.state.resources)

                    if can_allocate:
                        p_alloc = self.state.allocation[p]
                        work_before = copy.deepcopy(work)

                        # Work = Work + Allocation[p]
                        for r in self.state.resources:
                            work[r] = work.get(r, 0) + p_alloc.get(r, 0)

                        finish[p] = True
                        safe_seq.append(p)
                        found_candidate = True

                        steps.append(
                            SafetyStep(
                                step_number=step_counter,
                                process_id=p,
                                work_before=work_before,
                                need=copy.deepcopy(p_need),
                                allocation=copy.deepcopy(p_alloc),
                                work_after=copy.deepcopy(work),
                                satisfied=True,
                                explanation=(
                                    f"{p} needs {p_need} <= Work {work_before}. "
                                    f"Executed and released resources {p_alloc}. New Work = {work}."
                                ),
                            )
                        )
                        step_counter += 1
                        break  # Restart loop with updated Work

            if not found_candidate:
                # No process could proceed; system is in unsafe state
                break

        is_safe = len(safe_seq) == len(self.state.processes)
        unresolved = [p for p in self.state.processes if not finish[p]]

        if is_safe:
            msg = f"System is in a SAFE state. Safe execution sequence: <{', '.join(safe_seq)}>."
        else:
            msg = (
                f"System is in an UNSAFE state. Deadlock could occur. "
                f"Unresolved processes: {', '.join(unresolved)}."
            )

        return SafetyResult(
            is_safe=is_safe,
            safe_sequence=safe_seq,
            steps=steps,
            unresolved_processes=unresolved,
            message=msg,
        )

    def request_resources(
        self, process_id: str, request: Dict[str, int]
    ) -> ResourceRequestResult:
        """
        Evaluates dynamic resource request from a process using Banker's Algorithm:
        1. Request_i <= Need_i
        2. Request_i <= Available
        3. Tentative allocation & Safety check
        4. Commit if safe, rollback if unsafe.
        """
        if process_id not in self.state.processes:
            return ResourceRequestResult(
                granted=False,
                process_id=process_id,
                request=request,
                reason=f"Process {process_id} not recognized in system processes.",
            )

        need_matrix = self.get_need_matrix()
        p_need = need_matrix[process_id]

        # Step 1: Check Request <= Need
        for r in self.state.resources:
            req_val = request.get(r, 0)
            if req_val < 0:
                return ResourceRequestResult(
                    granted=False,
                    process_id=process_id,
                    request=request,
                    reason=f"Resource request cannot contain negative value for resource {r}.",
                )
            if req_val > p_need.get(r, 0):
                return ResourceRequestResult(
                    granted=False,
                    process_id=process_id,
                    request=request,
                    reason=(
                        f"Process {process_id} exceeded its maximum claim: requested {req_val} "
                        f"for {r}, but Need is {p_need.get(r, 0)}."
                    ),
                )

        # Step 2: Check Request <= Available
        for r in self.state.resources:
            req_val = request.get(r, 0)
            avail_val = self.state.available.get(r, 0)
            if req_val > avail_val:
                return ResourceRequestResult(
                    granted=False,
                    process_id=process_id,
                    request=request,
                    reason=(
                        f"Insufficient available resources: requested {req_val} "
                        f"for {r}, but only {avail_val} is available. {process_id} must wait."
                    ),
                )

        # Step 3: Tentatively allocate
        tentative_state = copy.deepcopy(self.state)
        for r in self.state.resources:
            req_val = request.get(r, 0)
            tentative_state.available[r] -= req_val
            tentative_state.allocation[process_id][r] += req_val

        # Step 4: Run safety algorithm on tentative state
        tentative_banker = BankerAlgorithm(tentative_state)
        safety_result = tentative_banker.check_safety()

        if safety_result.is_safe:
            # Safe! Commit state changes
            self.state = tentative_state
            return ResourceRequestResult(
                granted=True,
                process_id=process_id,
                request=request,
                reason=(
                    f"Request GRANTED for {process_id}. System remains in a safe state with sequence: "
                    f"<{', '.join(safety_result.safe_sequence)}>."
                ),
                safety_result=safety_result,
                state_after=self.state,
            )
        else:
            # Unsafe! Rollback (tentative state discarded)
            return ResourceRequestResult(
                granted=False,
                process_id=process_id,
                request=request,
                reason=(
                    f"Request DENIED for {process_id}. Granting request would result in an UNSAFE state. "
                    f"{process_id} must wait."
                ),
                safety_result=safety_result,
                state_after=self.state,
            )
