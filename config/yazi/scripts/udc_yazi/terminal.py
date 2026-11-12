import os
from pathlib import Path
import shutil
import subprocess
from .settings import command, desktop_env


def terminal_argv(cwd):
    return [part.replace("{cwd}", str(cwd)) for part in command("terminal")]


def open_terminal():
    cwd = Path.cwd()
    argv = terminal_argv(cwd)
    env = desktop_env()
    if not shutil.which(argv[0], path=env.get("PATH")):
        raise FileNotFoundError(f"终端未安装：{argv[0]}；请配置 ~/.config/yazi/local.toml")
    subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=None)


def edit(paths):
    argv = command("editor") + ["--"] + paths
    os.execvpe(argv[0], argv, desktop_env())
