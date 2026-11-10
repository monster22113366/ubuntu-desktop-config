# 安装与部署

## 前提

以目标桌面用户在 Ubuntu 24.04 执行，不要用 `sudo bash`。先准备支持当前 Lua 接口的 **Hyprland 0.57.1**、hypridle、hyprlock、Ghostty，以及 sudo、apt、Python 3。脚本不添加第三方 apt 源，不安装桌面会话、显卡驱动、Chrome 或 Clash Verge，也不调整权限策略。

本机参数保存在 Git 忽略的 `profiles/hardware.lua`。新设备仅在文件不存在时参考 `hardware.example.lua` 创建，再填写真实显示器参数；已有文件不能覆盖。`user.lua` 目前没有读取方，不要求创建。用户目录中的 Profile 与仓库不同会使部署停止，必须先人工核对。

原生配置仍有本机路径、BAT1、代理端口等设置。更换用户名或仓库位置先按 [定制位置](docs/customization.md) 修改。安装器检查现有仓库路径与 Starship 家目录引用，发现不匹配就停止，不自动生成或重写配置。

## 执行

```bash
bash install/install.sh --dry-run  # 只检查和展示，不安装、不写链接
bash install/install.sh           # 安装依赖并建立链接
```

脚本通过自身真实路径定位仓库，不要求当前工作目录在仓库内。路径引用适配完成后可在其他目录调用。首次运行需要网络，apt 阶段可能要求 sudo 密码。

处理顺序：前置检查 → apt 缺失依赖 → Nix 和软件 → 配置链接。失败立即停止并输出统计；已完成的安装或链接不会自动回滚。重复运行会跳过正确链接和已有软件。

## 依赖

`nix/packages.txt` 包含 `tmux`、`neovim`、`yazi`、`starship`、`tree-sitter`、`nerd-fonts.jetbrains-mono`。已由 apt 管理或能找到可执行文件的软件不会重复安装，也不会强制升级。现有 Neovim 低于 0.11 会停止，需人工决定软件来源。该清单不锁定 nixpkgs 版本；可用 `NIXPKGS_REF` 指定经过验证的 nixpkgs 引用。

没有 Nix 时下载 [官方安装器](https://nixos.org/download/) 并以 `--no-daemon` 单用户方式安装；安装器可能修改用户的 Shell 初始化文件。软件通过 `nix profile install` 安装，实验特性只对命令启用，不建立 Flake 工程。旧 `nix-env` profile 不自动转换，检测到后停止。

`install/apt-packages.txt` 是 apt 依赖的唯一清单，包括 Waybar/Wofi/SwayNC、网络与音量控制、剪贴板和截图、C/C++ 编译与格式化、搜索和图标转换工具。只安装缺失项。Ubuntu 自带基础工具（coreutils、procps、iproute2 等）仍由系统提供。apt 软件维护脚本可能启动其服务；部署脚本本身不执行服务配置或重载命令。

Neovim 插件仍按原配置由 lazy.nvim 管理，首次启动可能下载插件和 Treesitter 组件。导入的 `config/nvim/README.md` 保留原项目说明；本仓库的软件安装以本文和清单为准，不要再重复执行其中的 Snap/npm 安装步骤。ImageMagick 6 缺少 `magick` 时，部署本机已有的 `convert` 兼容入口。Nix Nerd Font 链接到用户字体目录并刷新字体缓存。

## 链接与备份

完整链接清单在 `install/links.txt`，左侧相对仓库，右侧相对 HOME。Hyprland 保持逐文件链接，另将 `profiles/` 链接到 `~/.config/hypr/profiles`，不会整体替换 `~/.config/hypr`。

Neovim 目录链接到 `~/.config/nvim`；tmux 主配置链接到 `~/.tmux.conf`，通过 `~/.config/tmux/status.conf` 读取样式，资源脚本也从 `~/.config/tmux/scripts` 读取。Ghostty、Starship 和其他模块按清单部署。Yazi 不部署配置，保留现有数据。

冲突的普通文件、目录和符号链接会先移动到：

```text
~/.local/state/ubuntu-desktop-config/backups/<时间戳-随机后缀>/<原 HOME 相对路径>
```

原 Neovim 目录中的 `.git`、临时文件和未提交数据随整个目录备份，导入仓库时才排除这些内容。旧备份不删除。恢复时先核对备份与当前链接，人工移走相应链接再恢复原文件；没有自动回滚或卸载器。

仓库内 `config/hypr/backup/`、`config/waybar/backup/` 及历史文档保持原样；`portability-review/` 提案不自动应用。

## 部署之后

核对图形会话和终端 PATH 都包含 `~/.nix-profile/bin`、`~/.local/bin`。终端能找到命令不代表 GNOME 启动器、Hyprland 或已运行的 tmux server 能找到；旧进程需要重新启动或重新登录才能继承新环境。Starship 的 Shell 初始化沿用现有设置，新用户需自行接入。

脚本不重载桌面或 tmux，不修改代理配置。运行中的软件可能自行监测配置变化，建议在维护窗口部署。用户检查完成后再选择重新登录、打开新终端或重载对应软件。

新机的 GPU 驱动、intel_gpu_top 与采样权限、网络/蓝牙服务授权、中文字体、Chrome、代理服务、显示器热插拔均需独立验收；部署成功不代表这些功能已验证。
