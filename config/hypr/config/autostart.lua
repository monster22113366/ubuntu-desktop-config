-- ==========================================
-- Autostart
-- ==========================================

hl.on("hyprland.start", function()
    -- Status bar
    hl.exec_cmd("waybar")

    -- Idle management
    hl.exec_cmd("hypridle")

    -- Update D-Bus and systemd activation environment
    hl.exec_cmd(
        "dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP"
    )
end)
