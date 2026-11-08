
#!/usr/bin/env bash
set -euo pipefail

SINK="@DEFAULT_AUDIO_SINK@"

case "${1:-}" in
    toggle)
        wpctl set-mute "$SINK" toggle
        ;;
    up)
        wpctl set-volume -l 1.5 "$SINK" 5%+
        ;;
    down)
        wpctl set-volume "$SINK" 5%-
        ;;
esac

volume=$(wpctl get-volume "$SINK")
value=$(awk '{printf "%d", $2 * 100}' <<< "$volume")

if [[ "$volume" == *MUTED* ]]; then
    printf '{"text":"󰖁 %s%%","class":"muted","tooltip":"音量已静音"}\n' "$value"
else
    printf '{"text":"󰕾 %s%%","class":"normal","tooltip":"当前音量：%s%%"}\n' "$value" "$value"
fi

