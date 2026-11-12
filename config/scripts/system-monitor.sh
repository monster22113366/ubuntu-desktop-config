#!/usr/bin/env bash
set -euo pipefail

CONFIG="$HOME/.config/wofi/config"
STYLE="$HOME/.config/wofi/style.css"

# CPU / SSD temperature
hardware=$(timeout 5 bash "$HOME/Projects/ubuntu-desktop-config/config/waybar/scripts/hardware.sh" 2>/dev/null) || hardware='{}'
hardware_text=$(jq -er '.text // empty' <<< "$hardware" 2>/dev/null) || hardware_text="CPU / SSD / FAN：不可用"

# NVIDIA GPU
gpu=$(timeout 5 bash "$HOME/Projects/ubuntu-desktop-config/config/waybar/scripts/nvidia.sh" 2>/dev/null) || gpu='{}'
gpu_text=$(jq -er '.text // empty' <<< "$gpu" 2>/dev/null) || gpu_text="GPU：不可用"

# Include the existing auto-detected Intel/NVIDIA resource sampler.
resources=$(timeout 5 python3 "$HOME/.config/tmux/scripts/resources.py" 2>/dev/null) || resources="GPU 采样不可用"

# Memory
memory=$(free -h | awk '/^Mem:/ {
    printf "%s / %s", $3, $2
}')

# Root filesystem
disk=$(df -h / | awk 'NR==2 {
    printf "%s / %s (%s)", $3, $2, $5
}')

# CPU load
load=$(awk '{print $1, $2, $3}' /proc/loadavg)

# Battery
battery="N/A"

for capacity in /sys/class/power_supply/BAT*/capacity; do
    if [[ -r "$capacity" ]]; then
        battery="$(cat "$capacity")%"
        break
    fi
done

# System uptime
uptime_text=$(uptime -p)

{
    echo "━━━ SYSTEM ━━━"
    echo "运行时间：$uptime_text"
    echo "CPU Load：$load"

    echo ""
    echo "━━━ HARDWARE ━━━"
    echo "$hardware_text"
    echo "$gpu_text"
    echo "$resources"

    echo ""
    echo "━━━ MEMORY & STORAGE ━━━"
    echo "内存：$memory"
    echo "系统磁盘：$disk"
    echo "电池：$battery"

    echo ""
    echo "━━━ SHORTCUT ━━━"
    echo "ESC：关闭面板"
} | wofi \
    --conf "$CONFIG" \
    --style "$STYLE" \
    --dmenu \
    --prompt "系统状态" \
    --width 680 \
    --height 420 >/dev/null || {
    status=$?
    (( status == 1 )) || exit "$status"
}
