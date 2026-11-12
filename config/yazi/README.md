# Yazi 基础配置

支持基线：Ubuntu 24.04、Yazi 26.9.1。保持上游文件类型规则、解压、预览、导航和删除交互，不引入插件管理器或主题包。

## 操作

| 按键 | 行为 |
| --- | --- |
| `O`（Shift+o） | 系统“打开方式”：从已安装应用中选择；取消无副作用，不修改默认关联 |
| `T`（Shift+t） | 在当前浏览目录打开独立终端窗口；空目录也可用，不是打开所选文件的父目录 |
| `g` 然后 `o` | Yazi 原生交互打开菜单，保留编辑、解压、查看等原生动作 |
| `Enter` / `o` | 继续按文件类型执行默认打开规则；文本默认在 Neovim 编辑 |

系统打开方式支持单文件、目录和相同 MIME 类型的多选；混合类型请分别打开。候选来自系统 desktop/MIME 注册，不保证每个应用都支持每种文件；列出所有应用方便手动选择。GUI 程序可能复用已有窗口。

## 模块边界

- `yazi.toml`：仅覆盖编辑器和系统打开器，继承上游 open.rules。
- `keymap.toml`：仅追加三组快捷键。
- `scripts/actions.py`：参数校验、分派和错误日志。
- `scripts/udc_yazi/settings.py`：读取本机参数、清理 Nix 专属图形变量。
- `scripts/udc_yazi/terminal.py`：终端 cwd 与编辑器 argv。
- `scripts/udc_yazi/desktop.py`：XDG 默认应用、GTK 应用选择。
- `local.example.toml`：本机参数模板；不包含本机用户名或绝对安装路径。

不为拆分而引入 Lua 层，TOML 继续使用 Yazi 原生格式；Python 模块仅负责系统集成。

## 迁移与本机参数

安装器按文件链接三个入口，不整体覆盖 ~/.config/yazi。需要 `/usr/bin/python3`（Ubuntu Python 3.11+）、python3-gi、gir1.2-gtk-3.0、xdg-utils；桌面沿用工程的 Ghostty/Neovim。其他发行版或非 Linux 系统需 AI 适配，不能宣称已经跨平台验证。

默认使用 PATH 中的 `ghostty --working-directory={cwd}` 和 `nvim`。其他设备仅需复制示例：

```bash
cp config/yazi/local.example.toml ~/.config/yazi/local.toml
```

如果文件已存在，先阅读并保留，不能无条件覆盖。本机文件不在仓库里，安装器不会覆盖。配置与动作入口统一遵循 YAZI_CONFIG_HOME → XDG_CONFIG_HOME/yazi → ~/.config/yazi；部署清单默认使用 ~/.config/yazi，采用自定义目录时 AI 应将这三个部署目标一并调整。

配置为 argv 数组，不支持 shell 片段：

```toml
[terminal]
argv = ["ghostty", "--working-directory={cwd}"]
[editor]
argv = ["nvim"]
```

`{cwd}` 以单独参数值安全传递；空格、中文和 shell 特殊字符不会作为命令执行。终端动作会设置进程 cwd；编辑器动作追加 `--` 和文件绝对路径。选用其他编辑器时应核实其支持 `--`。

AI 迁移检查：核对 Yazi 版本模板语法、GTK 系统解释器、终端命令、MIME 应用注册和图形会话；验证 O 选择/取消、同类多选、T 在空目录和中文空格目录中工作。不要把扫描到的本机应用清单写死进公共 TOML。

## 错误与验证

动作错误显示桌面通知，并写入 `${XDG_STATE_HOME:-~/.local/state}/ubuntu-desktop-config/yazi-actions.log`。终端启动后的 stderr 继承 Yazi 动作输出；第三方 GUI 启动结果仍需实际确认。

配置修改对新启动的 Yazi 生效，不需要重载 Hyprland。

可考虑的后续配置（暂未启用）：退出时让 Shell 跟随当前目录的 `y` 函数、常用目录书签、Git 状态、预览工具补齐。优先明确使用习惯，再引入插件。
