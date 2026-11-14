"""
Python-Bash Integration Layer
Provides secure subprocess execution, timeout enforcement, output parsing,
and robust mock fallbacks for Linux monitoring utilities.
"""

import os
import sys
import json
import time
import shutil
import platform
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

import psutil

from core.config import (
    BASH_DIR,
    BASH_DEFAULT_TIMEOUT,
    BASH_ALLOWED_SCRIPTS,
)


@dataclass
class ExecutionResult:
    """Represents the outcome of a script execution."""
    success: bool
    return_code: int
    stdout: str = ""
    stderr: str = ""
    parsed_data: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    is_mock: bool = False

    @property
    def data(self) -> Dict[str, Any]:
        """Convenience property returning the parsed JSON data dict."""
        if self.parsed_data and isinstance(self.parsed_data, dict):
            return self.parsed_data.get("data", self.parsed_data)
        return {}


class BashExecutor:
    """
    Executes Bash scripts with timeout controls, strict argument sanitization,
    JSON parsing, and dynamic cross-platform fallbacks.
    """

    def __init__(
        self,
        scripts_dir: Optional[Path] = None,
        default_timeout: int = BASH_DEFAULT_TIMEOUT,
        force_mock: bool = False,
    ):
        self.scripts_dir: Path = (scripts_dir or BASH_DIR).resolve()
        self.default_timeout: int = default_timeout
        self.force_mock: bool = force_mock
        self._bash_path: Optional[str] = self._locate_bash()

    def _locate_bash(self) -> Optional[str]:
        """Locates the most appropriate bash binary available."""
        if self.force_mock:
            return None

        # On native Linux / Unix
        if platform.system().lower() != "windows":
            return shutil.which("bash") or shutil.which("sh")

        # On Windows: Check Git Bash or WSL
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.exists():
            return str(git_bash)

        which_bash = shutil.which("bash.exe") or shutil.which("bash")
        if which_bash and "System32" not in which_bash:
            return which_bash

        return None

    def is_bash_available(self) -> bool:
        """Checks if a valid bash interpreter is available."""
        return self._bash_path is not None and not self.force_mock

    def validate_script(self, script_name: str) -> Path:
        """
        Validates script presence and prevents path traversal attacks.
        """
        if ".." in script_name or "/" in script_name or "\\" in script_name:
            raise ValueError(f"Path traversal detected in script name: {script_name}")

        if script_name not in BASH_ALLOWED_SCRIPTS:
            raise PermissionError(f"Script '{script_name}' is not in allowed scripts whitelist.")

        script_path = (self.scripts_dir / script_name).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        return script_path

    def execute(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Executes a script and returns an ExecutionResult.
        """
        start_time = time.perf_counter()
        args = args or []
        effective_timeout = timeout or self.default_timeout

        # Fallback to mock mode if bash is not available or mock forced
        if not self.is_bash_available():
            mock_data = self._generate_mock_data(script_name, args)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=json.dumps(mock_data),
                parsed_data=mock_data,
                execution_time_ms=elapsed_ms,
                is_mock=True,
            )

        try:
            script_path = self.validate_script(script_name)
        except (ValueError, PermissionError, FileNotFoundError) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-1,
                error_message=str(e),
                execution_time_ms=elapsed_ms,
            )

        cmd = [self._bash_path, str(script_path)] + [str(a) for a in args]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            stdout_str = proc.stdout.strip()
            stderr_str = proc.stderr.strip()

            if proc.returncode != 0:
                return ExecutionResult(
                    success=False,
                    return_code=proc.returncode,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    error_message=f"Script exited with status {proc.returncode}: {stderr_str}",
                    execution_time_ms=elapsed_ms,
                )

            # Parse JSON output
            parsed = None
            try:
                parsed = json.loads(stdout_str)
            except json.JSONDecodeError as jde:
                return ExecutionResult(
                    success=False,
                    return_code=proc.returncode,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    error_message=f"Failed to parse script output as JSON: {jde}",
                    execution_time_ms=elapsed_ms,
                )

            return ExecutionResult(
                success=True,
                return_code=0,
                stdout=stdout_str,
                stderr=stderr_str,
                parsed_data=parsed,
                execution_time_ms=elapsed_ms,
                is_mock=False,
            )

        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-2,
                error_message=f"Execution timed out after {effective_timeout} seconds.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as ex:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=False,
                return_code=-3,
                error_message=f"Unexpected execution error: {ex}",
                execution_time_ms=elapsed_ms,
            )

    def _generate_mock_data(self, script_name: str, args: List[str]) -> Dict[str, Any]:
        """Generates realistic telemetry using psutil and platform."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if script_name == "system_info.sh":
            uname = platform.uname()
            boot_time = psutil.boot_time()
            uptime_secs = round(time.time() - boot_time, 2)
            hours, rem = divmod(int(uptime_secs), 3600)
            minutes, _ = divmod(rem, 60)
            return {
                "status": "ok",
                "timestamp": now_iso,
                "data": {
                    "hostname": uname.node or "mock-host",
                    "os_name": f"{uname.system} {uname.release}",
                    "kernel_release": uname.version or "1.0.0-mock",
                    "architecture": uname.machine or "x86_64",
                    "cpu_model": uname.processor or "Mock Virtual CPU @ 2.40GHz",
                    "cpu_cores": psutil.cpu_count(logical=True) or 4,
                    "uptime_seconds": uptime_secs,
                    "uptime_human": f"{hours} hours, {minutes} minutes (Mock)",
                },
            }

        elif script_name == "resource_monitor.sh":
            vm = psutil.virtual_memory()
            sm = psutil.swap_memory()
            cpu_pct = psutil.cpu_percent(interval=0.1)
            load = (
                psutil.getloadavg()
                if hasattr(psutil, "getloadavg")
                else (cpu_pct / 100.0, cpu_pct / 100.0, cpu_pct / 100.0)
            )
            return {
                "status": "ok",
                "timestamp": now_iso,
                "data": {
                    "cpu": {
                        "usage_percent": cpu_pct,
                        "load_1m": round(load[0], 2),
                        "load_5m": round(load[1], 2),
                        "load_15m": round(load[2], 2),
                    },
                    "memory": {
                        "total_mb": round(vm.total / (1024 * 1024), 2),
                        "used_mb": round(vm.used / (1024 * 1024), 2),
                        "free_mb": round(vm.free / (1024 * 1024), 2),
                        "available_mb": round(vm.available / (1024 * 1024), 2),
                        "usage_percent": vm.percent,
                    },
                    "swap": {
                        "total_mb": round(sm.total / (1024 * 1024), 2),
                        "used_mb": round(sm.used / (1024 * 1024), 2),
                        "free_mb": round(sm.free / (1024 * 1024), 2),
                        "usage_percent": sm.percent,
                    },
                },
            }

        elif script_name == "disk_monitor.sh":
            partitions_list = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions_list.append(
                        {
                            "filesystem": part.device,
                            "mountpoint": part.mountpoint,
                            "total_gb": round(usage.total / (1024**3), 2),
                            "used_gb": round(usage.used / (1024**3), 2),
                            "available_gb": round(usage.free / (1024**3), 2),
                            "usage_percent": usage.percent,
                        }
                    )
                except (PermissionError, OSError):
                    continue
            return {
                "status": "ok",
                "timestamp": now_iso,
                "data": {"partitions": partitions_list},
            }

        elif script_name == "process_monitor.sh":
            limit = int(args[0]) if args and args[0].isdigit() else 10
            sort_key = args[1] if len(args) > 1 else "cpu"
            procs = []
            for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
                try:
                    info = p.info
                    procs.append(
                        {
                            "pid": info["pid"],
                            "user": info.get("username") or "system",
                            "name": info.get("name") or "unknown",
                            "cpu_percent": round(info.get("cpu_percent") or 0.0, 1),
                            "memory_percent": round(info.get("memory_percent") or 0.0, 1),
                            "status": info.get("status") or "running",
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            key = "cpu_percent" if sort_key == "cpu" else "memory_percent"
            procs.sort(key=lambda x: x[key], reverse=True)

            return {
                "status": "ok",
                "timestamp": now_iso,
                "data": {
                    "limit": limit,
                    "sort_by": sort_key,
                    "processes": procs[:limit],
                },
            }

        elif script_name == "health_check.sh":
            return {
                "status": "ok",
                "timestamp": now_iso,
                "data": {
                    "subsystem": "mock_python_subsystem",
                    "all_healthy": True,
                    "commands": {
                        "bash": False,
                        "awk": False,
                        "sed": False,
                        "grep": False,
                        "df": False,
                        "ps": False,
                        "uname": False,
                    },
                    "procfs": {
                        "meminfo": False,
                        "stat": False,
                        "uptime": False,
                        "cpuinfo": False,
                    },
                },
            }

        return {"status": "ok", "timestamp": now_iso, "data": {}}
