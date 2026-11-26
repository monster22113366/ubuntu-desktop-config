# Hyprland 的 HiDPI 策略与应用调查

## 当前默认值

内屏 eDP-2 为 2560×1600、165 Hz、1.6 倍，外屏 DP-1 为 2560×1440、60 Hz、1 倍。显示器参数仍来自本机 Hardware Profile。运行 `hidpi-check` 可看到输出、窗口类、后端、活动窗口标记，以及窗口当前所在屏幕的风险提示。切换到终端会改变活动窗口；应用仍在列表内。

- GTK 3/4 和 WebKitGTK 沿用桌面的 Wayland 环境及工具包选择。当前原生应用沿用各自启动入口。全局固定 GTK 缩放会同时改变两屏尺寸。参见 [GTK 3 Wayland 后端](https://docs.gtk.org/gtk3/wayland.html)。
- Qt 使用 Hyprland Lua 的 `hl.env("QT_QPA_PLATFORM", "wayland;xcb")`。只给该合成器启动的子进程；不写环境文件，也未加入 systemd/D-Bus 导入列表。已有进程保留原环境。系统 Qt 5.15.13 和 Qt 6.4.2 的 fcitx 探针均实际加载 Wayland；将首选项换成不存在的平台时，二者均加载 XCB。应用自带的启动器、D-Bus 启动或沙箱可能使用独立环境。参见 [Qt QPA 选择顺序及插件 ABI](https://doc.qt.io/qt-6/qpa.html)。
- Electron 38 起默认按会话选 Ozone，已移除旧的环境提示。捆绑的 Electron、供应商参数或内部设置仍可能改变结果。沿用已正常映射的 Chrome 入口。对老程序逐个核对实际版本及一次性启动结果。参见 [Electron 38 变更](https://www.electronjs.org/docs/latest/breaking-changes#breaking-changes-380)。
- Hyprland 在 `config/hypr/config/monitor.lua` 持久设置 `xwayland.force_zero_scaling=true`。X11 客户端按原生像素绘制，自行决定字体和控件尺寸。1.6 倍内屏上缺少 DPI 适配的软件可能清晰但偏小；1 倍外屏通常无需额外放大。原生 Wayland 窗口继续使用各自的输出缩放。[Hyprland 0.57 选项](https://wiki.hypr.land/0.57.0/configuring/core/config-options/#xwayland)

## 应用调查 · 2026-11-26

数据来自 Hyprland 窗口、已加载库、包版本、desktop 条目及有限安装目录。下表的“实测”指窗口后端；有人工视觉验收的应用另行注明。用户提供的高清基线为 Ghostty、CC Switch、Chrome。QQ 与 WPS 是用户指定的显示问题案例；本轮没有据窗口后端新增“已确认模糊”判定。

| 应用 / 来源 | 框架与版本证据 | 结果、风险与处置 |
|---|---|---|
| Ghostty 1.3.1、CC Switch 4.0.28 / DEB | GTK4、Tauri/WebKitGTK | 内屏原生窗口实测，Ghostty 外屏也有原生窗口；沿用现有入口 |
| Chrome 157.0.8103.38 / DEB、用户 desktop | Chromium/Ozone | 外屏原生窗口实测；现有代理、动作和启动参数继续使用 |
| QQ 3.2.35-54395 / DEB、/opt/QQ | Electron，主程序含 Electron/40.0.0 标记 | 先前为 XWayland；本轮单独加 Wayland 参数实际映射为 QQ、xwayland=false。用户 desktop 保留图标、分类、StartupWMClass 和 %U；仅在 Hyprland Wayland 会话加参数。首个进程决定后端，托盘进程也算。高清显示已通过人工验收；中文输入、截图、拖拽、登录未单独记录 |
| WPS 12.1.2.29183 / DEB、/opt/kingsoft | 运行进程 maps 确认私有 Qt5CoreKso 5.12.12 和 libqxcb.so；平台目录无 Wayland 插件 | 实际后端为 XWayland；零缩放配合 WPS 自动 DPI，在内屏 1.6 倍和外屏 1.0 倍的清晰度、界面尺寸均通过人工验收 |
| MarkText 0.24.0~rc.2 / DEB、/opt/MarkText | 主程序含 Electron/45.0.0 标记 | 人工实测为原生 Wayland，沿用默认入口 |
| Clash Verge 2.5.10 / DEB | Tauri/WebKitGTK；URI 处理器与主程序分开 | 未运行窗口验证；不改 URL 处理及代理 |
| MATLAB / Simulink R2026b / /usr/local/MATLAB、用户 desktop | 安装含 CEF、JCEF、Qt 6.8.5 和 X11 显示组件 | R2026b Update 1 主桌面实测 XWayland；从外屏移入内屏再移回后均正常映射。主桌面控件尺寸及 Figure、Simulink 等子窗口的视觉效果待人工验收 |
| gsycloud 2.2.3 / DEB | Flutter Linux，含 flutter_assets | 实际后端、文字尺寸待验 |
| LibreOffice 24.2.7 / DEB | VCL，后端取决于可用集成插件 | Writer/Math 等未运行；不设置 SAL 全局变量 |
| Fcitx 配置 / DEB | Qt5/Qt6，fcitx5-config-qt 5.1.4 | 实测系统插件选择。配置器、迁移器、键盘布局预览的真实 UI 待验 |
| GNOME 和桌面工具 / DEB | 主机 GTK 3.24.41 / 4.14.5；例如 Nautilus 46.4、Calculator 46.3、Evince 46.3.1、eog 45.3 | 文件管理器、编辑器、日志、系统监视器、时钟、密码管理器、蓝牙发送、终端、磁盘、设置子面板、语言/更新管理均按自身后端运行；逐窗未验 |
| ImageMagick display 6.9、NVIDIA Settings 510.47 / DEB | 传统 X11 或依赖 X11 显示扩展 | 分数缩放潜在风险，未实测模糊；保留 XWayland |
| Firefox 147.0.3 / Snap | Gecko，Snap 自有环境 | 支持原生后端；窗口与 about:support 的 Window Protocol 待验 |
| Snap Store、Firmware Updater / Snap | Snap 自带应用栈；包版本 0+git.319ac514 / 0+git.64c41a0 | 未运行，检查沙箱 Wayland 接口及实际窗口后端 |
| Neovim、Yazi / Nix Profile；btop、nvtop 等终端入口 | TUI | 终端决定后端；通过 Ghostty 使用时随其渲染 |

检索了系统、用户、Nix、Snap desktop 目录，包括 URL handler、隐藏条目及桌面启动动作。系统设置的子面板共享程序；命令行和服务入口无需单独调整 DPI。`flatpak list --app` 无应用。检查 /opt、用户下载目录、~/.local/bin、~/.local/opt、~/Applications 等常见位置，未发现 AppImage。这是有范围的清点，任意目录中未注册的程序仍可能存在。

## WPS 的双屏方案

人工验收使用 `force_zero_scaling=true`，并仅给 WPS 设置 `QT_QPA_PLATFORM=xcb QT_AUTO_SCREEN_SCALE_FACTOR=1`。内屏 eDP-2（1.6 倍）与外屏 DP-1（1.0 倍）的清晰度和界面尺寸均正常。此前单独打开零缩放时内屏控件偏小，固定 `QT_SCALE_FACTOR=1.6` 未见明显改善。

Wofi 和文件管理器通过与软件包同名的用户 desktop 入口调用 `~/.local/bin/wps-hidpi`。脚本仅在 Hyprland Wayland 会话设置这两个变量，随后转交原厂启动器。在 GNOME 中转交原环境。之前对新 WPS 进程的检查已确认自动 DPI 变量可以传至私有 Qt/XCB 进程。

| desktop ID | 原厂入口与参数 |
|---|---|
| wps-office-wps.desktop（文字） | `/usr/bin/wps %U` |
| wps-office-et.desktop（表格） | `/usr/bin/et %F` |
| wps-office-wpp.desktop（演示） | `/usr/bin/wpp %F` |
| wps-office-pdf.desktop（PDF） | `/usr/bin/wpspdf %F` |
| wps-office-prometheus.desktop（WPS Office 综合入口） | `/usr/bin/wps %F`，本机多种办公格式的默认处理器 |

命令行需要同一策略时用 `~/.local/bin/wps-hidpi /usr/bin/wps "文件名"`，其他组件换用表中的原厂路径。直接调用原厂命令仍遵循调用者环境。已运行的 WPS 可能接管后续文件请求；核验启动环境时，应在保存工作并正常退出全部 WPS 组件后，从受管入口新开实例。

## 新安装应用的诊断与适配

1. 在两屏显示相同内容，运行 `hidpi-check` 找到目标窗口的 class、后端、输出和当前全局选项。菜单、字体、图标、点击区域分别观察，并检查跨屏后新打开的对话框。主窗口与工具窗口可能采用不同后端。
2. 原生 Wayland 应用先检查其自身界面设置。对内屏控件偏小的 XWayland 应用，优先测试软件支持的原生后端；仅支持 X11 时，先看其自带的界面或字体缩放。记录软件版本、组件和输出，仅为已验证的应用设置例外。WPS 的两个变量只适用于已验收的 WPS 入口。
3. MATLAB 可从标准桌面入口启动，分别观察主桌面、编辑器、Figure 与 Simulink 的菜单、工具栏和按钮。若有严重回归，记录具体窗口、后端、输出和现象，再判断该应用的处理方式。
4. WPS 软件包升级后，逐项对比 `/usr/share/applications/wps-office-*.desktop` 和仓库副本，特别核对 Exec、Actions、MimeType、URI/文件占位符；保留原始动作和参数。可用 `xdg-mime query default application/vnd.ms-excel` 检查表格的实际处理器。

## 回滚

- QQ 单次回退：用户正常退出 QQ（含托盘）后运行 `/opt/QQ/qq --ozone-platform=x11`。恢复软件包入口：删除本次新增的用户链接 `~/.local/share/applications/qq.desktop` 和 `~/.local/bin/qq-hidpi`，从 install/links.txt 移除这两行，避免下次部署重建。包升级时对比 `/usr/share/applications/qq.desktop`，同步新增动作及关联。
- Qt 单应用回退用 `env QT_QPA_PLATFORM=xcb 应用命令`。恢复原会话默认值时移除 autostart.lua 新增的 QT_QPA_PLATFORM 行，正常下次登录后生效；已运行进程保持其启动环境。
- **仅撤销 XWayland 零缩放**：把 `config/hypr/config/monitor.lua` 的 `force_zero_scaling = true` 改为 `false`。用 `hyprctl -j getoption xwayland:force_zero_scaling` 检查；如会话尚未更新，用 `hyprctl eval 'hl.config({xwayland={force_zero_scaling=false}})'` 立即应用。恢复新策略时将同一项设回 true。
- **仅撤销 WPS 启动适配**：在仓库根目录执行下列命令，仅移除仍指向本仓库的六个用户链接。本机部署前六个目标均不存在。其他机器如曾备份同名目标，按 INSTALL.md 恢复对应备份。随后移除 `install/links.txt` 中这六行，以免下次部署重建，下一次全新启动 WPS 即回到包入口。原有默认应用关联继续按相同 desktop ID 解析。

```bash
while IFS='|' read -r src dst; do
    case "$src" in
        config/scripts/wps-hidpi|config/applications/wps-office-*.desktop)
            target="$HOME/$dst"
            if [ -L "$target" ] && [ "$(readlink -f -- "$target")" = "$(realpath -- "$src")" ]; then
                unlink -- "$target"
            fi ;;
    esac
done < install/links.txt
```

- 移除诊断命令时删除 `~/.local/bin/hidpi-check` 链接及 install/links.txt 对应一行。上述本机链接首次部署时目标均不存在，其他机器有冲突时按 INSTALL.md 恢复安装器备份。
