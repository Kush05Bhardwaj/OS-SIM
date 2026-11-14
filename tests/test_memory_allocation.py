"""
Unit tests for Contiguous Memory Allocation (First Fit, Best Fit, Worst Fit, Next Fit, Coalescing, Compaction).
"""

import pytest
from algorithms.memory.base import MemoryPool, MemoryBlock


def test_first_fit():
    pool = MemoryPool(total_size=1000)
    # Pre-split into blocks: [100 Free, 200 Free, 300 Free, 400 Free]
    pool.blocks = [
        MemoryBlock(0, 100, False),
        MemoryBlock(100, 200, False),
        MemoryBlock(300, 300, False),
        MemoryBlock(600, 400, False),
    ]

    # First Fit for size 150 -> should allocate in the 200 block (index 1)
    res = pool.allocate("P1", 150, strategy="first_fit")
    assert res.success is True
    assert res.allocated_block.start_address == 100
    assert res.allocated_block.size == 150
    # Remainder 50 free block inserted at 250
    assert pool.blocks[2].size == 50
    assert pool.blocks[2].is_allocated is False


def test_best_fit():
    pool = MemoryPool(total_size=1000)
    pool.blocks = [
        MemoryBlock(0, 300, False),
        MemoryBlock(300, 150, False),
        MemoryBlock(450, 400, False),
        MemoryBlock(850, 150, False),
    ]

    # Best fit for size 140 -> should pick one of the 150 blocks (index 1)
    res = pool.allocate("P1", 140, strategy="best_fit")
    assert res.success is True
    assert res.allocated_block.start_address == 300
    assert res.allocated_block.size == 140


def test_worst_fit():
    pool = MemoryPool(total_size=1000)
    pool.blocks = [
        MemoryBlock(0, 100, False),
        MemoryBlock(100, 500, False),
        MemoryBlock(600, 200, False),
        MemoryBlock(800, 200, False),
    ]

    # Worst fit for size 100 -> should pick the largest block (500)
    res = pool.allocate("P1", 100, strategy="worst_fit")
    assert res.success is True
    assert res.allocated_block.start_address == 100
    assert res.allocated_block.size == 100
    # Remaining 400 free block
    assert pool.blocks[2].size == 400


def test_next_fit():
    pool = MemoryPool(total_size=1000)
    pool.blocks = [
        MemoryBlock(0, 200, False),
        MemoryBlock(200, 300, False),
        MemoryBlock(500, 500, False),
    ]

    # Alloc 1: in block 0
    res1 = pool.allocate("P1", 100, strategy="next_fit")
    assert res1.allocated_block.start_address == 0

    # Alloc 2: should continue from index 1 (the remaining 100 or block at 200)
    res2 = pool.allocate("P2", 250, strategy="next_fit")
    assert res2.allocated_block.start_address == 200


def test_deallocation_and_coalescing():
    pool = MemoryPool(total_size=600)
    pool.allocate("P1", 200)
    pool.allocate("P2", 200)
    pool.allocate("P3", 200)
    assert len(pool.blocks) == 3

    # Deallocate middle block P2
    assert pool.deallocate("P2") is True
    assert len(pool.blocks) == 3

    # Deallocate P1 -> should merge with P2 (200 + 200 = 400 free block)
    assert pool.deallocate("P1") is True
    assert len(pool.blocks) == 2
    assert pool.blocks[0].is_allocated is False
    assert pool.blocks[0].size == 400

    # Deallocate P3 -> merges everything into 1 single 600 free block
    assert pool.deallocate("P3") is True
    assert len(pool.blocks) == 1
    assert pool.blocks[0].size == 600
    assert pool.blocks[0].is_allocated is False


def test_external_fragmentation():
    pool = MemoryPool(total_size=600)
    pool.allocate("P1", 200)
    pool.allocate("P2", 200)
    pool.allocate("P3", 200)

    # Deallocate P1 and P3, leaving P2 in between
    pool.deallocate("P1")
    pool.deallocate("P3")
    # Free space = 200 + 200 = 400 KB, but separated by P2!
    assert pool.total_free_memory == 400

    # Request 300 KB -> cannot fit in any single 200 block!
    frag = pool.external_fragmentation(300)
    assert frag == 400

    res = pool.allocate("P4", 300)
    assert res.success is False
    assert "External fragmentation" in res.error_message


def test_compaction():
    pool = MemoryPool(total_size=600)
    pool.allocate("P1", 100)
    pool.allocate("P2", 100)
    pool.allocate("P3", 100)
    pool.allocate("P4", 100)
    pool.allocate("P5", 200)

    # Free P2 and P4 -> fragmented holes
    pool.deallocate("P2")
    pool.deallocate("P4")
    assert pool.total_free_memory == 200
    assert pool.free_blocks_count == 2

    # Compact memory!
    pool.compact()
    # Allocated P1, P3, P5 shifted to 0, 100, 200
    assert len(pool.blocks) == 4
    assert pool.blocks[0].pid == "P1"
    assert pool.blocks[0].start_address == 0
    assert pool.blocks[1].pid == "P3"
    assert pool.blocks[1].start_address == 100
    assert pool.blocks[2].pid == "P5"
    assert pool.blocks[2].start_address == 200

    # Single contiguous free hole at end of size 200
    assert pool.blocks[3].is_allocated is False
    assert pool.blocks[3].start_address == 400
    assert pool.blocks[3].size == 200

    # Now a 200 KB allocation succeeds!
    res = pool.allocate("P_NEW", 200)
    assert res.success is True
