#!/usr/bin/env bash
set -euo pipefail

trap 'notify-send "设备控制" "操作失败，请检查设备连接和依赖" || true' ERR

CONFIG="$HOME/.config/wofi/config"
STYLE="$HOME/.config/wofi/style.css"

VOLUME_SCRIPT="$HOME/Projects/ubuntu-desktop-config/config/waybar/scripts/volume.sh"
BACKLIGHT_SCRIPT="$HOME/Projects/ubuntu-desktop-config/config/waybar/scripts/backlight.sh"

BLUETOOTH_SCRIPT="$HOME/Projects/ubuntu-desktop-config/config/waybar/scripts/bluetooth.sh"

# Read current volume
volume_info=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null || true)

if [[ -n "$volume_info" ]]; then
    volume=$(awk '{printf "%.0f%%", $2 * 100}' <<< "$volume_info")
    [[ "$volume_info" == *MUTED* ]] && volume="静音"
else
    volume="N/A"
fi

# Read Bluetooth state
bluetooth_info=$(timeout 5 bluetoothctl show 2>/dev/null || true)

if [[ "$bluetooth_info" == *"Powered: yes"* ]]; then
    bluetooth="开启"
    bluetooth_action="关闭蓝牙"
elif [[ "$bluetooth_info" == *"Powered: no"* ]]; then
    bluetooth="关闭"
    bluetooth_action="开启蓝牙"
else
    bluetooth="不可用"
    bluetooth_action=""
fi

backlight=$(bash "$BACKLIGHT_SCRIPT" 2>/dev/null) || backlight='{}'
brightness=$(jq -r '.text // "亮度不可用"' <<< "$backlight" 2>/dev/null) || brightness="亮度不可用"

options=(
    "当前音量：$volume"
    "音量 +5%"
    "音量 -5%"
    "切换静音"
    "蓝牙：$bluetooth"
    "背光：$brightness"
    "亮度 +5%"
    "亮度 -5%"
)

if [[ -n "$bluetooth_action" ]]; then
    options+=("$bluetooth_action")
fi

choice=$(printf '%s\n' "${options[@]}" |
    wofi \
        --conf "$CONFIG" \
        --style "$STYLE" \
        --dmenu \
        --prompt "设备控制：音量 / 蓝牙 / 背光" \
        --width 420 \
        --height 560 \
        --cache-file /dev/null) || {
    status=$?
    (( status == 1 )) && exit 0
    exit "$status"
}

case "$choice" in
    "音量 +5%")
        bash "$VOLUME_SCRIPT" up >/dev/null
        notify-send "音量控制" "音量已增加" || true
        ;;

    "音量 -5%")
        bash "$VOLUME_SCRIPT" down >/dev/null
        notify-send "音量控制" "音量已降低" || true
        ;;

    "切换静音")
        bash "$VOLUME_SCRIPT" toggle >/dev/null
        notify-send "音量控制" "已切换静音状态" || true
        ;;

    "亮度 +5%"|"亮度 -5%")
        action=up
        [[ "$choice" == "亮度 -5%" ]] && action=down
        bash "$BACKLIGHT_SCRIPT" "$action" >/dev/null
        notify-send "背光控制" "亮度已调整" || true
        ;;

    "开启蓝牙"|"关闭蓝牙")
        action=on
        [[ "$choice" == "关闭蓝牙" ]] && action=off
        timeout 12 bash "$BLUETOOTH_SCRIPT" "$action" >/dev/null
        bluetooth_info=$(timeout 5 bluetoothctl show 2>/dev/null || true)
        expected="yes"
        [[ "$choice" == "关闭蓝牙" ]] && expected="no"
        [[ "$bluetooth_info" == *"Powered: $expected"* ]] || {
            notify-send "蓝牙控制" "未能确认状态，设备可能已断开" || true
            exit 1
        }
        notify-send "蓝牙控制" "已执行蓝牙状态切换" || true
        ;;
esac
