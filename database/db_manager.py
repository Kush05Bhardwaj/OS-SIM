"""
SQLite Database Persistence Manager for OS-SIM
Persists simulation runs, comparative benchmarks, and periodic telemetry snapshots.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from core.config import DATA_DIR

DEFAULT_DB_PATH = DATA_DIR / "os_sim.db"


class DatabaseManager:
    """Manages SQLite storage and historical query retrieval."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path: Path = db_path or DEFAULT_DB_PATH
        self._is_memory: bool = str(self.db_path) == ":memory:"
        self._mem_conn: Optional[sqlite3.Connection] = None
        if not self._is_memory and isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        elif self._is_memory:
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory and self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    algorithm_name TEXT NOT NULL,
                    input_params TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telemetry_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    swap_percent REAL,
                    raw_json TEXT
                );
                """
            )
            conn.commit()

    def save_simulation_run(
        self,
        category: str,
        algorithm_name: str,
        input_params: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> str:
        """Saves a simulation execution run and returns its unique run_id."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO simulation_runs (run_id, category, algorithm_name, input_params, metrics, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    category,
                    algorithm_name,
                    json.dumps(input_params),
                    json.dumps(metrics),
                    now_iso,
                ),
            )
            conn.commit()
        return run_id

    def get_simulation_runs(
        self, category: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Queries historical simulation runs."""
        with self._get_connection() as conn:
            if category:
                rows = conn.execute(
                    """
                    SELECT run_id, category, algorithm_name, input_params, metrics, created_at
                    FROM simulation_runs
                    WHERE category = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT run_id, category, algorithm_name, input_params, metrics, created_at
                    FROM simulation_runs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

            runs = []
            for r in rows:
                runs.append(
                    {
                        "run_id": r["run_id"],
                        "category": r["category"],
                        "algorithm_name": r["algorithm_name"],
                        "input_params": json.loads(r["input_params"]),
                        "metrics": json.loads(r["metrics"]),
                        "created_at": r["created_at"],
                    }
                )
            return runs

    def save_telemetry_snapshot(self, snapshot_data: Dict[str, Any]) -> int:
        """Persists a telemetry record into SQLite."""
        now_iso = snapshot_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        if isinstance(now_iso, datetime):
            now_iso = now_iso.isoformat()

        cpu = snapshot_data.get("cpu", {}).get("usage_percent", 0.0)
        mem = snapshot_data.get("memory", {}).get("usage_percent", 0.0)
        mem_mb = snapshot_data.get("memory", {}).get("used_mb", 0.0)
        swap = snapshot_data.get("swap", {}).get("usage_percent", 0.0)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO telemetry_snapshots (timestamp, cpu_percent, memory_percent, memory_used_mb, swap_percent, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now_iso, cpu, mem, mem_mb, swap, json.dumps(snapshot_data)),
            )
            conn.commit()
            return cursor.lastrowid

    def get_telemetry_snapshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent telemetry snapshots."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, cpu_percent, memory_percent, memory_used_mb, swap_percent
                FROM telemetry_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_all(self) -> None:
        """Clears all records in the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM simulation_runs;")
            conn.execute("DELETE FROM telemetry_snapshots;")
            conn.commit()


# Default singleton instance
db_manager = DatabaseManager()
