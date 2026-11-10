local M = {}

M.is_windows = vim.fn.has("win32") == 1

local function find_executable(name)
    local path = vim.fn.exepath(name)

    if path == "" then
        return nil
    end

    return path:gsub("\\", "/")
end

function M.setup()
    if not M.is_windows then
        return
    end

    -- Windows clipboard
    vim.g.clipboard = {
        name = "win32yank",
        copy = {
            ["+"] = { "win32yank.exe", "-i", "--crlf" },
            ["*"] = { "win32yank.exe", "-i", "--crlf" },
        },
        paste = {
            ["+"] = { "win32yank.exe", "-o", "--lf" },
            ["*"] = { "win32yank.exe", "-o", "--lf" },
        },
        cache_enabled = 0,
    }
end

function M.clangd_cmd()
    local cmd = {
        "clangd",
        "--background-index",
        "--clang-tidy",
    }

    -- Allow clangd to query compilers in the detected GCC directory
    local gcc = find_executable("gcc")

    if gcc then
        local directory = vim.fn.fnamemodify(gcc, ":h")
        directory = directory:gsub("\\", "/")

        table.insert(
            cmd,
            "--query-driver=" .. directory .. "/*"
        )
    end

    return cmd
end

return M
