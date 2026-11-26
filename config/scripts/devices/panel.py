#!/usr/bin/python3
import os
import sys
import gi

os.environ["GDK_BACKEND"] = "wayland"
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, Gio, GLib
from levels import Audio, Backlight, Channel
from bluetooth import Bluetooth, ADAPTER, DEVICE

try:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell as Layer
except (ValueError, ImportError):
    Layer = None

APP = "org.ubuntu.DesktopDevices"


def button(title, action):
    widget = Gtk.Button.new_with_label(title)
    widget.connect("clicked", lambda _: action())
    return widget


def label(value):
    return Gtk.Label(label=value, xalign=0, wrap=True)


def column(spacing=8):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)


def device_groups(objects, adapter):
    """Use one Device1 snapshot per object path, including same-name devices."""
    paired, nearby = [], []
    for path, props in dict(objects).items():
        if props.get("Adapter") != adapter:
            continue
        name = props.get("Alias") or props.get("Name") or props.get("Address") or path
        group = paired if props.get("Paired") else nearby
        group.append((path, name, bool(props.get("Connected"))))
    paired.sort(key=lambda row: (not row[2], row[1].casefold(), row[0]))
    nearby.sort(key=lambda row: (row[1].casefold(), row[0]))
    return paired, nearby


class Slider:
    def __init__(self, box, title, minimum, device):
        row = Gtk.Box(spacing=12)
        row.pack_start(label(title), True, True, 0)
        self.value = label("读取中…")
        row.add(self.value)
        self.mute = None
        if isinstance(device, Audio):
            self.mute = button("静音", lambda: self.channel.change("mute"))
            self.mute.set_sensitive(False)
            row.add(self.mute)
        box.add(row)
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, minimum, 100, 1)
        self.scale.set_draw_value(False)
        self.scale.set_sensitive(False)
        box.add(self.scale)
        self.signal = self.scale.connect("value-changed", self.changed)
        self.channel = Channel(device, self.render)

    def changed(self, scale):
        value = round(scale.get_value())
        self.channel.change(value)
        self.value.set_text(f"{value}% …")

    def render(self, result, error):
        self.scale.set_sensitive(result is not None)
        if self.mute:
            self.mute.set_sensitive(result is not None)
        if result is None:
            self.value.set_text("不可用 · " + error)
            return
        value, muted = result
        self.value.set_text(f"{value}%" + (" · 静音" if muted else ""))
        if self.mute:
            self.mute.set_label("解除静音" if muted else "静音")
        with self.scale.handler_block(self.signal):
            self.scale.set_value(value)


