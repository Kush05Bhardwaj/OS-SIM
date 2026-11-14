#!/usr/bin/env bash
# process_monitor.sh: Inspects active processes sorted by CPU or Memory formatted as JSON
set -euo pipefail

LIMIT="${1:-10}"
SORT_KEY="${2:-cpu}"

# Validate limit
if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [ "$LIMIT" -le 0 ]; then
    LIMIT=10
fi

SORT_FLAG="-%cpu"
if [ "$SORT_KEY" = "mem" ] || [ "$SORT_KEY" = "memory" ]; then
    SORT_FLAG="-%mem"
    SORT_KEY="memory"
else
    SORT_KEY="cpu"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

PROCESSES_JSON=""
FIRST=true

# Try Linux standard ps with custom formatting and sorting
RAW_PS=$(ps -eo pid,user,%cpu,%mem,stat,comm --sort="$SORT_FLAG" 2>/dev/null || echo "")

if [ -n "$RAW_PS" ] && [ "$(echo "$RAW_PS" | wc -l)" -gt 1 ]; then
    while read -r pid user cpu mem stat comm; do
        [ "$pid" = "PID" ] && continue
        [ -z "$pid" ] && continue

        CLEAN_USER=$(echo "$user" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
        CLEAN_COMM=$(echo "$comm" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
        CLEAN_STAT=$(echo "$stat" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

        # Ensure cpu and mem are floats
        [[ ! "$cpu" =~ ^[0-9]+(\.[0-9]+)?$ ]] && cpu="0.0"
        [[ ! "$mem" =~ ^[0-9]+(\.[0-9]+)?$ ]] && mem="0.0"

        ENTRY=$(cat <<EOF
      {
        "pid": $pid,
        "user": "$CLEAN_USER",
        "name": "$CLEAN_COMM",
        "cpu_percent": $cpu,
        "memory_percent": $mem,
        "status": "$CLEAN_STAT"
      }
EOF
)

        if [ "$FIRST" = true ]; then
            PROCESSES_JSON="$ENTRY"
            FIRST=false
        else
            PROCESSES_JSON="$PROCESSES_JSON,
$ENTRY"
        fi
    done < <(echo "$RAW_PS" | head -n "$((LIMIT + 1))")
else
    # Fallback for MSYS/Git-Bash/BSD ps
    while read -r uid pid ppid tty stime comm; do
        [ "$uid" = "UID" ] && continue
        [ -z "$pid" ] && continue

        CLEAN_USER=$(echo "$uid" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')
        CLEAN_COMM=$(echo "$comm" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

        ENTRY=$(cat <<EOF
      {
        "pid": $pid,
        "user": "$CLEAN_USER",
        "name": "$CLEAN_COMM",
        "cpu_percent": 0.0,
        "memory_percent": 0.0,
        "status": "R"
      }
EOF
)

        if [ "$FIRST" = true ]; then
            PROCESSES_JSON="$ENTRY"
            FIRST=false
        else
            PROCESSES_JSON="$PROCESSES_JSON,
$ENTRY"
        fi
    done < <(ps -ef 2>/dev/null | head -n "$((LIMIT + 1))" || echo "")
fi

cat <<EOF
{
  "status": "ok",
  "timestamp": "$TIMESTAMP",
  "data": {
    "limit": $LIMIT,
    "sort_by": "$SORT_KEY",
    "processes": [
$PROCESSES_JSON
    ]
  }
}
EOF
