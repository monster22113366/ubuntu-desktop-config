"""02.1 regression tests. No compositor interaction; commands are stubbed in PATH."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesktopScripts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.base),
                        PATH=str(self.base) + ':' + os.environ['PATH'])
        helpers = self.base / 'Projects/ubuntu-desktop-config/config/waybar/scripts'
        helpers.parent.mkdir(parents=True)
        helpers.symlink_to(ROOT / 'config/waybar/scripts', target_is_directory=True)
        self.trace = self.base / 'trace'
        self.stub('notify-send', 'exit 0')
        self.stub('xdg-user-dir', f'echo "{self.base}/pictures"')
        self.stub('grim', f'echo grim >> "{self.trace}"; printf PNG > "$3"')
        self.stub('wl-copy', f'cat > "{self.base}/clipboard"')

    def stub(self, name, body):
        path = self.base / name
        path.write_text('#!/bin/bash\n' + body + '\n')
        path.chmod(0o755)

    def run_script(self, name):
        return subprocess.run(['bash', str(ROOT / 'config/scripts' / name)],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_cancel_never_captures(self):
        for response in ['exit 1', 'exit 0']:
            self.stub('slurp', response)
            for script in ['screenshot-region.sh', 'screenshot-clipboard.sh']:
                self.assertEqual(self.run_script(script).returncode, 0)
                self.assertFalse(self.trace.exists())
                self.assertFalse((self.base / 'clipboard').exists())

    def test_capture_failure_preserves_clipboard_and_removes_file(self):
        self.stub('slurp', 'echo "0,0 20x20"')
        self.stub('grim', 'exit 1')
        for script in ['screenshot-region.sh', 'screenshot-clipboard.sh']:
            self.assertNotEqual(self.run_script(script).returncode, 0)
        self.assertFalse((self.base / 'clipboard').exists())
        self.assertEqual(list((self.base / 'pictures/Screenshots').glob('*.png')), [])

    def test_success_and_unique_filenames(self):
        self.stub('slurp', 'echo "0,0 20x20"')
        for _ in range(2):
            self.assertEqual(self.run_script('screenshot-region.sh').returncode, 0)
        self.assertEqual(len(list((self.base / 'pictures/Screenshots').glob('*.png'))), 2)
        self.assertEqual(self.run_script('screenshot-clipboard.sh').returncode, 0)
        self.assertEqual((self.base / 'clipboard').read_text(), 'PNG')

    def test_help_renders_modifiers_mouse_and_cancel(self):
        self.stub('hyprctl', '''cat <<'JSON'
[{"has_description":true,"description":"窗口｜测试","key":"H","modmask":65,"submap":""},
 {"has_description":true,"description":"鼠标｜拖动","key":"mouse:272","modmask":64,"submap":""}]
JSON''')
        self.stub('wofi', f'cat > "{self.base}/help"; exit 1')
        self.assertEqual(self.run_script('shortcut-help.sh').returncode, 0)
        result = (self.base / 'help').read_text()
        self.assertIn('Super + Shift + H', result)
        self.assertIn('Super + 左键拖动', result)

    def test_help_ipc_failure_is_not_hidden(self):
        self.stub('hyprctl', 'exit 1')
        self.stub('wofi', f'touch "{self.trace}"')
        self.assertNotEqual(self.run_script('shortcut-help.sh').returncode, 0)
        self.assertFalse(self.trace.exists())


    def test_monitor_sensor_failure_still_opens_panel(self):
        self.stub('timeout', 'exit 124')
        self.stub('wofi', f'cat > "{self.base}/monitor"; exit 1')
        self.assertEqual(self.run_script('system-monitor.sh').returncode, 0)
        result = (self.base / 'monitor').read_text()
        self.assertIn('CPU / SSD / FAN：不可用', result)
        self.assertIn('GPU：不可用', result)

    def test_device_action_failure_reports_error(self):
        self.stub('wpctl', 'exit 1')
        self.stub('timeout', 'exit 124')
        self.stub('wofi', 'cat >/dev/null; echo "音量 +5%"')
        self.stub('notify-send', f'echo "$*" >> "{self.trace}"')
        self.assertNotEqual(self.run_script('device-control.sh').returncode, 0)
        self.assertIn('操作失败', self.trace.read_text())
        self.assertNotIn('音量已增加', self.trace.read_text())


if __name__ == '__main__':
    unittest.main()
