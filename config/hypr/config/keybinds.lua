
-- ==========================================
-- Hyprland 0.57.1
-- Keyboard bindings
-- Tokyo Night Storm
-- ==========================================

local mod = "SUPER"

-- Native Ubuntu Ghostty with corrected font locale
local ghostty = "env LC_CTYPE=C.UTF-8 /usr/bin/ghostty"

-- Repository scripts and native window-management helpers
local scripts = os.getenv("HOME") ..
    "/Projects/ubuntu-desktop-config/config/scripts"

-- Load from the repository: existing installations symlink individual modules.
local windows = dofile(scripts .. "/../hypr/config/window-management.lua")
local function script(name)
    return "'" .. (scripts .. "/" .. name):gsub("'", "'\"'\"'") .. "'"
end

-- ==========================================
-- 1. Application launching
-- ==========================================

-- Super + G: Ghostty
hl.bind(
    mod .. " + G",
    hl.dsp.exec_cmd(ghostty),
    { description = "应用｜打开 Ghostty" }
)

-- Super + T: Ghostty + tmux
hl.bind(
    mod .. " + T",
    hl.dsp.exec_cmd(
        "python3 " .. script("tmux-launch.py")
    ),
    { description = "应用｜打开 Ghostty + tmux" }
)

-- Super + E: Yazi
hl.bind(
    mod .. " + E",
    hl.dsp.exec_cmd(
        ghostty .. " -e yazi"
    ),
    { description = "应用｜打开 Yazi 文件管理器" }
)

-- Super + D: Application launcher
hl.bind(
    mod .. " + D",
    hl.dsp.exec_cmd("wofi --show drun"),
    { description = "应用｜打开 Wofi 应用启动器" }
)

-- ==========================================
-- 2. Window switching
-- ==========================================

-- Alt + Tab: Next window within the current workspace
hl.bind(
    "ALT + Tab",
    function() windows.cycle_workspace(true) end,
    { description = "窗口｜当前工作区 MRU 下一个窗口" }
)

-- Alt + Shift + Tab: Previous window within the current workspace
hl.bind(
    "ALT + SHIFT + Tab",
    function() windows.cycle_workspace(false) end,
    { description = "窗口｜当前工作区 MRU 上一个窗口" }
)

-- ==========================================
-- 3. Session management
-- ==========================================

-- Super + L: Lock screen
hl.bind(
    mod .. " + L",
    hl.dsp.exec_cmd("hyprlock"),
    { description = "系统｜锁屏" }
)

-- ==========================================
-- 4. Window operations
-- ==========================================

-- Super + X: Close active window
hl.bind(
    mod .. " + X",
    hl.dsp.window.close(),
    { description = "窗口｜关闭当前窗口" }
)

-- Super + V: Toggle floating
hl.bind(
    mod .. " + V",
    hl.dsp.window.float({ action = "toggle" }),
    { description = "窗口｜切换浮动 / 平铺" }
)

-- Super + J: Toggle split
hl.bind(
    mod .. " + J",
    hl.dsp.layout("togglesplit"),
    { description = "窗口｜切换 Dwindle 分割方向" }
)

-- ==========================================
-- 5. Focus movement
-- ==========================================

hl.bind(
    mod .. " + LEFT",
    function() windows.swap_direction("left") end,
    { description = "窗口｜同工作区向左交换" }
)

hl.bind(
    mod .. " + RIGHT",
    function() windows.swap_direction("right") end,
    { description = "窗口｜同工作区向右交换" }
)

hl.bind(
    mod .. " + UP",
    function() windows.swap_direction("up") end,
    { description = "窗口｜同工作区向上交换" }
)

hl.bind(
    mod .. " + DOWN",
    function() windows.swap_direction("down") end,
    { description = "窗口｜同工作区向下交换" }
)

-- ==========================================
-- 6. Multi-monitor management
-- ==========================================

-- Super + Shift + Right: Move window to external monitor
hl.bind(
    mod .. " + SHIFT + RIGHT",
    function() windows.move_to_monitor("external") end,
    { description = "显示器｜移动窗口到外接屏并跟随" }
)

-- Super + Shift + Left: Move window to laptop monitor
hl.bind(
    mod .. " + SHIFT + LEFT",
    function() windows.move_to_monitor("internal") end,
    { description = "显示器｜移动窗口到笔记本屏并跟随" }
)

-- ==========================================
-- 7. Workspace management
-- ==========================================

-- Super + C: Create and switch to the lowest unused numbered workspace
hl.bind(
    mod .. " + C",
    windows.create_workspace,
    { description = "工作区｜创建并切换到新工作区" }
)

for i = 1, 10 do
    local key = i % 10

    -- Super + 1~0: Switch workspace
    hl.bind(
        mod .. " + " .. key,
        hl.dsp.focus({ workspace = i }),
        { description = "工作区｜切换到工作区 " .. i }
    )

    -- Super + Shift + 1~0: Move window to workspace
    hl.bind(
        mod .. " + SHIFT + " .. key,
        hl.dsp.window.move({ workspace = i, follow = true }),
        { description = "工作区｜移动窗口并跟随到工作区 " .. i }
    )
end

-- ==========================================
-- 8. Mouse window management
-- ==========================================

-- Super + Left mouse: Drag window
hl.bind(
    mod .. " + mouse:272",
    hl.dsp.window.drag(),
    { mouse = true, description = "鼠标｜拖动窗口" }
)

-- Super + Right mouse: Resize window
hl.bind(
    mod .. " + mouse:273",
    hl.dsp.window.resize(),
    { mouse = true, description = "鼠标｜调整窗口大小" }
)

-- ==========================================
-- 9. Screenshot
-- ==========================================

-- Super + Shift + S: Screenshot region and save
hl.bind(
    mod .. " + SHIFT + S",
    hl.dsp.exec_cmd(
        script("screenshot-region.sh")
    ),
    { description = "截图｜区域截图并保存" }
)

-- Super + Ctrl + S: Screenshot region to clipboard
hl.bind(
    mod .. " + CTRL + S",
    hl.dsp.exec_cmd(
        script("screenshot-clipboard.sh")
    ),
    { description = "截图｜区域截图到剪贴板" }
)


-- ==========================================
-- 10. Desktop control center
-- ==========================================

-- Super + F1: Keyboard shortcut reference
hl.bind(
    mod .. " + F1",
    hl.dsp.exec_cmd(
        script("shortcut-help.sh")
    ),
    { description = "辅助｜快捷键帮助" }
)

-- Super + F2: System monitor
hl.bind(
    mod .. " + F2",
    hl.dsp.exec_cmd(
        script("system-monitor.sh")
    ),
    { description = "辅助｜系统监控" }
)

-- Super + F3: Volume and Bluetooth control
hl.bind(
    mod .. " + F3",
    hl.dsp.exec_cmd(
        script("device-control.sh")
    ),
    { description = "辅助｜音量与蓝牙控制" }
)

-- Freeze traversal order while Alt is held; next gesture starts with updated MRU.
for _, key in ipairs({ "Alt_L", "Alt_R" }) do
    hl.bind(key, windows.end_cycle, { release = true, non_consuming = true, ignore_mods = true })
end
hl.bind("SUPER + SHIFT + UP", hl.dsp.window.resize({x=0,y=-40,relative=true}), {description="窗口｜垂直缩小"})
hl.bind("SUPER + SHIFT + DOWN", hl.dsp.window.resize({x=0,y=40,relative=true}), {description="窗口｜垂直放大"})
