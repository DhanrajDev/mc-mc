"""Focused offline checks; never downloads or starts Minecraft."""
import time
import tempfile
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch, MagicMock
import launcher_gui as gui


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.patches = [
            patch.object(gui.mc.utils, 'get_version_list', return_value=[]),
            patch.object(gui.messagebox, 'showerror'),
        ]
        for p in self.patches:
            p.start()
        self.app = gui.Launcher(self.root)

    def tearDown(self):
        self.app.close()
        for p in reversed(self.patches):
            p.stop()

    def drain(self):
        deadline = time.monotonic() + 3
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.01)
        self.assertFalse(self.app.busy)

    def test_requires_online_account_before_install(self):
        with patch.object(gui.mc.install, 'install_minecraft_version') as install:
            self.app.launch()
            install.assert_not_called()
            gui.messagebox.showerror.assert_called_once()

    def test_local_launch_callbacks_and_command(self):
        self.app.mode.set('Local / no authentication')
        process = MagicMock()
        process.wait.return_value = 0
        def install(version, directory, callback):
            callback['setMax'](10)
            callback['setProgress'](5)
        with patch.object(gui.mc.install, 'install_minecraft_version', side_effect=install), patch.object(gui.mc.command, 'get_minecraft_command', return_value=['java', 'example']) as command, patch.object(gui.subprocess, 'Popen', return_value=process) as popen, patch.object(gui.Path, 'open', unittest.mock.mock_open()):
            self.app.launch()
            self.drain()
            options = command.call_args.args[2]
            self.assertEqual(options['token'], '')
            self.assertEqual(options['jvmArguments'], ['-Xms512M', '-Xmx2G'])
            self.assertEqual(self.app.progress['value'], 5)
            popen.assert_called_once()

    def test_failed_install_reenables_play(self):
        self.app.mode.set('Local / no authentication')
        with patch.object(gui.mc.install, 'install_minecraft_version', side_effect=ConnectionError('private response')), patch.object(gui.subprocess, 'Popen') as popen:
            self.app.launch()
            self.drain()
            popen.assert_not_called()
            self.assertNotIn('private response', self.app.status.get())

    def test_pkce_rejects_wrong_state(self):
        with self.assertRaises(Exception):
            gui.mc.microsoft_account.parse_auth_code_url(gui.REDIRECT + '?code=example&state=wrong', 'expected')

    def test_online_uses_signed_in_profile(self):
        self.app.account = {'name': 'Example', 'id': 'profile-id', 'access_token': 'test-token'}
        process = MagicMock()
        process.wait.return_value = 0
        with patch.object(gui.mc.install, 'install_minecraft_version'), patch.object(gui.mc.command, 'get_minecraft_command', return_value=['java']) as command, patch.object(gui.subprocess, 'Popen', return_value=process), patch.object(gui.Path, 'open', unittest.mock.mock_open()):
            self.app.launch()
            self.drain()
            self.assertEqual(command.call_args.args[2]['token'], 'test-token')
            self.assertEqual(command.call_args.args[2]['username'], 'Example')

    def test_installed_optifine_listed_when_manifest_unavailable(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(gui, 'GAME', Path(folder)), patch.object(gui.mc.utils, 'get_version_list', side_effect=ConnectionError):
            version = '1.20.1-OptiFine_HD_U_I6'
            profile = Path(folder) / 'versions' / version / (version + '.json')
            profile.parent.mkdir(parents=True)
            profile.write_text('{}')
            self.app.load_versions()
            self.app.poll()
            self.assertIn(version, self.app.versions['values'])

    def test_optifine_installer_uses_game_java_and_selects_new_profile(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(gui, 'GAME', Path(folder)):
            version = '1.20.1-OptiFine_HD_U_I6'
            def installer(command, **kwargs):
                self.assertEqual(command[0], 'bundled-java')
                self.assertEqual(command[1], '-jar')
                self.assertEqual(kwargs['cwd'], Path(folder))
                profile = Path(folder) / 'versions' / version / (version + '.json')
                profile.parent.mkdir(parents=True)
                profile.write_text('{}')
                return MagicMock(returncode=0)
            with patch.object(gui.filedialog, 'askopenfilename', return_value=str(Path(folder) / 'OptiFine.jar')), patch.object(gui.messagebox, 'showinfo'), patch.object(gui.mc.install, 'install_minecraft_version'), patch.object(gui.mc.command, 'get_minecraft_command', return_value=['bundled-java']), patch.object(gui.subprocess, 'run', side_effect=installer), patch.object(gui, 'BASE', Path(folder)):
                self.app.install_optifine()
                self.drain()
                self.assertEqual(self.app.version.get(), version)
                self.assertTrue((Path(folder) / 'launcher_profiles.json').exists())


if __name__ == '__main__':
    unittest.main()
