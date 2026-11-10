
#!/usr/bin/env bash
set -uo pipefail

# ==========================================
# Proxy Status Monitor
# ==========================================
# Hardware-independent except for local proxy
# endpoint and port.
#
# Adapt these values when migrating to another
# proxy client or changing its local port.
# ==========================================

PROXY_URL="http://127.0.0.1:7897"
TEST_URL="https://chatgpt.com"
TIMEOUT=8

# Check whether curl is available.
if ! command -v curl >/dev/null 2>&1; then
    printf '{"text":"PROXY N/A","class":"unavailable","tooltip":"curl 未安装"}\n'
    exit 0
fi

# Check local proxy port.
if ! timeout 2 bash -c \
    "echo > /dev/tcp/127.0.0.1/7897" 2>/dev/null; then

    printf '{"text":"PROXY OFF","class":"critical","tooltip":"本地代理端口未监听"}\n'
    exit 0
fi

# Test actual connectivity through the proxy.
http_code=$(curl \
    --silent \
    --show-error \
    --head \
    --output /dev/null \
    --write-out '%{http_code}' \
    --proxy "$PROXY_URL" \
    --noproxy "" \
    --connect-timeout 3 \
    --max-time "$TIMEOUT" \
    "$TEST_URL" 2>/dev/null) || http_code="000"

if [[ "$http_code" =~ ^[23][0-9][0-9]$ ]]; then
    printf '{"text":"PROXY OK","class":"normal","tooltip":"代理可用\\nHTTP: %s\\n目标: %s"}\n' \
        "$http_code" "$TEST_URL"
else
    printf '{"text":"PROXY ON","class":"warning","tooltip":"本地代理端口已监听；目标探测未通过（不代表代理关闭）\\nHTTP: %s"}\n' \
        "$http_code"
fi

