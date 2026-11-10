vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("core.platform").setup()

require("core.options")
require("core.keymaps")
require("core.lazy")
require("core.lsp")
