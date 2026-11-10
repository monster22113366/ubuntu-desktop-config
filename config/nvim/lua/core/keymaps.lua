
local map = vim.keymap.set

-- Telescope 文件导航
map("n", "<leader>ff", "<cmd>Telescope find_files<CR>",
    { desc = "Find files" })

map("n", "<leader>fb", "<cmd>Telescope buffers<CR>",
    { desc = "Find buffers" })

map("n", "<leader>fr", "<cmd>Telescope oldfiles<CR>",
    { desc = "Recent files" })

map("n", "<leader>fg", "<cmd>Telescope live_grep<CR>",
    { desc = "Find text in project" })

-- Clear search highlights
map("n", "<Esc>", "<cmd>nohlsearch<CR>",
    { desc = "Clear search highlights" })

-- Neo-tree 文件浏览器
map("n", "<leader>e", "<cmd>Neotree toggle<CR>",
    { desc = "Toggle file explorer" })

-- Format current buffer
map("n", "<leader>cf", function()
    require("conform").format({
        async = true,
        lsp_format = "never",
    })
end, { desc = "Format code" })

-- LSP
map("n", "gd", vim.lsp.buf.definition,
    { desc = "Go to definition" })

-- Flash: quick jump
vim.keymap.set({ "n", "x", "o" }, "s", function()
    require("flash").jump()
end, { desc = "Flash Jump" })

vim.keymap.set({ "n", "x", "o" }, "S", function()
    require("flash").treesitter()
end, { desc = "Flash Treesitter" })
