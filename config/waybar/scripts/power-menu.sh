#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
# Wofi 1.4.1 requires a seekable CSS file; process-substitution FIFOs can crash it.
style=$(mktemp --suffix=.css)
trap 'rm -f -- "$style"' EXIT
cat "$ROOT/wofi/style.css" "$ROOT/wofi/power-menu.css" > "$style"

# No history reordering, search box or free-form action. Entries return indices.
# Use an empty config so user search/submit overrides cannot weaken confirmation.
menu() {
    local prompt="$1" height="$2"
    shift 2
    printf '%s\n' "$@" | wofi \
        --conf /dev/null --style "$style" \
        --dmenu --prompt "$prompt" --width 380 --height "$height" \
        --cache-file /dev/null --sort-order default \
        --define hide_search=true --define exec_search=false \
        --define allow_markup=false --define allow_images=false \
        --define dmenu-print_line_num=true
}

confirm() {
    local choice
    # The visible labels identify the action even though search is hidden.
    choice=$(menu "$1确认" 200 "取消$1（默认）" "确认$1") || return 1
    [[ "$choice" == 1 ]]
}

choice=$(menu "电源菜单" 360 "锁屏" "睡眠" "注销" "重启" "关机") || exit 0
case "$choice" in
    0) hyprlock ;;
    1)
        # Preserve the existing working lock-before-suspend sequence.
        if ! pgrep -x hyprlock >/dev/null; then
            hyprlock &
            locker=$!
            sleep 1
            kill -0 "$locker" 2>/dev/null || {
                notify-send -u critical "睡眠取消" "锁屏程序启动失败" || true
                exit 1
            }
        fi
        systemctl suspend
        ;;
    2) hyprctl eval 'hl.dispatch(hl.dsp.exit())' ;;
    3) if confirm "重启"; then systemctl reboot; fi ;;
    4) if confirm "关机"; then systemctl poweroff; fi ;;
esac
