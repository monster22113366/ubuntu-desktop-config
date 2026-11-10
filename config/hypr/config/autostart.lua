-- ==========================================
-- Autostart
-- ==========================================

-- Input method environment for Hyprland and its child processes
hl.env("GTK_IM_MODULE", "fcitx")
hl.env("QT_IM_MODULE", "fcitx")
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("SDL_IM_MODULE", "fcitx")

hl.on("hyprland.start", function()
    -- Sync activation environments before starting Fcitx5, once per user
    hl.exec_cmd(
        "dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP "
            .. "GTK_IM_MODULE QT_IM_MODULE XMODIFIERS SDL_IM_MODULE"
            .. ' && (pgrep -u "$(id -u)" -x fcitx5 >/dev/null || fcitx5 -d)'
    )

    -- Status bar
    hl.exec_cmd("waybar")

    -- Idle management
    hl.exec_cmd("hypridle")
end)
