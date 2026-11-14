#!/usr/bin/env bash
# resource_monitor.sh: Collects CPU, Memory, and Swap utilization formatted as JSON
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

# Memory & Swap Extraction
MEM_TOTAL=0
MEM_FREE=0
MEM_AVAIL=0
SWAP_TOTAL=0
SWAP_FREE=0

if [ -f /proc/meminfo ]; then
    MEM_TOTAL=$(awk '/MemTotal:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    MEM_FREE=$(awk '/MemFree:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    MEM_AVAIL=$(awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "$MEM_FREE")
    SWAP_TOTAL=$(awk '/SwapTotal:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    SWAP_FREE=$(awk '/SwapFree:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
elif command -v free >/dev/null 2>&1; then
    MEM_TOTAL=$(free -m 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "0")
    MEM_FREE=$(free -m 2>/dev/null | awk '/^Mem:/ {print $4}' || echo "0")
    MEM_AVAIL=$(free -m 2>/dev/null | awk '/^Mem:/ {print ($7 != "" ? $7 : $4)}' || echo "0")
    SWAP_TOTAL=$(free -m 2>/dev/null | awk '/^Swap:/ {print $2}' || echo "0")
    SWAP_FREE=$(free -m 2>/dev/null | awk '/^Swap:/ {print $4}' || echo "0")
fi

# Fallback defaults if zero
[ -z "$MEM_TOTAL" ] && MEM_TOTAL=0
[ -z "$MEM_FREE" ] && MEM_FREE=0
[ -z "$MEM_AVAIL" ] && MEM_AVAIL=0
[ -z "$SWAP_TOTAL" ] && SWAP_TOTAL=0
[ -z "$SWAP_FREE" ] && SWAP_FREE=0

MEM_USED=$(( MEM_TOTAL > MEM_AVAIL ? MEM_TOTAL - MEM_AVAIL : 0 ))
SWAP_USED=$(( SWAP_TOTAL > SWAP_FREE ? SWAP_TOTAL - SWAP_FREE : 0 ))

MEM_PERCENT=0.0
if [ "$MEM_TOTAL" -gt 0 ]; then
    MEM_PERCENT=$(awk "BEGIN {printf \"%.2f\", ($MEM_USED / $MEM_TOTAL) * 100}")
fi

SWAP_PERCENT=0.0
if [ "$SWAP_TOTAL" -gt 0 ]; then
    SWAP_PERCENT=$(awk "BEGIN {printf \"%.2f\", ($SWAP_USED / $SWAP_TOTAL) * 100}")
fi

# Load Average
LOAD_1M=0.0
LOAD_5M=0.0
LOAD_15M=0.0
if [ -f /proc/loadavg ]; then
    LOAD_1M=$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo "0.0")
    LOAD_5M=$(awk '{print $2}' /proc/loadavg 2>/dev/null || echo "0.0")
    LOAD_15M=$(awk '{print $3}' /proc/loadavg 2>/dev/null || echo "0.0")
fi

# CPU Usage Calculation
CPU_USAGE=0.0
if [ -f /proc/stat ]; then
    # Sample 1
    read -r cpu u1 n1 s1 i1 w1 q1 sq1 st1 _ < /proc/stat
    t1=$((u1 + n1 + s1 + i1 + w1 + q1 + sq1 + st1))
    idle1=$((i1 + w1))

    sleep 0.2

    # Sample 2
    read -r cpu u2 n2 s2 i2 w2 q2 sq2 st2 _ < /proc/stat
    t2=$((u2 + n2 + s2 + i2 + w2 + q2 + sq2 + st2))
    idle2=$((i2 + w2))

    total_diff=$((t2 - t1))
    idle_diff=$((idle2 - idle1))

    if [ "$total_diff" -gt 0 ]; then
        CPU_USAGE=$(awk "BEGIN {printf \"%.2f\", (1 - ($idle_diff / $total_diff)) * 100}")
    fi
elif command -v top >/dev/null 2>&1; then
    CPU_USAGE=$(top -bn1 2>/dev/null | grep -E "Cpu|CPU" | head -n1 | awk '{print $2}' | tr -d '%us,' || echo "0.0")
fi

[ -z "$CPU_USAGE" ] && CPU_USAGE=0.0

cat <<EOF
{
  "status": "ok",
  "timestamp": "$TIMESTAMP",
  "data": {
    "cpu": {
      "usage_percent": $CPU_USAGE,
      "load_1m": $LOAD_1M,
      "load_5m": $LOAD_5M,
      "load_15m": $LOAD_15M
    },
    "memory": {
      "total_mb": $MEM_TOTAL,
      "used_mb": $MEM_USED,
      "free_mb": $MEM_FREE,
      "available_mb": $MEM_AVAIL,
      "usage_percent": $MEM_PERCENT
    },
    "swap": {
      "total_mb": $SWAP_TOTAL,
      "used_mb": $SWAP_USED,
      "free_mb": $SWAP_FREE,
      "usage_percent": $SWAP_PERCENT
    }
  }
}
EOF
