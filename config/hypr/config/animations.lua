
-- ==========================================
-- Window and workspace animations
-- ==========================================

hl.config({
    animations = {
        enabled = true,
    },
})

-- Smooth curves
hl.curve("easeOutQuint", {
    type = "bezier",
    points = {{0.23, 1}, {0.32, 1}},
})

hl.curve("easeInOutCubic", {
    type = "bezier",
    points = {{0.65, 0.05}, {0.36, 1}},
})

hl.curve("almostLinear", {
    type = "bezier",
    points = {{0.5, 0.5}, {0.75, 1}},
})

-- Near-critical damping keeps a little spring without visible bouncing.
hl.curve("easy", {
    type = "spring",
    mass = 1,
    stiffness = 320,
    damping = 34,
})

hl.animation({
    leaf = "global",
    enabled = true,
    speed = 3,
    bezier = "default",
})

hl.animation({
    leaf = "windows",
    enabled = true,
    speed = 3,
    spring = "easy",
})

hl.animation({
    leaf = "windowsIn",
    enabled = true,
    speed = 3,
    spring = "easy",
    style = "popin 94%",
})

hl.animation({
    leaf = "windowsOut",
    enabled = true,
    speed = 1.5,
    bezier = "easeOutQuint",
    style = "popin 96%",
})

-- Tiling layout, move and resize transitions settle quickly.
hl.animation({
    leaf = "windowsMove",
    enabled = true,
    speed = 1.8,
    bezier = "easeOutQuint",
})

hl.animation({
    leaf = "fade",
    enabled = true,
    speed = 1.8,
    bezier = "almostLinear",
})

hl.animation({
    leaf = "border",
    enabled = true,
    speed = 1.6,
    bezier = "easeOutQuint",
})

-- Fade the focus opacity and colored outer shadow together.
for _, leaf in ipairs({ "fadeSwitch", "fadeShadow" }) do
    hl.animation({
        leaf = leaf,
        enabled = true,
        speed = 1.6,
        bezier = "easeOutQuint",
    })
end

hl.animation({
    leaf = "workspaces",
    enabled = true,
    speed = 2.2,
    bezier = "easeOutQuint",
    style = "slidefade 12%",
})

