#!/usr/bin/env bash
set -euo pipefail

CONFIG="$HOME/.config/wofi/config"
STYLE="$HOME/.config/wofi/style.css"

# Descriptions in keybinds.lua are the only help text source: 分组｜说明.
# Read IPC before formatting so failures cannot disappear in process substitution.
for dependency in hyprctl jq wofi; do
    command -v "$dependency" >/dev/null || { echo "缺少依赖：$dependency" >&2; exit 1; }
done
bindings=$(hyprctl -j binds)
rows=$(jq -er '
    [.[] | select(.has_description and .description != "" and .key != "")]
    | sort_by(.description | split("｜")[0])
    | .[]
    | ([if (.modmask / 64 | floor % 2) == 1 then "Super" else empty end,
        if (.modmask / 4 | floor % 2) == 1 then "Ctrl" else empty end,
        if (.modmask / 8 | floor % 2) == 1 then "Alt" else empty end,
        if (.modmask % 2) == 1 then "Shift" else empty end,
        (.key | ascii_upcase | if . == "LEFT" then "←" elif . == "RIGHT" then "→"
          elif . == "UP" then "↑" elif . == "DOWN" then "↓"
          elif . == "MOUSE:272" then "左键拖动" elif . == "MOUSE:273" then "右键拖动"
          else . end)] | join(" + ")) as $keys
    | (if .submap != "" then "[\(.submap)] " else "" end)
      + .description + "    " + $keys
' <<< "$bindings")
printf '%s\n' "$rows" | wofi \
    --conf "$CONFIG" --style "$STYLE" --dmenu \
    --prompt "快捷键速查（Esc 关闭）" --width 900 --height 650 >/dev/null || {
    status=$?
    # Wofi uses 1 for an ordinary Escape/cancel.
    (( status == 1 )) || exit "$status"
}
