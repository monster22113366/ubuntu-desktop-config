#!/usr/bin/env bash
set -euo pipefail

for dependency in grim slurp wl-copy; do
    command -v "$dependency" >/dev/null || { echo "缺少依赖：$dependency" >&2; exit 1; }
done
geometry=$(slurp) || exit 0
[[ -n "$geometry" ]] || exit 0
# Capture fully before replacing the clipboard; a grim failure preserves it.
image=$(mktemp --suffix=.png)
trap 'rm -f -- "$image"' EXIT
grim -g "$geometry" "$image"
wl-copy --type image/png < "$image"
notify-send "截图" "已复制到剪贴板" || true
