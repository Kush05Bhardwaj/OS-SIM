#!/usr/bin/env bash
# system_info.sh: Collects OS, kernel, and hardware metadata formatted as JSON
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

HOSTNAME_VAL=$(hostname 2>/dev/null || echo "unknown")
KERNEL_VAL=$(uname -r 2>/dev/null || echo "unknown")
ARCH_VAL=$(uname -m 2>/dev/null || echo "unknown")

# OS Name / Distribution
OS_NAME="Linux"
if [ -f /etc/os-release ]; then
    # Extract PRETTY_NAME or NAME
    OS_NAME=$(grep -E '^(PRETTY_NAME|NAME)=' /etc/os-release | head -n 1 | cut -d '=' -f 2 | tr -d '"' || echo "Linux")
elif command -v uname >/dev/null 2>&1; then
    OS_NAME=$(uname -s 2>/dev/null || echo "Linux")
fi

# CPU Model
CPU_MODEL="Generic CPU"
if [ -f /proc/cpuinfo ]; then
    CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | sed 's/^[ \t]*//' || echo "Generic CPU")
elif command -v lscpu >/dev/null 2>&1; then
    CPU_MODEL=$(lscpu 2>/dev/null | grep "Model name:" | cut -d: -f2 | sed 's/^[ \t]*//' || echo "Generic CPU")
fi

# CPU Cores
CPU_CORES=1
if [ -f /proc/cpuinfo ]; then
    CPU_CORES=$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "1")
elif command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc 2>/dev/null || echo "1")
fi

# Uptime
UPTIME_SECS=0
UPTIME_HUMAN="unknown"
if [ -f /proc/uptime ]; then
    UPTIME_SECS=$(awk '{print $1}' /proc/uptime 2>/dev/null || echo "0")
fi
if command -v uptime >/dev/null 2>&1; then
    UPTIME_HUMAN=$(uptime 2>/dev/null | sed -e 's/^[ \t]*//' | sed -e 's/"/\\"/g' || echo "unknown")
fi

# Escape JSON strings
clean_json() {
    echo "$1" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr -d '\r\n'
}

CLEAN_HOSTNAME=$(clean_json "$HOSTNAME_VAL")
CLEAN_OS=$(clean_json "$OS_NAME")
CLEAN_KERNEL=$(clean_json "$KERNEL_VAL")
CLEAN_ARCH=$(clean_json "$ARCH_VAL")
CLEAN_CPU=$(clean_json "$CPU_MODEL")
CLEAN_UPTIME_H=$(clean_json "$UPTIME_HUMAN")

cat <<EOF
{
  "status": "ok",
  "timestamp": "$TIMESTAMP",
  "data": {
    "hostname": "$CLEAN_HOSTNAME",
    "os_name": "$CLEAN_OS",
    "kernel_release": "$CLEAN_KERNEL",
    "architecture": "$CLEAN_ARCH",
    "cpu_model": "$CLEAN_CPU",
    "cpu_cores": $CPU_CORES,
    "uptime_seconds": $UPTIME_SECS,
    "uptime_human": "$CLEAN_UPTIME_H"
  }
}
EOF
