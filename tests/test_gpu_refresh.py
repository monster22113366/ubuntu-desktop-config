import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('resources',Path(__file__).resolve().parents[1]/'config/tmux/scripts/resources.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class RefreshTests(unittest.TestCase):
    def test_device_numbering_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,vendor in [('card7','0x8086'),('card2','0x10de'),('card7-HDMI-A-1','0x8086')]:
                (root/name/'device').mkdir(parents=True);(root/name/'device/vendor').write_text(vendor)
            self.assertEqual(r.intel_device(root),'/dev/dri/card7')
            (root/'card9/device').mkdir(parents=True);(root/'card9/device/vendor').write_text('0x8086')
            self.assertIsNone(r.intel_device(root))
    def test_expired_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for data in ['bad',json.dumps(dict(time=time.monotonic()-20,boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),intel='0%',nvidia='3%'))]:
                (root/'status-v2.json').write_text(data)
                self.assertEqual(r.read_gpu_cache(root)[0],('N/A','N/A'))
    def test_failure_independent_and_zero_preserved(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(r,'intel_percent',side_effect=OSError),patch.object(r,'gpu_percent',return_value='0%'):
            r.refresh_gpu_cache(Path(temp))
            self.assertEqual(r.read_gpu_cache(Path(temp))[0],('N/A','0%'))
    def test_reader_returns_without_sampling(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,XDG_CACHE_HOME=temp),patch.object(r.subprocess,'Popen') as worker,patch.object(r,'intel_percent') as intel:
            self.assertEqual(r.gpu_status(),('N/A','N/A'))
            worker.assert_called_once();intel.assert_not_called()
    def test_held_lock_does_not_spawn(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,XDG_CACHE_HOME=temp),patch.object(r.subprocess,'Popen') as worker:
            with (r.cache_directory()/'refresh.lock').open('a') as lock:
                r.fcntl.flock(lock,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
                self.assertEqual(r.gpu_status(),('N/A','N/A'))
                worker.assert_not_called()
if __name__=='__main__':unittest.main()
