import os
from pathlib import Path
import tomllib


def config_dir():
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return Path(os.environ.get("YAZI_CONFIG_HOME", base / "yazi"))


def command(section):
    defaults = {"terminal": ["ghostty", "--working-directory={cwd}"], "editor": ["nvim"]}
    path = config_dir() / "local.toml"
    config = tomllib.loads(path.read_text()) if path.exists() else {}
    value = config.get(section, {}).get("argv", defaults[section])
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise ValueError(f"{section}.argv 必须是非空字符串数组：{path}")
    return value


def desktop_env():
    env = os.environ.copy()
    # Only remove this deployment's Nix graphics overrides, not unrelated user settings.
    for key in ("GBM_BACKENDS_PATH", "LIBGL_DRIVERS_PATH", "__EGL_VENDOR_LIBRARY_FILENAMES"):
        if "/nix/store/" in env.get(key, ""):
            env.pop(key)
    return env
