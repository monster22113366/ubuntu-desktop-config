return {
    "Mirsmog/real-icons.nvim",

    opts = {
        pack = "jetbrains",

        packs = {
            jetbrains = {
                type = "vscode",
                path = vim.fn.stdpath("config")
                    .. "/assets/jetbrains-file-icons",
                manifest = "themes/dark-jetbrains-icon-theme.json",
            },
        },

        integrations = {
            neo_tree = true,
        },
    },
}
