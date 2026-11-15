"""Tests reproductibles sans toucher à une configuration Codex réelle."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'atelier_codex.py'

class AtelierCodexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        (self.home / '.codex').mkdir()
        self.conf = self.home / '.codex/config.toml'
        self.conf.write_text('[desktop]\ntheme = "dark"\n\n[mcp_servers.node_repl.env]\nFAKE_SECRET = "keep-me"\n')
        self.env = dict(os.environ, HOME=str(self.home))
        self.args = ['--atelier', str(self.home / 'Arche/atelier-ael'), '--partage', str(self.home / 'Arche/partage-claude')]

    def run_tool(self, *args, ok=True):
        proc = subprocess.run([sys.executable, str(TOOL), *args], env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        else:
            self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn('keep-me', proc.stdout + proc.stderr)
        return proc

    def declare_copy(self):
        atelier = self.home / 'Arche/atelier-ael'
        atelier.mkdir(parents=True, exist_ok=True)
        (atelier / 'SAUVEGARDE.txt').write_text('Copie factice\n')

    def test_snail_bouder_without_evidence(self):
        self.run_tool('install', *self.args, '--apply')
        result = self.run_tool('check', *self.args, ok=False)
        self.assertIn('Ayez une autre copie', result.stdout)
        self.assertIn('ABSENTE', result.stdout)

    def test_snail_declaration_without_reading_contents(self):
        self.run_tool('install', *self.args, '--apply')
        atelier = self.home / 'Arche/atelier-ael'
        token = 'DONT-PRINT-THIS-PRIVATE-BACKUP-LOCATION'
        (atelier / 'SAUVEGARDE.txt').write_text(token)
        result = self.run_tool('check', *self.args)
        self.assertIn('DÉCLARÉE', result.stdout)
        self.assertNotIn(token, result.stdout)

    def test_snail_git_in_parent_not_home(self):
        self.run_tool('install', *self.args, '--apply')
        (self.home / '.git').mkdir()
        self.run_tool('check', *self.args, ok=False)
        (self.home / 'Arche/.git').mkdir()
        result = self.run_tool('check', *self.args)
        self.assertIn('GIT', result.stdout)

    def test_dry_run_no_write(self):
        before = self.conf.read_bytes()
        self.run_tool('install', *self.args)
        self.assertEqual(self.conf.read_bytes(), before)
        self.assertFalse((self.home / 'Arche/atelier-ael').exists())

    def test_install_idempotence_and_rollback(self):
        original = self.conf.read_bytes()
        self.run_tool('install', *self.args, '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertEqual(data['sandbox_mode'], 'workspace-write')
        self.assertEqual(data['approval_policy'], 'on-request')
        self.assertEqual(data['desktop']['theme'], 'dark')
        self.assertEqual(data['mcp_servers']['node_repl']['env']['FAKE_SECRET'], 'keep-me')
        self.assertFalse(data['sandbox_workspace_write']['network_access'])
        self.declare_copy()
        self.run_tool('check', *self.args)
        backup = list((self.home / '.codex').glob('config.toml.atelier-backup-*'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_bytes(), original)
        self.run_tool('install', *self.args, '--apply')
        self.assertEqual(len(list((self.home / '.codex').glob('config.toml.atelier-backup-*'))), 1)
        self.run_tool('rollback', '--backup', backup[0].name, '--apply')
        self.assertEqual(self.conf.read_bytes(), original)

    def test_existing_globals_and_section(self):
        self.conf.write_text('sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n[desktop]\ntheme = "dark"\n[sandbox_workspace_write]\nnetwork_access = false\n')
        self.run_tool('install', *self.args, '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertEqual(data['sandbox_workspace_write']['writable_roots'], [str(self.home / 'Arche/atelier-ael'),str(self.home / 'Arche/partage-claude')])

    def test_conflict_refused_with_no_write(self):
        self.conf.write_text('sandbox_mode = "danger-full-access"\n[desktop]\nfoo = 1\n')
        before = self.conf.read_bytes()
        self.run_tool('install', *self.args, '--apply', ok=False)
        self.assertEqual(self.conf.read_bytes(), before)

    def test_section_conflict_refused(self):
        self.conf.write_text('[sandbox_workspace_write]\nnetwork_access = true\n')
        before = self.conf.read_bytes()
        self.run_tool('install', *self.args, '--apply', ok=False)
        self.assertEqual(self.conf.read_bytes(), before)

    def test_reject_home_root(self):
        self.run_tool('install', '--atelier', str(self.home), '--apply', ok=False)

    # --- contre-audit Silus ---
    def test_reject_hidden_home_dirs(self):
        for d in ('.codex', '.config', '.local/bin', '.ssh'):
            before = self.conf.read_bytes()
            self.run_tool('install', '--atelier', str(self.home / d), '--apply', ok=False)
            self.assertEqual(self.conf.read_bytes(), before, d)

    def test_dotdot_is_normalized_before_checks(self):
        (self.home / 'Arche/x').mkdir(parents=True)
        self.run_tool('install', '--atelier', str(self.home / 'Arche/x/..'), '--apply', ok=False)
        self.run_tool('install', '--atelier', str(self.home / '.codex/../Arche/at'), '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertEqual(data['sandbox_workspace_write']['writable_roots'], [str((self.home / 'Arche/at').resolve())])

    def test_missing_final_newline_existing_section(self):
        # TOML valide, section deja presente, une seule cle absente et pas de LF final.
        self.conf.write_text('sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n[sandbox_workspace_write]\nnetwork_access = false')
        self.run_tool('install', *self.args, '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertIs(data['sandbox_workspace_write']['network_access'], False)
        self.assertEqual(data['sandbox_workspace_write']['writable_roots'], [str(self.home / 'Arche/atelier-ael'), str(self.home / 'Arche/partage-claude')])
        self.declare_copy()
        self.run_tool('check', *self.args)

    def test_missing_final_newline_existing_section_other_key(self):
        self.conf.write_text('sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n[sandbox_workspace_write]\nwritable_roots = ["' + str(self.home / 'Arche/atelier-ael') + '"]')
        self.run_tool('install', '--atelier', str(self.home / 'Arche/atelier-ael'), '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertIs(data['sandbox_workspace_write']['network_access'], False)

    def test_emoji_path_serialization(self):
        emoji = self.home / 'Arche/atelier-🦊'
        self.run_tool('install', '--atelier', str(emoji), '--apply')
        data = tomllib.loads(self.conf.read_text())
        self.assertEqual(data['sandbox_workspace_write']['writable_roots'], [str(emoji)])
        (emoji / 'SAUVEGARDE.txt').write_text('Copie de test factice\n')
        self.run_tool('check', '--atelier', str(emoji))

if __name__ == '__main__':
    unittest.main()
