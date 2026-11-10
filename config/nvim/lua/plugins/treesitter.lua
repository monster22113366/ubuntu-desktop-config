return {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",

    config = function()
        local ts = require("nvim-treesitter")

        ts.setup({})

        vim.api.nvim_create_autocmd("FileType", {
            pattern = {
                "c",
                "cpp",
                "python",
                "matlab",
                "lua",
                "vim",
                "help",
            },
            callback = function()
                vim.treesitter.start()
            end,
        })
    end,
}
