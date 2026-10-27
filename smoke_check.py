"""Packaged-app first-run checks in a disposable game folder."""
from pathlib import Path
import json
import tempfile
import time
import tkinter as tk


def run(report):
    import launcher_gui as app
    from launcher_core import Settings, register_version
    original_game = app.GAME
    original_versions = app.mc.utils.get_version_list
    with tempfile.TemporaryDirectory(prefix='craftline-first-run-') as folder:
        app.GAME = Path(folder) / '.minecraft'
        app.mc.utils.get_version_list = lambda: [{'id': '26.3', 'type': 'release'}]
        try:
            root = tk.Tk()
            root.withdraw()
            ui = app.Launcher(root)
            ui.name.set('SamePlayer')
            ui.server.set('play.example.org')
            ui.ram.set('4')
            version = 'iris-fabric-loader-smoke-26.3'
            path = app.GAME / 'versions' / version / (version + '.json')
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'id': version, 'inheritsFrom': '26.3'}))
            register_version(app.GAME, version)
            ui.events.put(('installed', version))
            until = time.monotonic() + .35
            while time.monotonic() < until:
                root.update()
                time.sleep(.01)
            assert ui.version.get() == version
            assert version in ui.versions['values']
            font = ui.font_family
            identity = ui.settings.active['uuid']
            ui.close()
            root = tk.Tk()
            root.withdraw()
            restored = app.Launcher(root)
            root.update()
            assert restored.name.get() == 'SamePlayer'
            assert restored.version.get() == version
            assert restored.server.get() == 'play.example.org'
            assert restored.settings.active['uuid'] == identity
            assert (app.GAME / 'launcher_profiles.json').exists()
            assert font == 'Manrope', 'Bundled font did not load'
            restored.close()
            Path(report).write_text(json.dumps({'passed': True, 'font': font, 'first_run_metadata': True,
                'username_uuid_server_persisted': True, 'installed_version_visible_selected_persisted': True}, indent=2))
        finally:
            app.GAME = original_game
            app.mc.utils.get_version_list = original_versions
