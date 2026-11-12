#!/usr/bin/python3
"""Entry point: validate arguments, dispatch modules, retain actionable errors."""
import os
from pathlib import Path
import subprocess
import sys
import traceback
from udc_yazi import desktop, terminal


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("terminal", "edit", "open", "choose"):
        raise ValueError("用法：actions.py terminal | edit/open/choose FILE...")
    action = sys.argv[1]
    if action == "terminal":
        terminal.open_terminal()
        return
    paths = [os.path.abspath(p) for p in sys.argv[2:]]
    if not paths:
        raise ValueError("当前没有选中的文件")
    {"edit": terminal.edit, "open": desktop.open_default, "choose": desktop.choose}[action](paths)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "ubuntu-desktop-config/yazi-actions.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as stream:
            traceback.print_exc(file=stream)
        print(str(exc), file=sys.stderr)
        try:
            subprocess.run(["notify-send", "Yazi 操作失败", f"{exc}\n日志：{log}"], check=False)
        except OSError:
            pass
        sys.exit(1)
