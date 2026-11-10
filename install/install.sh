#!/usr/bin/env bash
# Run as the desktop user: bash install/install.sh [--dry-run]
set -Eeuo pipefail
ROOT=$(dirname -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")")
dry_run=false
success=0 skipped=0 failed=0
backup_root=
nix_installer=

ok() { printf '[OK] %s\n' "$*"; success=$((success + 1)); }
skip() { printf '[SKIP] %s\n' "$*"; skipped=$((skipped + 1)); }
die() { printf '[FAIL] %s\n' "$*" >&2; failed=$((failed + 1)); exit 1; }
summary() {
    local status=$?
    [[ -z "$nix_installer" ]] || rm -f -- "$nix_installer"
    printf '\n完成：成功 %s，跳过/计划 %s，失败 %s（exit=%s）\n' "$success" "$skipped" "$failed" "$status"
    [[ -z "$backup_root" ]] || printf '原配置备份：%s\n' "$backup_root"
}
apt_installed() { [[ $(dpkg-query -W -f='${Status}' "$1" 2>/dev/null) == 'install ok installed' ]]; }
# No evaluation of package-list contents; each validated line is one argument.
read_packages() {
    local line
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=${line%%#*}
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue
        [[ "$line" =~ ^[a-zA-Z0-9][a-zA-Z0-9.+-]*$ ]] || die "无效软件包名：$line"
        printf '%s\n' "$line"
    done < "$1"
}

link_config() {
    local source=$1 target=$2 relative saved
    [[ -e "$source" ]] || die "链接源不存在：$source"
    [[ "$target" == "$HOME/"* ]] || die "拒绝部署到 HOME 以外：$target"
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ $(readlink -f -- "$target" || true) == "$(readlink -f -- "$source")" ]]; then
            skip "链接已正确：$target"
            return
        fi
    fi
    if "$dry_run"; then
        skip "计划：备份现有目标（如有），链接 $target -> $source"
        return
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ -z "$backup_root" ]]; then
            mkdir -p "$HOME/.local/state/ubuntu-desktop-config/backups"
            backup_root=$(mktemp -d "$HOME/.local/state/ubuntu-desktop-config/backups/$(date +%Y%m%d-%H%M%S)-XXXXXX")
        fi
        relative=${target#"$HOME/"}
        saved="$backup_root/$relative"
        mkdir -p -- "$(dirname -- "$saved")"
        mv -T -- "$target" "$saved"
        printf '[BACKUP] %s -> %s\n' "$target" "$saved"
    fi
    mkdir -p -- "$(dirname -- "$target")"
    ln -s -- "$source" "$target"
    ok "链接：$target"
}

