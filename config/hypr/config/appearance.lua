
-- ==========================================
-- Tokyo Night Storm appearance
-- ==========================================

local c = require("colors.tokyo-night")

hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 10,

        border_size = 2,

        col = {
            active_border = {
                colors = {
                    "rgba(" .. c.blue .. "ee)",
                    "rgba(" .. c.purple .. "ee)",
                },
                angle = 45,
            },

            inactive_border =
                "rgba(" .. c.border_inactive .. "aa)",
        },

        resize_on_border = true,
        allow_tearing = false,
        layout = "dwindle",
    },

    decoration = {
        rounding = 10,
        rounding_power = 2,

        active_opacity = 0.96,
        inactive_opacity = 0.90,

        shadow = {
            enabled = true,
            range = 12,
            render_power = 3,
            color = 0xee1a1a1a,
        },

        blur = {
            enabled = true,
            size = 6,
            passes = 2,
            vibrancy = 0.15,
        },
    },

    dwindle = {
        preserve_split = true,
    },
})

