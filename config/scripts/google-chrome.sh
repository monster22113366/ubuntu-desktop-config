#!/bin/sh
set -eu

# Google Chrome with Clash Verge proxy
exec /usr/bin/google-chrome \
    --proxy-server="http://127.0.0.1:7897" \
    "$@"
