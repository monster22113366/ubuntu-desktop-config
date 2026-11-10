return {
    "stevearc/conform.nvim",

    event = { "BufReadPre", "BufNewFile" },

    opts = {
        formatters_by_ft = {
            c = { "clang_format" },
            cpp = { "clang_format" },
        },

        default_format_opts = {
            timeout_ms = 3000,
        },
    },
}
