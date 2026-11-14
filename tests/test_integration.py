"""
End-to-end integration tests for OS-SIM full simulation and persistence pipeline.
"""

import pytest
from algorithms.cpu.schedulers import FCFSScheduler, RoundRobinScheduler
from algorithms.cpu.base import Process
from algorithms.cpu.metrics import compare_all_schedulers
from algorithms.memory.base import MemoryPool
from algorithms.paging.replacers import FIFOPageReplacer, LRUPageReplacer
from algorithms.disk.schedulers import FCFSDiskScheduler, SSTFDiskScheduler
from database.db_manager import DatabaseManager
from analytics.export import export_simulation_runs_to_csv, export_simulation_runs_to_json


def test_full_simulation_pipeline_and_persistence():
    # 1. Execute CPU Simulation
    cpu_procs = [Process("P1", 0, 4), Process("P2", 1, 2), Process("P3", 2, 1)]
    cpu_res = RoundRobinScheduler(quantum=2).schedule(cpu_procs)
    assert cpu_res.total_time == 7

    # 2. Execute Memory Allocation & Compaction
    pool = MemoryPool(total_size=500)
    pool.allocate("P1", 200, strategy="first_fit")
    pool.allocate("P2", 200, strategy="best_fit")
    pool.deallocate("P1")
    pool.compact()
    assert pool.blocks[0].pid == "P2"

    # 3. Execute Virtual Memory Paging
    paging_res = LRUPageReplacer().simulate([1, 2, 3, 1, 4, 5], num_frames=3)
    assert paging_res.page_faults > 0

    # 4. Execute Disk Arm Traversal
    disk_res = SSTFDiskScheduler().schedule([10, 50, 20], initial_head=15)
    assert disk_res.total_head_movement > 0

    # 5. Persist runs into Database
    db = DatabaseManager(db_path=":memory:")
    run_id1 = db.save_simulation_run(
        category="CPU Scheduling",
        algorithm_name=cpu_res.algorithm_name,
        input_params={"processes": len(cpu_procs)},
        metrics={"avg_wt": cpu_res.avg_waiting_time, "avg_tat": cpu_res.avg_turnaround_time},
    )
    run_id2 = db.save_simulation_run(
        category="Disk Scheduling",
        algorithm_name=disk_res.algorithm_name,
        input_params={"requests": [10, 50, 20]},
        metrics={"total_seek": disk_res.total_head_movement},
    )

    runs = db.get_simulation_runs()
    assert len(runs) == 2

    # 6. Export to CSV & JSON
    csv_out = export_simulation_runs_to_csv(runs)
    assert run_id1 in csv_out
    assert run_id2 in csv_out

    json_out = export_simulation_runs_to_json(runs)
    assert run_id1 in json_out
    assert run_id2 in json_out
