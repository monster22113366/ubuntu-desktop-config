# ubuntu-desktop-config

Ubuntu 24.04 桌面与开发环境的原生配置仓库，面向由 AI 协助维护和移植的个人环境。保留现有快捷键、Tokyo Night 外观及软件原生配置；不提供硬件自动适配或通用桌面安装器。

## 目录

```text
config/
  hypr/          Hyprland Lua、配色、锁屏与空闲配置
  waybar/        JSONC、CSS 与状态脚本
  scripts/       截图、网络、设备、tmux 启动等入口
  applications/  Desktop Entry
  ghostty/       终端配置
  tmux/          主配置、状态栏、资源与剪贴板脚本
  nvim/          本机实际 Neovim 配置、插件锁文件与资源
  starship/      三行提示符
  wofi/ swaync/  菜单与通知样式
  yazi/          空模块预留（Git 不保存空目录）
profiles/        示例及 Git 忽略的本机参数
nix/packages.txt Nix 软件包属性清单
install/         部署脚本、apt 清单与链接清单
tests/           Python / Lua 回归
docs/            当前说明与保留的历史报告
portability-review/  前阶段提案，仅供参考，不参与部署
```

## 使用

先按 [INSTALL.md](INSTALL.md) 准备桌面基础组件、本机 Profile 和路径，再运行：

```bash
bash install/install.sh --dry-run
bash install/install.sh
```

脚本安装缺失依赖、备份冲突配置并建立链接，不主动重载桌面。已有软件来源和个人 Profile 保留。换设备时先让 AI 按 [移植指南](docs/ai-porting-guide.md) 修改实际差异，再部署。

Neovim 来自当前 `~/.config/nvim` 的磁盘内容，含未提交的本机修改；tmux 主配置也已纳管。Yazi 尚无配置，SwayNC 目前只管理样式。Shell 初始化、驱动、代理软件及系统服务仍需人工维护。

## 文档与验证

- [架构](docs/architecture.md)：配置读取与部署边界。
- [定制位置](docs/customization.md)：外观、快捷键与硬件参数。
- `docs/02*`、窗口管理、GPU 等专项报告保留为历史记录；历史测试数量和现场状态不代表当前验收。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
luajit -e 'print(dofile("tests/test-window-management.lua"))'
bash -n install/install.sh
git diff --check
```

自动测试不能代替物理热插拔、图形会话与新设备上的实际验收。
