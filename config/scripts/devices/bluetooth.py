"""Panel-owned BlueZ discovery and pairing on the system bus."""
from gi.repository import Gio, GLib

BLUEZ = "org.bluez"
ADAPTER = BLUEZ + ".Adapter1"
DEVICE = BLUEZ + ".Device1"
MANAGER = BLUEZ + ".AgentManager1"
PATH = "/org/ubuntu/DesktopDevices/Agent"

# Direction and type of each argument per org.bluez.Agent1.
METHODS = {
    "Release": ("", ""), "Cancel": ("", ""),
    "RequestPinCode": ("o", "s"), "RequestPasskey": ("o", "u"),
    "DisplayPinCode": ("os", ""), "DisplayPasskey": ("ouq", ""),
    "RequestConfirmation": ("ou", ""), "RequestAuthorization": ("o", ""),
    "AuthorizeService": ("os", ""),
}
xml = '<node><interface name="org.bluez.Agent1">'
for name, (inputs, outputs) in METHODS.items():
    xml += f'<method name="{name}">'
    for direction, signature in (("in", inputs), ("out", outputs)):
        for kind in signature:
            xml += f'<arg type="{kind}" direction="{direction}"/>'
    xml += '</method>'
AGENT = Gio.DBusNodeInfo.new_for_xml(xml + '</interface></node>').interfaces[0]


def properties(proxy):
    return {key: proxy.get_cached_property(key).unpack()
            for key in proxy.get_cached_property_names() or []}


