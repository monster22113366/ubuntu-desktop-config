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
set_brightness() {
    local target="$1" session reply object
    brightnessctl -d "$name" set "$target" >/dev/null 2>&1 && return 0
    # Ubuntu's brightnessctl may lack logind support; use the active user's
    # session API rather than requiring root or changing sysfs permissions.
    session=${XDG_SESSION_ID:-$(loginctl show-user "$(id -u)" -p Display --value)}
    [[ -n "$session" ]] || return 1
    reply=$(busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager GetSession s "$session") || return 1
    object=$(printf '%s' "$reply" | cut -d '"' -f 2)
    busctl call org.freedesktop.login1 "$object" org.freedesktop.login1.Session SetBrightness ssu backlight "$name" "$target"
}
case "$action" in
    up) set_brightness "$(( current + maximum / 20 > maximum ? maximum : current + maximum / 20 ))" ;;
    down) set_brightness "$(( current - maximum / 20 < 1 ? 1 : current - maximum / 20 ))" ;;
esac
current=$(brightnessctl -d "$name" get)
[[ "$current" =~ ^[0-9]+$ ]] || exit 1
value=$((current * 100 / maximum))
printf '{"text":"󰃠 %s%%","class":"normal","tooltip":"屏幕亮度：%s%%"}\n' "$value" "$value"
