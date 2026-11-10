-- Native Hyprland 0.57 window operations. No persistent window IDs or tag queue.
local M = {}
local hardware = require("profiles.hardware")

-- Workspace existence is compositor state, including empty visible workspaces.
-- Leaving an empty, nonpersistent workspace lets Hyprland remove it normally.
function M.create_workspace()
    local used = {}
    for _, workspace in ipairs(hl.get_workspaces()) do
        if not workspace.special and workspace.id then used[workspace.id] = true end
    end
    local id = 1
    while used[id] do id = id + 1 end
    hl.dispatch(hl.dsp.focus({ workspace = id }))
end

-- Keep identity history, while resolving fresh objects for every operation.
local histories, history, session, session_workspace = {}, {}, nil, nil
local function identity(w) return tostring(w.stable_id or w.address) end
local function reconcile(workspace)
    history = histories[workspace.id] or {}
    local available, initial = {}, {}
    for n, w in ipairs(hl.get_windows({ mapped = true })) do
        if w.mapped and not w.hidden and w.accepts_input and w.workspace
            and not w.workspace.special and w.workspace.id == workspace.id then
            available[identity(w)] = w
            initial[#initial + 1] = { w = w, n = n }
        end
    end
    table.sort(initial, function(a, b)
        local x, y = a.w.workspace.id or math.huge, b.w.workspace.id or math.huge
        if x == y then return a.n < b.n end
        return x < y
    end)
    local kept, seen = {}, {}
    for _, id in ipairs(history) do
        if available[id] then kept[#kept + 1], seen[id] = id, true end
    end
    for _, item in ipairs(initial) do
        local id = identity(item.w)
        if not seen[id] then kept[#kept + 1] = id end
    end
    history = kept
    histories[workspace.id] = history
    return available
end
function M.end_cycle() session, session_workspace = nil, nil end
function M.cycle_workspace(forward)
    local workspace = hl.get_active_workspace()
    if not workspace or workspace.special then M.end_cycle(); return end
    if session_workspace ~= workspace.id then M.end_cycle() end
    local available = reconcile(workspace)
    if #history == 0 then session = nil; return end
    if not session then
        -- Seed each gesture with actual focus, including mouse/application focus.
        local active = hl.get_active_window()
        if active and available[identity(active)] then
            local id = identity(active)
            for i, value in ipairs(history) do
                if value == id then table.remove(history, i); break end
            end
            table.insert(history, 1, id)
        end
        session_workspace = workspace.id
        session = {}
        for _, id in ipairs(history) do session[#session + 1] = id end
    end
    local order, seen = {}, {}
    for _, id in ipairs(session) do
        if available[id] then order[#order + 1], seen[id] = id, true end
    end
    for _, id in ipairs(history) do
        if not seen[id] then order[#order + 1] = id end
    end
    session = order
    local active, index = hl.get_active_window(), nil
    for i, id in ipairs(order) do
        if active and identity(active) == id then index = i end
    end
    local step = forward == false and -1 or 1
    local target = available[order[index and ((index - 1 + step) % #order + 1)
        or (forward == false and #order or 1)]]
    hl.dispatch(hl.dsp.focus({ window = target }))
    -- Dispatch can fail: commit only after observing the actual focused window.
    local focused = hl.get_active_window()
    if focused and identity(focused) == identity(target) then
        local id = identity(target)
        for i, value in ipairs(history) do
            if value == id then table.remove(history, i); break end
        end
        table.insert(history, 1, id)
    end
end

function M.swap_direction(direction)
    local active = hl.get_active_window()
    if not active or not active.workspace or active.workspace.special or active.floating then return end
    local best, distance
    local horizontal = direction == "left" or direction == "right"
    local sign = (direction == "left" or direction == "up") and -1 or 1
    for _, w in ipairs(hl.get_windows({ mapped = true })) do
        if w.address ~= active.address and w.workspace and w.workspace.id == active.workspace.id
            and not w.floating and not w.hidden then
            local dx = w.at.x + w.size.x/2 - active.at.x - active.size.x/2
            local dy = w.at.y + w.size.y/2 - active.at.y - active.size.y/2
            local along, across = horizontal and dx or dy, horizontal and dy or dx
            local score = along * along + 4 * across * across
            if along * sign > 0 and (not distance or score < distance) then best, distance = w, score end
        end
    end
    if best then hl.dispatch(hl.dsp.window.swap({ window = active, target = best })) end
end

local function internal(name)
    return name:match("^eDP%-") or name:match("^LVDS%-")
end

function M.move_to_monitor(role)
    local window = hl.get_active_window()
    if not window then return end
    local monitors = hl.get_monitors()
    local candidates = {}
    for _, monitor in ipairs(monitors) do
        if monitor.enabled and not monitor.is_mirror
            and (not not internal(monitor.name)) == (role == "internal") then
            candidates[#candidates + 1] = monitor
        end
    end
    -- Prefer the existing hardware profile; do not duplicate DP/eDP numbers.
    local target
    for _, configured in ipairs(hardware.monitors) do
        for _, monitor in ipairs(candidates) do
            if monitor.name == configured.name then target = monitor; break end
        end
        if target then break end
    end
    -- A renamed connector is safe to resolve when there is one candidate.
    if not target and #candidates == 1 then target = candidates[1] end
    if target then
        hl.dispatch(hl.dsp.window.move({ monitor = target, window = window, follow = true }))
    end
    -- Disconnected/ambiguous target: leave the window where it is.
end

return M
