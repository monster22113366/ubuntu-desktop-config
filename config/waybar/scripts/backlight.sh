#!/usr/bin/env bash
set -euo pipefail

action=${1:-status}
case "$action" in status|up|down) ;; *) exit 2 ;; esac
unavailable() {
    printf '{"text":"󰃠 N/A","class":"unavailable","tooltip":"未检测到可用背光设备"}\n'
    [[ "$action" == status ]]
}
command -v brightnessctl >/dev/null || { unavailable; exit $?; }
# brightnessctl selects a real backlight (not keyboard LEDs); no fixed device name.
device=$(brightnessctl --class=backlight --machine-readable info 2>/dev/null) || { unavailable; exit $?; }
IFS=, read -r name kind current percent maximum <<< "$device"
[[ "$kind" == backlight && "$maximum" =~ ^[1-9][0-9]*$ && "$current" =~ ^[0-9]+$ ]] || { unavailable; exit $?; }
case "$action" in
    up) brightnessctl -d "$name" --min-value=1 set +5% >/dev/null ;;
    down) brightnessctl -d "$name" --min-value=1 set 5%- >/dev/null ;;
esac
current=$(brightnessctl -d "$name" get)
[[ "$current" =~ ^[0-9]+$ ]] || exit 1
value=$((current * 100 / maximum))
printf '{"text":"󰃠 %s%%","class":"normal","tooltip":"屏幕亮度：%s%%"}\n' "$value" "$value"