class Panel(Gtk.ApplicationWindow):
    def __init__(self, app, monitor, preferred):
        super().__init__(application=app, title="设备控制")
        self.set_decorated(False)
        self.set_default_size(440, 460)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        if Layer and Layer.is_supported():
            Layer.init_for_window(self)
            Layer.set_namespace(self, "desktop-devices")
            Layer.set_layer(self, Layer.Layer.OVERLAY)
            Layer.set_keyboard_mode(self, Layer.KeyboardMode.EXCLUSIVE)
            Layer.set_exclusive_zone(self, 0)
            display = self.get_display()
            for i in range(display.get_n_monitors()):
                if screen.get_monitor_plug_name(i) == monitor:
                    Layer.set_monitor(self, display.get_monitor(i))
                    break
        self.connect("key-press-event", self.key)
        css = Gtk.CssProvider()
        css.load_from_data(b"""
window { background: rgba(36,40,59,.97); color: #c0caf5; border-radius: 14px; }
button { background: #343b58; color: #c0caf5; border-radius: 7px; }
button:hover, scale highlight { background: #728bd2; }
scale slider { background: #bb9af7; }
""")
        Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box = column(10)
        box.set_border_width(18)
        self.add(box)
        self.sliders = [Slider(box, "输出音量", 0, Audio()),
                        Slider(box, "屏幕亮度", 5, Backlight(preferred))]
        box.add(Gtk.Separator())
        self.radio = Gtk.Box(spacing=8)
        box.add(self.radio)
        self.sections = []
        for title in ("已配对设备", "附近未配对设备"):
            box.add(label(title))
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll.set_min_content_height(80)
            rows = column()
            scroll.add(rows)
            box.pack_start(scroll, True, True, 0)
            self.sections.append(rows)
        self.status = label("正在读取蓝牙…")
        box.add(self.status)
        self.prompt_box = column()
        box.add(self.prompt_box)
        self.adapter = None
        self.bt = Bluetooth(self.refresh, self.status.set_text, self.prompt)
        self.connect("destroy", self.cleanup)

    def key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def cleanup(self, *_):
        for slider in self.sliders:
            slider.channel.close()
        self.bt.close()

    def prompt(self, method, details):
        for widget in self.prompt_box.get_children():
            widget.destroy()
        if not method:
            return
        names = {"RequestPinCode": "输入 PIN", "RequestPasskey": "输入配对码",
                 "RequestConfirmation": "核对两端配对码", "AuthorizeService": "允许服务",
                 "RequestAuthorization": "允许配对"}
        self.prompt_box.add(label(names[method] + " · " + details))
        entry = Gtk.Entry()
        if method in ("RequestPinCode", "RequestPasskey"):
            self.prompt_box.add(entry)
        actions = Gtk.Box(spacing=8)
        actions.add(button("确认", lambda: self.bt.answer(entry.get_text())))
        actions.add(button("拒绝", lambda: self.bt.answer(None)))
        self.prompt_box.add(actions)
        self.prompt_box.show_all()

    def select_adapter(self, selector):
        self.adapter = selector.get_active_id()
        self.refresh()

    def refresh(self):
        bt = self.bt
        for box in (*self.sections, self.radio):
            for child in box.get_children():
                child.destroy()
        adapters = bt.objects(ADAPTER)
        if not adapters:
            self.radio.add(label("蓝牙适配器不可用"))
        else:
            available = dict(adapters)
            if bt.scan not in available:
                bt.scan = None
            if self.adapter not in available:
                self.adapter = adapters[0][0]
            path = self.adapter
            adapter = available[path]
            if len(adapters) > 1:
                select = Gtk.ComboBoxText()
                for key, item in adapters:
                    select.append(key, item.get("Alias") or key)
                select.set_active_id(path)
                select.connect("changed", self.select_adapter)
                self.radio.add(select)
            on = adapter.get("Powered", False)
            self.radio.add(label("蓝牙 · " + ("开启" if on else "关闭")))
            self.radio.add(button("关闭" if on else "开启", lambda: bt.action(path, "Set", not on)))
            if on:
                method = "StopDiscovery" if bt.scan == path else "StartDiscovery"
                self.radio.add(button("停止扫描" if bt.scan == path else "扫描",
                                      lambda: bt.action(path, method)))
            paired, nearby = device_groups(bt.objects(DEVICE), path)
            self.fill_devices(self.sections[0], paired, paired=True)
            self.fill_devices(self.sections[1], nearby, paired=False)
            for section in self.sections:
                section.set_sensitive(on and not bt.busy)
        for control in self.radio.get_children():
            control.set_sensitive(not bt.busy and not (bt.scan and isinstance(control, Gtk.ComboBoxText)))
        if bt.pair:
            self.radio.add(button("取消配对", bt.cancel_pair))
        if self.status.get_text() == "正在读取蓝牙…":
            self.status.set_text("")
        self.radio.show_all()
        for section in self.sections:
            section.show_all()

    def fill_devices(self, box, devices, paired):
        if not devices:
            box.add(label("暂无已配对设备" if paired else "暂无附近设备"))
        for path, name, connected in devices:
            row = Gtk.Box(spacing=6)
            state = "已连接" if connected else "未连接"
            row.pack_start(label(f"{name}\n{state}"), True, True, 0)
            actions = []
            if not paired:
                actions.append(("配对", "Pair"))
            if connected:
                actions.append(("断开", "Disconnect"))
            elif paired:
                actions.append(("连接", "Connect"))
            for title, action in actions:
                row.add(button(title, lambda d=path, a=action: self.bt.action(d, a)))
            box.add(row)


def main():
    monitor, preferred = (sys.argv[1:] + ["", ""])[:2]
    GLib.set_prgname(APP)
    app = Gtk.Application(application_id=APP, flags=Gio.ApplicationFlags.FLAGS_NONE)

    def activate(application):
        window = application.get_active_window()
        if window is None:
            window = Panel(application, monitor, preferred)
            window.show_all()
        window.present()

    app.connect("activate", activate)
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    sys.exit(main())
