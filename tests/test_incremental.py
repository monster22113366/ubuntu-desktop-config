import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

gpu = module('gpu', 'config/tmux/scripts/resources.py')

class IncrementalTests(unittest.TestCase):
    def test_nvidia_power_guards_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            device = Path(directory)
            (device / 'vendor').write_text('0x10de')
            (device / 'class').write_text('0x030000')
            (device / 'driver').mkdir()
            (device / 'power').mkdir()
            (device / 'power/runtime_usage').write_text('1')
            with patch.object(gpu.Path, 'glob', return_value=[device]), patch.object(gpu.subprocess, 'run') as run:
                for state in ['suspended', 'suspending', 'unsupported']:
                    (device / 'power/runtime_status').write_text(state)
                    self.assertEqual(gpu.gpu_percent(), 'N/A')
                run.assert_not_called()
                (device / 'power/runtime_status').write_text('active')
                (device / 'power/runtime_usage').write_text('0')
                self.assertEqual(gpu.gpu_percent(), 'N/A')
                run.assert_not_called()
                (device / 'power/runtime_usage').write_text('1')
                for raw, expected in [('0', '0%'), ('42', '42%'), ('101', 'N/A'), ('N/A', 'N/A')]:
                    run.return_value = subprocess.CompletedProcess([], 0, raw)
                    self.assertEqual(gpu.gpu_percent(), expected)
                run.side_effect = subprocess.TimeoutExpired('nvidia-smi', 1)
                self.assertEqual(gpu.gpu_percent(), 'N/A')

    def test_cache_avoids_repeated_queries(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, XDG_CACHE_HOME=directory), patch.object(gpu, 'gpu_percent', return_value='12%') as sample, patch.object(gpu, 'intel_percent', return_value='N/A'):
            gpu.refresh_gpu_cache(gpu.cache_directory())
            for _ in range(20):
                self.assertEqual(gpu.gpu_status(), ('N/A', '12%'))
            sample.assert_called_once()

if __name__ == '__main__':
    unittest.main()
