#!/usr/bin/env bash
set -euo pipefail

PICTURES_DIR="$(xdg-user-dir PICTURES)"
SCREENSHOT_DIR="$PICTURES_DIR/Screenshots"

mkdir -p "$SCREENSHOT_DIR"

OUTPUT="$SCREENSHOT_DIR/screenshot-$(date +%Y%m%d-%H%M%S).png"

grim -g "$(slurp)" "$OUTPUT"

notify-send "Screenshot" "Saved to $OUTPUT"
