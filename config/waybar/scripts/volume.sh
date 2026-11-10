#!/usr/bin/env bash
set -euo pipefail
SINK="@DEFAULT_AUDIO_SINK@"
action=${1:-status}
case "$action" in status|toggle|up|down) ;; *) exit 2 ;; esac
volume=$(wpctl get-volume "$SINK" 2>/dev/null) || {
    printf '{"text":"󰖁 N/A","class":"unavailable","tooltip":"默认音频输出不可用"}\n'
    [[ "$action" == status ]] && exit 0
    exit 1
}
case "$action" in
    toggle) wpctl set-mute "$SINK" toggle ;;
    up) wpctl set-volume -l 1.5 "$SINK" 5%+ ;;
    down) wpctl set-volume "$SINK" 5%- ;;
esac
volume=$(wpctl get-volume "$SINK")
value=$(awk '{printf "%d", $2 * 100}' <<< "$volume")
if [[ "$volume" == *MUTED* ]]; then
    printf '{"text":"󰖁 %s%%","class":"muted","tooltip":"音量已静音"}\n' "$value"
else
    printf '{"text":"󰕾 %s%%","class":"normal","tooltip":"当前音量：%s%%"}\n' "$value" "$value"
fi
