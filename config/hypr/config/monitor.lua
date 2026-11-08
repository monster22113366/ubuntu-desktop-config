-- ==========================================
-- Monitor Configuration
-- ==========================================

local hardware = require("profiles.hardware")

for _, monitor in ipairs(hardware.monitors) do
    hl.monitor({
        output = monitor.name,
        mode = monitor.mode,
        position = monitor.position,
        scale = monitor.scale,
    })
end
