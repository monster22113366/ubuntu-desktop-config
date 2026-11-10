return {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",

    dependencies = {
        "nvim-lua/plenary.nvim",
        "MunifTanjim/nui.nvim",
        "nvim-tree/nvim-web-devicons",
    },

    cmd = "Neotree",

    opts = {
        close_if_last_window = true,

        filesystem = {
            follow_current_file = {
                enabled = true,
            },

            filtered_items = {
                hide_dotfiles = false,
                hide_gitignored = false,
            },
        },

        window = {
            position = "left",
            width = 30,
        },
    },
}
