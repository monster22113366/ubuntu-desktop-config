#!/usr/bin/env bash
set -euo pipefail
action=${1:-status}
case "$action" in status|toggle|on|off) ;; *) exit 2 ;; esac
controller=$(timeout 5 bluetoothctl show 2>/dev/null || true)
if [[ "$controller" != *"Controller "* ]]; then
    printf '{"text":"󰂲","class":"unavailable","tooltip":"未检测到蓝牙适配器"}\n'
    [[ "$action" == status ]] && exit 0
    exit 1
fi
if [[ "$action" == toggle ]]; then
    if [[ "$controller" == *"Powered: yes"* ]]; then action=off; else action=on; fi
fi
if [[ "$action" == on || "$action" == off ]]; then
    timeout 5 bluetoothctl power "$action" >/dev/null
    controller=$(timeout 5 bluetoothctl show 2>/dev/null)
    expected=no
    [[ "$action" == on ]] && expected=yes
    [[ "$controller" == *"Powered: $expected"* ]] || exit 1
fi
if [[ "$controller" == *"Powered: yes"* ]]; then
    printf '{"text":"󰂯","class":"enabled","tooltip":"蓝牙已开启"}\n'
else
    printf '{"text":"󰂲","class":"disabled","tooltip":"蓝牙已关闭"}\n'
fi
