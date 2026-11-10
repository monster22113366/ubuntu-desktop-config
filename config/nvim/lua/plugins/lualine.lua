return {
    "nvim-lualine/lualine.nvim",

    dependencies = {
        "nvim-tree/nvim-web-devicons",
    },

    event = "VeryLazy",

    opts = {
        options = {
            theme = "tokyonight",
            globalstatus = true,
            component_separators = "|",
            section_separators = "",
        },

        sections = {
            lualine_a = { "mode" },
            lualine_b = { "branch" },
            lualine_c = { "filename" },
            lualine_x = { "diagnostics", "filetype" },
            lualine_y = { "progress" },
            lualine_z = { "location" },
        },
    },
}
