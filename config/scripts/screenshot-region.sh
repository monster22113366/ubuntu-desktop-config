#!/usr/bin/env bash
set -euo pipefail

for dependency in grim slurp xdg-user-dir; do
    command -v "$dependency" >/dev/null || { echo "缺少依赖：$dependency" >&2; exit 1; }
done
# Esc must stop here rather than invoking grim with an invalid empty geometry.
geometry=$(slurp) || exit 0
[[ -n "$geometry" ]] || exit 0
PICTURES_DIR=$(xdg-user-dir PICTURES)
SCREENSHOT_DIR="${PICTURES_DIR:-$HOME/Pictures}/Screenshots"
mkdir -p "$SCREENSHOT_DIR"
OUTPUT=$(mktemp "$SCREENSHOT_DIR/screenshot-$(date +%Y%m%d-%H%M%S)-XXXXXX.png")
if ! grim -g "$geometry" "$OUTPUT"; then
    rm -f -- "$OUTPUT"
    exit 1
fi
notify-send "截图" "已保存到 $OUTPUT" || true
