
#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# Waybar Power Menu
# Hyprland + Wofi
# ==========================================

choose() {
    printf '%s\n' "$@" | wofi \
        --dmenu \
        --prompt "$1" \
        --width 240 \
        --height 280
}

confirm() {
    local action="$1"

    local choice
    choice=$(printf '%s\n' "取消" "确认${action}" | wofi \
        --dmenu \
        --prompt "确认${action}？" \
        --width 240 \
        --height 120) || return 1

    [[ "$choice" == "确认${action}" ]]
}

# Main menu
choice=$(printf '%s\n' \
    "锁屏" \
    "睡眠" \
    "注销" \
    "重启" \
    "关机" |
    wofi --dmenu \
        --prompt "电源菜单" \
        --width 240 \
        --height 280) || exit 0

case "$choice" in
    锁屏)
        exec hyprlock
        ;;

    睡眠)
        # Start lockscreen before suspending
        hyprlock &
        sleep 1
        systemctl suspend
        ;;

    注销)
        hyprctl dispatch exit
        ;;

    重启)
        if confirm "重启"; then
            systemctl reboot
        fi
        ;;

    关机)
        if confirm "关机"; then
            systemctl poweroff
        fi
        ;;
esac

