"""Exercise installer operations only with temporary HOME and mocked packages."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'install/install.sh'


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='udc-install-test-')
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'home with space'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')

    def shell(self, code, *args, check=True):
        return subprocess.run(['bash', '-c', 'source "$1"\n' + code, 'test', str(SCRIPT), *map(str,args)],
                              env=self.env, text=True, capture_output=True, check=check, timeout=10)

    def test_directory_and_user_data_backed_up_and_second_run_skips(self):
        source = self.home / 'checkout/config/nvim'
        source.mkdir(parents=True)
        (source / 'init.lua').write_text('return {}')
        target = self.home / '.config/nvim'
        (target / '.git').mkdir(parents=True)
        (target / 'unsaved.lua').write_text('personal changes')
        self.shell('link_config "$2" "$3"; link_config "$2" "$3"',source,target)
        self.assertTrue(target.is_symlink())
        backups = list((self.home / '.local/state/ubuntu-desktop-config/backups').glob('*/.config/nvim'))
        self.assertEqual(len(backups),1)
        self.assertEqual((backups[0] / 'unsaved.lua').read_text(),'personal changes')
        self.assertTrue((backups[0] / '.git').is_dir())

    def test_regular_file_and_dangling_link_preserved(self):
        source = self.home / 'source'
        source.write_text('new')
        regular = self.home / '.tmux.conf'
        regular.write_text('old')
        dangling = self.home / '.config/example'
        dangling.parent.mkdir()
        dangling.symlink_to(self.home / 'missing')
        self.shell('link_config "$2" "$3"; link_config "$2" "$4"',source,regular,dangling)
        backup = next((self.home / '.local/state/ubuntu-desktop-config/backups').iterdir())
        self.assertEqual((backup/'.tmux.conf').read_text(),'old')
        self.assertTrue((backup/'.config/example').is_symlink())
        self.assertEqual(os.readlink(backup/'.config/example'),str(self.home/'missing'))

    def test_dry_run_and_missing_source_do_not_touch_destination(self):
        source = self.home/'source'
        source.write_text('new')
        target = self.home/'original'
        target.write_text('keep')
        self.shell('dry_run=true; link_config "$2" "$3"',source,target)
        self.assertEqual(target.read_text(),'keep')
        self.assertFalse((self.home/'.local').exists())
        result=self.shell('link_config "$2" "$3"',self.home/'absent',target,check=False)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(target.read_text(),'keep')

    def test_apt_only_installs_missing_and_propagates_failure(self):
        checkout=self.home/'checkout'
        (checkout/'install').mkdir(parents=True)
        (checkout/'install/apt-packages.txt').write_text('git\njq\n')
        result=self.shell('''ROOT="$2"
apt_installed() { [[ "$1" == git ]]; }
sudo() { printf 'MOCK sudo %s\\n' "$*"; }
install_apt''',checkout)
        self.assertIn('MOCK sudo apt-get install -y --no-install-recommends jq',result.stdout)
        self.assertNotIn('--no-install-recommends git',result.stdout)
        result=self.shell('''ROOT="$2"
apt_installed() { return 1; }
sudo() { return 42; }
install_apt''',checkout,check=False)
        self.assertEqual(result.returncode,42)

    def test_nix_keeps_apt_managed_program_and_skips_existing_nix(self):
        checkout=self.home/'checkout'
        (checkout/'nix').mkdir(parents=True)
        (checkout/'nix/packages.txt').write_text('tmux\n')
        result=self.shell('''ROOT="$2"
nix() { echo 'UNEXPECTED NIX INSTALL'; return 99; }
apt_installed() { [[ "$1" == tmux ]]; }
install_nix''',checkout)
        self.assertIn('已有软件',result.stdout)
        self.assertNotIn('UNEXPECTED',result.stdout)

    def test_package_list_cannot_execute_shell(self):
        package_list=self.home/'packages'
        package_list.write_text('tmux; touch marker\n')
        result=self.shell('read_packages "$2"',package_list,check=False)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('无效软件包名',result.stderr)

    def test_manifest_targets_exist_and_excludes_empty_yazi(self):
        destinations=set()
        for line in (ROOT/'install/links.txt').read_text().splitlines():
            if not line or line.startswith('#'):continue
            source,target=line.split('|')
            self.assertTrue((ROOT/source).exists(),source)
            self.assertNotIn(target,destinations)
            destinations.add(target)
            self.assertNotEqual(source,'config/yazi')
            self.assertNotEqual(target,'.config/hypr')
            self.assertNotIn(target,('.config/hypr/profiles/hardware.lua','.config/hypr/profiles/user.lua'))


if __name__=='__main__':
    unittest.main()
