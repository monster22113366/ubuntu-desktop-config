-- ==========================================
-- Autostart
-- ==========================================

-- Input method environment for Hyprland and its child processes
hl.env("GTK_IM_MODULE", "fcitx")
hl.env("QT_IM_MODULE", "fcitx")
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("SDL_IM_MODULE", "fcitx")

hl.on("hyprland.start", function()
    local function native_exec(command)
        local runner = os.getenv("HOME") .. "/.local/bin/udc-native-run"
        local function quote(value) return "'" .. value:gsub("'", "'\"'\"'") .. "'" end
        hl.exec_cmd(quote(runner) .. " /bin/sh -c " .. quote(command))
    end
    -- Sync activation environments before starting Fcitx5, once per user
    native_exec(
        "dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP PATH "
            .. "GTK_IM_MODULE QT_IM_MODULE XMODIFIERS SDL_IM_MODULE"
            .. ' && (pgrep -u "$(id -u)" -x fcitx5 >/dev/null || fcitx5 -d)'
    )

    -- Status bar
    native_exec('"$HOME/.nix-profile/bin/waybar" > "$HOME/.local/state/ubuntu-desktop-config/waybar-session.log" 2>&1')

    -- Idle management
    native_exec("hypridle")
end)
