# Build with: .venv\Scripts\python.exe -m PyInstaller Craftline.spec --noconfirm
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('minecraft_launcher_lib')
datas += [('assets', 'assets'), ('README.md', '.'), ('THIRD_PARTY_NOTICES.md', '.')]
a = Analysis(['launcher.py'], pathex=[], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Craftline',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, icon='assets/craftline.ico', version='version_info.txt')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Craftline')
