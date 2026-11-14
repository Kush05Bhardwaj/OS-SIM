#!/usr/bin/env bash
# health_check.sh: Verifies subsystem dependencies, CLI utilities, and procfs availability
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

REQUIRED_CMDS=("awk" "sed" "grep" "df" "ps" "uname")
ALL_HEALTHY=true
CMDS_JSON=""
FIRST=true

for cmd in "${REQUIRED_CMDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        STATUS="true"
    else
        STATUS="false"
        ALL_HEALTHY=false
    fi

    ENTRY="\"$cmd\": $STATUS"
    if [ "$FIRST" = true ]; then
        CMDS_JSON="$ENTRY"
        FIRST=false
    else
        CMDS_JSON="$CMDS_JSON, $ENTRY"
    fi
done

# Check optional commands
FREE_AVAILABLE=false
if command -v free >/dev/null 2>&1; then
    FREE_AVAILABLE=true
fi
CMDS_JSON="$CMDS_JSON, \"free\": $FREE_AVAILABLE"

# Check procfs files
PROCFS_MEMINFO=false
[ -r /proc/meminfo ] && PROCFS_MEMINFO=true

PROCFS_STAT=false
[ -r /proc/stat ] && PROCFS_STAT=true

PROCFS_UPTIME=false
[ -r /proc/uptime ] && PROCFS_UPTIME=true

PROCFS_CPUINFO=false
[ -r /proc/cpuinfo ] && PROCFS_CPUINFO=true

SUBSYSTEM="unknown"
if [ -f /proc/version ]; then
    if grep -qi "microsoft" /proc/version; then
        SUBSYSTEM="wsl"
    else
        SUBSYSTEM="native_linux"
    fi
elif uname -s | grep -qi "mingw\|msys\|cygwin"; then
    SUBSYSTEM="git_bash"
fi

cat <<EOF
{
  "status": "ok",
  "timestamp": "$TIMESTAMP",
  "data": {
    "subsystem": "$SUBSYSTEM",
    "all_healthy": $ALL_HEALTHY,
    "commands": {
      $CMDS_JSON
    },
    "procfs": {
      "meminfo": $PROCFS_MEMINFO,
      "stat": $PROCFS_STAT,
      "uptime": $PROCFS_UPTIME,
      "cpuinfo": $PROCFS_CPUINFO
    }
  }
}
EOF