class Bluetooth:
    def __init__(self, redraw, message, prompt):
        self.redraw, self.message, self.prompt = redraw, message, prompt
        self.manager = self.bus = self.owner = None
        self.closed = self.registered = self.busy = False
        self.scan = self.pair = self.pending = None
        self.timeout = self.export = 0
        self.signals = []
        self.cancel = Gio.Cancellable()
        Gio.DBusObjectManagerClient.new_for_bus(
            Gio.BusType.SYSTEM, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START,
            BLUEZ, "/", None, None, self.cancel, self.ready)

    def ready(self, _, result):
        try:
            self.manager = Gio.DBusObjectManagerClient.new_for_bus_finish(result)
            if self.closed:
                return
            self.bus = self.manager.get_connection()
            self.export = self.bus.register_object(PATH, AGENT, self.agent)
            for signal in ("object-added", "object-removed", "interface-added",
                           "interface-removed"):
                self.signals.append(self.manager.connect(signal, lambda *_: self.redraw()))
            self.signals.append(self.manager.connect(
                "interface-proxy-properties-changed", self.properties_changed))
            self.signals.append(self.manager.connect("notify::name-owner", self.owner_changed))
            self.owner_changed()
        except GLib.Error as error:
            if not self.closed:
                self.message(error.message)

    def properties_changed(self, manager, obj, proxy, changed, invalidated):
        updates = changed.unpack()
        relevant = {"Powered", "Discovering", "Adapter", "Alias", "Address", "Paired", "Connected"}
        if relevant.isdisjoint(updates) and relevant.isdisjoint(invalidated):
            return
        if obj.get_object_path() == self.scan and proxy.get_interface_name() == ADAPTER:
            if updates.get("Powered") is False or updates.get("Discovering") is False:
                self.scan = None
        self.redraw()

    def owner_changed(self, *_):
        self.answer(None)
        self.owner = self.manager.get_name_owner()
        self.registered = self.busy = False
        self.scan = self.pair = None
        self.redraw()

    def objects(self, interface):
        if not self.manager or not self.owner:
            return []
        return sorted((obj.get_object_path(), properties(obj.get_interface(interface)))
                      for obj in self.manager.get_objects() if obj.get_interface(interface))

    def call(self, path, interface, method, args=None, done=None, timeout=20000):
        owner = self.owner

        def finish(bus, result):
            error = ""
            try:
                bus.call_finish(result)
            except GLib.Error as exc:
                error = exc.message
            if done and not self.closed and owner == self.owner:
                done(error)

        self.bus.call(owner, path, interface, method, args, None, Gio.DBusCallFlags.NONE,
                      timeout, None, finish)

    def action(self, path, method, value=None):
        if self.busy or not self.owner:
            return
        self.busy = True
        title = {"StartDiscovery": "扫描", "StopDiscovery": "停止扫描", "Set": "切换蓝牙电源",
                 "Pair": "配对", "Connect": "连接", "Disconnect": "断开连接"}[method]
        self.message(f"{title}…")
        if method == "Pair":
            self.pair = path
        self.redraw()

        def finish(error):
            if not error and method == "StartDiscovery":
                self.scan = path
            if not error and (method == "StopDiscovery" or (method == "Set" and not value)):
                self.scan = None
            if method == "Pair":
                self.answer(None)
                self.pair = None
            self.busy = False
            self.message(error or f"{title}完成")
            self.redraw()

        if method == "Set":
            self.call(path, "org.freedesktop.DBus.Properties", method, GLib.Variant(
                "(ssv)", (ADAPTER, "Powered", GLib.Variant("b", value))), finish)
        elif method == "Pair":
            def registered(error):
                if error:
                    finish(error)
                else:
                    self.registered = True
                    if self.pair == path:
                        self.call(path, DEVICE, "Pair", done=finish, timeout=90000)
                    else:
                        finish("配对已取消")
            if self.registered:
                registered("")
            else:
                self.call("/org/bluez", MANAGER, "RegisterAgent",
                          GLib.Variant("(os)", (PATH, "KeyboardDisplay")), registered)
        else:
            interface = ADAPTER if method.endswith("Discovery") else DEVICE
            self.call(path, interface, method, done=finish)

    def cancel_pair(self):
        path = self.pair
        self.pair = None
        self.answer(None)
        if path and self.registered:
            self.call(path, DEVICE, "CancelPairing")
        self.redraw()

    def agent(self, bus, sender, path, interface, method, parameters, invocation):
        args = parameters.unpack()
        if sender != self.owner:
            invocation.return_dbus_error("org.bluez.Error.Rejected", "Unknown sender")
            return
        if method in ("Cancel", "Release"):
            self.answer(None)
            if method == "Release":
                self.registered = False
            invocation.return_value(None)
            return
        if not args or args[0] != self.pair:
            invocation.return_dbus_error("org.bluez.Error.Rejected", "No local pairing request")
            return
        self.answer(None)
        details = " · ".join(map(str, args[1:]))
        if method in ("DisplayPasskey", "RequestConfirmation"):
            details = f"{args[1]:06d}"
            if method == "DisplayPasskey":
                details += f"（已输入 {args[2]} 位）"
        if method.startswith("Display"):
            self.message(f"请在配对设备输入 {details}")
            invocation.return_value(None)
            return
        self.pending = (method, invocation)
        self.timeout = GLib.timeout_add_seconds(45, self.expire)
        self.prompt(method, f"{args[0].split('/')[-1]}  {details}")

    def expire(self):
        self.timeout = 0
        self.answer(None)
        return False

    def answer(self, value):
        if not self.pending:
            return
        method, invocation = self.pending
        if value is None:
            invocation.return_dbus_error("org.bluez.Error.Rejected", "Pairing declined or expired")
        elif method == "RequestPasskey":
            if not (value.isascii() and value.isdigit() and len(value) <= 6):
                self.message("请输入最多六位数字")
                return
            invocation.return_value(GLib.Variant("(u)", (int(value),)))
        elif method == "RequestPinCode":
            if not 1 <= len(value.encode()) <= 16:
                self.message("请输入 1–16 字节的 PIN")
                return
            invocation.return_value(GLib.Variant("(s)", (value,)))
        else:
            invocation.return_value(None)
        self.pending = None
        if self.timeout:
            GLib.source_remove(self.timeout)
            self.timeout = 0
        self.prompt(None, "")

    def close(self):
        self.closed = True
        self.cancel.cancel()
        self.answer(None)
        if self.manager:
            for signal in self.signals:
                self.manager.disconnect(signal)
        if self.owner:
            if self.scan:
                self.call(self.scan, ADAPTER, "StopDiscovery")
            if self.pair:
                self.call(self.pair, DEVICE, "CancelPairing")
            if self.registered:
                self.call("/org/bluez", MANAGER, "UnregisterAgent", GLib.Variant("(o)", (PATH,)))
        if self.export:
            self.bus.unregister_object(self.export)
        # BlueZ also drops in-flight discovery/agent registrations on bus peer exit.
