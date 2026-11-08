#!/usr/bin/env bash
set -euo pipefail

# Hardware-specific configuration
DEVICE="nvidia_wmi_ec_backlight"
SYS_PATH="/sys/class/backlight/$DEVICE"

case "${1:-}" in
    up)
        brightnessctl -d "$DEVICE" set +5% >/dev/null
        ;;
    down)
        brightnessctl -d "$DEVICE" set 5%- >/dev/null
        ;;
esac

# Read standard Linux sysfs interface
current=$(<"$SYS_PATH/brightness")
maximum=$(<"$SYS_PATH/max_brightness")

if (( maximum > 0 )); then
    value=$((current * 100 / maximum))
else
    value=0
fi

printf '{"text":"󰃠 %s%%","tooltip":"屏幕亮度：%s%%"}\n' \
    "$value" "$value"
