"""No hardware mutations. Exercise serialized writes and interactive agent responses."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "config/scripts/devices"))
from bluetooth import Bluetooth, GLib
from levels import Backlight, Channel
from panel import device_groups


class DeviceListTests(unittest.TestCase):
    adapter = "/org/bluez/hci0"

    def device(self, path, name, paired=False, connected=False):
        return (path, dict(Adapter=self.adapter, Alias=name, Paired=paired, Connected=connected))

    def test_connected_first_and_offline_paired_stays_visible(self):
        devices = [self.device("/a", "Alpha", True), self.device("/z", "Zulu", True, True),
                   self.device("/c", "Charlie", True, True), self.device("/n", "Nearby")]
        paired, nearby = device_groups(devices, self.adapter)
        self.assertEqual([p for p, _, _ in paired], ["/c", "/z", "/a"])
        self.assertEqual(nearby, [("/n", "Nearby", False)])

    def test_pairing_moves_one_row_between_sections(self):
        device = self.device("/phone", "Phone", connected=True)
        self.assertEqual(device_groups([device], self.adapter), ([], [("/phone", "Phone", True)]))
        paired_device = self.device("/phone", "Phone", paired=True, connected=True)
        self.assertEqual(device_groups([device, paired_device], self.adapter),
                         ([("/phone", "Phone", True)], []))

    def test_same_name_distinct_paths_and_adapter_filter(self):
        devices = [self.device("/b", "Phone"), self.device("/a", "Phone"),
                   ("/other", {"Adapter": "/org/bluez/hci1", "Paired": True})]
        self.assertEqual(device_groups(devices, self.adapter),
                         ([], [("/a", "Phone", False), ("/b", "Phone", False)]))

    def test_disconnect_and_reconnect_follow_current_properties(self):
        devices = [self.device("/a", "Alpha", True), self.device("/k", "Keyboard", True)]
        for connected, order in [(True, ["/k", "/a"]), (False, ["/a", "/k"]), (True, ["/k", "/a"])]:
            devices[1][1]["Connected"] = connected
            paired, nearby = device_groups(devices, self.adapter)
            self.assertEqual([path for path, _, _ in paired], order)
            self.assertFalse(nearby)


class PanelTests(unittest.TestCase):
    def test_final_write_survives_close(self):
        device = Mock()
        channel = Channel(device, Mock())
        for value in (10, 20, 30, "mute", 40, 50):
            channel.change(value)
        channel.close()
        channel.pool.shutdown(wait=True)
        self.assertEqual([call.args[0] for call in device.write.call_args_list], [30, "mute", 50])

    def test_multiple_backlights_require_selection(self):
        with patch.object(Path, "iterdir", return_value=[Path("panel1"), Path("panel2")]):
            with self.assertRaises(ValueError):
                Backlight("").args()
            self.assertEqual(Backlight("panel2").args(), ["brightnessctl", "-c", "backlight", "-d", "panel2"])

    def setUp(self):
        self.bt = Bluetooth.__new__(Bluetooth)
        self.bt.owner = ":1.2"
        self.bt.pair = "/device1"
        self.bt.prompt = Mock()
        self.bt.message = Mock()
        self.bt.pending = None
        self.bt.timeout = 0
        self.addCleanup(self.bt.answer, None)

    def ask(self, method, signature, args, sender=":1.2"):
        invocation = Mock()
        self.bt.agent(None, sender, None, None, method, GLib.Variant(signature, args), invocation)
        return invocation

    def test_confirmation_requires_explicit_response(self):
        invocation = self.ask("RequestConfirmation", "(ou)", ("/device1", 12))
        invocation.return_value.assert_not_called()
        self.assertIn("000012", self.bt.prompt.call_args.args[1])
        self.bt.answer("")
        invocation.return_value.assert_called_once_with(None)

    def test_pin_reject_and_passkey_validation(self):
        invocation = self.ask("RequestPinCode", "(o)", ("/device1",))
        self.bt.answer(None)
        invocation.return_dbus_error.assert_called_once()
        invocation = self.ask("RequestPasskey", "(o)", ("/device1",))
        self.bt.answer("1234567")
        invocation.return_value.assert_not_called()
        self.bt.answer("001234")
        self.assertEqual(invocation.return_value.call_args.args[0].unpack(), (1234,))

    def test_spoofed_or_unrequested_device(self):
        for sender, device in [(":1.9", "/device1"), (":1.2", "/device2")]:
            invocation = self.ask("RequestAuthorization", "(o)", (device,), sender)
            invocation.return_dbus_error.assert_called_once()
            self.bt.prompt.assert_not_called()

    def test_bluez_cancel_resolves_pending_request(self):
        invocation = self.ask("RequestPinCode", "(o)", ("/device1",))
        self.ask("Cancel", "()", ())
        invocation.return_dbus_error.assert_called_once()
        self.assertIsNone(self.bt.pending)

    def test_timeout_refuses_passkey(self):
        invocation = self.ask("RequestPasskey", "(o)", ("/device1",))
        GLib.source_remove(self.bt.timeout)
        self.bt.expire()
        invocation.return_dbus_error.assert_called_once()
        self.assertIsNone(self.bt.pending)

    def test_successful_pin_keeps_leading_zeroes(self):
        invocation = self.ask("RequestPinCode", "(o)", ("/device1",))
        self.bt.answer("0012")
        self.assertEqual(invocation.return_value.call_args.args[0].unpack(), ("0012",))

    def test_stop_discovery_only_if_owned(self):
        self.bt.cancel = Mock()
        self.bt.bus = Mock()
        self.bt.manager = None
        self.bt.signals = []
        self.bt.export = 1
        self.bt.pair = None
        self.bt.call = Mock()
        self.bt.registered = True
        for scan, expected in [(None, ["UnregisterAgent"]),
                               ("/adapter", ["StopDiscovery", "UnregisterAgent"])]:
            self.bt.call.reset_mock()
            self.bt.scan = scan
            self.bt.close()
            self.assertEqual([call.args[2] for call in self.bt.call.call_args_list], expected)
