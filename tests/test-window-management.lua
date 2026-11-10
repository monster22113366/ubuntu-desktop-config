-- Run inside Hyprland's Lua interpreter. The injected API never changes desktop state.
local root = os.getenv("HOME") .. "/Projects/ubuntu-desktop-config"
local list, workspaces, active, dispatched = {}, {}, nil, nil
local fake = {
    get_windows = function() return list end,
    get_workspaces = function() return workspaces end,
    get_active_workspace = function() return {id=1} end,
    get_active_window = function() return active end,
    dispatch = function(action) dispatched = action; if action.window then active = action.window end end,
    dsp = { focus = function(action) return action end },
}
local env = setmetatable({ hl = fake, require = function() return { monitors = {} } end }, { __index = _G })
local windows = assert(loadfile(root .. "/config/hypr/config/window-management.lua", "t", env))()
local function window(id, workspace)
    return { address = id, stable_id = id, mapped = true, hidden = false,
        accepts_input = true, workspace = workspace or { special = false, id = 1 } }
end
local a, b, c = window("01"), window("02"), window("03")
local other = window("06", {id=2})
local hidden, special = window("04"), window("05", { special = true })
hidden.hidden = true
list = { other, a, hidden, b, special, c }
active = a
windows.cycle_workspace(true); assert(dispatched.window == b)
windows.cycle_workspace(true); assert(dispatched.window == c)
windows.cycle_workspace(true); assert(dispatched.window == a)
windows.cycle_workspace(false); assert(dispatched.window == c)
windows.end_cycle() -- MRU now C,A,B; next gesture selects A.
windows.cycle_workspace(true); assert(dispatched.window == a)
windows.end_cycle()
windows.cycle_workspace(true); assert(dispatched.window == c)
list = { b }
windows.cycle_workspace(true); assert(dispatched.window == b)
list, dispatched = { hidden, special }, nil
windows.cycle_workspace(true); assert(dispatched == nil)
list, active = { a, c }, b
windows.cycle_workspace(true); assert(dispatched.window == a)
workspaces = { {id=1}, {id=2}, {id=4}, {special=true}, {name="named"} }
windows.create_workspace(); assert(dispatched.workspace == 3)
workspaces = {}
windows.create_workspace(); assert(dispatched.workspace == 1)
for i = 1, 10 do workspaces[i] = {id=i} end
windows.create_workspace(); assert(dispatched.workspace == 11)
return "PASS: workspace cycle filtering/order/wrap/empty/closed; workspace gaps/empty/above 10"
