"""
Contiguous Dynamic Memory Allocation Engine
Models physical memory blocks, allocation strategies (First, Best, Worst, Next Fit),
automatic hole coalescing, and dynamic compaction.
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class MemoryBlock:
    """Represents a continuous partition in physical memory."""
    start_address: int
    size: int
    is_allocated: bool = False
    pid: Optional[str] = None

    @property
    def end_address(self) -> int:
        return self.start_address + self.size

    def copy(self) -> "MemoryBlock":
        return MemoryBlock(
            start_address=self.start_address,
            size=self.size,
            is_allocated=self.is_allocated,
            pid=self.pid,
        )


@dataclass
class AllocationResult:
    """Result of an allocation request."""
    success: bool
    pid: str
    size: int
    strategy: str
    allocated_block: Optional[MemoryBlock] = None
    error_message: Optional[str] = None


class MemoryPool:
    """
    Manages physical memory partitions, supporting dynamic variable-partition
    allocation, adjacent block coalescing, and compaction.
    """

    STRATEGIES = ["first_fit", "best_fit", "worst_fit", "next_fit"]

    def __init__(self, total_size: int = 1024):
        if total_size <= 0:
            raise ValueError("Total memory size must be a positive integer.")
        self.total_size: int = total_size
        self.blocks: List[MemoryBlock] = [
            MemoryBlock(start_address=0, size=total_size, is_allocated=False, pid=None)
        ]
        self._last_fit_index: int = 0

    def reset(self) -> None:
        """Resets memory pool to a single contiguous free partition."""
        self.blocks = [
            MemoryBlock(start_address=0, size=self.total_size, is_allocated=False, pid=None)
        ]
        self._last_fit_index = 0

    @property
    def total_free_memory(self) -> int:
        return sum(b.size for b in self.blocks if not b.is_allocated)

    @property
    def total_allocated_memory(self) -> int:
        return sum(b.size for b in self.blocks if b.is_allocated)

    @property
    def free_blocks_count(self) -> int:
        return sum(1 for b in self.blocks if not b.is_allocated)

    def external_fragmentation(self, requested_size: int) -> int:
        """
        Calculates external fragmentation: total free space available when no
        single free partition is large enough to satisfy the request.
        """
        can_satisfy = any(not b.is_allocated and b.size >= requested_size for b in self.blocks)
        if not can_satisfy and self.total_free_memory >= requested_size:
            return self.total_free_memory
        return 0

    def allocate(self, pid: str, size: int, strategy: str = "first_fit") -> AllocationResult:
        """
        Allocates memory of requested size for a given process PID.
        """
        if size <= 0:
            return AllocationResult(False, pid, size, strategy, error_message="Size must be positive.")

        # Check for existing PID
        if any(b.is_allocated and b.pid == pid for b in self.blocks):
            return AllocationResult(False, pid, size, strategy, error_message=f"Process {pid} is already allocated.")

        strategy = strategy.lower().strip()
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown allocation strategy: {strategy}. Must be one of {self.STRATEGIES}")

        target_idx = self._find_block_index(size, strategy)

        if target_idx is None:
            ext_frag = self.external_fragmentation(size)
            err = (
                f"Insufficient contiguous memory. External fragmentation: {ext_frag} KB available."
                if ext_frag > 0
                else "Out of memory."
            )
            return AllocationResult(False, pid, size, strategy, error_message=err)

        target_block = self.blocks[target_idx]

        if target_block.size == size:
            # Exact fit
            target_block.is_allocated = True
            target_block.pid = pid
            self._last_fit_index = target_idx
            return AllocationResult(True, pid, size, strategy, allocated_block=target_block.copy())
        else:
            # Split block: [Allocated Sized Block] + [Remaining Free Block]
            allocated_block = MemoryBlock(
                start_address=target_block.start_address,
                size=size,
                is_allocated=True,
                pid=pid,
            )
            free_remainder = MemoryBlock(
                start_address=target_block.start_address + size,
                size=target_block.size - size,
                is_allocated=False,
                pid=None,
            )
            self.blocks[target_idx] = allocated_block
            self.blocks.insert(target_idx + 1, free_remainder)
            self._last_fit_index = target_idx + 1
            return AllocationResult(True, pid, size, strategy, allocated_block=allocated_block.copy())

    def _find_block_index(self, size: int, strategy: str) -> Optional[int]:
        """Finds target block index matching the requested strategy."""
        candidates: List[Tuple[int, MemoryBlock]] = [
            (idx, b) for idx, b in enumerate(self.blocks) if not b.is_allocated and b.size >= size
        ]

        if not candidates:
            return None

        if strategy == "first_fit":
            return candidates[0][0]

        elif strategy == "best_fit":
            # Smallest free block >= size
            best = min(candidates, key=lambda item: item[1].size)
            return best[0]

        elif strategy == "worst_fit":
            # Largest free block >= size
            worst = max(candidates, key=lambda item: item[1].size)
            return worst[0]

        elif strategy == "next_fit":
            # Circular search starting from self._last_fit_index
            n = len(self.blocks)
            for offset in range(n):
                idx = (self._last_fit_index + offset) % n
                b = self.blocks[idx]
                if not b.is_allocated and b.size >= size:
                    return idx
            return candidates[0][0]

        return None

    def deallocate(self, pid: str) -> bool:
        """
        Deallocates all blocks belonging to the specified PID and coalesces free adjacent holes.
        """
        found = False
        for b in self.blocks:
            if b.is_allocated and b.pid == pid:
                b.is_allocated = False
                b.pid = None
                found = True

        if found:
            self.coalesce()
        return found

    def coalesce(self) -> None:
        """Merges adjacent unallocated memory blocks into single contiguous blocks."""
        if len(self.blocks) <= 1:
            return

        coalesced: List[MemoryBlock] = []
        current = self.blocks[0].copy()

        for next_block in self.blocks[1:]:
            if not current.is_allocated and not next_block.is_allocated:
                # Merge into current
                current.size += next_block.size
            else:
                coalesced.append(current)
                current = next_block.copy()

        coalesced.append(current)
        self.blocks = coalesced
        self._last_fit_index = min(self._last_fit_index, len(self.blocks) - 1)

    def compact(self) -> None:
        """
        Performs memory compaction: shifts all allocated blocks to contiguous lower addresses,
        combining all free holes into a single continuous free block at the high address.
        """
        allocated_blocks = [b.copy() for b in self.blocks if b.is_allocated]
        total_free = self.total_free_memory

        new_blocks: List[MemoryBlock] = []
        current_addr = 0

        for b in allocated_blocks:
            b.start_address = current_addr
            current_addr += b.size
            new_blocks.append(b)

        if total_free > 0:
            free_block = MemoryBlock(
                start_address=current_addr,
                size=total_free,
                is_allocated=False,
                pid=None,
            )
            new_blocks.append(free_block)

        self.blocks = new_blocks
        self._last_fit_index = 0
