
-- ==========================================
-- Hyprland 0.57.1
-- Keyboard bindings
-- Tokyo Night Storm
-- ==========================================

local mod = "SUPER"

-- Native Ubuntu Ghostty with corrected font locale
local ghostty = "env LC_CTYPE=C.UTF-8 /usr/bin/ghostty"

-- Screenshot scripts
local scripts = os.getenv("HOME") ..
    "/Projects/ubuntu-desktop-config/config/scripts"

-- ==========================================
-- 1. Application launching
-- ==========================================

-- Super + G: Ghostty
hl.bind(
    mod .. " + G",
    hl.dsp.exec_cmd(ghostty),
    { description = "Open Ghostty" }
)

-- Super + T: Ghostty + tmux
hl.bind(
    mod .. " + T",
    hl.dsp.exec_cmd(
        ghostty .. " -e tmux new-session -A -s main"
    ),
    { description = "Open Ghostty with tmux" }
)

-- Super + E: Yazi
hl.bind(
    mod .. " + E",
    hl.dsp.exec_cmd(
        ghostty .. " -e yazi"
    ),
    { description = "Open Yazi file manager" }
)

-- Super + D: Application launcher
hl.bind(
    mod .. " + D",
    hl.dsp.exec_cmd("wofi --show drun"),
    { description = "Open application launcher" }
)

-- ==========================================
-- 2. Window switching
-- ==========================================

-- Alt + Tab: Next window
hl.bind(
    "ALT + Tab",
    hl.dsp.window.cycle_next(),
    { description = "Focus next window" }
)

-- Alt + Shift + Tab: Previous window
hl.bind(
    "ALT + SHIFT + Tab",
    hl.dsp.window.cycle_next({ next = false }),
    { description = "Focus previous window" }
)

-- ==========================================
-- 3. Session management
-- ==========================================

-- Super + L: Lock screen
hl.bind(
    mod .. " + L",
    hl.dsp.exec_cmd("hyprlock"),
    { description = "Lock screen" }
)

-- ==========================================
-- 4. Window operations
-- ==========================================

-- Super + X: Close active window
hl.bind(
    mod .. " + X",
    hl.dsp.window.close(),
    { description = "Close active window" }
)

-- Super + H: Minimize active window
hl.bind(
    mod .. " + H",
    function()
        local window = hl.get_active_window()

        if not window then
            return
        end

        hl.dispatch(
            hl.dsp.window.tag({
                tag = "minimized",
                window = window,
            })
        )

        hl.dispatch(
            hl.dsp.window.move({
                workspace = "special:minimized",
                follow = false,
            })
        )
    end,
    { description = "Minimize active window" }
)

-- Super + Shift + H: Restore all minimized windows
hl.bind(
    mod .. " + SHIFT + H",
    function()
        local workspace = hl.get_active_workspace()

        if not workspace then
            return
        end

        hl.dispatch(
            hl.dsp.window.move({
                workspace = workspace,
                window = "tag:minimized",
            })
        )

        hl.dispatch(
            hl.dsp.window.clear_tags({
                window = "tag:minimized",
            })
        )
    end,
    { description = "Restore minimized windows" }
)

-- Super + V: Toggle floating
hl.bind(
    mod .. " + V",
    hl.dsp.window.float({ action = "toggle" }),
    { description = "Toggle floating window" }
)

-- Super + J: Toggle split
hl.bind(
    mod .. " + J",
    hl.dsp.layout("togglesplit"),
    { description = "Toggle split" }
)

-- ==========================================
-- 5. Focus movement
-- ==========================================

hl.bind(
    mod .. " + LEFT",
    hl.dsp.focus({ direction = "left" }),
    { description = "Focus left window" }
)

hl.bind(
    mod .. " + RIGHT",
    hl.dsp.focus({ direction = "right" }),
    { description = "Focus right window" }
)

hl.bind(
    mod .. " + UP",
    hl.dsp.focus({ direction = "up" }),
    { description = "Focus upper window" }
)

hl.bind(
    mod .. " + DOWN",
    hl.dsp.focus({ direction = "down" }),
    { description = "Focus lower window" }
)

-- ==========================================
-- 6. Multi-monitor management
-- ==========================================

-- Super + Shift + Right: Move window to external monitor
hl.bind(
    mod .. " + SHIFT + RIGHT",
    hl.dsp.window.move({
        monitor = "DP-4",
        follow = true,
    }),
    { description = "Move window to external monitor" }
)

-- Super + Shift + Left: Move window to laptop monitor
hl.bind(
    mod .. " + SHIFT + LEFT",
    hl.dsp.window.move({
        monitor = "eDP-1",
        follow = true,
    }),
    { description = "Move window to laptop monitor" }
)

-- ==========================================
-- 7. Workspace management
-- ==========================================

for i = 1, 10 do
    local key = i % 10

    -- Super + 1~0: Switch workspace
    hl.bind(
        mod .. " + " .. key,
        hl.dsp.focus({ workspace = i }),
        { description = "Switch to workspace " .. i }
    )

    -- Super + Shift + 1~0: Move window to workspace
    hl.bind(
        mod .. " + SHIFT + " .. key,
        hl.dsp.window.move({ workspace = i }),
        { description = "Move window to workspace " .. i }
    )
end

-- ==========================================
-- 8. Mouse window management
-- ==========================================

-- Super + Left mouse: Drag window
hl.bind(
    mod .. " + mouse:272",
    hl.dsp.window.drag(),
    { mouse = true }
)

-- Super + Right mouse: Resize window
hl.bind(
    mod .. " + mouse:273",
    hl.dsp.window.resize(),
    { mouse = true }
)

-- ==========================================
-- 9. Screenshot
-- ==========================================

-- Super + Shift + S: Screenshot region and save
hl.bind(
    mod .. " + SHIFT + S",
    hl.dsp.exec_cmd(
        "bash " .. scripts .. "/screenshot-region.sh"
    ),
    { description = "Screenshot region" }
)

-- Super + Ctrl + S: Screenshot region to clipboard
hl.bind(
    mod .. " + CTRL + S",
    hl.dsp.exec_cmd(
        "bash " .. scripts .. "/screenshot-clipboard.sh"
    ),
    { description = "Screenshot to clipboard" }
)

