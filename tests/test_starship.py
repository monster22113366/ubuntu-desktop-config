"""Render the real prompt against isolated repositories and environments."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

CONFIG = Path(__file__).resolve().parents[1] / 'config/starship/starship.toml'


@unittest.skipUnless(shutil.which('starship'), 'starship is required')
class StarshipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='prompt-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if k in ('PATH', 'USER', 'LOGNAME', 'LANG', 'TERM')}
        (self.root / 'home').mkdir()
        self.env.update(HOME=str(self.root / 'home'), STARSHIP_CONFIG=str(CONFIG),
                        STARSHIP_SHELL='bash', TERM='xterm-256color')

    def run_cmd(self, args, cwd=None, env=None):
        return subprocess.run(args, cwd=cwd or self.root,
                              env=env or self.env, text=True,
                              capture_output=True, check=True, timeout=15)

    def prompt(self, cwd=None, extra=None, args=()):
        cwd = cwd or self.root
        env = dict(self.env, PWD=str(cwd), **(extra or {}))
        result = self.run_cmd(['starship', 'prompt', *args], cwd, env)
        self.assertEqual(result.stderr, '')
        text = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        return text.replace('\\[', '').replace('\\]', '').replace('\\$', '$').strip('\n')

    def test_full_path_special_characters_and_narrow_terminal(self):
        folder = self.root / '中文 folder' / '[test](x)$' / 'deep'
        folder.mkdir(parents=True)
        for width in ('40', '160'):
            result = self.prompt(folder, args=('--terminal-width', width))
            self.assertIn(str(folder), result)
            self.assertEqual(len(result.splitlines()), 3)
            self.assertTrue(result.endswith('> '))

    def test_real_venv_activation_and_deactivation(self):
        venv = self.root / 'demo-env'
        self.run_cmd(['python3', '-m', 'venv', '--without-pip', str(venv)])
        result = self.run_cmd(['bash', '--noprofile', '--norc', '-c',
                              'source "$1/bin/activate"; starship prompt; '
                              'deactivate; starship prompt', 'bash', str(venv)])
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.count('(demo-env)'), 1)

    def test_conda_base_and_named_environment(self):
        for name in ('base', 'data-science'):
            self.assertIn(f'({name})', self.prompt(extra={'CONDA_DEFAULT_ENV': name}))

    def test_failed_command_jobs_and_duration(self):
        result = self.prompt(args=('--status', '1', '--jobs', '2', '--cmd-duration', '3000'))
        self.assertIn('took 3s', result.splitlines()[0])
        self.assertTrue(result.endswith('> '))
        self.assertNotEqual(result, self.prompt())

    def test_git_branch_dirty_detached_and_merge(self):
        repo = self.root / 'repo'
        repo.mkdir()
        def git(*args):
            return self.run_cmd(['git', *args], repo)
        git('init', '-b', 'main')
        git('config', 'user.name', 'Prompt Test')
        git('config', 'user.email', 'prompt@example.invalid')
        (repo / 'file').write_text('initial\n')
        git('add', 'file')
        git('commit', '-m', 'initial')
        self.assertIn('⎇ main', self.prompt(repo))
        self.assertIn(str(repo), self.prompt(repo))
        (repo / 'untracked').touch()
        self.assertIn('?1', self.prompt(repo))
        git('checkout', '--detach')
        self.assertIn(git('rev-parse', '--short=7', 'HEAD').stdout.strip(), self.prompt(repo))
        (repo / '.git' / 'MERGE_HEAD').write_text(git('rev-parse', 'HEAD').stdout)
        self.assertIn('MERGING', self.prompt(repo))
