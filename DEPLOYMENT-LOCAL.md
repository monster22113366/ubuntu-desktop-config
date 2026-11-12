# 本机部署与接续日志

最后更新：2026-11-11（Asia/Shanghai）。本文件是本机运维记录，包含本机路径；不是通用部署指南，不包含密码。未经用户要求不要提交或推送。

## 接手时先读

1. 阅读本文件及 `AI-PORTING.md`、`INSTALL.md`。
2. 检查 `git status --short`，保留已有未提交修改；不要重置、清理或重新覆盖配置。
3. **部署及自动检查已完成，下一阶段是用户实机验收。** 不要因历史日志中的失败重装环境。
4. 用户会从 GNOME 注销，在登录界面选择 **Hyprland (Ubuntu Desktop Config)**。独立 Hyprland 登录尚未验证。遇到问题可选 Ubuntu 回到 GNOME。
5. 不自动注销、重启、重载桌面或触发锁屏/休眠。后续以用户反馈为依据排障。

## 用户授权与约束

用户已同意迁移工程、安装依赖、备份后替换 Ghostty/Neovim 配置；要求实地调查并适配所有本地参数。
用户明确确认代理入口为 7890，已授权对应配置修正。
用户明确授权专用 Intel GPU 工具副本授予 CAP_PERFMON；授权范围为下文的 root 管理、monster 组可执行工具，不是放宽全局 perf 或赋予通用免密 sudo。
密码不保存在本文件或脚本中；需要认证时通过安全交互处理。

## 实测环境

| 项目 | 实测值 |
| --- | --- |
| 系统 | Ubuntu 24.04.4 LTS；内核 7.0.0-38-generic |
| 当前原桌面 | GNOME / Wayland |
| 机型 | NbDE-WXX9 |
| CPU / GPU | i5-1155G7 / Intel Iris Xe（Tiger Lake，i915） |
| DRM | /dev/dri/card1、renderD128；采样器按 PCI vendor 自动发现，不写死 card1 |
| 屏幕 | eDP-1，1920x1080@60.012，位置 0x0，缩放 1；来自 Mutter 实际输出 |
| 电池 / 背光 | BAT1 / intel_backlight |
| 温度 | coretemp、nvme 正常；未发现可读取风扇转速，显示 N/A |
| 代理 | http://127.0.0.1:7890，verge-mihomo 监听 |
| 现有软件 | Ghostty 1.3.1（/usr/bin）；Neovim 0.12.6（Snap）；Fcitx5 |

## 工程位置与安装

原位置：`/home/monster/下载/ubuntu-desktop-config`。
现位置：`/home/monster/Projects/ubuntu-desktop-config`。工程已移动，所有链接使用新位置。

依照 `install/links.txt` 部署，未整体替换 Hyprland 目录。安装器最后成功：32 项成功，34 项跳过，0 失败。

- apt 补齐：clang-format、ripgrep、fd-find、xclip、wofi、waybar、sway-notification-center、brightnessctl、grim、slurp、luajit、tmux，以及后续的 intel-gpu-tools。其余依赖保留原来源。
- Nix：官方单用户安装，未创建 Nix daemon；安装 Hyprland 0.57.1、hypridle 0.1.8、hyprlock 0.9.7、Yazi、Starship、JetBrains Mono Nerd Font。已有 tree-sitter、Neovim 不重复安装。
- Nixpkgs 固定来源：`/nix/store/psj9s9xk5s3yqjz0i60k0nfyz5rj5z84-nixpkgs/nixpkgs`，revision `4fe25e12eb9f4c744966dd3de5a05246cf098601`。
- Mesa：`/nix/store/j6846pd6a2i4bx16wcdn571sq7jznr71-mesa-26.2.6`；GC root 为 `~/.local/state/ubuntu-desktop-config/mesa-root`。
- 下载曾发生 TLS 中断，重试已完成，不是当前阻塞。

## 工程内修改

