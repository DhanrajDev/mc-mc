import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import zipfile

import mod_installers as mods
from launcher_core import installed_versions


class ModInstallerTests(unittest.TestCase):
    def test_iris_without_content_length_creates_registered_selectable_version(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as package:
            for mod in ('iris', 'sodium'):
                data = io.BytesIO()
                with zipfile.ZipFile(data, 'w') as jar:
                    jar.writestr('fabric.mod.json', json.dumps({'id': mod, 'version': 'test'}))
                package.writestr(mod + '.jar', data.getvalue())
        response = MagicMock()
        response.headers = {}  # The exact condition rejected by the standalone installer.
        response.iter_content.return_value = [payload.getvalue()]
        session = MagicMock()
        session.get.return_value.__enter__.return_value = response
        metadata = [
            {'assets': [{'name': 'Iris-Sodium-26.3.zip', 'browser_download_url': 'https://example.invalid/package'}]},
            [{'loader': {'stable': True, 'version': '0.20.1'}}],
            {'id': 'fabric-loader-0.20.1-26.3', 'inheritsFrom': '26.3', 'arguments': {'jvm': []}},
        ]
        with tempfile.TemporaryDirectory() as folder, patch.object(mods, 'session') as factory, patch.object(mods, 'get_json', side_effect=metadata), patch.object(mods.mc.install, 'install_minecraft_version'):
            factory.return_value.__enter__.return_value = session
            result = mods.install_iris('26.3', folder)
            self.assertIn(result, installed_versions(folder))
            profiles = json.loads((Path(folder) / 'launcher_profiles.json').read_text())['profiles']
            self.assertEqual(profiles['craftline-' + result]['lastVersionId'], result)
            data = json.loads((Path(folder) / 'versions' / result / (result + '.json')).read_text())
            self.assertIn('-Dfabric.modsFolder=' + str(Path(folder) / 'iris-reserved/26.3'), data['arguments']['jvm'])

    def test_optifine_rejects_unrelated_jar_before_installing(self):
        with tempfile.TemporaryDirectory() as folder:
            jar = Path(folder) / 'not-optifine.jar'
            with zipfile.ZipFile(jar, 'w') as stream:
                stream.writestr('example.txt', 'not an installer')
            with patch.object(mods.mc.install, 'install_minecraft_version') as install:
                with self.assertRaisesRegex(ValueError, 'official OptiFine'):
                    mods.install_optifine(jar, '26.3', folder)
                install.assert_not_called()


if __name__ == '__main__':
    unittest.main()
