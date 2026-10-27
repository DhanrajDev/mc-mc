import json
from pathlib import Path
import tempfile
import unittest
from launcher_core import Settings, local_options, register_version, installed_versions


class PersistenceTests(unittest.TestCase):
    def test_profile_survives_restart_without_tokens(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Settings(folder)
            first.active.update(username='SamePlayer', uuid=local_options('SamePlayer')['uuid'], version='iris-example', ram='4', server='play.example.org', access_token='never-save-this')
            first.save()
            second = Settings(folder)
            self.assertEqual(second.active['username'], 'SamePlayer')
            self.assertEqual(second.active['uuid'], first.active['uuid'])
            self.assertEqual(second.active['version'], 'iris-example')
            self.assertEqual(second.active['server'], 'play.example.org')
            self.assertNotIn('never-save-this', first.path.read_text())

    def test_first_install_creates_profiles_and_preserves_existing_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            game = Path(folder) / 'fresh .minecraft'
            register_version(game, '26.3')
            file = game / 'launcher_profiles.json'
            data = json.loads(file.read_text())
            data['profiles']['official'] = {'name': 'Keep me'}
            file.write_text(json.dumps(data))
            register_version(game, 'iris-new')
            self.assertEqual(json.loads(file.read_text())['profiles']['official']['name'], 'Keep me')
            self.assertEqual(json.loads(file.read_text())['profiles']['craftline-iris-new']['lastVersionId'], 'iris-new')

    def test_corrupt_config_keeps_recovery_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Settings(folder)
            first.path.parent.mkdir(parents=True)
            first.path.write_text('broken JSON')
            restored = Settings(folder)
            self.assertTrue(restored.notice)
            self.assertEqual(next(first.path.parent.glob('settings-recovery-*')).read_text(), 'broken JSON')

    def test_installed_profiles_require_valid_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'versions' / 'iris-new' / 'iris-new.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"id":"iris-new","inheritsFrom":"26.3"}')
            self.assertIn('iris-new', installed_versions(folder))
            path.write_text('incomplete')
            self.assertNotIn('iris-new', installed_versions(folder))


if __name__ == '__main__':
    unittest.main()
