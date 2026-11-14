#!/usr/bin/env bash
# disk_monitor.sh: Collects mounted filesystems and storage utilization formatted as JSON
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

PARTITIONS_JSON=$(df -Pk 2>/dev/null | awk '
BEGIN {
    first = 1
}
NR > 1 {
    # In df -Pk:
    # NF is mountpoint
    # NF-1 is capacity %
    # NF-2 is available
    # NF-3 is used
    # NF-4 is total blocks
    # Everything from 1 to NF-5 is the filesystem name
    
    target = $NF
    pcent = $(NF-1)
    avail = $(NF-2)
    used = $(NF-3)
    blocks = $(NF-4)
    
    fs = ""
    for (i = 1; i <= NF-5; i++) {
        fs = (fs == "" ? $i : fs " " $i)
    }
    if (fs == "") {
        fs = $1
    }
    
    # Filter out common pseudo-filesystems unless mounted on /
    if ((fs == "none" || fs == "udev" || fs == "tmpfs" || fs == "devtmpfs") && target != "/") {
        next
    }
    
    # Clean percentage
    gsub("%", "", pcent)
    if (pcent !~ /^[0-9]+$/) {
        pcent = 0
    }
    
    # Convert blocks (1KB) to GB with 2 decimals
    total_gb = (blocks ~ /^[0-9]+$/ && blocks > 0) ? sprintf("%.2f", blocks / 1048576) : "0.00"
    used_gb  = (used ~ /^[0-9]+$/ && used > 0) ? sprintf("%.2f", used / 1048576) : "0.00"
    avail_gb = (avail ~ /^[0-9]+$/ && avail > 0) ? sprintf("%.2f", avail / 1048576) : "0.00"
    
    # Escape quotes
    gsub("\"", "\\\"", fs)
    gsub("\"", "\\\"", target)
    
    if (!first) {
        printf ",\n"
    }
    first = 0
    
    printf "      {\n"
    printf "        \"filesystem\": \"%s\",\n", fs
    printf "        \"mountpoint\": \"%s\",\n", target
    printf "        \"total_gb\": %s,\n", total_gb
    printf "        \"used_gb\": %s,\n", used_gb
    printf "        \"available_gb\": %s,\n", avail_gb
    printf "        \"usage_percent\": %s\n", pcent
    printf "      }"
}
END {
    printf "\n"
}
')

cat <<EOF
{
  "status": "ok",
  "timestamp": "$TIMESTAMP",
  "data": {
    "partitions": [
$PARTITIONS_JSON
    ]
  }
}
EOF