- `profiles/hardware.lua`：实测屏幕参数；被 Git 忽略。未创建无读取方的 user.lua。
- `config/scripts/google-chrome.sh`：代理 7897 → 7890。
- `config/waybar/scripts/proxy.sh`：代理 URL 与端口探测同步改为 7890。
- `config/hypr/config/autostart.lua`：DBus/systemd 激活环境同步加入 PATH。
- `config/waybar/scripts/backlight.sh`：直接写背光失败时，通过当前用户会话的 logind SetBrightness 回退；动态发现会话和设备，无 sudo、无全局权限修改。
- `config/scripts/system-monitor.sh`：复用现有资源采样器补充 Intel GPU 信息，保留原 NVIDIA 降级功能。
- `config/waybar/scripts/hardware.sh`：移除错误的原机型注释，保留传感器自动探测。
- `config/tmux/scripts/resources.py`：优先使用 `~/.local/bin/intel_gpu_top`，避免老 tmux server 的 PATH 找不到授权工具；否则仍回退普通命令。
- Neovim 插件按锁文件恢复；lazy.nvim 自身沿用已有缓存版本，恢复操作自动改写的 lazy-lock.json 已还原，未升级工程锁文件。

以上修改未提交。README/INSTALL 引用的部分 docs 文件在工程中缺失；不要把文档缺失当作部署成功证明。

## 工程外配置（重要，重装脚本不会重建）

- `~/.profile`：接入 `~/.nix-profile/etc/profile.d/nix.sh`。
- `~/.bashrc`：接入用户工具 PATH 与 Starship。
- `~/.local/bin/ubuntu-desktop-hyprland`：设置 PATH、Hyprland 会话环境和 Nix Mesa 路径，再启动 Hyprland。
- `/usr/share/wayland-sessions/ubuntu-desktop-hyprland.desktop`：登录入口。
- `~/.local/bin/hyprlock`：为 Nix Hyprlock 预加载 Ubuntu PAM 及其依赖，使用系统认证模块和 unix_chkpwd；PCRE2 使用与 Nix 组件一致的库。`--version` 已验证，但真实解锁未验证。
- `~/.local/bin/intel_gpu_top`：指向下述专用 root 工具的符号链接。

## Intel GPU 问题与最终修复

原工具在普通用户下触发 `get_num_gts: Assertion !errno || errno == ENOENT`。管理员限时采样成功，现有解析器可解析读数，确认权限相关，而非 GPU 缺失。

最终工具：`/usr/local/libexec/ubuntu-desktop-config/intel_gpu_top`。

- 来自 `/usr/bin/intel_gpu_top` 的相同二进制副本（部署时 SHA256 一致）。
- 所有者 root:monster，权限 0750，能力 `cap_perfmon=ep`。
- `kernel.perf_event_paranoid` 保持 **4**；采样器不调用 sudo。
- 普通用户实时采样读到 26%，缓存读到 31%，tmux 格式输出读到 29%（瞬时值，仅为成功证据）。
- 首次或缓存过期后可能暂时 N/A，异步刷新后恢复；缓存位于 `~/.cache/udc-gpu/status-v2.json`。
- 工具副本不会随 apt 自动升级。更新 intel-gpu-tools 后，需要核对并重新复制，再恢复上述所有权、权限及能力。
- 仅撤销能力：`sudo setcap -r /usr/local/libexec/ubuntu-desktop-config/intel_gpu_top`；撤销后预期采样失去权限。

## 验证结果与边界

已通过：

- 60 项 Python 回归测试，无跳过。
- Lua 窗口管理测试。
- Hyprland 0.57.1 `--verify-config` 返回 `config ok`。验证模式有 IPC socket 提示，不代表图形会话已验证。
- Ghostty 配置验证；独立测试 tmux server 启动；Neovim 无界面启动及插件恢复。
- 全部部署链接核对、字体匹配、Shell 语法、git diff --check。
- 代理实际请求：Google generate_204 返回 204；ChatGPT 探测返回 200，Waybar 显示 PROXY OK。
- 电池、亮度读取、默认音频输出、CPU/SSD 温度。
- logind 设置为当前亮度成功（没有主动改变用户屏幕亮度）。
- 普通用户 Intel GPU 真实采样及 tmux 输出。

尚未通过实际操作验收：

- 独立 Hyprland 登录、真实画面、输入、工作区、快捷键、窗口行为。
- 实际锁屏解锁、休眠唤醒、显示器热插拔、截图、通知、输入法、应用图形渲染。
- Nix 图形运行环境与 Ubuntu 原生图形应用的共同运行仍需实机验证；启动脚本会向子进程继承 Mesa 环境，出现渲染问题优先检查这一点。
- GNOME 内嵌套测试失败：宿主 wl_seat 版本 8，目标要求 9。一次尝试设置 AQ_BACKEND=headless 仍进入同样后端并失败，不能描述为 headless 测试成功。独立登录结果未知。

## 备份、日志与回退

原应用配置：
`~/.local/state/ubuntu-desktop-config/backups/20261111-123111-q1oh9w/`

