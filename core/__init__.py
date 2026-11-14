"""Core package for OS-SIM."""

from core.config import config, APP_NAME, APP_VERSION
from core.executor import BashExecutor, ExecutionResult

__all__ = ["config", "APP_NAME", "APP_VERSION", "BashExecutor", "ExecutionResult"]
