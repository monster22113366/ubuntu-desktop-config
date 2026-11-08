
#!/usr/bin/env bash

# NVIDIA GPU monitoring for Waybar
# Output: compact JSON

set -euo pipefail

if ! command -v nvidia-smi >/dev/null 2>&1; then
    printf '{"text":"GPU N/A","class":"unavailable"}\n'
    exit 0
fi

data=$(nvidia-smi \
    --query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw \
    --format=csv,noheader,nounits 2>/dev/null) || {
    printf '{"text":"GPU N/A","class":"unavailable"}\n'
    exit 0
}

IFS=',' read -r temp util mem_used mem_total power <<< "$data"

# Remove whitespace
temp=${temp//[[:space:]]/}
util=${util//[[:space:]]/}
mem_used=${mem_used//[[:space:]]/}
mem_total=${mem_total//[[:space:]]/}
power=${power//[[:space:]]/}

# Validate data
if [[ ! "$temp" =~ ^[0-9]+$ ]]; then
    printf '{"text":"GPU N/A","class":"unavailable"}\n'
    exit 0
fi

# Temperature-based status
if (( temp >= 85 )); then
    class="critical"
elif (( temp >= 75 )); then
    class="warning"
else
    class="normal"
fi

printf '{"text":"GPU %s°C %s%% VRAM %s/%s MiB %.1fW","tooltip":"NVIDIA GeForce RTX 4060 Laptop GPU","class":"%s"}\n' \
    "$temp" "$util" "$mem_used" "$mem_total" "$power" "$class"