Shell 原文件：
`~/.local/state/ubuntu-desktop-config/backups/shell-20261111-002907/`

记录目录：`~/.local/state/ubuntu-desktop-config/`
包括 install.log（早期失败）、install-retry.log（成功）、tests.log、nvim.log、mesa.log、hyprland-smoke.log、hyprland-headless.log、migration-status.txt。

`migration-status.txt` 是追加历史，前段包含已经过时的“未安装”“7897”“GPU N/A”“等待授权”等描述；以本文件和实际状态为准。

回退先核对具体目标、链接和备份，再移走对应链接、恢复备份，不删除备份。不要批量删除 ~/.config。若图形登录失败，先回到 Ubuntu/GNOME 排查，不需要重装系统。

## 接续检查命令

```bash
cd ~/Projects/ubuntu-desktop-config
git status --short
export PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:$PATH"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
luajit -e 'print(dofile("tests/test-window-management.lua"))'
Hyprland --verify-config
getcap /usr/local/libexec/ubuntu-desktop-config/intel_gpu_top
cat /proc/sys/kernel/perf_event_paranoid
python3 config/tmux/scripts/resources.py
bash config/waybar/scripts/proxy.sh
```

不要为了重复验证而自动触发注销、锁屏、睡眠、重启或修改权限。


## 2026-11-11 晚间实机验收后的修复（优先于前文状态）

用户已经独立登录过 Hyprland，反馈原生 GUI 无法启动、未使用 start-hyprland 警告、Waybar 消失；随后返回 GNOME。旧的“独立登录未知”已过时，但完整桌面仍待二次验收。

确证与修复：

1. 原会话启动脚本全局注入 Nix Mesa 环境，污染 Ubuntu GUI。使用系统 libEGL 的对照测试：原环境 EGL_INIT=0；清理后三个变量 EGL_INIT=1、版本 1.5。
2. 新增 `~/.local/bin/udc-native-run`，清除 GBM_BACKENDS_PATH、LIBGL_DRIVERS_PATH、__EGL_VENDOR_LIBRARY_FILENAMES。keybinds.lua 中所有命令派发和 autostart.lua 中自启动经此入口；包括 Wofi 的后续应用、Ghostty、tmux、Clash 等。合成器保留自身 Nix Mesa 环境。
3. 新增 `~/.local/bin/Xwayland`，清理环境后启动 `/usr/bin/Xwayland`。原会话日志曾报告 GBM backend unavailable / glamor fallback。
4. 登录脚本改为 `start-hyprland --no-nixgl --path "$HOME/.nix-profile/bin/Hyprland" -- ...`，使用官方 watchdog；自有 Mesa 设置保留。
5. `~/.local/bin/hyprlock` 单独设置 Nix Mesa EGL/DRI 环境，保留既有 Ubuntu PAM 适配。真实解锁仍未验证。
6. Waybar 崩溃转储 `/var/crash/_usr_bin_waybar.1000.crash` 的 gdb 栈确认为旧 0.9.24 在 hyprland/window.cpp:95 的 monitors.isArray() 断言失败。已从原固定 Nixpkgs 安装 Waybar 0.15.0，Hyprland autostart 用绝对 Nix profile 路径启动。
7. Ubuntu waybar.service 全局启用会在 GNOME 中失败，且启动 `/usr/bin/waybar` 旧版。已仅在 monster 用户范围 mask 该服务，未修改系统级启用状态；新版由 Hyprland 自启动。回退用户 mask：`systemctl --user unmask waybar.service`，但会恢复旧版服务，慎用。
8. 新版状态栏日志：`~/.local/state/ubuntu-desktop-config/waybar-session.log`；升级日志为 waybar-upgrade.log。

本轮备份：`~/.local/state/ubuntu-desktop-config/backups/gui-fix-20261111-203712/`。
验证：60 项 Python 测试、Lua 测试、Hyprland 配置解析、Shell 语法及 git diff --check 通过；原生 EGL 对照测试通过。没有重启、重载或注销当前桌面。新版 Waybar、Ghostty/Clash 实际在独立 Hyprland 内的显示仍待用户二次登录确认，不得称为已完成实机验收。

截图提示：Super+Ctrl+S 仅复制剪贴板，注销后不可依赖其保留；Super+Shift+S 保存到 `$(xdg-user-dir PICTURES)/Screenshots/`。本次未找到用户所述截图文件，依据 journal 和 Waybar core 排障。

## 自动登录修复与工程定位复核

