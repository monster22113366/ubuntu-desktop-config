
-- ==========================================
-- Tokyo Night Storm appearance
-- ==========================================

local c = require("colors.tokyo-night")

hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 10,

        border_size = 3,

        col = {
            active_border = {
                colors = {
                    "rgba(" .. c.blue .. "ff)",
                    "rgba(" .. c.purple .. "ff)",
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
            -- Outer neon approximation: native colored shadow, not bloom.
            -- decoration.glow in 0.57.1 is INNER glow; keep text unobscured.
            enabled = true,
            range = 26,
            render_power = 2,
            color = {
                colors = {
                    "rgba(" .. c.blue .. "cc)",
                    "rgba(" .. c.purple .. "cc)",
                },
                angle = 45,
            },
            color_inactive = "rgba(" .. c.bg_dark .. "00)",
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

