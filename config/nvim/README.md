# Neovim

Ubuntu 24.04 配置，面向 C/C++、嵌入式开发与日常代码阅读。采用模块化 Lua、原生 Neovim 快捷键和 lazy.nvim。

## 1. 安装依赖

```bash
sudo snap install nvim --classic

sudo apt update
sudo apt install -y \
  git build-essential clangd clang-format ripgrep \
  curl wl-clipboard imagemagick nodejs npm
```

安装 Tree-sitter CLI：

```bash
sudo npm install -g tree-sitter-cli
```

## 2. 安装 Ghostty

```bash
sudo add-apt-repository ppa:mkasberg/ghostty-ubuntu
sudo apt update
sudo apt install ghostty
```

Ghostty 配置文件：`~/.config/ghostty/config`。终端建议使用 Nerd Font；彩色文件图标使用 Kitty Graphics Protocol。

## 3. 部署 Neovim 配置

配置目录：`~/.config/nvim`。

```bash
git clone <仓库地址> ~/.config/nvim
nvim
```

首次启动时，`lazy.nvim` 会自动安装插件管理器及配置中声明的插件。手动同步：

```vim
:Lazy sync
:TSUpdate
:checkhealth
```

## 4. 文件图标

Linux 使用 `real-icons.nvim`，图标资源采用 Fogio 的 JetBrains New UI SVG 文件主题。

请保留仓库中的 `assets/jetbrains-file-icons/` 目录；不要单独移动 SVG 文件。图标显示需要 Ghostty 和支持 Kitty Graphics Protocol 的终端环境。

Ubuntu 24.04 提供 ImageMagick 6。如果配置调用 `magick` 命令，可创建兼容入口：

```bash
mkdir -p ~/.local/bin
printf '#!/bin/sh\nexec /usr/bin/convert "$@"\n' > ~/.local/bin/magick
chmod +x ~/.local/bin/magick
```

确保 `~/.local/bin` 已加入 `PATH`。

## 5. 常用快捷键

| 按键 | 功能 |
|---|---|
| `<Space>ff` | 搜索文件 |
| `<Space>fg` | 全文搜索 |
| `<Space>fb` | 搜索 Buffer |
| `<Space>fr` | 最近文件 |
| `<Space>e` | Neo-tree |
| `<Space>cf` | 格式化当前文件 |
| `gd` | 跳转定义 |
| `K` | 悬停信息 |
| `s` | Flash 快速跳转 |
| `Ctrl+w h/j/k/l` | 切换窗口 |

## 6. 日常维护

```vim
:Lazy sync       "安装/更新插件
:TSUpdate        "更新解析器
:checkhealth     "检查环境
```

Git 提交配置：

```bash
git add .
git diff --cached --stat
git commit -m "Update Neovim configuration"
git push
```

建议提交 `init.lua`、`lua/`、`assets/`、`README.md` 和 `lazy-lock.json`；不要提交插件目录、缓存或编译后的解析器。
