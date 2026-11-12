import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'config/yazi/scripts'))
from udc_yazi import settings, terminal, desktop


class YaziActionsTests(unittest.TestCase):
    def test_terminal_special_paths_are_one_argument(self):
        with tempfile.TemporaryDirectory() as config, patch.dict(os.environ, {'YAZI_CONFIG_HOME': config}):
            cwd = Path('/tmp/中文 空格;$(touch should-not-exist)')
            self.assertEqual(terminal.terminal_argv(cwd), ['ghostty', '--working-directory=' + str(cwd)])

    def test_local_terminal_override(self):
        with tempfile.TemporaryDirectory() as config, patch.dict(os.environ, {'YAZI_CONFIG_HOME': config}):
            Path(config, 'local.toml').write_text('[terminal]\nargv=["kitty", "--directory", "{cwd}"]\n')
            self.assertEqual(terminal.terminal_argv(Path('/tmp/empty')), ['kitty', '--directory', '/tmp/empty'])

    def test_invalid_override_rejected(self):
        with tempfile.TemporaryDirectory() as config, patch.dict(os.environ, {'YAZI_CONFIG_HOME': config}):
            Path(config, 'local.toml').write_text('[terminal]\nargv="sh -c bad"\n')
            with self.assertRaises(ValueError):
                settings.command('terminal')

    def test_native_environment_preserves_other_settings(self):
        with patch.dict(os.environ, {'LIBGL_DRIVERS_PATH': '/nix/store/mesa/lib/dri',
                                    'GBM_BACKENDS_PATH': '/custom/drivers', 'DISPLAY': ':1'}):
            env = settings.desktop_env()
            self.assertNotIn('LIBGL_DRIVERS_PATH', env)
            self.assertEqual(env['GBM_BACKENDS_PATH'], '/custom/drivers')
            self.assertEqual(env['DISPLAY'], ':1')
            self.assertIn('LIBGL_DRIVERS_PATH', os.environ)

    def test_default_open_preserves_each_path(self):
        paths = ['/tmp/文件 one.txt', '/tmp/$(echo nope).txt']
        with patch.object(desktop.subprocess, 'run') as run:
            desktop.open_default(paths)
            self.assertEqual([call.args[0] for call in run.call_args_list],
                             [['xdg-open', p] for p in paths])

    def test_terminal_receives_browsed_empty_directory(self):
        with tempfile.TemporaryDirectory() as config, patch.dict(os.environ, {'YAZI_CONFIG_HOME': config}), \
             patch.object(terminal.Path, 'cwd', return_value=Path('/tmp/empty')), \
             patch.object(terminal.shutil, 'which', return_value='/usr/bin/ghostty'), \
             patch.object(terminal.subprocess, 'Popen') as spawn:
            terminal.open_terminal()
            self.assertEqual(spawn.call_args.kwargs['cwd'], Path('/tmp/empty'))
            self.assertEqual(spawn.call_args.args[0], ['ghostty', '--working-directory=/tmp/empty'])