2026-11-11 20:42：用户报告重启直接进入 Hyprland，无法先选择 GNOME。实测 `/etc/gdm3/custom.conf` 原有 AutomaticLoginEnable=true、AutomaticLogin=monster，修改时间为 2026-03-15，早于本次部署。Ubuntu/GNOME 会话文件仍在。已备份到 `/etc/gdm3/custom.conf.udc-backup-20261111-204235`，改为 AutomaticLoginEnable=false；未重启 GDM，当前会话未中断。下次登录应显示认证及会话选择，仍需用户确认。

工程当前是配置迁移基线而非完整一键桌面安装器：README/INSTALL 明确把桌面组件、驱动、代理和系统策略放在安装器之外；user.lua 尚无读取方；本机参数分散；缺少组件组合兼容性校验和真实桌面集成验证。60 项测试通过不等于 GUI 可用。

本次部署责任：助手自行选用了 Nix Hyprland 与 Ubuntu GUI 混合方案，却泄漏 Mesa 环境；遗漏 start-hyprland；未提前发现 apt Waybar 0.9.24 与新版 Hyprland 的 IPC 不兼容；代理和自动登录调查不足。不能把这些全部归因于用户工程。后续若建设真正一键部署，需单独明确范围，把已验证的依赖组合、会话入口、本机参数、权限及集成验收纳入可复现部署；当前外置修复尚未全部纳入 install.sh。

## 用户明确的工程定位与持续 issue 维护

用户澄清：目标不是无人值守通用安装器，而是“脚本按明确版本安装软件依赖，AI 按 AI-PORTING.md 实测并适配硬件及本地参数”的开放式工程。后续不得将目标误解为脚本包办所有硬件。

工程迭代建议已记录在根目录 `issue.md`（ISSUE-001 至 ISSUE-011）。用户要求：后续继续实机反馈时，持续把属于工程的问题更新到该文件；区分工程缺陷、指南缺口、AI 执行失误、本机环境问题与待验证假设。先取证再归因，本机修复不能直接作为工程 issue 关闭依据。本轮只编写建议，不代表已实施整套架构或安装器迭代。

二次登录前复核：配置解析、Shell 语法、60 项回归通过；自动登录 false，Waybar 0.15.0 与旧服务 mask 已确认。Chrome desktop 当前为普通文件（20:05），三个 Exec 仍指向工程脚本，其余部署链接一致；保留现状，没有覆盖修改。issue.md 记录范围已扩展为工程缺陷、疏漏及 AI 踩坑，后续持续维护。

## Yazi 模块化配置（2026-11-11）

用户反馈已在 Hyprland 中使用，当前整体效果与另一台设备一致、观感正常；这是总体实机反馈，不替代锁屏/休眠等尚无逐项记录的验收。

应用户需求新增 config/yazi：yazi.toml、keymap.toml、scripts/actions.py 及 udc_yazi/settings.py、terminal.py、desktop.py。系统“打开方式”使用 GTK/GIO 已注册应用；选择后不修改 MIME 默认关联。O 打开选择窗口；T 在当前浏览目录打开独立终端；g o 保留 Yazi 原生菜单。保留上游 MIME 规则、预览、压缩包操作。

本机参数为 ~/.config/yazi/local.toml（可选，未创建，当前默认 Ghostty/Neovim）；local.example.toml 是模板。遵循 YAZI_CONFIG_HOME/XDG_CONFIG_HOME。已逐文件部署 yazi.toml、keymap.toml、scripts，install/links.txt、apt 依赖和 README/INSTALL 同步更新。没有重载 Hyprland。

依赖：系统 /usr/bin/python3、python3-gi、gir1.2-gtk-3.0、xdg-utils。现场 GTK 应用选择组件构造成功，text/plain 注册应用查询成功；真实 Yazi 成功加载，T 的 PTY 端到端测试用替身终端验证了中文、空格、空目录 cwd。66 项回归通过。用户实际选择 GUI 应用及打开真实终端窗口仍请操作确认；不宣称全部应用均支持全部文件类型。

说明及迁移步骤：config/yazi/README.md。错误日志：~/.local/state/ubuntu-desktop-config/yazi-actions.log。其他习惯类功能仅提出建议，未自动加入。
最终配置补充测试：自定义 YAZI_CONFIG_HOME 下真实 Yazi 的 T 键成功传递中文空格空目录；O 键用隔离动作替身验证包含中文、空格与 $(...) 的文件名保持单一字面参数。曾有一次自动 PTY 测试因尚未就绪而未生成捕获文件，随后真实交互复测通过。
