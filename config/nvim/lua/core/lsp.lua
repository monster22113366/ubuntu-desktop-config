-- C/C++ language server
local platform = require("core.platform")

vim.lsp.config("clangd", {
    cmd = platform.clangd_cmd(),

    filetypes = { "c", "cpp" },

    root_markers = {
        "compile_commands.json",
        "compile_flags.txt",
        ".clangd",
        ".git",
    },
})

vim.diagnostic.config({
    update_in_insert = true,
    virtual_text = true,
    underline = true,
    signs = true,
})

vim.lsp.enable("clangd")