preflight() {
    [[ $EUID -ne 0 ]] || die '请以桌面用户执行，不要 sudo bash install/install.sh'
    # /etc/os-release is maintained by the distribution, not user input.
    source /etc/os-release
    [[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 24.04 ]] || die '目前只支持 Ubuntu 24.04；请先让 AI 审阅目标发行版差异'
    local tool source destination profile
    for tool in sudo apt-get dpkg-query python3 readlink; do
        command -v "$tool" >/dev/null || die "缺少基础工具：$tool"
    done
    for tool in Hyprland hypridle hyprlock ghostty; do
        command -v "$tool" >/dev/null || die "请先准备桌面基础组件：$tool（脚本不添加第三方软件源）"
    done
    [[ $(Hyprland --version) == *'0.57.1'* ]] || die '当前 Lua 配置面向 Hyprland 0.57.1；其他版本先经 AI 适配'
    [[ -f "$ROOT/profiles/hardware.lua" ]] || die '缺少 profiles/hardware.lua；请复制示例并填写真实显示器参数，再运行脚本'
    for profile in hardware.lua user.lua; do
        if [[ -f "$HOME/.config/hypr/profiles/$profile" ]]; then
            cmp -s "$ROOT/profiles/$profile" "$HOME/.config/hypr/profiles/$profile" ||
                die "现有 Hyprland $profile 与仓库不同；请人工核对，脚本不会覆盖或导入"
        fi
    done
    while IFS='|' read -r source destination; do
        [[ -z "$source" || "$source" == \#* ]] && continue
        [[ -n "$destination" && "$destination" != /* && "$destination" != *'..'* ]] || die "无效链接目标：$destination"
        [[ -e "$ROOT/$source" ]] || die "缺少配置源：$source"
    done < "$ROOT/install/links.txt"
    # Preserve working native configs. On a new account/location AI edits their
    # few local references first; do not silently rewrite or generate configs.
    python3 - "$ROOT" <<'PY'
import os, re, sys, tomllib
from pathlib import Path
root = Path(sys.argv[1]).resolve()
files = [root/'config/hypr/config/keybinds.lua', root/'config/waybar/config.jsonc',
         root/'config/scripts/system-monitor.sh', root/'config/scripts/device-control.sh',
         *root.glob('config/applications/*.desktop')]
for path in files:
    text = path.read_text()
    if '/Projects/ubuntu-desktop-config' in text:
        expected = Path.home()/'Projects/ubuntu-desktop-config'
        if expected.resolve() != root:
            sys.exit(f'请先适配仓库路径：{path}（当前仍要求 {expected}）')
    for literal in re.findall(r'/home/[^/\s"\x27]+/Projects/ubuntu-desktop-config', text):
        if Path(literal).resolve() != root:
            sys.exit(f'请先适配用户名/路径：{path}: {literal}')
config = tomllib.loads((root/'config/starship/starship.toml').read_text())
home = config.get('directory', {}).get('home_symbol', '~')
if home.startswith('/') and home != str(Path.home()):
    sys.exit('请先适配 Starship directory.home_symbol 为目标用户家目录')
PY
    if command -v nvim >/dev/null; then
        local version
        version=$(nvim --version)
        if [[ "$version" =~ NVIM[[:space:]]v0\.([0-9]+)\. ]] && (( BASH_REMATCH[1] < 11 )); then
            die '现有 Neovim 低于 0.11，不支持此配置的 vim.lsp.config；请先人工决定软件来源，不重复安装'
        fi
    fi
    ok '系统、Profile、链接源与现有本机路径检查'
}

install_apt() {
    local package list
    local -a missing=()
    list=$(read_packages "$ROOT/install/apt-packages.txt")
    while IFS= read -r package; do
        if apt_installed "$package"; then skip "apt 已安装：$package"; else missing+=("$package"); fi
    done <<< "$list"
    if (( ${#missing[@]} )); then
        if "$dry_run"; then skip "计划 apt 安装：${missing[*]}"; else
            sudo apt-get update
            sudo apt-get install -y --no-install-recommends "${missing[@]}"
            ok "apt 安装：${missing[*]}"
        fi
    fi
}

install_nix() {
    local package command apt_equivalent list
    export PATH="$HOME/.nix-profile/bin:$PATH"
    if ! command -v nix >/dev/null; then
        if "$dry_run"; then skip '计划：从 nixos.org 下载并执行 Nix 单用户安装器（--no-daemon）'; else
            printf '未检测到 Nix，将运行官方单用户安装器；不会创建 Nix daemon 服务。\n'
            nix_installer=$(mktemp)
            curl --fail --location --proto '=https' --tlsv1.2 https://nixos.org/nix/install -o "$nix_installer"
            NIX_INSTALLER_NO_MODIFY_PROFILE=1 sh "$nix_installer" --no-daemon
            [[ -r "$HOME/.nix-profile/etc/profile.d/nix.sh" ]] || die 'Nix 环境初始化脚本缺失，请查看安装器输出'
            # Initialise this process; do not edit user Shell startup files.
            # The official profile script may read unset optional variables.
            set +u
            source "$HOME/.nix-profile/etc/profile.d/nix.sh"
            set -u
            command -v nix >/dev/null || die 'Nix 安装后仍不可用，请查看安装器输出'
            ok 'Nix 已安装'
        fi
    else skip 'Nix 已存在，不重装'; fi
    if [[ -e "$HOME/.nix-profile/manifest.nix" && ! -e "$HOME/.nix-profile/manifest.json" ]]; then
        die '检测到旧 nix-env profile，请人工规划迁移；脚本不改写旧 profile'
    fi
    list=$(read_packages "$ROOT/nix/packages.txt")
    while IFS= read -r package; do
        case "$package" in
            tmux) command=tmux; apt_equivalent=tmux ;;
            neovim) command=nvim; apt_equivalent=neovim ;;
            yazi) command=yazi; apt_equivalent=yazi ;;
            starship) command=starship; apt_equivalent=starship ;;
            tree-sitter) command=tree-sitter; apt_equivalent=tree-sitter-cli ;;
            nerd-fonts.jetbrains-mono)
                if [[ -d "$HOME/.nix-profile/share/fonts/truetype/NerdFonts/JetBrainsMono" ]] ||
                   { command -v fc-list >/dev/null && [[ $(fc-list : family) == *'JetBrainsMono Nerd Font'* ]]; }; then
                    skip 'JetBrains Mono Nerd Font 已存在'; continue
                fi
                command=; apt_equivalent=fonts-jetbrains-mono-nerd ;;
            *) die "请为新增 Nix 软件包配置已安装检测：$package" ;;
        esac
        if apt_installed "$apt_equivalent" || { [[ -n "$command" ]] && command -v "$command" >/dev/null; }; then
            skip "已有软件，保留现有来源：$package"
        elif "$dry_run"; then skip "计划 Nix 安装：$package"; else
            nix --extra-experimental-features 'nix-command flakes' profile install "${NIXPKGS_REF:-nixpkgs}#$package"
            ok "Nix 安装：$package"
        fi
    done <<< "$list"
}

deploy_configs() {
    local source destination
    while IFS='|' read -r source destination; do
        [[ -z "$source" || "$source" == \#* ]] && continue
        link_config "$ROOT/$source" "$HOME/$destination"
    done < "$ROOT/install/links.txt"
    # Ubuntu ImageMagick 6 has convert, while real-icons.nvim calls magick.
    if command -v magick >/dev/null; then skip 'magick 已存在'; else
        link_config "$ROOT/install/helpers/magick" "$HOME/.local/bin/magick"
    fi
    source="$HOME/.nix-profile/share/fonts/truetype/NerdFonts/JetBrainsMono"
    if [[ -d "$source" ]]; then
        link_config "$source" "$HOME/.local/share/fonts/udc-jetbrains-mono"
        if ! "$dry_run"; then fc-cache -f "$HOME/.local/share/fonts"; fi
    else skip 'Nix 字体目录未出现；已有系统字体保持不变（新安装请核对字体）'; fi
    skip 'Yazi 无仓库配置，保留已有用户数据，不创建虚构配置'
    printf '\n不会重载桌面或 tmux，不修改系统代理、服务设置或 Shell 初始化。\n'
    printf '请核对图形会话 PATH 包含 ~/.nix-profile/bin、~/.local/bin；Starship 的 Shell 初始化沿用现有配置。\n'
}

main() {
    case "${1:-}" in
        '') ;;
        --dry-run) dry_run=true ;;
        --help) printf '用法：bash install/install.sh [--dry-run]\n'; return ;;
        *) die "未知参数：$1" ;;
    esac
    (( $# <= 1 )) || die '参数过多'
    trap 'failed=$((failed + 1)); printf "[FAIL] 第 %s 行执行失败：%s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
    trap summary EXIT
    preflight
    install_apt
    install_nix
    deploy_configs
}
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then main "$@"; fi
