"""02.3: no real power, radio, audio, backlight or connection mutations."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'config/scripts/network'))
import backend
import menu
spec = importlib.util.spec_from_file_location('resources', ROOT / 'config/tmux/scripts/resources.py')
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


class NetworkTests(unittest.TestCase):
    def test_terse_colons_and_backslashes(self):
        self.assertEqual(backend.split_terse(r'a\:b:c\\d:AA\:BB'), ['a:b', 'c\\d', 'AA:BB'])

    def test_no_device(self):
        nm = backend.NetworkManager()
        with patch.object(nm, 'run', return_value=''):
            self.assertEqual(nm.devices(), [])
        with patch.object(nm, 'devices', return_value=[]):
            with self.assertRaises(backend.NetworkError):
                menu.Controller(nm).device('wifi')

    def test_saved_identity_and_ssid(self):
        nm = backend.NetworkManager()
        with patch.object(nm, 'run', side_effect=['uuid:name\\:duplicate:802-11-wireless', r'Cafe\:WiFi']):
            profile = nm.profiles('802-11-wireless')[0]
        self.assertEqual((profile.uuid, profile.ssid), ('uuid', 'Cafe:WiFi'))

    def test_password_is_only_in_anonymous_fd(self):
        password = 'dummy-S3cret:$() ; space'
        def run(command, **kwargs):
            self.assertNotIn(password, str(command))
            self.assertNotIn(password, str(kwargs['env']))
            self.assertEqual(command[-2], 'passwd-file')
            fd = kwargs['pass_fds'][0]
            self.assertEqual(os.read(fd, 4096).decode(), '802-11-wireless-security.psk:' + password + '\n')
            return subprocess.CompletedProcess(command, 0, '', '')
        with patch.object(backend.subprocess, 'run', side_effect=run):
            backend.NetworkManager().run('connection', 'up', 'uuid', 'test', secret=password)

    def test_failure_does_not_relay_secret_or_raw_output(self):
        result = subprocess.CompletedProcess([], 4, '', 'raw sensitive dummy-secret')
        with patch.object(backend.subprocess, 'run', return_value=result):
            with self.assertRaises(backend.NetworkError) as error:
                backend.NetworkManager().run('connection', 'up', 'uuid', 'test')
        self.assertNotIn('dummy-secret', str(error.exception))
        self.assertIn('激活失败', str(error.exception))

    def test_timeout_is_reported(self):
        with patch.object(backend.subprocess, 'run', side_effect=subprocess.TimeoutExpired('nmcli', 20)):
            with self.assertRaisesRegex(backend.NetworkError, '超时'):
                backend.NetworkManager().devices()

    def test_new_connection_failure_deletes_only_own_uuid(self):
        nm = backend.NetworkManager()
        with patch.object(backend.uuid, 'uuid4', return_value='created-uuid'), patch.object(nm, 'run', side_effect=['', backend.NetworkError('failed'), '']) as run:
            with self.assertRaises(backend.NetworkError):
                nm.connect_new('SSID', 'wifi0', 'wpa-psk', 'dummy-pass')
        self.assertEqual(run.call_args_list[-1].args, ('connection', 'delete', 'uuid', 'created-uuid'))
        self.assertNotIn('dummy-pass', str(run.call_args_list[0].args))

    def test_open_connection_does_not_need_password(self):
        nm = backend.NetworkManager()
        with patch.object(nm, 'run', return_value='') as run:
            nm.connect_new('Open', 'wifi0', 'open')
        self.assertIsNone(run.call_args_list[1].kwargs['secret'])
        self.assertEqual(run.call_args_list[2].args[-2:], ('connection.autoconnect', 'yes'))

    def test_disconnect_does_not_delete_profile(self):
        nm = backend.NetworkManager()
        with patch.object(nm, 'run') as run:
            nm.disconnect('wifi0')
        run.assert_called_once_with('device', 'disconnect', 'wifi0')

    def test_cancel_password_does_not_create_connection(self):
        nm = backend.NetworkManager()
        device = backend.Device('wifi0', 'wifi', 'disconnected', '')
        with patch.object(menu, 'wofi', return_value=None), patch.object(nm, 'connect_new') as connect:
            menu.Controller(nm).new(device, 'SSID', 'wpa-psk')
        connect.assert_not_called()

    def test_menu_index_and_password_settings(self):
        with patch.object(menu.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '99\n', '')):
            self.assertIsNone(menu.wofi('test', ['entry']))
        with patch.object(menu.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'dummy\n', '')) as run:
            self.assertEqual(menu.wofi('password', password=True, entry=True), 'dummy')
            args = run.call_args.args[0]
            self.assertIn('--password', args)
            self.assertEqual(args[args.index('--cache-file') + 1], '/dev/null')

    def test_scan_preserves_hidden_ssid(self):
        nm = backend.NetworkManager()
        with patch.object(nm, 'run', return_value=r'::40:WPA2:AA\:BB\:CC\:DD\:EE\:FF'):
            ap = nm.scan('wifi0')[0]
        self.assertEqual(ap.ssid, '')
        self.assertEqual(ap.bssid, 'AA:BB:CC:DD:EE:FF')


class ResourceTests(unittest.TestCase):
    def test_cpu_delta(self):
        self.assertEqual(resources.cpu_percent((100, 50), (200, 120)), '30%')
        self.assertEqual(resources.cpu_percent((100, 50), (100, 50)), 'N/A')

    def test_failure_is_na(self):
        output = io.StringIO()
        with patch.object(resources, 'cpu_sample', side_effect=OSError), patch.object(resources, 'memory_percent', side_effect=OSError), patch.object(resources, 'gpu_status', return_value=('N/A', 'N/A')), contextlib.redirect_stdout(output):
            resources.main()
        self.assertEqual(output.getvalue(), 'CPU N/A | RAM N/A | Intel GPU N/A | NVIDIA GPU N/A\n')

    def test_gpu_missing_device_never_runs_smi(self):
        with patch.object(resources.Path, 'glob', return_value=[]), patch.object(resources.subprocess, 'run') as run:
            self.assertEqual(resources.gpu_percent(), 'N/A')
            run.assert_not_called()

    def test_gpu_failure_preserves_cpu_and_ram(self):
        output = io.StringIO()
        with patch.object(resources, 'cpu_sample', side_effect=[(100, 50), (200, 120)]), patch.object(resources.time, 'sleep'), patch.object(resources, 'memory_percent', return_value='40%'), patch.object(resources, 'gpu_status', return_value=('N/A', 'N/A')), contextlib.redirect_stdout(output):
            resources.main()
        self.assertEqual(output.getvalue(), 'CPU 30% | RAM 40% | Intel GPU N/A | NVIDIA GPU N/A\n')

    def test_ram_uses_available(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'meminfo'
            path.write_text('MemTotal: 1000 kB\nMemAvailable: 600 kB\nMemFree: 100 kB\n')
            self.assertEqual(resources.memory_percent(path), '40%')


class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = dict(os.environ, PATH=str(self.base) + ':' + os.environ['PATH'])
        self.calls = self.base / 'calls'
        for name in ['systemctl', 'hyprctl', 'hyprlock', 'notify-send']:
            self.stub(name, f'echo "{name} $*" >> "{self.calls}"')

    def stub(self, name, body):
        path = self.base / name
        path.write_text('#!/bin/bash\n' + body + '\n')
        path.chmod(0o755)

    def power(self, first, second):
        count = self.base / 'count'
        self.stub('wofi', f'''cat >/dev/null
printf '%s\\n' "$*" >> "{self.base}/wofi-args"
previous=
for argument in "$@"; do
 if [[ "$previous" == --style ]]; then
  [[ -f "$argument" ]] || exit 99
  cat "$argument" > "{self.base}/css"
 fi
 previous=$argument
done
if [[ -f "{count}" ]]; then {second}; else touch "{count}"; {first}; fi''')
        return subprocess.run(['bash', str(ROOT / 'config/waybar/scripts/power-menu.sh')], env=self.env, capture_output=True, timeout=5)

    def test_power_default_cancel(self):
        self.power('echo 3', 'echo 0')
        self.assertFalse(self.calls.exists())
        self.assertIn('rgba(26, 27, 38, 0.96)', (self.base / 'css').read_text())
        self.assertIn('#bb9af7', (self.base / 'css').read_text())
        args = (self.base / 'wofi-args').read_text()
        for option in ['hide_search=true', 'exec_search=false', '/dev/null', 'dmenu-print_line_num=true']:
            self.assertIn(option, args)

    def test_power_escape_cancel(self):
        self.power('echo 4', 'exit 1')
        self.assertFalse(self.calls.exists())

    def test_power_typed_text_is_rejected(self):
        self.power('echo 3', 'echo 确认重启')
        self.assertFalse(self.calls.exists())

    def test_power_reboot_confirm(self):
        self.power('echo 3', 'echo 1')
        self.assertEqual(self.calls.read_text().strip(), 'systemctl reboot')

    def test_power_shutdown_confirm(self):
        self.power('echo 4', 'echo 1')
        self.assertEqual(self.calls.read_text().strip(), 'systemctl poweroff')

    def test_lock_preserved(self):
        self.power('echo 0', 'exit 1')
        self.assertEqual(self.calls.read_text().strip(), 'hyprlock')

    def test_suspend_with_existing_locker(self):
        self.stub('pgrep', 'exit 0')
        self.power('echo 1', 'exit 1')
        self.assertEqual(self.calls.read_text().strip(), 'systemctl suspend')

    def test_logout_uses_native_lua_dispatcher(self):
        self.power('echo 2', 'exit 1')
        self.assertEqual(self.calls.read_text().strip(), 'hyprctl eval hl.dispatch(hl.dsp.exit())')

    def test_proxy_distinguishes_listener_from_remote_probe(self):
        script = str(ROOT / 'config/waybar/scripts/proxy.sh')
        self.stub('timeout', 'exit 0')
        for http, text, css in [('200', 'PROXY OK', 'normal'), ('403', 'PROXY ON', 'warning'), ('000', 'PROXY ON', 'warning')]:
            self.stub('curl', f'printf {http}')
            result = subprocess.run(['bash', script], env=self.env, capture_output=True, text=True)
            status = json.loads(result.stdout)
            self.assertEqual((status['text'], status['class']), (text, css))
        self.stub('timeout', 'exit 1')
        result = subprocess.run(['bash', script], env=self.env, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['text'], 'PROXY OFF')

    def test_missing_devices(self):
        for command in ['brightnessctl', 'wpctl', 'bluetoothctl']:
            self.stub(command, 'exit 1')
        for name in ['backlight', 'volume', 'bluetooth']:
            path = str(ROOT / f'config/waybar/scripts/{name}.sh')
            status = subprocess.run(['bash', path], env=self.env, capture_output=True, text=True)
            self.assertEqual(status.returncode, 0, name)
            self.assertEqual(json.loads(status.stdout)['class'], 'unavailable')
            action = 'on' if name == 'bluetooth' else 'up'
            self.assertNotEqual(subprocess.run(['bash', path, action], env=self.env, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
