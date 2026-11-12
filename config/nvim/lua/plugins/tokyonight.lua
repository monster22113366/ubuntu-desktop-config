return {
    "folke/tokyonight.nvim",

    lazy = false,
    priority = 1000,

    opts = {
        style = "storm",
        -- Inherit Ghostty background and opacity, like the tmux status line.
        transparent = true,
        terminal_colors = true,

        styles = {
            sidebars = "transparent",
            floats = "transparent",
        },
    },

    config = function(_, opts)
        require("tokyonight").setup(opts)
        vim.cmd.colorscheme("tokyonight")
    end,
}
