
-- ==========================================
-- Input configuration
-- ==========================================

hl.config({
	input = {
    kb_layout = "us",
    kb_options = "caps:swapescape",
    follow_mouse = 1,
    sensitivity = 0,

        touchpad = {
            natural_scroll = false,
        },
    },
})

-- Three-finger horizontal workspace switching
hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

