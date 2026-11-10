return {
    "folke/tokyonight.nvim",

    lazy = false,
    priority = 1000,

    opts = {
        style = "storm",
        transparent = false,
        terminal_colors = true,

        styles = {
            sidebars = "dark",
            floats = "dark",
        },

        on_colors = function(colors)
            colors.bg = "#2B3048"
            colors.bg_dark = "#252B40"
            colors.bg_float = "#303750"
            colors.bg_sidebar = "#292F45"
        end,
    },

    config = function(_, opts)
        require("tokyonight").setup(opts)
        vim.cmd.colorscheme("tokyonight")
    end,
}
