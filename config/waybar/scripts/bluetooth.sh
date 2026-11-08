
#!/usr/bin/env bash
set -euo pipefail

# Check Bluetooth controller availability.
controller=$(bluetoothctl show 2>/dev/null || true)

if [[ -z "$controller" || "$controller" != *"Controller "* ]]; then
    printf '{"text":"󰂲","class":"unavailable","tooltip":"未检测到蓝牙适配器"}\n'
    exit 0
fi

case "${1:-}" in
    toggle)
        if grep -q "Powered: yes" <<< "$controller"; then
            bluetoothctl power off >/dev/null
        else
            bluetoothctl power on >/dev/null
        fi
        controller=$(bluetoothctl show 2>/dev/null || true)
        ;;
esac

if grep -q "Powered: yes" <<< "$controller"; then
    printf '{"text":"󰂯","class":"enabled","tooltip":"蓝牙已开启"}\n'
else
    printf '{"text":"󰂲","class":"disabled","tooltip":"蓝牙已关闭"}\n'
fi

