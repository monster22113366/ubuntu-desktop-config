"""Device operations run on one serial worker per slider."""
import re
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from gi.repository import GLib


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=3)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"{args[0]} 失败 ({result.returncode})")
    return result.stdout.strip()


class Audio:
    target = "@DEFAULT_AUDIO_SINK@"

    def read(self):
        value = command("wpctl", "get-volume", self.target)
        match = re.fullmatch(r"Volume: ([0-9.]+)( \[MUTED\])?", value)
        if not match:
            raise ValueError("无法解析默认输出音量")
        return round(float(match[1]) * 100), bool(match[2])

    def write(self, value):
        if value == "mute":
            command("wpctl", "set-mute", self.target, "toggle")
        else:
            command("wpctl", "set-volume", self.target, f"{value}%")


class Backlight:
    def __init__(self, preferred):
        self.preferred = preferred

    def args(self):
        devices = sorted(p.name for p in Path("/sys/class/backlight").iterdir())
        if self.preferred in devices:
            name = self.preferred
        elif len(devices) == 1 and not self.preferred:
            name = devices[0]
        else:
            raise ValueError("检查屏幕背光设备及 hardware.lua 的 backlight 字段")
        return ["brightnessctl", "-c", "backlight", "-d", name]

    def read(self):
        _, kind, current, _, maximum = command(*self.args(), "-m", "info").split(",")
        if kind != "backlight" or int(maximum) <= 0:
            raise ValueError("无可用屏幕背光")
        return round(int(current) * 100 / int(maximum)), False

    def write(self, value):
        command(*self.args(), "set", f"{value}%")


class Channel:
    """GTK timer drains coalesced edits. Discard snapshots superseded by user input."""
    def __init__(self, device, render):
        self.device = device
        self.render = render
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pending = []
        self.future = None
        self.next_read = 0
        self.timer = GLib.timeout_add(70, self.tick)
        self.tick()

    def change(self, value):
        if value != "mute" and self.pending and self.pending[-1] != "mute":
            self.pending[-1] = value
        else:
            self.pending.append(value)

    def exchange(self, edits):
        for value in edits:
            self.device.write(value)
        return self.device.read()

    def tick(self):
        if self.future:
            if not self.future.done():
                return True
            try:
                result = self.future.result()
                if not self.pending:
                    self.render(result, "")
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                self.render(None, str(error))
            self.future = None
        now = GLib.get_monotonic_time()
        if self.pending or now >= self.next_read:
            edits, self.pending = self.pending, []
            self.future = self.pool.submit(self.exchange, edits)
            self.next_read = now + 750_000
        return True

    def close(self):
        GLib.source_remove(self.timer)
        if self.pending:
            self.pool.submit(self.exchange, self.pending)
        self.pool.shutdown(wait=False)
