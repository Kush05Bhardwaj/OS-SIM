"""
Unit tests for BashExecutor and Python-Bash integration layer.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from core.executor import BashExecutor, ExecutionResult
from core.config import BASH_DIR


@pytest.fixture
def executor():
    return BashExecutor()


@pytest.fixture
def mock_executor():
    return BashExecutor(force_mock=True)


def test_executor_initialization(executor):
    assert executor.scripts_dir == BASH_DIR.resolve()
    assert executor.default_timeout > 0


def test_validate_script_whitelist(executor):
    # Valid allowed script
    valid_path = executor.validate_script("system_info.sh")
    assert valid_path.exists()
    assert valid_path.name == "system_info.sh"

    # Unauthorized script
    with pytest.raises(PermissionError):
        executor.validate_script("malicious.sh")

    # Path traversal attack
    with pytest.raises(ValueError):
        executor.validate_script("../system_info.sh")

    with pytest.raises(ValueError):
        executor.validate_script("dir/system_info.sh")


def test_mock_mode_execution(mock_executor):
    assert mock_executor.is_bash_available() is False

    for script in ["system_info.sh", "resource_monitor.sh", "disk_monitor.sh", "process_monitor.sh", "health_check.sh"]:
        result = mock_executor.execute(script)
        assert result.success is True
        assert result.return_code == 0
        assert result.is_mock is True
        assert result.parsed_data is not None
        assert result.parsed_data["status"] == "ok"
        assert isinstance(result.data, dict)


def test_mock_process_monitor_args(mock_executor):
    res = mock_executor.execute("process_monitor.sh", args=["3", "mem"])
    assert res.success is True
    assert len(res.data.get("processes", [])) <= 3


def test_live_execution_if_available(executor):
    if not executor.is_bash_available():
        pytest.skip("Bash binary not available in current test environment")

    res = executor.execute("health_check.sh")
    assert res.success is True
    assert res.return_code == 0
    assert res.is_mock is False
    assert res.parsed_data["status"] == "ok"
    assert "commands" in res.data


def test_timeout_handling():
    executor = BashExecutor()
    if not executor.is_bash_available():
        pytest.skip("Bash not available for timeout test")

    # Mock subprocess.run to raise TimeoutExpired
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="bash", timeout=1)):
        res = executor.execute("system_info.sh", timeout=1)
        assert res.success is False
        assert res.return_code == -2
        assert "timed out" in res.error_message.lower()


def test_nonzero_exit_handling():
    executor = BashExecutor()
    if not executor.is_bash_available():
        pytest.skip("Bash not available")

    mock_proc = MagicMock()
    mock_proc.returncode = 127
    mock_proc.stdout = ""
    mock_proc.stderr = "command not found"

    with patch("subprocess.run", return_value=mock_proc):
        res = executor.execute("system_info.sh")
        assert res.success is False
        assert res.return_code == 127
        assert "127" in res.error_message


def test_malformed_json_handling():
    executor = BashExecutor()
    if not executor.is_bash_available():
        pytest.skip("Bash not available")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "NOT_JSON_DATA"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        res = executor.execute("system_info.sh")
        assert res.success is False
        assert "JSON" in res.error_message
