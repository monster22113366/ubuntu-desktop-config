import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch, MagicMock
ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec=importlib.util.spec_from_file_location(name, ROOT/path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
launch=load('launch','config/scripts/tmux-launch.py')
gpu=load('gpu','config/tmux/scripts/resources.py')
class Tests(unittest.TestCase):
    def test_first_launch(self):
        with patch.object(launch,'snapshot',side_effect=[([],[]),(['$0'],[{'pid':'1'}])]), patch.object(launch.subprocess,'Popen') as spawn, patch.object(launch.time,'sleep'):
            launch.launch()
            self.assertEqual(spawn.call_args.args[0],['/usr/bin/ghostty','-e','tmux','new-session','-s','main'])
    def test_detached_sole(self):
        with patch.object(launch,'snapshot',side_effect=[(['$4'],[]),(['$4'],[{'pid':'1'}])]), patch.object(launch.subprocess,'Popen') as spawn, patch.object(launch.time,'sleep'):
            launch.launch(); self.assertEqual(spawn.call_args.args[0][-3:],['attach-session','-t','$4'])
    def test_multiple_detached_rejected(self):
        with patch.object(launch,'snapshot',return_value=(['$1','$2'],[])), patch.object(launch.subprocess,'Popen') as spawn:
            with self.assertRaises(launch.LaunchError):launch.launch()
            spawn.assert_not_called()
    def test_selection(self):
        clients=[{'pid':'10','session':'$0','activity':'1'},{'pid':'20','session':'$1','activity':'2'}]
        windows=[{'pid':10,'address':'0xa','class':'ghostty','mapped':True,'workspace':{'id':1}}, {'pid':20,'address':'0xb','class':'ghostty','mapped':True,'workspace':{'id':2}}]
        with patch.object(launch,'ancestors',side_effect=lambda pid:{pid}):
            self.assertEqual(launch.choose(clients,windows,'0xa')[0]['session'],'$0')
            with self.assertRaises(launch.LaunchError): launch.choose(clients,windows,None)
    def test_reuse_creates_window_without_ghostty(self):
        client={'pid':'10','session':'$0','activity':'1'};window={'address':'0xa'}
        with patch.object(launch,'snapshot',return_value=(['$0'],[client])), patch.object(launch,'choose',return_value=(client,window)), patch.object(launch,'run',side_effect=['[]','{}','ok','{"address":"0xa"}','10\t$0','']) as run, patch.object(launch.subprocess,'Popen') as spawn:
            launch.launch(); self.assertEqual(run.call_args.args,('tmux','new-window','-t','$0:'));spawn.assert_not_called()
    def test_intel_frames(self):
        for value, expected in [(0,'0%'),(12.7,'13%'),(-1,'N/A'),(101,'N/A'),(None,'N/A')]:
            raw=json.dumps([{}, {'engines':{'Render/3D':{'busy':value}}}])
            self.assertEqual(gpu.parse_intel(raw),expected)
        for raw in ['', '[{}]', '[{}, {"engines":{}}]']:
            self.assertEqual(gpu.parse_intel(raw),'N/A')
    def test_intel_failed_collector(self):
        with patch.object(gpu, 'intel_device', return_value='/dev/dri/card7'), patch.object(gpu.subprocess,'Popen') as p:
            p.return_value.wait.return_value=1
            self.assertEqual(gpu.intel_percent(),'N/A')
            self.assertIn('drm:/dev/dri/card7',p.call_args.args[0])
if __name__=='__main__':unittest.main()
