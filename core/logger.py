"""
Activity Logging & Audit Trail Engine for OS-SIM
Provides structured activity logging, memory buffering for UI inspection,
and file persistence for audit trails.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import threading
import json

from core.config import DATA_DIR


class ActivityLogger:
    """Thread-safe activity logger for simulation events and system audit trails."""

    def __init__(self, log_file: Optional[Path] = None, max_entries: int = 1000):
        self.log_file = log_file or (DATA_DIR / "activity.log")
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        level: str,
        module: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an activity event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "level": level.upper(),
            "module": module,
            "message": message,
            "details": details or {},
        }

        with self._lock:
            self._entries.insert(0, entry)
            if len(self._entries) > self.max_entries:
                self._entries.pop()

            # Append to log file
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass

        return entry

    def info(self, module: str, message: str, details: Optional[Dict[str, Any]] = None):
        return self.log("INFO", module, message, details)

    def success(self, module: str, message: str, details: Optional[Dict[str, Any]] = None):
        return self.log("SUCCESS", module, message, details)

    def warning(self, module: str, message: str, details: Optional[Dict[str, Any]] = None):
        return self.log("WARNING", module, message, details)

    def error(self, module: str, message: str, details: Optional[Dict[str, Any]] = None):
        return self.log("ERROR", module, message, details)

    def get_entries(
        self,
        module_filter: Optional[str] = None,
        level_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve filtered log entries."""
        with self._lock:
            results = self._entries
            if module_filter and module_filter != "All Modules":
                results = [e for e in results if e["module"] == module_filter]
            if level_filter and level_filter != "All Levels":
                results = [e for e in results if e["level"] == level_filter]
            return results[:limit]

    def clear(self):
        """Clears in-memory log buffer."""
        with self._lock:
            self._entries.clear()


# Global Singleton instance
activity_logger = ActivityLogger()
