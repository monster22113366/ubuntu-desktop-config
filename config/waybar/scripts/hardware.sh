
#!/usr/bin/env bash

# Hardware monitoring via detected hwmon sensors
# CPU / NVMe / Fan

set -euo pipefail

read_temp() {
    local path="$1"
    if [[ -r "$path" ]]; then
        awk '{printf "%.0f", $1 / 1000}' "$path"
    else
        echo "N/A"
    fi
}

# Locate sensors dynamically rather than relying on hwmon numbering
find_hwmon() {
    local target="$1"
    for h in /sys/class/hwmon/hwmon*; do
        [[ -r "$h/name" ]] || continue
        if [[ "$(cat "$h/name")" == "$target" ]]; then
            echo "$h"
            return 0
        fi
    done
    return 1
}

coretemp=$(find_hwmon coretemp || true)
nvme=$(find_hwmon nvme || true)
fan=$(find_hwmon acpi_fan || true)

cpu_temp="N/A"
nvme_temp="N/A"
fan_rpm="N/A"

[[ -n "$coretemp" ]] && \
    cpu_temp=$(read_temp "$coretemp/temp1_input")

[[ -n "$nvme" ]] && \
    nvme_temp=$(read_temp "$nvme/temp1_input")

[[ -n "$fan" && -r "$fan/fan1_input" ]] && \
    fan_rpm=$(cat "$fan/fan1_input")

# CPU temperature classification
cpu_class="normal"
if [[ "$cpu_temp" =~ ^[0-9]+$ ]]; then
    (( cpu_temp >= 90 )) && cpu_class="critical" ||
    (( cpu_temp >= 80 )) && cpu_class="warning"
fi

# NVMe temperature classification
nvme_class="normal"
if [[ "$nvme_temp" =~ ^[0-9]+$ ]]; then
    (( nvme_temp >= 75 )) && nvme_class="critical" ||
    (( nvme_temp >= 65 )) && nvme_class="warning"
fi

printf '{"text":"CPU %s°C | SSD %s°C | FAN %s RPM","tooltip":"CPU Package: %s°C\\nNVMe Composite: %s°C\\nFan: %s RPM","class":"%s","percentage":%s}\n' \
    "$cpu_temp" "$nvme_temp" "$fan_rpm" \
    "$cpu_temp" "$nvme_temp" "$fan_rpm" \
    "$cpu_class" \
    "${cpu_temp:-0}"
